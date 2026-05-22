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
from config_utils import get_enabled_apps, get_repo_details, QR_SVG

next_ver_code = os.environ.get("NEXT_VER_CODE", "UNKNOWN_TAG")
owner, repo_name = get_repo_details()

base_url = "https://apk.thetoto.fr"

def get_patch_status(default_enabled, explicitly_enabled, explicitly_disabled, exclusive):
    if explicitly_disabled:
        return "explicitly_disabled"
    if explicitly_enabled:
        return "explicitly_enabled"
    if exclusive:
        return "disabled"
    if default_enabled:
        return "enabled"
    return "disabled"

out_dir = "/tmp/pages"
os.makedirs(out_dir, exist_ok=True)

enabled_apps = get_enabled_apps()
slug_to_name = {slug: info['name'] for slug, info in enabled_apps.items()}

build_dir = "build"
apks = glob.glob(os.path.join(build_dir, "*.apk"))
built_slugs = set()

for apk_path in apks:
    filename = os.path.basename(apk_path)

    slug = "unknown"
    for valid_slug in sorted(slug_to_name.keys(), key=len, reverse=True):
        if filename.startswith(valid_slug + "-"):
            slug = valid_slug
            break
            
    if slug == "unknown":
        parts = filename.split('-')
        slug = parts[0] if parts else "unknown"

    app_display_name = slug_to_name.get(slug, slug.replace('-', ' ').title())
    built_slugs.add(slug)

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

    patches_json_path = apk_path.replace(".apk", ".patches.json")
    patches_list_html = ""
    if os.path.exists(patches_json_path):
        try:
            with open(patches_json_path, "r") as f:
                patches_data = json.load(f)
            if patches_data:
                if isinstance(patches_data, dict):
                    patches = patches_data.get("patches", [])
                    exclusive = patches_data.get("exclusive", False)
                else:
                    patches = patches_data
                    exclusive = False

                processed_patches = []
                applied_count = 0
                for p in patches:
                    name = p.get('name', '')
                    desc = p.get('description', '') or "No description available."
                    if desc.strip().lower() == "null" or not desc:
                        desc = "No description available."
                    default_enabled = p.get('default_enabled', False)
                    if isinstance(default_enabled, str):
                        default_enabled = default_enabled.lower() == "true"
                    explicitly_enabled = p.get('explicitly_enabled', False)
                    if isinstance(explicitly_enabled, str):
                        explicitly_enabled = explicitly_enabled.lower() == "true"
                    explicitly_disabled = p.get('explicitly_disabled', False)
                    if isinstance(explicitly_disabled, str):
                        explicitly_disabled = explicitly_disabled.lower() == "true"
                    
                    status = get_patch_status(default_enabled, explicitly_enabled, explicitly_disabled, exclusive)
                    if status in ("explicitly_enabled", "enabled"):
                        applied_count += 1
                        
                    processed_patches.append({
                        "name": name,
                        "description": desc,
                        "status": status,
                        "default_enabled": default_enabled
                    })
                
                status_order = {
                    "explicitly_disabled": 0,
                    "explicitly_enabled": 1,
                    "enabled": 2,
                    "disabled": 3
                }
                processed_patches.sort(key=lambda x: (status_order.get(x["status"], 4), x["name"].lower()))

                patches_list_html += f"""
        <div class="patches-section">
            <h3 class="patches-title">⚙️ Applied Patches ({applied_count}/{len(processed_patches)})</h3>
            <div class="patches-list">
"""
                for p in processed_patches:
                    status = p["status"]
                    status_class = {
                        "explicitly_disabled": "excluded",
                        "explicitly_enabled": "applied",
                        "enabled": "applied",
                        "disabled": "disabled"
                    }.get(status, "disabled")

                    if status == "explicitly_disabled":
                        status_label = "Explicitly Disabled"
                    elif status == "explicitly_enabled":
                        if p["default_enabled"]:
                            status_label = "Explicitly Enabled (Default)"
                        else:
                            status_label = "Explicitly Enabled (Not Default)"
                    elif status == "enabled":
                        status_label = "Enabled"
                    else:
                        status_label = "Disabled"
                    
                    patches_list_html += f"""
                <div class="patch-card {status_class}">
                    <div class="patch-header">
                        <span class="patch-name">{p['name']}</span>
                        <span class="patch-status status-{status_class}">{status_label}</span>
                    </div>
                    <div class="patch-desc">{p['description']}</div>
                </div>
"""
                patches_list_html += """
            </div>
        </div>
"""
        except Exception as e:
            print(f"Warning: could not read/process patches file for {filename}: {e}")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download {app_display_name}</title>
    <link rel="stylesheet" href="./style.css">
</head>
<body class="app-page">
    <div class="container app-container">
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
                {QR_SVG}
            </button>

            <a href="{obtainium_link}" class="badge-obtainium">
                <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium">
            </a>
            <button class="btn-qr" onclick="document.getElementById('qr-modal-obt').classList.add('active')" title="Show Obtainium QR Code">
                {QR_SVG}
            </button>
        </div>
        {patches_list_html}
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


# Copy style.css to pages output directory
import shutil
css_source = os.path.join(os.path.dirname(__file__), "style.css")
css_dest = os.path.join(out_dir, "style.css")
if os.path.exists(css_source):
    shutil.copy2(css_source, css_dest)
    print("Copied style.css to pages directory.")

print("App pages generation complete.")
