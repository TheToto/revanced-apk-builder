#!/usr/bin/env python3
import os
import glob

import urllib.parse

# This script runs AFTER releases are built and uploaded.
# The NEXT_VER_CODE environment variable contains the release tag.
# GITHUB_REPOSITORY contains the repo path (e.g. j-hc/revanced-magisk-module).

next_ver_code = os.environ.get("NEXT_VER_CODE", "UNKNOWN_TAG")
repo_full = os.environ.get("GITHUB_REPOSITORY", "TheToto/revanced-magisk-module")

try:
    owner, repo_name = repo_full.split('/')
except ValueError:
    owner, repo_name = "TheToto", "revanced-magisk-module"

base_url = f"https://{owner}.github.io/{repo_name}"

out_dir = "/tmp/pages"
os.makedirs(out_dir, exist_ok=True)

build_dir = "build"
apks = glob.glob(os.path.join(build_dir, "*.apk"))

if not apks:
    print("No APKs found in build directory. Skipping app page generation.")
    exit(0)

for apk_path in apks:
    filename = os.path.basename(apk_path)
    
    # Filename format: <slug>-<brand>-v<version>-<arch>.apk
    valid_slugs = []
    try:
        with open("config.toml", "r") as f:
            for line in f:
                if line.strip().startswith("[") and line.strip().endswith("]"):
                    app_name = line.strip()[1:-1]
                    valid_slugs.append(app_name.lower().replace(' ', '-'))
    except Exception:
        pass

    slug = "unknown"
    for valid_slug in sorted(valid_slugs, key=len, reverse=True):
        if filename.startswith(valid_slug + "-"):
            slug = valid_slug
            break
            
    if slug == "unknown":
        parts = filename.split('-')
        slug = parts[0] if parts else "unknown"

    download_url = f"https://github.com/{repo_full}/releases/download/{next_ver_code}/{filename}"
    
    page_url = f"{base_url}/{slug}.html"
    encoded_url = urllib.parse.quote(page_url, safe='')
    obtainium_link = f"obtainium://add/{encoded_url}"

    # User requested a clean UI with a back link, while keeping it simple for Obtainium.
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download {slug}</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --border: #334155;
            --obtainium-color: #10b981;
            --obtainium-hover: #059669;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .container {{
            max-width: 600px;
            width: 100%;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 3rem 2rem;
            text-align: center;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        }}
        .back-link {{
            display: inline-flex;
            align-items: center;
            color: var(--text-secondary);
            text-decoration: none;
            margin-bottom: 2rem;
            font-weight: 500;
            transition: color 0.2s ease;
        }}
        .back-link:hover {{
            color: var(--text-primary);
        }}
        h1 {{
            margin: 0 0 1rem 0;
            font-size: 2rem;
            text-transform: capitalize;
        }}
        .version {{
            color: var(--text-secondary);
            margin-bottom: 2.5rem;
            word-break: break-all;
            font-size: 0.9rem;
        }}
        .actions {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        @media (min-width: 480px) {{
            .actions {{
                flex-direction: row;
                justify-content: center;
            }}
        }}
        .btn {{
            display: inline-block;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
        }}
        @media (min-width: 480px) {{
            .btn {{ width: auto; }}
        }}
        .btn-download {{
            background-color: var(--accent);
            color: #fff;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.4);
        }}
        .btn-download:hover {{
            background-color: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
        }}
        .btn-obtainium {{
            background-color: transparent;
            color: var(--obtainium-color);
            border: 2px solid var(--obtainium-color);
        }}
        .btn-obtainium:hover {{
            background-color: rgba(16, 185, 129, 0.1);
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Apps List</a>
        <h1>{slug.replace('-', ' ')}</h1>
        <p class="version">{filename}</p>
        <div class="actions">
            <a href="{download_url}" class="btn btn-download">Download APK</a>
            <a href="{obtainium_link}" class="btn btn-obtainium">Add to Obtainium</a>
        </div>
    </div>
</body>
</html>
"""

    with open(os.path.join(out_dir, f"{slug}.html"), "w") as f:
        f.write(html_content)
    
    print(f"Generated {slug}.html for {filename}")

print("App pages generation complete.")
