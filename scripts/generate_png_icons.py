"""
generate_png_icons.py
Pure Python standard library script to render the Bolti Slip icon at 192x192 and 512x512 PNGs.
Zero dependencies (uses struct and zlib).
"""
import zlib
import struct
import math
from pathlib import Path

def create_png(width, height, rgba_data):
    # PNG signature
    png = bytearray(b'\x89PNG\r\n\x1a\n')
    
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    png.extend(struct.pack('>I', len(ihdr_data)))
    png.extend(b'IHDR')
    png.extend(ihdr_data)
    png.extend(struct.pack('>I', ihdr_crc))
    
    # IDAT
    # Each row starts with filter type 0
    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0)
        start = y * width * 4
        raw_data.extend(rgba_data[start:start + width * 4])
        
    compressed = zlib.compress(raw_data, 9)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    png.extend(struct.pack('>I', len(compressed)))
    png.extend(b'IDAT')
    png.extend(compressed)
    png.extend(struct.pack('>I', idat_crc))
    
    # IEND
    iend_crc = zlib.crc32(b'IEND')
    png.extend(struct.pack('>I', 0))
    png.extend(b'IEND')
    png.extend(struct.pack('>I', iend_crc))
    
    return bytes(png)

def is_inside_icon(x, y):
    # Coordinates in 512x512 space
    # 1. Background rounded rect: width 512, height 512, rx 128
    in_bg = False
    rx = 128.0
    if x < 0 or x >= 512 or y < 0 or y >= 512:
        return False, False
        
    # Check 4 corners of bg
    if x < rx and y < rx:
        in_bg = ((x - rx)**2 + (y - rx)**2) <= rx**2
    elif x > (512 - rx) and y < rx:
        in_bg = ((x - (512 - rx))**2 + (y - rx)**2) <= rx**2
    elif x < rx and y > (512 - rx):
        in_bg = ((x - rx)**2 + (y - (512 - rx))**2) <= rx**2
    elif x > (512 - rx) and y > (512 - rx):
        in_bg = ((x - (512 - rx))**2 + (y - (512 - rx))**2) <= rx**2
    else:
        in_bg = True
        
    if not in_bg:
        return False, False
        
    # 2. Check microphone foreground
    # Capsule (mic head)
    # x in [192, 320], radius = 64, center_x = 256
    # Top arc center: (256, 184), Bottom arc center: (256, 280)
    in_mic = False
    if 184 <= y <= 280 and abs(x - 256) <= 64:
        in_mic = True
    elif y < 184 and ((x - 256)**2 + (y - 184)**2) <= 64**2:
        in_mic = True
    elif y > 280 and ((x - 256)**2 + (y - 280)**2) <= 64**2:
        in_mic = True
        
    # Cradle U-curve:
    # Outer radius 120, Inner radius 88, Center (256, 248)
    if not in_mic and y >= 248:
        dist_sq = (x - 256)**2 + (y - 248)**2
        if 88**2 <= dist_sq <= 120**2 and y <= 368:
            in_mic = True
            
    # Stem:
    # y from 366 to 408, width 32 (x in [240, 272])
    if not in_mic and 366 <= y <= 408 and abs(x - 256) <= 16:
        in_mic = True
        
    # Base:
    # y from 408 to 440, width 132 (x in [190, 322])
    if not in_mic and 408 <= y <= 440 and abs(x - 256) <= 66:
        in_mic = True
        
    return in_bg, in_mic

def render_icon(size):
    # Render with 4x supersampling for crisp anti-aliasing
    scale = 512.0 / size
    subsamples = 4
    sub_step = 1.0 / subsamples
    
    rgba = bytearray()
    
    # Colors:
    # BG: #4F46E5 -> R=79, G=70, B=229
    # FG: #FFFFFF -> R=255, G=255, B=255
    bg_r, bg_g, bg_b = 79, 70, 229
    fg_r, fg_g, fg_b = 255, 255, 255
    
    for py in range(size):
        for px in range(size):
            bg_hits = 0
            mic_hits = 0
            total_samples = subsamples * subsamples
            
            for sy in range(subsamples):
                for sx in range(subsamples):
                    fx = (px + (sx + 0.5) * sub_step) * scale
                    fy = (py + (sy + 0.5) * sub_step) * scale
                    in_bg, in_mic = is_inside_icon(fx, fy)
                    if in_mic:
                        mic_hits += 1
                        bg_hits += 1
                    elif in_bg:
                        bg_hits += 1
                        
            if bg_hits == 0:
                # Transparent
                rgba.extend([0, 0, 0, 0])
            else:
                alpha = int(255 * (bg_hits / total_samples))
                # Mix mic (white) and background (indigo)
                mic_ratio = mic_hits / bg_hits
                r = int(bg_r * (1 - mic_ratio) + fg_r * mic_ratio)
                g = int(bg_g * (1 - mic_ratio) + fg_g * mic_ratio)
                b = int(bg_b * (1 - mic_ratio) + fg_b * mic_ratio)
                rgba.extend([r, g, b, alpha])
                
    return create_png(size, size, rgba)

def main():
    icons_dir = Path(r"c:\Programs\Project\Bolti-Slip\frontend\public\icons")
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating icon-192.png...")
    png_192 = render_icon(192)
    (icons_dir / "icon-192.png").write_bytes(png_192)
    print(f"  -> icon-192.png written ({len(png_192)} bytes)")
    
    print("Generating icon-512.png...")
    png_512 = render_icon(512)
    (icons_dir / "icon-512.png").write_bytes(png_512)
    print(f"  -> icon-512.png written ({len(png_512)} bytes)")
    
    print("Generating icon-maskable-192.png and icon-maskable-512.png...")
    # For maskable icons, provide padding or full bleed
    (icons_dir / "icon-maskable-192.png").write_bytes(png_192)
    (icons_dir / "icon-maskable-512.png").write_bytes(png_512)
    print("Done!")

if __name__ == "__main__":
    main()
