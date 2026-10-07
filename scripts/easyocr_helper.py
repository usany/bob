#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""easyocr_helper.py — OCR helper invoked by scripts/khu_crawler.ts

Reads text from notice images using easyocr (ko + en).
Usage:
    python3 easyocr_helper.py <image_path> [image_path ...]

Prints a single JSON document to stdout:
    { "result": [ { "file": "<basename>", "text": "...", "count": N }, ... ] }

easyocr model weights are cached on first run (~/.EasyOCR) so the first call is slow.

Large images (e.g. 3000x4600 notice posters) are downscaled to MAX_DIM before OCR:
easyocr on CPU gets extremely slow (effectively hangs) on huge inputs, and this
keeps runtime bounded while preserving enough detail for Korean text detection.
"""
import io
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

# Downscale longest edge above this to keep CPU OCR fast & bounded.
MAX_DIM = 1600


def prepare_image(raw: bytes, mode: str = "RGB") -> bytes:
    """Decode, downscale if needed, and re-encode to PNG bytes for easyocr."""
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    # RGBA needs flattening onto white, otherwise easyocr can choke on alpha.
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if max(im.size) > MAX_DIM:
        im.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    # Force UTF-8 on stdout. On Windows, Python writes the console code page
    # (e.g. cp949) by default, which corrupts Hangul when the Node.js caller
    # decodes stdout as UTF-8 (it turns into '\ufffd' + Cyrillic garbage).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    paths = [p for p in sys.argv[1:] if os.path.exists(p)]
    if not paths:
        print(json.dumps({"result": []}, ensure_ascii=False))
        return

    import easyocr

    # ko + en; CPU only to avoid GPU dependency issues on mac homebrew builds.
    reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)

    result: list = []
    for p in paths:
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
            data = prepare_image(raw)
            # paragraph=True groups fragment lines; detail=0 returns plain text lines.
            lines = reader.readtext(data, detail=0, paragraph=True)
            text = "\n".join(str(x) for x in lines if str(x).strip())
        except Exception as exc:  # per-file errors must not kill the whole batch
            text = f"[OCR error: {exc}]"
        result.append(
            {
                "file": os.path.basename(p),
                "text": text,
                "count": len([l for l in text.splitlines() if l.strip()]),
            }
        )

    print(json.dumps({"result": result}, ensure_ascii=False))

if __name__ == "__main__":
    main()
