import os
import sys
import json


def read_config(deployment):
    config_file_path = f'configs/{deployment}.nrel-op.json'
    if not os.path.exists(config_file_path):
        print(f"There is no deployment called {deployment} - no changes made.")
        sys.exit(1)
    with open(config_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_config(deployment, new_config, msg):
    config_file_path = f'configs/{deployment}.nrel-op.json'
    if new_config and msg:
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4, ensure_ascii=False)
            f.write("\n")
        print(f"Updated {config_file_path} with new config.")
    else:
        print("No changes made.")
