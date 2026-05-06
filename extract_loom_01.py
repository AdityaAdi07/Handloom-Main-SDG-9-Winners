import json

input_file = 'final_dataset_fixed.json'
output_file = 'loom_01_data_200k.json'
target_loom = 'loom_01'
limit = 200000

extracted_data = []
count = 0

print(f"Starting extraction of {limit} rows for {target_loom}...")

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get('device_id') == target_loom:
                    extracted_data.append(data)
                    count += 1
                    
                    if count % 10000 == 0:
                        print(f"Progress: {count} rows extracted...")
                        
                    if count >= limit:
                        break
            except json.JSONDecodeError:
                # Handle cases where a line might not be valid JSON
                continue

    print(f"Extraction complete. Total rows: {len(extracted_data)}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in extracted_data:
            f.write(json.dumps(item) + '\n')
        
    print(f"Data saved to {output_file}")

except FileNotFoundError:
    print(f"Error: {input_file} not found.")
except Exception as e:
    print(f"An error occurred: {e}")
