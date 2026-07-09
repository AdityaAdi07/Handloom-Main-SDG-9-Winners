# Handloom-Twin — Algorithms

This document formalizes the five core algorithms that power the Handloom-Twin digital twin system. Each algorithm is presented as pseudocode followed by a plain-English explanation of its purpose, design rationale, and where it fits in the project.

---

## Table of Contents

1. [Algorithm 1 — IoT Telemetry Ingestion & FIWARE Pipeline](#algorithm-1--iot-telemetry-ingestion--fiware-pipeline)
2. [Algorithm 2 — Random Forest Training Pipeline](#algorithm-2--random-forest-training-pipeline)
3. [Algorithm 3 — Composite Anomaly Score & Threshold Detection](#algorithm-3--composite-anomaly-score--threshold-detection)
4. [Algorithm 4 — Sandbox Parameter Sweep Optimizer](#algorithm-4--sandbox-parameter-sweep-optimizer)
5. [Algorithm 5 — Dual-Channel Alert Dispatch](#algorithm-5--dual-channel-alert-dispatch)

---

## Algorithm 1 — IoT Telemetry Ingestion & FIWARE Pipeline

```
Algorithm 1: IoT Telemetry Ingestion and FIWARE Pipeline
─────────────────────────────────────────────────────────
Input : Raw sensor readings from ESP32  (every T = 10 s)
Output: Context entity persisted in MongoDB; ML predictions dispatched

 1: loop every T seconds do
 2:   Read channels: tension, vibration, speed, temperature, humidity
 3:   if any channel = NULL then
 4:     Apply forward-fill imputation from t-1 reading
 5:   end if
 6:   Enrich reading with timestamp, loom_id, session metadata
 7:   POST NGSI-v2 entity update  ->  FIWARE Orion Context Broker
 8:   Orion notifies Cygnus subscriber
 9:   Cygnus writes timestamped record  ->  MongoDB historical collection
10:   Compute first-order differences:
         Dvibration = v(t) - v(t-1)
         Dtension   = T(t) - T(t-1)
11:   Compute composite anomaly score  (see Algorithm 3)
12:   Send feature vector x to FastAPI /predict endpoint
13:   Receive: quality_grade, defect_rate, fault_class, maintenance_flag
14:   if fault_class != Normal  OR  A(t) > threshold then
15:     Invoke Algorithm 5  (Dual-Channel Alert Dispatch)
16:   end if
17: end loop
```

### Explanation

This algorithm is the heartbeat of the entire system. Every 10 seconds, the ESP32 microcontroller reads five sensor channels — warp/weft tension, frame vibration, weaving speed, temperature, and humidity — and kicks off a pipeline that spans hardware, middleware, and ML inference.

The forward-fill imputation step (lines 3–5) handles the 0.042% null rate observed in real loom data, where a loose wire or transient wireless dropout can produce a missing reading. Dropping these records entirely would break time-series continuity; filling from the previous value preserves the temporal structure without introducing fake spikes.

FIWARE Orion acts as the single source of truth for the current loom state. By following the NGSI-v2 standard (line 7), the system stays interoperable — any dashboard, third-party analytics tool, or additional loom node can subscribe to the same context without custom integration work. Cygnus then fans the update out to MongoDB (line 9), giving the system a full 30-day queryable history at no extra code cost.

The temporal difference features computed in line 10 (Dvibration, Dtension) are fed directly into the ML models. These rate-of-change values are more informative for fault detection than absolute readings — a loose bearing shows up as a sharp Dvibration spike even when the absolute reading is still within normal range.

**Files:** `Fiware/bckend/` relay · `loom_simulation.py` streamer · ESP32 firmware sampling loop

---

## Algorithm 2 — Random Forest Training Pipeline

```
Algorithm 2: Random Forest Training Pipeline
─────────────────────────────────────────────
Input : Raw dataset D  (777,600 records, 13 channels, 3 looms x 30 days)
Output: Four trained RF models {M_q, M_d, M_f, M_m}

 1: Remove NULL records via forward-fill; drop OFF-state rows
      -> D_clean  (702,033 ON-state records, 0.042% null rate removed)
 2: Derive engineered features:
      Dvibration,  Dtension,  A(t),  pattern_complexity_index (5 ordinal levels)
 3: Draw stratified subsample S in D_clean,  |S| = 120,000
 4: Split S  ->  Train (80%) / Validation (20%)  with stratification on target
 5: for each model M in {Quality, Defect, Fault, Maintenance} do
 6:   Define feature vector x_M and target y_M
 7:   if M = FaultClassifier then
 8:     Set class_weight = inverse_class_frequency    # 0.28% positive class
 9:   end if
10:   Grid G = {n_est} x {max_depth} x {min_split}
            = {50,100,150,200,250} x {6,9,12,15} x {2,5,10}   # 75 configs each
11:   for each (n_est, max_depth, min_split) in G do
12:     Train RF with 5-fold stratified cross-validation on Train split
13:     Record mean metric: Accuracy (classifiers)  or  RMSE (regressor)
14:   end for
15:   best_params_M = argmax over G of Metric(G)
16:   Retrain M with best_params_M on full Train split
17:   Serialize M  ->  disk as .pkl artifact
18: end for
19: return {M_q, M_d, M_f, M_m}

Optimized hyperparameters:
  Quality Classifier     -> n_est=200, max_depth=15, min_split=5
  Defect Regressor       -> n_est=250, max_depth=15, min_split=2
  Fault Classifier       -> n_est=150, max_depth=12, min_split=5
  Maintenance Classifier -> n_est=100, max_depth= 6, min_split=2
```

### Explanation

Rather than training a single monolithic model, Handloom-Twin deploys four specialized Random Forest models, each with its own feature set and target. This keeps each model small, interpretable, and easy to retrain independently when new data arrives.

The dataset starts at 777,600 records but 9.7% of those are OFF-state records (idle loom periods between runs). These are dropped in line 1 because training on idle-state data dilutes the decision boundaries for active weaving conditions. What remains — 702,033 ON-state records — is what actually matters for production monitoring.

The 120,000-record stratified subsample (line 3) was chosen empirically: validation accuracy varied by less than 0.3% from the full-dataset baseline, while training time dropped by 6x. Stratification ensures that rare fault events (0.28% of records) appear proportionally in both train and validation splits.

The grid search covers 75 hyperparameter configurations per model (line 10). Depth 15 for the Quality and Defect models captures the nonlinear coupling between environmental and mechanical features — for example, the interaction between high humidity and low tension that causes a specific type of weft skip. The Fault Classifier uses depth 12 with inverse-frequency class weights (line 8) because the positive fault class is extremely rare and a naive model would learn to always predict "Normal." The Maintenance Classifier needs only depth 6 because the composite anomaly score alone carries 50% of the predictive signal.

**Results:** Quality 95.4% acc · Fault 96.8% acc · Defect RMSE 0.041 (50% lower than SVR baseline)

---

## Algorithm 3 — Composite Anomaly Score & Threshold Detection

```
Algorithm 3: Composite Anomaly Detection
─────────────────────────────────────────
Input : Sensor reading at time t:  vibration v(t),  temperature T(t),  speed s(t)
Output: Anomaly flag alpha in {0,1},  anomaly score A(t) in [0,1]

 1: Compute min-max normalized features over rolling 30-day window W:
       v_norm(t)  = ( v(t)  - v_min  ) / ( v_max  - v_min  )
       DT_norm(t) = ( |T(t)-T(t-1)| - DT_min ) / ( DT_max - DT_min )
       Ds_norm(t) = ( |s(t)-s(t-1)| - Ds_min ) / ( Ds_max - Ds_min )
 2: Compute weighted composite score:
       A(t) = w_v * v_norm(t)  +  w_t * DT_norm(t)  +  w_s * Ds_norm(t)
            ─────────────────────────────────────────────────────────────
              w_v = 0.50  (vibration — Pearson r = +0.25 with fault events)
              w_t = 0.30  (temperature rate-of-change)
              w_s = 0.20  (speed deviation)
 3: if A(t) > tau  {tau = 0.22}  then
 4:   Set alpha = 1                         # fault condition
 5:   Query Maintenance Classifier M_m with feature vector x_m
 6:   Append event (timestamp, A(t), loom_id)  ->  MongoDB fault_log
 7: else
 8:   Set alpha = 0                         # normal operation
 9: end if
10: return alpha,  A(t)

Empirical score distributions (30-day trial):
  Normal -> mean = 0.08,  std = 0.06
  Fault  -> mean = 0.41,  std = 0.09
  Threshold tau = 0.22  (midpoint of the two means)
  Overlap zone [0.17, 0.27] covers < 2% of all observations
```

### Explanation

The composite anomaly score A(t) condenses three separate sensor channels into a single number that a dashboard gauge, an alert rule, or the Maintenance Classifier can act on directly. The key design decision is the weighting: vibration gets the largest weight (0.50) because it shows the strongest empirical correlation with imminent faults (Pearson r = +0.25 measured across the full 30-day dataset). Temperature rate-of-change (0.30) captures overheating events that develop gradually, while speed deviation (0.20) catches motor-load anomalies.

Each channel is min-max normalized over a rolling 30-day window rather than the full dataset. This makes the score season-aware — during Monsoon, the "normal" vibration baseline is lower, so the same absolute reading maps to a different normalized value compared to Dry/Winter when baselines shift upward. Without rolling normalization, a Dry/Winter reading might not trigger the same threshold that correctly flagged the same physical condition during Pre-Monsoon.

The threshold tau = 0.22 sits at the midpoint between the Normal mean (0.08) and the Fault mean (0.41). The two distributions are well-separated enough that a simple scalar threshold outperforms a probabilistic classifier here — the overlap zone covers fewer than 2% of observations, giving a very low equal-error rate. This keeps the inference path fast and explainable: the operator can see the A(t) gauge on the dashboard and understand how close the loom is to the alarm threshold.

**Files:** `loom_simulation.py` anomaly score computation · FastAPI inference engine · MongoDB `fault_log` collection

---

## Algorithm 4 — Sandbox Parameter Sweep Optimizer

```
Algorithm 4: Sandbox Parameter Sweep Optimizer
───────────────────────────────────────────────
Input : Live loom state x_live,  yarn_type y,
        parameter range [theta_min, theta_max],  step size delta
Output: Optimal parameter theta*,  predicted defect rate D_hat(theta*),  95% CI

 1: Clone live FIWARE context  ->  shadow state x_s
      # isolated /sandbox REST namespace; separate MongoDB collection
 2: Initialize result buffer R = []
 3: for theta = theta_min  to  theta_max  step delta  do
 4:   Update  x_s.tension = theta    # (or speed / temperature as specified)
 5:   Construct feature vector x_feat from {x_s, env_sensors, yarn_type}
 6:   Predict  D_hat(theta) = M_d(x_feat)      # Defect Regressor forward pass
 7:   Compute 95% CI from K=250 tree leaf distributions of M_d
 8:   Append  (theta,  D_hat(theta),  CI)  ->  R
 9: end for
10: Fit polynomial regression  p(theta)  to R  using least-squares
11: theta* = argmin over [theta_min, theta_max] of  p(theta)
12: if operator approves theta* then
13:   PATCH production FIWARE entity with theta*   # live /orion namespace
14: end if
15: return theta*,  D_hat(theta*),  CI

Results from the 30-day trial:
  Cotton -> theta* = 72.7 N  (manual preset 60.0 N  ->  24.5% defect reduction)
  Silk   -> theta* = 48.8 N  (manual preset 45.0 N  ->  23.8% defect reduction)
  Sweep: 200 tension configurations per run,  completed in < 2 s  (2-vCPU VPS)
```

### Explanation

The Sandbox is the core USP of Handloom-Twin. The fundamental problem it solves is that weavers set parameters — tension in particular — by feel and experience, but feel is calibrated to average conditions, not the current day's temperature, humidity, and yarn batch. A weaver who has run Cotton at 60 N for years does not know that 72.7 N would cut defects by 24% under today's specific humidity without a tool like this.

The isolation architecture (line 1) is what makes this safe. The sandbox operates on a cloned in-memory loom state under a separate `/sandbox` REST namespace and a separate MongoDB collection. None of the sweep operations touch the live FIWARE entity or the production loom. The operator only sees a recommendation; the production state changes only if they explicitly approve it (line 12).

The sweep queries the Defect Regressor at each 0.5 N tension increment across the safe operating envelope (line 6). Because the Random Forest ensemble has 250 trees, each query also produces a 95% confidence interval from the spread of leaf-node predictions (line 7). This means the optimizer does not just return a point estimate — it tells the operator how confident the model is at the optimum. A narrow CI at theta* means the recommendation is robust; a wide CI would prompt a small physical test first.

The polynomial fit (line 10) smooths out noise in the Defect Regressor's discrete tree predictions and gives a differentiable response surface from which the true minimum can be found cleanly. The result is a tension-vs-defect curve with 95% confidence bands — exactly the kind of output that makes the recommendation trustworthy to a non-ML-expert weaver.

**Files:** `sandbox/core/ParameterEngine.js` · `sandbox/core/SandboxState.js` · FastAPI `/sandbox/predict` route

---

## Algorithm 5 — Dual-Channel Alert Dispatch

```
Algorithm 5: Dual-Channel Alert Dispatch
─────────────────────────────────────────
Input : Live sensor reading x(t),  anomaly flag alpha,  fault_class f
Output: Local buzzer/TFT fired (<=120 ms),  SMTP email delivered (<=1.8 s)

# PATH A — ESP32 Interrupt Service Routine (outside the 10 s sampling loop)
 1: if tension(t) < T_min  {T_min = 10 N}  then
 2:   GPIO -> Buzzer ON                       # latency: 85 ms
 3:   Write "THREAD BREAK" alert to TFT display
 4:   fault_type = "Thread Break"
 5: else if temperature(t) > T_max  {T_max = 45 C}  then
 6:   GPIO -> Buzzer ON                       # latency: 120 ms
 7:   Write "OVERHEAT" to TFT
 8:   Throttle loom speed by 30%  via PWM output
 9:   fault_type = "Motor Overheat"
10: else if alpha = 1  (from Algorithm 3)  then
11:   fault_type = "Pre-fault Vibration"     # ~10 min advance warning
12: end if

# PATH B — Async SMTP  (parallel; does NOT block PATH A)
13: Compose email payload:
      { loom_id, fault_type, timestamp, sensor_snapshot x(t) }
14: Flask relay: enrich payload  ->  POST to SMTP server          (+120 ms)
15: SMTP handshake                                                (+400 ms)
16: Mail server delivery                                          (+~1.28 s)
17: Total email latency <= 1.8 s
      # within the 5 s limit in Indian textile machinery safety guidelines

18: Log event  ->  MongoDB  fault_log  collection
```

### Explanation

Alert systems in industrial settings fail in two typical ways: they are either too slow to be actionable, or they flood operators with so many notifications that real alerts get ignored. This algorithm addresses both by running two completely independent paths simultaneously.

Path A (lines 1–12) runs inside the ESP32's interrupt service routine, completely outside the normal 10-second sensor sampling loop. This means a tension drop below 10 N fires the GPIO buzzer in 85 ms regardless of where the sampling loop is in its cycle — there is no queuing, no network round-trip, and no software overhead. The buzzer is the weaver's immediate, physical cue to stop the loom. The TFT display reinforces it with a human-readable fault label. For motor overheat specifically, the ESP32 also issues a PWM command to throttle loom speed by 30% automatically — the system acts before the weaver has even fully registered the alert.

Path B (lines 13–17) handles the SMTP notification asynchronously via the Flask relay. The 1.8-second total latency breaks down as: Flask enrichment (120 ms) + SMTP handshake (400 ms) + mail server delivery (~1.28 s). This path is for supervisors, maintenance staff, or factory managers who are not physically at the loom. Running it asynchronously ensures it never delays the buzzer in Path A — the two paths share no blocking resource.

The pre-fault vibration case (line 10) is the most valuable alert type. It is triggered by Algorithm 3's anomaly score crossing tau = 0.22 during the Phase 2 vibration escalation window — roughly 10 minutes before a physical fault occurs. This lead time is enough for the weaver to slow the loom, inspect the mechanical linkage, and prevent the fault entirely, rather than reacting after thread breakage has already damaged fabric.

**Latency profile:** Local buzzer 85 ms · TFT display 120 ms · SMTP email 1.8 s · Pre-fault advance ~10 min  
**Files:** ESP32 ISR firmware · `Fiware/bckend/` Flask relay · MongoDB `fault_log`

---

*All algorithms are implemented across the Handloom-Twin codebase and validated against the 30-day, 777,600-record dataset from R V Handlooms & Powerlooms, Yelahanka, Bangalore.*
