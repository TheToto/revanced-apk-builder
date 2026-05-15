#!/usr/bin/env python3
import tomllib
import os

# Read config file to find active apps
config_file = "config.toml"
active_apps = []

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
    <title>ReVanced Repository</title>
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
        .app-link {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem 1.5rem;
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
        }
        .app-link:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
        }
        .app-link h2 {
            margin: 0 0 0.5rem 0;
            font-size: 1.25rem;
        }
        .tag {
            font-size: 0.75rem;
            background-color: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ReVanced Repository</h1>
        <div class="grid">
"""

for app in active_apps:
    html_content += f"""            <a href="{app['slug']}.html" class="app-link">
                <h2>{app['name']}</h2>
                <span class="tag">Active</span>
            </a>\n"""

html_content += """        </div>
    </div>
</body>
</html>
"""

with open(os.path.join(out_dir, "index.html"), "w") as f:
    f.write(html_content)

print("Generated index.html successfully.")
