#!/usr/bin/env python3
"""Z fotek v lokální složce udělá album hostované u nás (bez Zoneramy).

Zonerama od 10/2026 vrací na fotky vložené mimo svůj web obrázek
„Bot Detected". Fotky od obce (stažené z jejich alba) proto zmenšíme
a uložíme do w/data/<albumId>/, seznam do w/data/<albumId>.json.
Widget pak u takového alba sahá jen na tyhle soubory.

Použití:
    python3 hosted.py <složka s fotkami> <albumId nebo URL alba>
    python3 hosted.py ~/Downloads/turnaj https://eu.zonerama.com/N322T/Album/15900167

Zmenšuje přes sips (macOS). Fotky se řadí podle názvu souboru.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).parent / "w" / "data"
THUMB_H = 400   # výška náhledu v mřížce (px)
BIG_MAX = 1800  # delší strana fotky v prohlížeči (px)
EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def size(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                         capture_output=True, text=True, check=True).stdout
    w = int(re.search(r"pixelWidth: (\d+)", out).group(1))
    h = int(re.search(r"pixelHeight: (\d+)", out).group(1))
    return w, h


def resize(src, dst, w, h):
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                    "-z", str(h), str(w), str(src), "--out", str(dst)],
                   capture_output=True, check=True)


def main(folder, album):
    m = re.search(r"(\d+)\D*$", album)
    if not m:
        sys.exit("Chybí albumId (číslo alba ze Zoneramy).")
    album_id = m.group(1)
    files = sorted(p for p in Path(folder).expanduser().iterdir()
                   if p.suffix.lower() in EXT and not p.name.startswith("."))
    if not files:
        sys.exit(f"Ve složce {folder} nejsou žádné fotky.")

    out = DATA / album_id
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    photos = []
    for i, f in enumerate(files, 1):
        # sips -g vrací rozměry bez ohledu na EXIF orientaci, proto nejdřív
        # vyrobíme velkou verzi (sips ji otočí správně) a rozměry čteme z ní
        big = out / f"{i:04d}.jpg"
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82"]
        if max(size(f)) > BIG_MAX:  # menší fotky nezvětšujeme
            cmd += ["-Z", str(BIG_MAX)]
        subprocess.run(cmd + [str(f), "--out", str(big)], capture_output=True, check=True)
        w, h = size(big)
        thumb = out / f"{i:04d}_t.jpg"
        resize(big, thumb, max(1, round(THUMB_H * w / h)), THUMB_H)
        photos.append({"id": i, "w": w, "h": h,
                       "t": f"{album_id}/{thumb.name}", "b": f"{album_id}/{big.name}"})
        print(f"\r{i}/{len(files)}", end="", flush=True)

    (DATA / f"{album_id}.json").write_text(
        json.dumps({"albumId": album_id, "hosted": True, "photos": photos},
                   ensure_ascii=False, indent=1) + "\n")
    mb = sum(p.stat().st_size for p in out.iterdir()) / 1e6
    print(f"\nHotovo: {len(photos)} fotek, {mb:.1f} MB v {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
