#!/usr/bin/env python3
import os
import glob
import re
import json
import sys
import urllib.parse

# Ensure the scripts/ directory is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
from apk_utils import get_package_id, extract_apk_icon

# This script runs AFTER releases are built and uploaded.
# The NEXT_VER_CODE environment variable contains the release tag.
# GITHUB_REPOSITORY contains the repo path (e.g. j-hc/revanced-magisk-module).

next_ver_code = os.environ.get("NEXT_VER_CODE", "UNKNOWN_TAG")
repo_full = os.environ.get("GITHUB_REPOSITORY", "TheToto/revanced-magisk-module")

try:
    owner, repo_name = repo_full.split('/')
except ValueError:
    owner, repo_name = "TheToto", "revanced-magisk-module"

base_url = "https://apk.thetoto.fr"

out_dir = "/tmp/pages"
os.makedirs(out_dir, exist_ok=True)

build_dir = "build"
apks = glob.glob(os.path.join(build_dir, "*.apk"))

if not apks:
    print("No APKs found in build directory. Skipping app page generation.")
    exit(0)


for apk_path in apks:
    filename = os.path.basename(apk_path)
    
    slug_to_name = {}
    try:
        with open("config.toml", "r") as f:
            for line in f:
                if line.strip().startswith("[") and line.strip().endswith("]"):
                    app_name = line.strip()[1:-1]
                    valid_slug = app_name.lower().replace(' ', '-')
                    slug_to_name[valid_slug] = app_name
    except Exception:
        pass

    slug = "unknown"
    for valid_slug in sorted(slug_to_name.keys(), key=len, reverse=True):
        if filename.startswith(valid_slug + "-"):
            slug = valid_slug
            break
            
    if slug == "unknown":
        parts = filename.split('-')
        slug = parts[0] if parts else "unknown"

    app_display_name = slug_to_name.get(slug, slug.replace('-', ' ').title())

    # Resolve Obtainium App ID (Package Name) from apk using aapt
    app_id = get_package_id(apk_path)

    download_url = f"{base_url}/releases/download/{next_ver_code}/{filename}"
    page_url = f"{base_url}/{slug}.html"
    
    icon_filename = f"{slug}.png"
    icon_out_path = os.path.join(build_dir, icon_filename)
    icon_pages_path = os.path.join(out_dir, icon_filename)
    icon_source_path = os.path.join("icons", icon_filename)
    icon_url = f"./{icon_filename}"
    
    if not os.path.exists(icon_out_path):
        if os.path.exists(icon_source_path):
            import shutil
            shutil.copy2(icon_source_path, icon_out_path)
            print(f"Copied static icon from {icon_source_path}")
        else:
            extract_apk_icon(apk_path, icon_out_path)
    
    # Copy icon to pages output dir
    if os.path.exists(icon_out_path) and not os.path.exists(icon_pages_path):
        import shutil
        shutil.copy2(icon_out_path, icon_pages_path)
    
    # Extract info for display
    m = re.search(r"^(.*?)-v([0-9a-zA-Z.-]+)-((?:arm64-v8a|arm-v7a|x86_64|x86|all))\.apk$", filename)
    if m:
        brand_part = m.group(1)
        brand = brand_part[len(slug)+1:] if brand_part.startswith(slug+"-") else brand_part
        if not brand:
            brand = "Original"
        version = m.group(2)
        arch = m.group(3)
    else:
        brand, version, arch = "Unknown", "Unknown", "Unknown"

    # Craft the Obtainium JSON payload
    additional_settings = {
        "versionExtractionRegEx": r"-v([0-9a-zA-Z.-]+)-(arm64-v8a|arm-v7a|x86_64|x86|all)\.apk",
        "matchGroupToUse": "$1",
        "defaultPseudoVersioningMethod": "APKLinkHash",
        "appName": app_display_name,
        "appAuthor": owner,
        "about": f"{app_display_name} {brand}"
    }
    
    app_json = {
        "id": app_id,
        "url": page_url,
        "author": owner,
        "name": app_display_name,
        "preferredApkIndex": 0,
        "additionalSettings": json.dumps(additional_settings)
    }
    json_str = json.dumps(app_json)
    encoded_json = urllib.parse.quote(json_str, safe='')
    obtainium_link = f"obtainium://app/{encoded_json}"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download {app_display_name}</title>
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
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .app-icon-wrap {{
            width: 72px;
            height: 72px;
            border-radius: 16px;
            overflow: hidden;
            flex-shrink: 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .app-icon {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            transform: scale(1.35);
        }}
        h1 {{
            margin: 0;
            font-size: 2.2rem;
            text-transform: capitalize;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 2.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        .info-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            letter-spacing: 0.05em;
        }}
        .info-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
        }}
        .filename-raw {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            word-break: break-all;
            background: rgba(0,0,0,0.2);
            padding: 0.5rem;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}
        .actions {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem 0.75rem;
            width: 100%;
            max-width: 270px;
            margin: 0 auto;
            align-items: center;
        }}
        .actions > a {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 52px;
            width: 100%;
        }}
        .btn {{
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-sizing: border-box;
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
        .badge-obtainium {{
            display: inline-block;
            transition: transform 0.2s ease;
        }}
        .badge-obtainium:hover {{
            transform: translateY(-2px) scale(1.02);
        }}
        .badge-obtainium img {{
            height: 52px;
            width: 100%;
            max-width: 170px;
            object-fit: contain;
            border-radius: 8px;
        }}
        .btn-qr {{
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            padding: 0;
            width: 52px;
            height: 52px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-qr:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }}
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(4px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal-content {{
            background: var(--card-bg);
            padding: 2.5rem;
            border-radius: 20px;
            border: 1px solid var(--border);
            text-align: center;
            position: relative;
            max-width: 90%;
            animation: modalFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}
        @keyframes modalFadeIn {{
            from {{ opacity: 0; transform: translateY(20px) scale(0.95); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .modal-close {{
            position: absolute;
            top: 1rem; right: 1rem;
            background: none; border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
            padding: 0.5rem;
        }}
        .modal-close:hover {{ color: var(--text-primary); }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Apps List</a>
        <div class="header-content">
            <div class="app-icon-wrap">
                <img src="{icon_url}" alt="{app_display_name} icon" class="app-icon" onerror="this.parentElement.style.display='none'">
            </div>
            <h1>{app_display_name}</h1>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Version</span>
                <span class="info-value">v{version}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Brand</span>
                <span class="info-value" style="text-transform: capitalize;">{brand}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Architecture</span>
                <span class="info-value">{arch}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Package ID</span>
                <span class="info-value" style="font-size: 0.9rem; word-break: break-all;">{app_id}</span>
            </div>
        </div>
        
        <div class="filename-raw">
            File: <code>{filename}</code>
        </div>
        
        <div class="actions">
            <a href="{download_url}" class="btn btn-download">Download APK</a>
            <button class="btn-qr" onclick="document.getElementById('qr-modal-apk').classList.add('active')" title="Show APK QR Code">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="5" height="5" x="3" y="3" rx="1"/>
                    <rect width="5" height="5" x="16" y="3" rx="1"/>
                    <rect width="5" height="5" x="3" y="16" rx="1"/>
                    <path d="M21 16h-3a2 2 0 0 0-2 2v3"/>
                    <path d="M21 21v.01"/>
                    <path d="M12 7v3a2 2 0 0 1-2 2H7"/>
                    <path d="M3 12h.01"/>
                    <path d="M12 3h.01"/>
                    <path d="M12 16v.01"/>
                    <path d="M16 12h1"/>
                    <path d="M21 12v.01"/>
                    <path d="M12 21v-1"/>
                </svg>
            </button>

            <a href="{obtainium_link}" class="badge-obtainium">
                <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium">
            </a>
            <button class="btn-qr" onclick="document.getElementById('qr-modal-obt').classList.add('active')" title="Show Obtainium QR Code">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="5" height="5" x="3" y="3" rx="1"/>
                    <rect width="5" height="5" x="16" y="3" rx="1"/>
                    <rect width="5" height="5" x="3" y="16" rx="1"/>
                    <path d="M21 16h-3a2 2 0 0 0-2 2v3"/>
                    <path d="M21 21v.01"/>
                    <path d="M12 7v3a2 2 0 0 1-2 2H7"/>
                    <path d="M3 12h.01"/>
                    <path d="M12 3h.01"/>
                    <path d="M12 16v.01"/>
                    <path d="M16 12h1"/>
                    <path d="M21 12v.01"/>
                    <path d="M12 21v-1"/>
                </svg>
            </button>
        </div>
    </div>

    <div class="modal-overlay" id="qr-modal-apk" onclick="if(event.target === this) this.classList.remove('active')">
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('qr-modal-apk').classList.remove('active')">&times;</button>
            <p style="margin: 0 0 1.5rem 0; font-weight: 600; font-size: 1.1rem; color: var(--text-primary);">Scan to Download APK</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=1&data={urllib.parse.quote(download_url, safe='')}" alt="APK QR Code" style="background: white; padding: 0.5rem; border-radius: 12px; width: 280px; height: 280px;">
        </div>
    </div>

    <div class="modal-overlay" id="qr-modal-obt" onclick="if(event.target === this) this.classList.remove('active')">
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('qr-modal-obt').classList.remove('active')">&times;</button>
            <p style="margin: 0 0 1.5rem 0; font-weight: 600; font-size: 1.1rem; color: var(--text-primary);">Scan to add in Obtainium</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=1&data={urllib.parse.quote(obtainium_link, safe='')}" alt="Obtainium QR Code" style="background: white; padding: 0.5rem; border-radius: 12px; width: 280px; height: 280px;">
        </div>
    </div>
</body>
</html>
"""

    with open(os.path.join(out_dir, f"{slug}.html"), "w") as f:
        f.write(html_content)
    
    print(f"Generated {slug}.html for {filename}")

print("App pages generation complete.")
