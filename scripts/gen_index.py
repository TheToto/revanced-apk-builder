#!/usr/bin/env python3
import tomllib
import os

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
            # If 'enabled' is missing, it defaults to True according to project logic
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
    </style>
</head>
<body>
    <div class="container">
        <h1>TheToto Modded APKs Repository</h1>
        <div class="grid">
"""

for app in active_apps:
    html_content += f"""            <a href="{app['slug']}.html" class="card">
                <h2>{app['name']}</h2>
            </a>\n"""

html_content += """        </div>
    </div>
</body>
</html>
"""

with open(os.path.join(out_dir, "index.html"), "w") as f:
    f.write(html_content)

print("Generated index.html successfully.")
