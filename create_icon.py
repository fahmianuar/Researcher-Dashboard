# -*- coding: utf-8 -*-
"""
AcademiX Icon Generator + Build Helper
Run once before building the executable:
    python create_icon.py
Requires: pip install pillow
"""
import sys
import os
import struct
import zlib

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def create_icon_pillow():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        m = max(1, size // 16)
        # Background circle
        draw.ellipse([m, m, size-m-1, size-m-1],
                     fill=(22, 28, 48, 255))
        # Accent ring
        rw = max(1, size // 12)
        draw.ellipse([m, m, size-m-1, size-m-1],
                     outline=(94, 173, 242, 255), width=rw)

        # Letter A
        font_size = int(size * 0.52)
        font = None
        try:
            if sys.platform == "win32":
                for fname in ["arialbd.ttf", "arial.ttf", "segoeui.ttf"]:
                    try:
                        font = ImageFont.truetype(fname, font_size)
                        break
                    except Exception:
                        pass
            if font is None:
                font = ImageFont.load_default()
        except Exception:
            font = None

        if font and size >= 16:
            try:
                bbox = draw.textbbox((0, 0), "A", font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                tx = (size - tw) // 2 - bbox[0]
                ty = (size - th) // 2 - bbox[1] - max(0, size // 20)
                draw.text((tx+1, ty+1), "A", font=font, fill=(0,0,0,100))
                draw.text((tx, ty), "A", font=font, fill=(94,173,242,255))
            except Exception:
                _draw_A_manual(draw, size)
        else:
            _draw_A_manual(draw, size)

        images.append(img)

    images[0].save(
        "academix.ico", format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print("Created: academix.ico")
    images[-1].save("academix_256.png", format="PNG")
    print("Created: academix_256.png")


def _draw_A_manual(draw, size):
    cx   = size // 2
    top  = size // 5
    bot  = size * 4 // 5
    lw   = max(1, size // 10)
    col  = (94, 173, 242, 255)
    draw.line([(cx - size//4, bot), (cx, top)],    fill=col, width=lw)
    draw.line([(cx, top), (cx + size//4, bot)],    fill=col, width=lw)
    draw.line([(cx - size//7, size//2 + size//10),
               (cx + size//7, size//2 + size//10)], fill=col, width=lw)


def create_icon_basic():
    def make_png(size, bg, fg, rw):
        cx = cy = size / 2
        ro = size / 2 - 1
        ri = ro - rw
        raw = b""
        for y in range(size):
            raw += b"\x00"
            for x in range(size):
                dx = x + 0.5 - cx
                dy = y + 0.5 - cy
                d  = (dx*dx + dy*dy) ** 0.5
                if d <= ri:
                    raw += bytes(bg + [255])
                elif d <= ro:
                    raw += bytes(fg + [255])
                else:
                    raw += b"\x00\x00\x00\x00"

        def chunk(name, data):
            c = struct.pack(">I", len(data)) + name + data
            return c + struct.pack(">I", zlib.crc32(c[4:]) & 0xFFFFFFFF)

        png  = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 6))
        png += chunk(b"IEND", b"")
        return png

    bg  = [22, 28, 48]
    fg  = [94, 173, 242]
    entries_spec = [(16,2),(32,3),(48,4),(64,5),(128,8),(256,14)]
    pngs = [(s, make_png(s, bg, fg, rw)) for s, rw in entries_spec]

    n   = len(pngs)
    off = 6 + n * 16
    hdr = struct.pack("<HHH", 0, 1, n)
    ent = b""
    dat = b""
    for s, p in pngs:
        ss = s if s < 256 else 0
        ent += struct.pack("<BBBBHHII", ss, ss, 0, 0, 1, 32, len(p), off)
        dat += p
        off += len(p)

    with open("academix.ico", "wb") as f:
        f.write(hdr + ent + dat)
    print("Created: academix.ico (basic ring icon)")


if __name__ == "__main__":
    print("=== AcademiX Icon Generator ===")
    if HAS_PILLOW:
        print("Pillow found - creating high quality icon...")
        create_icon_pillow()
    else:
        print("Pillow not found - creating basic icon...")
        print("For a better result: pip install pillow")
        create_icon_basic()

    print()
    print("=== Icon created! ===")
    print()
    print("Now build the standalone executable by running:")
    print()
    print("  pyinstaller --onefile --windowed --icon=academix.ico --name=AcademiX academix.py")
    print()
    print("The .exe will appear in the  dist  folder when done.")
