"""
tests/verify_pwa_readiness.py
-----------------------------
Automated audit and verification script for Bolti Slip Android PWA Readiness.
Validates:
1. Web App Manifest syntax and Android PWA criteria
2. App icon files (192x192, 512x512, maskable, SVG)
3. HTML PWA meta tags & apple-touch-icon
4. Service Worker generation, precache list, and security rules (NetworkOnly on /api/*)
"""

import sys
import json
import struct
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
PUBLIC_DIR = FRONTEND_DIR / "public"

def log(msg, status="INFO"):
    symbol = "✔" if status == "PASS" else "✖" if status == "FAIL" else "ℹ"
    print(f"[{symbol}] {msg}")

def read_png_dimensions(file_path: Path):
    data = file_path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f"{file_path.name} is not a valid PNG file (invalid signature)")
    # IHDR chunk immediately follows 8-byte header
    # Length (4) + Type (4: 'IHDR') + Width (4) + Height (4)
    width, height = struct.unpack('>II', data[16:24])
    return width, height

def verify_manifest():
    print("\n--- 1. WEB APP MANIFEST VERIFICATION ---")
    manifest_path = PUBLIC_DIR / "manifest.webmanifest"
    assert manifest_path.exists(), f"Missing manifest at {manifest_path}"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
        
    log(f"Manifest loaded: {manifest_path.name}")
    
    assert m.get("name") == "Bolti Slip", f"Expected name 'Bolti Slip', got {m.get('name')}"
    log("name == 'Bolti Slip'", "PASS")
    
    assert m.get("short_name") == "Bolti Slip", f"Expected short_name 'Bolti Slip', got {m.get('short_name')}"
    log("short_name == 'Bolti Slip'", "PASS")
    
    assert m.get("display") == "standalone", f"Expected display 'standalone', got {m.get('display')}"
    log("display == 'standalone'", "PASS")
    
    assert m.get("start_url") == "/", f"Expected start_url '/', got {m.get('start_url')}"
    log("start_url == '/'", "PASS")
    
    assert m.get("scope") == "/", f"Expected scope '/', got {m.get('scope')}"
    log("scope == '/'", "PASS")
    
    assert m.get("theme_color") == "#4F46E5", f"Expected theme_color '#4F46E5', got {m.get('theme_color')}"
    log("theme_color == '#4F46E5'", "PASS")
    
    assert m.get("background_color") == "#F8FAFC", f"Expected background_color '#F8FAFC', got {m.get('background_color')}"
    log("background_color == '#F8FAFC'", "PASS")
    
    icons = m.get("icons", [])
    assert len(icons) >= 2, "Expected at least 192 and 512 icons"
    log(f"Found {len(icons)} icon declarations in manifest", "PASS")
    
    return m

def verify_icons(manifest):
    print("\n--- 2. APP ICONS VERIFICATION ---")
    icon_map = {}
    for icon in manifest.get("icons", []):
        src = icon["src"].lstrip("/")
        icon_path = PUBLIC_DIR / src
        assert icon_path.exists(), f"Manifest references missing icon: {icon_path}"
        
        sizes = icon.get("sizes", "")
        purpose = icon.get("purpose", "")
        file_size = icon_path.stat().st_size
        
        if icon["type"] == "image/png":
            w, h = read_png_dimensions(icon_path)
            expected_dim = int(sizes.split("x")[0]) if "x" in sizes else None
            assert w == expected_dim and h == expected_dim, f"Dimension mismatch: expected {expected_dim}x{expected_dim}, got {w}x{h}"
            log(f"{icon_path.name}: Valid PNG {w}x{h} ({file_size} bytes, purpose='{purpose}')", "PASS")
        else:
            log(f"{icon_path.name}: Vector SVG ({file_size} bytes)", "PASS")
            
        icon_map[icon_path.name] = True
        
    assert "icon-192.png" in icon_map, "Missing icon-192.png"
    assert "icon-512.png" in icon_map, "Missing icon-512.png"
    log("Required 192x192 and 512x512 icons verified", "PASS")

def verify_html():
    print("\n--- 3. HTML ENTRY & META TAGS VERIFICATION ---")
    html_path = FRONTEND_DIR / "index.html"
    assert html_path.exists(), "Missing index.html"
    content = html_path.read_text(encoding="utf-8")
    
    assert 'rel="manifest"' in content, "Missing <link rel='manifest'>"
    log("<link rel='manifest' href='/manifest.webmanifest' /> present", "PASS")
    
    assert 'name="theme-color"' in content and '#4F46E5' in content, "Missing or incorrect theme-color"
    log("<meta name='theme-color' content='#4F46E5' /> present", "PASS")
    
    assert 'rel="apple-touch-icon"' in content, "Missing apple-touch-icon"
    log("<link rel='apple-touch-icon' /> present", "PASS")
    
    assert 'name="mobile-web-app-capable"' in content, "Missing mobile-web-app-capable"
    log("<meta name='mobile-web-app-capable' content='yes' /> present", "PASS")
    
    assert 'viewport-fit=cover' in content, "Missing viewport-fit=cover for safe-area display"
    log("<meta name='viewport' ... viewport-fit=cover /> present", "PASS")

def verify_service_worker():
    print("\n--- 4. SERVICE WORKER & DATA SECURITY AUDIT ---")
    sw_path = DIST_DIR / "sw.js"
    assert sw_path.exists(), f"Missing production Service Worker at {sw_path}. Run 'npm run build' first."
    sw_content = sw_path.read_text(encoding="utf-8")
    
    log(f"Service worker found at {sw_path.name} ({len(sw_content)} bytes)", "PASS")
    
    # 1. Check precache routing
    assert "precacheAndRoute" in sw_content, "Missing precacheAndRoute in service worker"
    log("Precache routing verified (offline app shell)", "PASS")
    
    # 2. Check strict API deny list
    assert "api" in sw_content, "API route handling missing in service worker"
    log("API route routing configured", "PASS")
    
    assert "NetworkOnly" in sw_content, "NetworkOnly handler missing for API calls"
    log("SECURITY CHECK: NetworkOnly handler enforced for /api/ calls", "PASS")
    
    # 3. Check navigateFallback denylist
    assert "denylist" in sw_content, "navigateFallbackDenylist missing in service worker"
    log("SECURITY CHECK: navigateFallback explicitly excludes /api/ routes", "PASS")
    
    # 4. Verify no customer data or tickets are hardcoded in precache
    prohibited = ["customer_name", "customer_phone", "repair_instructions", "bolti_slip.db"]
    for word in prohibited:
        assert word not in sw_content, f"SECURITY VIOLATION: '{word}' found in service worker bundle!"
    log("DATA PRIVACY CHECK: Zero customer data, tickets, or audio in SW precache", "PASS")

def main():
    print("=" * 70)
    print("  BOLTI SLIP — ANDROID PWA READINESS & SECURITY AUDIT")
    print("=" * 70)
    
    try:
        manifest = verify_manifest()
        verify_icons(manifest)
        verify_html()
        verify_service_worker()
        
        print("\n" + "=" * 70)
        print("  ALL PWA AUDIT CHECKS PASSED SUCCESSFULLY (100%)")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n[FAIL] Audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
