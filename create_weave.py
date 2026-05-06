import os
import re

base_path = r"c:\Users\sushm\OneDrive\Desktop\llm_engineering-main\Handloom-Twin\Fiware\frntend"
with open(os.path.join(base_path, "ind2.html"), "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update twin state definition
text = text.replace(
    "pattern_id: null\n};",
    "pattern_id: null,\n  pattern_matrix: [[1,0,1],[0,1,0],[1,1,0]]\n};"
)

# 2. Update FIWARE fetching
text = text.replace(
    "twin.pattern_id = data.process_pattern_id?.value ?? null;",
    "twin.pattern_id = data.process_pattern_id?.value ?? null;\n    twin.pattern_matrix = data.process_pattern_matrix?.value ?? [[1,0,1],[0,1,0],[1,1,0]];"
)

# 3. Replace Animation Loop
anim_code = """// ═══════════════════════════════════════════════
//  TRUE WEAVING ANIMATION LOOP
// ═══════════════════════════════════════════════
const clock=new THREE.Clock();
let frameCount=0;

// Remove static weft rows
fabricGroup.children.filter(m => m.geometry.type === 'CylinderGeometry').forEach(m => {
    fabricGroup.remove(m);
    m.geometry.dispose();
});
fabricMesh.material.opacity = 0.4;
fabricMesh.material.transparent = true;

let weavePhase = 0;
let currentWeaveStep = 0;
let shuttleDirWeave = 1;
let fabricLines = [];
let fabricProgress = 0;

function animate(){
  requestAnimationFrame(animate);
  const delta=clock.getDelta();
  const elapsed=clock.getElapsedTime();
  frameCount++;

  const isRunning=twin.status==='ON'||twin.status==='FAULT';
  const speedFactor=twin.speed/200; // 0..1.5
  const isFault=twin.status==='FAULT';

  if(isRunning && twin.speed > 5 && twin.pattern_matrix && twin.pattern_matrix.length > 0){
      const cycleSpeed = (twin.speed / 100) * 0.8;
      weavePhase += delta * cycleSpeed;
      
      if(weavePhase >= 1.0) {
          weavePhase -= 1.0;
          currentWeaveStep = (currentWeaveStep + 1) % twin.pattern_matrix.length;
          shuttleDirWeave *= -1;
          
          // Deposit weft thread exactly at beating line
          const weft = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 3.8, 6), MAT.weftThread.clone());
          weft.rotation.z = Math.PI/2;
          weft.userData.baseZ = fabricProgress;
          fabricGroup.add(weft);
          fabricLines.push(weft);
          if(fabricLines.length > 60) {
              const old = fabricLines.shift();
              fabricGroup.remove(old);
              old.geometry.dispose();
          }
      }
      
      fabricProgress += delta * cycleSpeed * 0.12; 

      // ── 1. WARP SHEDDING ──
      const row = twin.pattern_matrix[currentWeaveStep];
      if(row) {
          for(let i=0; i<warpPositions.length; i++){
              const isUp = row[i % row.length] === 1;
              const targetY = isUp ? 2.65 : 2.35;
              warpPositions[i].position.y += (targetY - warpPositions[i].position.y) * 0.15;
          }
      }

      // ── 2. SHUTTLE FLIGHT ──
      let startX = shuttleDirWeave > 0 ? -2.6 : 2.6;
      let endX   = shuttleDirWeave > 0 ? 2.6 : -2.6;
      
      if(weavePhase < 0.2) {
          shuttleGroup.position.x = startX;
      } else if(weavePhase > 0.7) {
          shuttleGroup.position.x = endX;
      } else {
          let t = (weavePhase - 0.2) / 0.5;
          shuttleGroup.position.x = startX + (endX - startX) * t;
          shuttleGroup.children[3].rotation.x += delta * 30; // bobbin
          shuttleGroup.position.y = 2.5 + Math.sin(t * Math.PI) * 0.05;
      }

      // ── 3. BEATING (REED) ──
      const reedBaseZ = 1.25;
      if(weavePhase > 0.7) {
          let t = (weavePhase - 0.7) / 0.3; 
          let swing = Math.sin(t * Math.PI); 
          reedGroup.position.z = reedBaseZ - swing * 0.45;
          reedGroup.rotation.x = -swing * 0.3;
          beaterArm1.rotation.x = -swing * 0.3;
          beaterArm2.rotation.x = -swing * 0.3;
      } else {
          reedGroup.position.z = reedBaseZ;
          reedGroup.rotation.x = 0;
          beaterArm1.rotation.x = 0;
          beaterArm2.rotation.x = 0;
      }

      // ── 4. FABRIC ADVANCEMENT ──
      for(let i=0; i<fabricLines.length; i++) {
          let mesh = fabricLines[i];
          let rel = fabricProgress - mesh.userData.baseZ; 
          let z = 0.8 - rel; // 0.8 is beat point
          mesh.position.set(0, 1.1, z);
      }
      
      // Fabric Mesh unroll
      fabricMesh.scale.y = Math.min(1.0, fabricMesh.scale.y + delta * 0.005);
      clothBeamGroup.children[0].rotation.x += delta * speedFactor * 1.5;
      warpBeamGroup.children[0].rotation.x -= delta * speedFactor * 0.5;
  }

  // ── VIBRATION & MISC ──
  if(isRunning && twin.vibration>0.05){
    const vib=twin.vibration*0.15;
    loomGroup.position.x=Math.sin(elapsed*50)*vib;
    loomGroup.position.z=Math.cos(elapsed*47)*vib*0.5;
  } else {
    loomGroup.position.x*=0.9;
    loomGroup.position.z*=0.9;
  }

  const tension=twin.warp_tension;
  const tc = tension<3?0x00e5ff : tension<7?0x76ff03 : tension<9?0xff9100 : 0xff1744;
  warpPositions.forEach(w=>{w.material.color.setHex(tc);});

  if(isFault){
    const pulse=0.5+Math.sin(elapsed*8)*0.5;
    faultMat.emissiveIntensity=pulse*1.5;
    faultPointLight.intensity=pulse*3;
    loomLight.color.setHex(0xff1744);
    loomLight.intensity=0.5+pulse*0.8;
  } else {
    faultMat.emissiveIntensity*=0.9;
    faultPointLight.intensity*=0.9;
    loomLight.color.setHex(0x00e5ff);
    loomLight.intensity=0.8+speedFactor*0.6;
  }

  // ── CALLOUT POSITIONING ──
  function updateCallout(id, x, y, z){
    const el = document.getElementById(id);
    if(!el) return;
    const pos = new THREE.Vector3(x, y, z);
    pos.project(camera);
    const cx = (pos.x * 0.5 + 0.5) * W();
    const cy = (-pos.y * 0.5 + 0.5) * H();
    if(pos.z > 1){
      el.classList.remove('visible');
    } else {
      el.classList.add('visible');
      el.style.transform = `translate(${cx}px, ${cy - 45}px)`; 
    }
  }
  
  // Provide defaults for callout tracking so it doesn't break if object falls out of scope
  let sx = shuttleGroup ? shuttleGroup.position.x : 0;
  updateCallout('co-speed', sx, 2.5, 1.25);
  updateCallout('co-temp', 2.4, 4.8, 1.3);
  updateCallout('co-tension', 0, 3.2, 1.2);
  updateCallout('co-vib', -2.4, 0.5, 0);

  renderer.render(scene,camera);

  if(elapsed>5){
    let ch = document.getElementById('controls-hint');
    if(ch) ch.style.opacity='0';
  }
}
animate();
"""

parts = text.split("// ═══════════════════════════════════════════════\n//  ANIMATION LOOP\n// ═══════════════════════════════════════════════")
if len(parts) == 2:
    anim_part_end = parts[1].find("</script>")
    if anim_part_end != -1:
        new_text = parts[0] + anim_code + "\n// Hide relay banner after initial check\nsetTimeout(()=>{\n  if(relayOk===null) demoMode=true;\n},3000);\n" + parts[1][anim_part_end:]
        
        with open(os.path.join(base_path, "weave.html"), "w", encoding="utf-8") as f:
            f.write(new_text)
        print("Success")
    else:
        print("Failed to find </script>")
else:
    print("Failed to find ANIMATION LOOP block")
