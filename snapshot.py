#!/usr/bin/env python3
"""Uloží seznam fotek z alba na Zoneramě do w/data/<albumId>.json.

Widget primárně čte data živě přes CORS proxy. Když proxy nedojede,
sáhne po tomhle snapshotu na GitHub Pages, takže galerie funguje i bez ní.

Použití:
    python3 snapshot.py https://eu.zonerama.com/N322T/Album/15900167
"""

import html as htmllib
import json
import re
import subprocess
import sys
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
DATA = Path(__file__).parent / "w" / "data"


def get(url):
    # přes curl, systémovému Pythonu na macu chybí CA balík
    r = subprocess.run(["curl", "-sfL", "-A", UA, url], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"Nepodařilo se stáhnout {url} (curl {r.returncode})")
    return r.stdout.decode("utf-8", "replace")


def meta(page, prop):
    m = re.search(r'<meta property="%s" content="([^"]*)"' % re.escape(prop), page)
    return htmllib.unescape(m.group(1)) if m else ""


def photos_from(items, seen):
    out = []
    for it in items:
        pid = it.get("photoId")
        if not pid or pid in seen:  # položky bez photoId jsou reklamní bannery
            continue
        seen.add(pid)
        out.append({"id": pid, "w": it["width"], "h": it["height"]})
    return out


def main(album_url):
    m = re.search(r"/Album/(\d+)", album_url)
    if not m:
        sys.exit("V URL alba chybí /Album/<id>")
    album_id = m.group(1)
    host = re.match(r"https?://[^/]+", album_url).group(0)

    page = get(album_url)
    if meta(page, "znrm:public") == "false":
        sys.exit("Album není veřejné.")
    title = meta(page, "og:title") or "Fotogalerie"

    seen = set()
    start = page.index("{", page.index("var result = "))
    first, _ = json.JSONDecoder().raw_decode(page[start:])
    photos = photos_from(first["items"], seen)
    index = len(first["items"])
    is_end = first["isEnd"]

    while not is_end and index <= 10000:
        batch = json.loads(get(
            f"{host}/JSON/FlowLayout_PhotosInAlbum?albumId={album_id}"
            f"&startIndex={index}&count=200"
        ))
        items = batch.get("items") or []
        if not items:
            break
        photos += photos_from(items, seen)
        index += len(items)
        is_end = batch.get("isEnd", True)

    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"{album_id}.json"
    out.write_text(json.dumps({
        "title": title,
        "host": host,
        "albumUrl": album_url,
        "photos": photos,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"{title}: {len(photos)} fotek → {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
