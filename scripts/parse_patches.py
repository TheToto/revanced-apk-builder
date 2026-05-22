#!/usr/bin/env python3
import sys
import json
import re

def parse_patch_list(patches_str):
    if not patches_str:
        return []
    s = patches_str.replace("\\'", "ESCAPED_SQ").replace('\\"', "ESCAPED_DQ")
    items = re.findall(r"'(.*?)'", s)
    if not items:
        items = re.findall(r'"(.*?)"', s)
    result = []
    for item in items:
        restored = item.replace("ESCAPED_SQ", "'").replace("ESCAPED_DQ", '"')
        if restored.strip():
            result.append(restored.strip())
    return result

def norm(s):
    return re.sub(r"\\|['\"\s]+", "", s).lower()

def main():
    included_str = sys.argv[1] if len(sys.argv) > 1 else ""
    excluded_str = sys.argv[2] if len(sys.argv) > 2 else ""
    exclusive_str = sys.argv[3] if len(sys.argv) > 3 else "false"

    exclusive = exclusive_str.lower() == "true"

    included_list = parse_patch_list(included_str)
    excluded_list = parse_patch_list(excluded_str)

    included_norm = {norm(p) for p in included_list}
    excluded_norm = {norm(p) for p in excluded_list}

    patches = []
    current_name = None
    current_desc = ""

    for line in sys.stdin:
        line = line.strip()
        if line.startswith("Name:"):
            current_name = line[len("Name:"):].strip()
            current_desc = ""
        elif line.startswith("Description:"):
            current_desc = line[len("Description:"):].strip()
        elif line.startswith("Enabled:"):
            if current_name is not None:
                val = line[len("Enabled:"):].strip().lower()
                default_enabled = (val == "true")
                norm_name = norm(current_name)
                patches.append({
                    "name": current_name,
                    "description": current_desc,
                    "default_enabled": default_enabled,
                    "explicitly_enabled": norm_name in included_norm,
                    "explicitly_disabled": norm_name in excluded_norm
                })
                current_name = None

    output_data = {
        "exclusive": exclusive,
        "patches": patches
    }
    json.dump(output_data, sys.stdout, indent=2)

if __name__ == "__main__":
    main()
