import re
import json
import os

def parse_settings(markdown_path):
    with open(markdown_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    categories = []
    current_category = None
    current_setting = None

    category_re = re.compile(r'^## .*Category \d+: (.*)')
    setting_re = re.compile(r'^### (.*)')
    table_row_re = re.compile(r'^\| \*\*(.*)\*\* \| `?(.*?)`? \|')

    for line in lines:
        cat_match = category_re.match(line)
        if cat_match:
            current_category = {
                "name": cat_match.group(1).strip(),
                "settings": []
            }
            categories.append(current_category)
            continue

        set_match = setting_re.match(line)
        if set_match:
            current_setting = {"name": set_match.group(1).strip()}
            if current_category:
                current_category["settings"].append(current_setting)
            continue

        if current_setting:
            row_match = table_row_re.match(line)
            if row_match:
                key = row_match.group(1).strip().lower()
                val = row_match.group(2).strip().replace('`', '')
                current_setting[key] = val

    return categories

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    markdown_path = os.path.join(base_dir, "docs", "registry_keys.md")
    output_dir = os.path.join(base_dir, "src", "resources")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "settings.json")

    results = parse_settings(markdown_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"Generated {output_path} with {sum(len(c['settings']) for c in results)} settings.")
