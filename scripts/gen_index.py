#!/usr/bin/env python3
import os
import json
import urllib.parse
import sys

# Ensure the scripts/ directory is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))
from config_utils import get_enabled_apps, get_repo_details, QR_SVG

owner, repo_name = get_repo_details()
enabled_apps = get_enabled_apps()
active_apps = []
for slug, info in enabled_apps.items():
    active_apps.append({
        'slug': slug,
        'name': info['name'],
        'brand': info['brand']
    })

base_url = "https://apk.thetoto.fr"

out_dir = "/tmp/pages"
os.makedirs(out_dir, exist_ok=True)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TheToto Modded APKs Repository</title>
    <link rel="stylesheet" href="./style.css">
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
        <div class="tools-grid">
            <div class="obtainium-section">
                <h2>📥 Obtainium</h2>
                <p>Installez <strong>Obtainium</strong> pour ajouter facilement nos applications et bénéficier de <strong>mises à jour automatiques</strong> via nos liens d'installation rapide.</p>
                <div class="obtainium-actions">
                    <a href="https://obtainium.imranr.dev/" class="btn-manual" target="_blank" rel="noopener">Installer Obtainium</a>
                    <button class="btn-qr" onclick="document.getElementById('qr-modal-obtainium').classList.add('active')" title="Scanner le QR Code">
                        {QR_SVG}
                    </button>
                </div>
            </div>

            <div class="microg-section">
                <h2>⚙️ MicroG RE</h2>
                <p>Certaines applications (notamment <strong>YouTube</strong> et <strong>YouTube Music</strong>) nécessitent <strong>MicroG RE</strong> pour fonctionner sans les services Google Play officiels.</p>
                <div class="microg-actions">
                    <a href="https://github.com/MorpheApp/MicroG-RE/releases" class="btn-manual" target="_blank" rel="noopener">Téléchargement manuel</a>
                    <button class="btn-qr" onclick="document.getElementById('qr-modal-apk-microg').classList.add('active')" title="Afficher le QR Code de l'APK">
                        {QR_SVG}
                    </button>

                    <a href="{microg_obtainium_link}" class="badge-obtainium">
                        <img src="https://raw.githubusercontent.com/ImranR98/Obtainium/main/assets/graphics/badge_obtainium.png" alt="Get it on Obtainium">
                    </a>
                    <button class="btn-qr" onclick="document.getElementById('qr-modal-obt-microg').classList.add('active')" title="Afficher le QR Code d'Obtainium">
                        {QR_SVG}
                    </button>
                </div>
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
                <span class="card-brand">{app['brand']}</span>
            </a>\n"""

html_content += f"""        </div>
        
        <footer>
            <p>Source code and CI on GitHub: <a href="https://github.com/{owner}/{repo_name}" target="_blank" rel="noopener">{owner}/{repo_name}</a></p>
        </footer>
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

    <div class="modal-overlay" id="qr-modal-obtainium" onclick="if(event.target === this) this.classList.remove('active')">
        <div class="modal-content">
            <button class="modal-close" onclick="document.getElementById('qr-modal-obtainium').classList.remove('active')">&times;</button>
            <p style="margin: 0 0 1.5rem 0; font-weight: 600; font-size: 1.1rem; color: var(--text-primary);">Scanner pour installer Obtainium</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=1&data={urllib.parse.quote('https://obtainium.imranr.dev/', safe='')}" alt="Obtainium Releases QR Code" style="background: white; padding: 0.5rem; border-radius: 12px; width: 280px; height: 280px;">
        </div>
    </div>
</body>
</html>
"""

with open(os.path.join(out_dir, "index.html"), "w") as f:
    f.write(html_content)

# Copy style.css to pages output directory
import shutil
css_source = os.path.join(os.path.dirname(__file__), "style.css")
css_dest = os.path.join(out_dir, "style.css")
if os.path.exists(css_source):
    shutil.copy2(css_source, css_dest)
    print("Copied style.css to pages directory.")

print("Generated index.html successfully.")
