import json
import os

input_file = r'Fiware\bckend\loom_01_data_200k.json'
temp_file = r'Fiware\bckend\loom_01_data_200k_filtered.json'

print(f"Filtering {input_file}...")
count_removed = 0
count_kept = 0

with open(input_file, 'r', encoding='utf-8') as fin, \
     open(temp_file, 'w', encoding='utf-8') as fout:
    for line in fin:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            # machine speed is often in nested structure machine -> speed
            speed = data.get('machine', {}).get('speed', 0)
            
            if speed > 0:
                fout.write(json.dumps(data) + '\n')
                count_kept += 1
            else:
                count_removed += 1
                
            if (count_kept + count_removed) % 20000 == 0:
                print(f"Processed {count_kept + count_removed} rows...")
        except Exception as e:
            print(f"Error parsing line: {e}")
            continue

print(f"Filtering complete.")
print(f"Rows kept: {count_kept}")
print(f"Rows removed (speed=0): {count_removed}")

# Replace original with filtered
os.replace(temp_file, input_file)
print(f"Original file updated.")
