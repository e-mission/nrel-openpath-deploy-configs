import os
import json

for filename in os.listdir('configs'):
    with open(f'configs/{filename}', 'r', encoding='utf-8') as f:
        config = json.load(f)
    with open(f'configs/{filename}', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
        f.write("\n")
        print(f"Formatted {filename}")
