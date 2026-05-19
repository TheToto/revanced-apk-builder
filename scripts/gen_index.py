#!/usr/bin/env python3
import tomllib
import os
import json
import urllib.parse

# Read config file to find active apps
config_file = "config.toml"
active_apps = []

# Get repository details for Obtainium links
repo_full = os.environ.get("GITHUB_REPOSITORY", "TheToto/revanced-magisk-module")
try:
    owner, repo_name = repo_full.split('/')
except ValueError:
    owner, repo_name = "TheToto", "revanced-magisk-module"

base_url = "https://apk.thetoto.fr"

try:
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
        
    for app_name, app_config in config.items():
        if isinstance(app_config, dict):
            is_enabled = app_config.get('enabled', True)
            if is_enabled is True or str(is_enabled).lower() == 'true':
                slug = app_name.lower().replace(' ', '-')
                active_apps.append({'name': app_name, 'slug': slug})

except FileNotFoundError:
    print(f"Error: {config_file} not found.")
    exit(1)
except Exception as e:
    print(f"Error parsing {config_file}: {e}")
    exit(1)

out_dir = "/tmp/pages"
os.makedirs(out_dir, exist_ok=True)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TheToto Modded APKs Repository</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --border: #334155;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            width: 100%;
        }
        h1 {
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
        }
        .card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem 1.5rem;
            text-align: center;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
        }
        .card h2 {
            margin: 0;
            font-size: 1.25rem;
        }
        .card-icon-wrap {
            width: 64px;
            height: 64px;
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 1rem;
            flex-shrink: 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .card-icon {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            transform: scale(1.35);
        }
        .microg-section {
            margin-bottom: 3rem;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        }
        .microg-section h2 {
            margin: 0 0 1rem 0;
            font-size: 1.5rem;
        }
        .microg-section p {
            color: var(--text-secondary);
            margin: 0 0 1.5rem 0;
            line-height: 1.6;
        }
        .microg-actions {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem 0.75rem;
            width: 100%;
            max-width: 270px;
            margin: 0 auto;
            align-items: center;
        }
        .microg-actions > a {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 52px;
            width: 100%;
        }
        .badge-obtainium {
            display: inline-block;
            transition: transform 0.2s ease;
        }
        .badge-obtainium:hover {
            transform: translateY(-2px) scale(1.02);
        }
        .badge-obtainium img {
            height: 52px;
            width: 100%;
            max-width: 170px;
            object-fit: contain;
            border-radius: 8px;
        }
        .btn-manual {
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            font-size: 0.95rem;
            background-color: transparent;
            color: var(--text-primary);
            border: 1px solid var(--border);
            transition: all 0.2s ease;
            box-sizing: border-box;
        }
        .btn-manual:hover {
            background-color: rgba(255, 255, 255, 0.05);
            border-color: var(--text-secondary);
            transform: translateY(-2px);
        }
        .btn-qr {
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
        }
        .btn-qr:hover {
            background-color: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(4px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal-overlay.active { display: flex; }
        .modal-content {
            background: var(--card-bg);
            padding: 2.5rem;
            border-radius: 20px;
            border: 1px solid var(--border);
            text-align: center;
            position: relative;
            max-width: 90%;
            animation: modalFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        @keyframes modalFadeIn {
            from { opacity: 0; transform: translateY(20px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .modal-close {
            position: absolute;
            top: 1rem; right: 1rem;
            background: none; border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
            padding: 0.5rem;
        }
        .modal-close:hover { color: var(--text-primary); }
    </style>
</head>
<body>
    <div class="container">
        <h1>TheToto Modded APKs Repository</h1>
"""

# Build Obtainium link for MicroG RE
microg_json = json.dumps({
    "id": "app.revanced.android.gms",
    "url": "https://github.com/MorpheApp/MicroG-RE",
    "author": "MorpheApp",
    "name": "MicroG RE"
})
microg_encoded = urllib.parse.quote(microg_json, safe='')
microg_obtainium_link = f"obtainium://app/{microg_encoded}"

html_content += f"""
        <div class="microg-section">
            <h2>⚙️ MicroG RE</h2>
            <p>Some apps listed below (notably <strong>YouTube</strong> and <strong>Music</strong>) require <strong>MicroG RE</strong> to work properly on non-rooted devices. It replaces Google Play Services.</p>
            <div class="microg-actions">
                <a href="https://github.com/MorpheApp/MicroG-RE/releases" class="btn-manual">Manual Download</a>
                <button class="btn-qr" onclick="document.getElementById('qr-modal-apk-microg').classList.add('active')" title="Show APK QR Code">
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

                <a href="{microg_obtainium_link}" class="badge-obtainium">
                    <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium">
                </a>
                <button class="btn-qr" onclick="document.getElementById('qr-modal-obt-microg').classList.add('active')" title="Show Obtainium QR Code">
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

        <div class="grid">
"""

for app in active_apps:
    icon_url = f"./{app['slug']}.png"
    html_content += f"""            <a href="{app['slug']}.html" class="card">
                <div class="card-icon-wrap">
                    <img src="{icon_url}" alt="{app['name']} icon" class="card-icon" onerror="this.parentElement.style.display='none'">
                </div>
                <h2>{app['name']}</h2>
            </a>\n"""

html_content += f"""        </div>
    </div>
    
    <div class="modal-overlay" id="qr-modal-apk-microg" onclick="if(event.target === this) this.classList.remove('active')">
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('qr-modal-apk-microg').classList.remove('active')">&times;</button>
            <p style="margin: 0 0 1.5rem 0; font-weight: 600; font-size: 1.1rem; color: var(--text-primary);">Scan to Download MicroG</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=1&data={urllib.parse.quote('https://github.com/MorpheApp/MicroG-RE/releases', safe='')}" alt="APK QR Code" style="background: white; padding: 0.5rem; border-radius: 12px; width: 280px; height: 280px;">
        </div>
    </div>

    <div class="modal-overlay" id="qr-modal-obt-microg" onclick="if(event.target === this) this.classList.remove('active')">
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('qr-modal-obt-microg').classList.remove('active')">&times;</button>
            <p style="margin: 0 0 1.5rem 0; font-weight: 600; font-size: 1.1rem; color: var(--text-primary);">Scan to add in Obtainium</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=1&data={urllib.parse.quote(microg_obtainium_link, safe='')}" alt="Obtainium QR Code" style="background: white; padding: 0.5rem; border-radius: 12px; width: 280px; height: 280px;">
        </div>
    </div>
</body>
</html>
"""

with open(os.path.join(out_dir, "index.html"), "w") as f:
    f.write(html_content)

print("Generated index.html successfully.")
