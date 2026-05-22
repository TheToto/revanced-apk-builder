#!/usr/bin/env python3
import os
import tomllib

def get_enabled_apps(config_path="config.toml"):
    """
    Reads the config file and returns a dictionary of active/enabled apps.
    Key is the slug, value is a dictionary containing:
      - name: the app name/section key
      - brand: the rv-brand value (defaults to 'ReVanced')
      - config: the raw app config dictionary
    """
    enabled = {}
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        for app_name, app_config in config.items():
            if isinstance(app_config, dict):
                is_enabled = app_config.get('enabled', True)
                if is_enabled is True or str(is_enabled).lower() == 'true':
                    slug = app_name.lower().replace(' ', '-')
                    enabled[slug] = {
                        "name": app_name,
                        "brand": app_config.get("rv-brand", "ReVanced"),
                        "config": app_config
                    }
    except Exception as e:
        print(f"Warning: Failed to load config {config_path}: {e}")
    return enabled

def get_repo_details():
    """
    Returns (owner, repo_name) from GITHUB_REPOSITORY environment variable,
    with fallbacks for local running.
    """
    repo_full = os.environ.get("GITHUB_REPOSITORY", "TheToto/revanced-magisk-module")
    try:
        owner, repo_name = repo_full.split('/')
    except ValueError:
        owner, repo_name = "TheToto", "revanced-magisk-module"
    return owner, repo_name

def load_svg(filename):
    """
    Loads SVG content from the scripts directory.
    """
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Warning: Failed to load SVG {filename}: {e}")
        return ""

QR_SVG = load_svg("qr.svg")
