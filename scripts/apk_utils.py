#!/usr/bin/env python3
"""
apk_utils.py — helpers for extracting metadata and icons from Android APKs.

Requirements:
  - aapt  (from android-sdk-build-tools)
  - aapt2 (from android-sdk-build-tools)
  - ImageMagick (convert CLI)
"""

import glob
import os
import re
import subprocess
import tempfile
import zipfile


# ---------------------------------------------------------------------------
# Tool resolution
# ---------------------------------------------------------------------------

def _find_aapt_tools():
    """Return (aapt, aapt2) binary paths, preferring ANDROID_HOME versions."""
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    aapt, aapt2 = "aapt", "aapt2"
    if android_home:
        for name in ("aapt", "aapt2"):
            paths = sorted(glob.glob(
                os.path.join(android_home, "build-tools", "*", name)
            ))
            if paths:
                if name == "aapt":
                    aapt = paths[-1]
                else:
                    aapt2 = paths[-1]
    return aapt, aapt2


# ---------------------------------------------------------------------------
# Package ID extraction
# ---------------------------------------------------------------------------

def get_package_id(apk_path: str) -> str:
    """Return the Android package name (e.g. 'com.google.android.youtube')."""
    aapt, _ = _find_aapt_tools()
    result = subprocess.run(
        [aapt, "dump", "badging", apk_path],
        capture_output=True, text=True, check=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("package:"):
            m = re.search(r"name='([^']+)'", line)
            if m:
                return m.group(1)
    raise ValueError(f"Could not extract package ID from {apk_path}")


# ---------------------------------------------------------------------------
# Icon extraction helpers
# ---------------------------------------------------------------------------

def _dump_resources(apk_path: str, aapt2: str) -> list[str]:
    """Return lines from `aapt2 dump resources`."""
    result = subprocess.run(
        [aapt2, "dump", "resources", apk_path],
        capture_output=True, text=True
    )
    return result.stdout.splitlines()


def _find_block_for_res_id(res_id_hex: str, lines: list[str]) -> list[str]:
    """Return lines belonging to the resource block for res_id_hex."""
    block = []
    in_block = False
    for line in lines:
        if res_id_hex.lower() in line.lower():
            in_block = True
        if in_block:
            if block and "resource 0x" in line and res_id_hex.lower() not in line.lower():
                break
            block.append(line)
    return block


def _find_best_image_for_res_id(res_id_hex: str, apk_path: str, aapt2: str) -> str | None:
    """
    Find the best-density raster file (PNG or WebP) for a given resource ID.
    Returns a path relative to the APK root, or None if not found.
    """
    lines = _dump_resources(apk_path, aapt2)
    block = _find_block_for_res_id(res_id_hex, lines)
    density_order = ["xxxhdpi", "xxhdpi", "xhdpi", "hdpi", "mdpi"]
    candidates = {}
    for line in block:
        m = re.search(
            r"\((" + "|".join(density_order) + r")\) \(file\) (res/\S+\.(?:png|webp))",
            line
        )
        if m:
            candidates[m.group(1)] = m.group(2)
    for density in density_order:
        if density in candidates:
            return candidates[density]
    return None


def _find_direct_color_for_res_id(res_id_hex: str, apk_path: str, aapt2: str) -> str | None:
    """
    Check if the resource is a plain color value (e.g. `color/` type with `#AARRGGBB`).
    Returns an #RRGGBB hex string, or None.
    """
    lines = _dump_resources(apk_path, aapt2)
    block = _find_block_for_res_id(res_id_hex, lines)
    for line in block:
        # Format: `      () #ffff4500`
        m = re.search(r'^\s*\(\)\s*(#[0-9a-fA-F]{8})\s*$', line)
        if m:
            argb = m.group(1)  # #AARRGGBB
            return "#" + argb[3:]  # → #RRGGBB
    return None


def _find_xml_file_for_res_id(res_id_hex: str, apk_path: str, aapt2: str) -> str | None:
    """Return the APK-relative path of an XML file associated with a resource ID."""
    lines = _dump_resources(apk_path, aapt2)
    block = _find_block_for_res_id(res_id_hex, lines)
    for line in block:
        m = re.search(r"\(file\) (res/\S+\.xml)", line)
        if m:
            return m.group(1)
    return None


def _extract_solid_color_from_xml_res(res_id_hex: str, apk_path: str, aapt2: str) -> str | None:
    """
    If the resource is a shape/drawable XML containing a `<solid android:color>`,
    decode it and return the color as an #RRGGBB string. Returns None otherwise.
    """
    # First check if it's a direct color value in the resource table
    direct = _find_direct_color_for_res_id(res_id_hex, apk_path, aapt2)
    if direct:
        return direct

    # Otherwise try to find an XML file and parse it
    xml_file = _find_xml_file_for_res_id(res_id_hex, apk_path, aapt2)
    if not xml_file:
        return None
    try:
        xml_dump = subprocess.run(
            [aapt2, "dump", "xmltree", "--file", xml_file, apk_path],
            capture_output=True, text=True
        )
        for line in xml_dump.stdout.splitlines():
            m = re.search(r"color\(.*\)=(#[0-9a-fA-F]{8})", line)
            if m:
                argb = m.group(1)
                return "#" + argb[3:]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Adaptive icon XML parsing
# ---------------------------------------------------------------------------

def _parse_adaptive_icon(icon_res_path: str, apk_path: str, aapt2: str) -> tuple[str | None, str | None]:
    """
    Decode an adaptive-icon XML and return (bg_res_id, fg_res_id).
    """
    xml_dump = subprocess.run(
        [aapt2, "dump", "xmltree", "--file", icon_res_path, apk_path],
        capture_output=True, text=True, check=True
    )
    bg_res_id = fg_res_id = None
    current_element = None
    for line in xml_dump.stdout.splitlines():
        if "E: background" in line:
            current_element = "bg"
        elif "E: foreground" in line:
            current_element = "fg"
        elif "E: monochrome" in line:
            current_element = None  # ignore monochrome layer
        elif "drawable" in line.lower() and "=@" in line and current_element:
            m = re.search(r"=@(0x[0-9a-fA-F]+)", line)
            if m:
                if current_element == "bg":
                    bg_res_id = m.group(1)
                elif current_element == "fg":
                    fg_res_id = m.group(1)
                current_element = None  # one value per element
    return bg_res_id, fg_res_id


# ---------------------------------------------------------------------------
# Public: extract_apk_icon
# ---------------------------------------------------------------------------

def extract_apk_icon(apk_path: str, out_path: str) -> bool:
    """
    Extract the launcher icon from an APK and save it as a PNG at out_path.
    Handles:
      - Direct PNG/WebP icons
      - Adaptive icons (XML) with PNG/WebP layers
      - Adaptive icons with solid color or XML-shape backgrounds
      - Adaptive icons with plain color resource backgrounds (e.g. Reddit)
    Returns True on success, False on failure.
    """
    aapt, aapt2 = _find_aapt_tools()
    try:
        # Step 1: find the icon resource path inside the APK
        result = subprocess.run(
            [aapt, "dump", "badging", apk_path],
            capture_output=True, text=True, check=True
        )
        icon_res_path = None
        for line in result.stdout.splitlines():
            if line.startswith("application:"):
                m = re.search(r"icon='([^']+)'", line)
                if m:
                    icon_res_path = m.group(1)
                    break

        if not icon_res_path:
            return False

        # Step 2a: direct raster (PNG/WebP)
        if icon_res_path.endswith(".png") or icon_res_path.endswith(".webp"):
            with zipfile.ZipFile(apk_path, "r") as z:
                with z.open(icon_res_path) as zf, open(out_path, "wb") as f:
                    f.write(zf.read())
            return True

        # Step 2b: adaptive icon XML
        bg_res_id, fg_res_id = _parse_adaptive_icon(icon_res_path, apk_path, aapt2)
        if not fg_res_id:
            return False

        fg_file = _find_best_image_for_res_id(fg_res_id, apk_path, aapt2)
        if not fg_file:
            # Fallback to legacy PNG if adaptive icon foreground is not a raster image (e.g. is XML/vector)
            lines = _dump_resources(apk_path, aapt2)
            root_res_id = None
            current_res_id = None
            for line in lines:
                if "resource 0x" in line:
                    m = re.search(r"resource (0x[0-9a-fA-F]+)", line)
                    if m:
                        current_res_id = m.group(1)
                elif icon_res_path in line and current_res_id:
                    root_res_id = current_res_id
                    break
            if root_res_id:
                legacy_file = _find_best_image_for_res_id(root_res_id, apk_path, aapt2)
                if legacy_file:
                    with zipfile.ZipFile(apk_path, "r") as z:
                        with z.open(legacy_file) as zf, open(out_path, "wb") as f:
                            f.write(zf.read())
                    return True
            return False

        # Determine background
        bg_file = _find_best_image_for_res_id(bg_res_id, apk_path, aapt2) if bg_res_id else None
        bg_color = None
        if not bg_file and bg_res_id:
            bg_color = _extract_solid_color_from_xml_res(bg_res_id, apk_path, aapt2)

        # Step 3: composite with ImageMagick
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(apk_path, "r") as z:
                fg_local = os.path.join(tmpdir, "fg")
                with z.open(fg_file) as zf, open(fg_local, "wb") as f:
                    f.write(zf.read())

                if bg_file:
                    bg_local = os.path.join(tmpdir, "bg")
                    with z.open(bg_file) as zf, open(bg_local, "wb") as f:
                        f.write(zf.read())
                    subprocess.run([
                        "convert",
                        bg_local, "-resize", "432x432!", "-colorspace", "sRGB",
                        fg_local, "-resize", "432x432!",
                        "-composite", out_path
                    ], check=True)
                else:
                    fill = bg_color or "none"  # transparent if unknown
                    subprocess.run([
                        "convert",
                        "-size", "432x432", f"xc:{fill}",
                        fg_local, "-resize", "432x432!",
                        "-composite", out_path
                    ], check=True)

        return True

    except Exception as e:
        print(f"Warning: Failed to extract icon for {apk_path}: {e}")
    return False
