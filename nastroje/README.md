# Převod videa pro web

Honza fotí a filmuje na kameru, která ukládá **surové mastery**: 4K, H.265,
24 Mbit/s. Ukázka z 2. 10. 2026 — minuta a půl videa měla **279 MB**.

Takový soubor na web nepatří ze dvou důvodů:

1. **H.265 Firefox nepřehraje vůbec** a Chrome jen na některých počítačích.
   Část návštěvníků by viděla jen černé místo.
2. Stahuje se nekonečně dlouho, protože se tahá celý soubor.

## Jak na to

Přetáhni video myší na **`prevod-videa.cmd`**. Vedle originálu vznikne
`<název>-web.mp4` — ten se nahrává do Odoo. Originál zůstane nedotčený.

Můžeš přetáhnout i víc videí najednou, zpracují se po sobě.

Převod trvá asi dvakrát delší dobu, než je samo video (minuta a půl videa
≈ dvě a půl minuty převodu).

## Co z toho vyjde

Naměřeno na tom Honzovu videu:

| | před | po |
|---|---|---|
| velikost | 279 MB | **24,1 MB** |
| kodek | H.265 | H.264 (jede všude) |
| rozlišení | 3840 × 2160 | 1920 × 1080 |
| délka | 1:34 | 1:34 (bit za bit stejná) |

Svislá videa na mobil zůstanou svislá — orientace se nemění, jen se zkrátí
nejdelší strana na 1920 px.

## Nahrání do Odoo

V editoru stránky klikni na blok s videem a v pravém panelu použij:

- **Nahrát video** — vodorovná verze pro počítač
- **Nahrát video na mobil** — svislá verze
- **Nahrát titulky** — soubor `.vtt`

## Když skript hlásí, že nenašel ffmpeg

```
winget install Gyan.FFmpeg
```

Potom otevři nové okno příkazové řádky (skript hledá ffmpeg i v instalaci
z wingetu, takže restart počítače není potřeba).
