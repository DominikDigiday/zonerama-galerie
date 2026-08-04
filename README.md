# Fotogalerie ze Zoneramy

Widget, který z veřejného alba na [Zoneramě](https://zonerama.com) udělá galerii vloženou
do webu obce jako iframe. Fotky zůstávají na Zoneramě a načítají se přímo z jejího CDN,
web je jen zobrazuje.

- **Generátor:** <https://dominikdigiday.github.io/zonerama-galerie/>
- **Widget:** <https://dominikdigiday.github.io/zonerama-galerie/w/?album=...>

## Jak to použít

1. Otevřít generátor, vložit odkaz na album (např. `https://eu.zonerama.com/N322T/Album/15900167`).
2. Nastavit nadpis, velikost dlaždic a barevné schéma.
3. Zkopírovat vygenerovaný iframe do stránky.

Album musí být veřejné, tedy bez hesla a bez tajného odkazu.

## Parametry widgetu

| Parametr | Hodnoty | Popis |
|---|---|---|
| `album` | URL alba nebo jen číslo alba | povinné |
| `title` | text | nadpis nad galerií, bez něj se hlavička nezobrazí |
| `size` | `s`, `m`, `l` | výška řad dlaždic, výchozí `m` |
| `theme` | `dark` | tmavá varianta, výchozí je světlá |
| `bg` | `transparent` | průhledné pozadí, aby prosvítal web pod iframem |
| `link` | `0` | skryje odkaz na album na Zoneramě |

## Automatická výška iframu

Widget hlásí svou výšku rodičovské stránce přes `postMessage`. Bez skriptu níže má iframe
pevnou výšku a uvnitř se roluje.

```html
<script>
window.addEventListener("message", function (e) {
  if (!e.data || e.data.type !== "zonerama-galerie-height") return;
  var f = document.getElementById("zonerama-galerie");
  if (f) f.style.height = e.data.height + "px";
});
</script>
```

## Záložní snapshot alba

Když proxy nedojede, widget sáhne po uloženém seznamu fotek v `w/data/<albumId>.json`,
takže galerie funguje dál. Snapshot se pořídí a aktualizuje takhle:

```bash
python3 snapshot.py https://eu.zonerama.com/N322T/Album/15900167
git add w/data && git commit -m "Snapshot alba" && git push
```

Snapshot obsahuje jen ID a rozměry fotek, obrázky se pořád berou ze Zoneramy. Když se do
alba přidají nové fotky, je potřeba ho pustit znovu (přes proxy se načtou samy).

## Jak to funguje

Zonerama nemá veřejné API a neposílá CORS hlavičky, takže seznam fotek nejde z prohlížeče
načíst napřímo. Widget čte interní endpoint `/JSON/FlowLayout_PhotosInAlbum` přes CORS proxy
`zonerama-proxy.vercel.app/api/fetch` (whitelist domén, lokálně `~/projects/zonerama-proxy`).
Přes proxy tečou jen metadata fotek, samotné obrázky jdou přímo z CDN Zoneramy.

Náhledy se tahají ve variantě `_{w}x{h}_18.jpg`, ve velkém zobrazení do 1800 px na delší
straně, odkaz „Originál“ míří na plné rozlišení.

Protože jde o nezdokumentovaný endpoint, může ho Zonerama kdykoli změnit. Pokud galerie
přestane načítat fotky, je to první místo, kde hledat.
