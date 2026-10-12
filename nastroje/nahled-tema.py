# -*- coding: utf-8 -*-
"""Náhledy našich návrhů do galerie editoru.

Editor si z cesty v data-img skládá dvě jména: _small.png do
dlaždice a _large.png do velkého náhledu. Oba musí mít přesně ty
rozměry, co mají vestavěné náhledy Odoo, jinak se dlaždice rozjede.

Kreslí se schematicky, ne screenshotem: jde o to poznat návrh na
první pohled podle barev a rozvržení, ne přečíst si text.

Pouští se uvnitř kontejneru (je tam Pillow i písma):

    docker cp nastroje/nahled-tema.py <kontejner>:/tmp/
    docker compose -p hauzr exec -T odoo python3 /tmp/nahled-tema.py
"""
from PIL import Image, ImageDraw, ImageFont

MALY = (156, 169)
VELKY = (500, 542)

ROBOTO = '/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-%s.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-%s.ttf'


def barva(text):
    text = text.lstrip('#')
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def nahled(navrh, sirka, vyska, cesta):
    """Vykreslí schéma návrhu. Vše se počítá z šířky, aby malý
    i velký obrázek vypadaly stejně, jen v jiném měřítku."""
    m = 3
    S, V = sirka * m, vyska * m
    u = S / 156.0

    o = Image.new('RGB', (S, V), barva(navrh['stranka']))
    k = ImageDraw.Draw(o)

    okraj = 9 * u
    k.rectangle([okraj, okraj, S - okraj, V - okraj],
                fill=barva(navrh['karta']),
                outline=barva(navrh['linka']), width=max(1, int(u)))

    x = okraj + 9 * u
    sir = S - 2 * okraj - 18 * u

    def pismo(cesta_pisma, rez, velikost):
        return ImageFont.truetype(cesta_pisma % rez, int(velikost * u))

    y = okraj + 9 * u
    k.text((x, y), navrh['znacka'], font=pismo(ROBOTO, 'Bold', 5),
           fill=barva(navrh['grafit']))
    y += 11 * u
    k.line([(okraj, y), (S - okraj, y)], fill=barva(navrh['linka']),
           width=max(1, int(u)))

    y += 11 * u
    k.text((x, y), navrh['eyebrow'], font=pismo(ROBOTO, 'Bold', 4.5),
           fill=barva(navrh['akcent']))
    y += 9 * u
    k.text((x, y), 'Nadpis zprávy',
           font=pismo(SERIF if navrh['serif'] else ROBOTO, 'Bold', 11),
           fill=barva(navrh['grafit']))
    y += 16 * u

    if navrh.get('prah'):
        k.rectangle([x, y, x + 15 * u, y + 1.5 * u], fill=barva(navrh['akcent']))
        y += 7 * u

    for sirka_radku in (1, 0.93):
        k.rectangle([x, y, x + sir * sirka_radku, y + 3 * u],
                    fill=barva(navrh['sede']))
        y += 7 * u

    if navrh.get('tmavy_blok'):
        y += 3 * u
        tmava = barva(navrh.get('blok') or navrh['grafit'])
        k.rectangle([x, y, x + sir, y + 17 * u], fill=tmava)
        k.rectangle([x, y, x + 1.5 * u, y + 17 * u], fill=barva(navrh['akcent']))
        for i, w in enumerate((0.72, 0.5)):
            k.rectangle([x + 6 * u, y + (5 + i * 6) * u,
                         x + 6 * u + (sir - 12 * u) * w,
                         y + (8 + i * 6) * u], fill=barva(navrh.get('blok_text') or navrh['karta']))
        y += 18 * u
    else:
        k.rectangle([x, y, x + sir * 0.58, y + 3 * u], fill=barva(navrh['sede']))
        y += 12 * u

    sirt, vyst = sir * 0.62, 14 * u
    lx = x + (sir - sirt) / 2
    k.rectangle([lx, y, lx + sirt, y + vyst], fill=barva(navrh['tlacitko']))
    t, f = 'TLAČÍTKO', pismo(ROBOTO, 'Bold', 5)
    l, tt, r, b = k.textbbox((0, 0), t, font=f)
    k.text((lx + (sirt - (r - l)) / 2, y + (vyst - (b - tt)) / 2 - tt),
           t, font=f, fill=(255, 255, 255))
    y += vyst + 7 * u

    k.line([(okraj, y), (S - okraj, y)], fill=barva(navrh['linka']),
           width=max(1, int(u)))
    y += 6 * u
    k.text((x, y), 'Honza',
           font=pismo(SERIF if navrh['serif'] else ROBOTO, 'Bold', 6),
           fill=barva(navrh['grafit']))

    # Paticka. U editorialu tmavy pruh u spodniho okraje karty.
    if navrh.get('tmava_paticka'):
        ph = 13 * u
        k.rectangle([okraj + 1, V - okraj - ph, S - okraj - 1, V - okraj - 1],
                    fill=barva(navrh.get('paticka') or navrh['grafit']))

    o.resize((sirka, vyska), Image.LANCZOS).save(cesta)


NAVRHY = {
    'tema_vr': {
        'stranka': '#f4efe6', 'karta': '#ffffff', 'linka': '#e2dacb',
        'grafit': '#23211d', 'akcent': '#a89681', 'sede': '#ded9d1',
        'tlacitko': '#23211d', 'znacka': 'VLASTNÍ REŽIE',
        'eyebrow': 'DEN 1 · VÝZVA', 'serif': False,
    },
    'tema_tmava': {
        'stranka': '#0a0a0f', 'karta': '#111a26', 'linka': '#1e2c40',
        'grafit': '#ffffff', 'akcent': '#6bb5ff', 'sede': '#2a3647',
        'tlacitko': '#2aa6ee', 'znacka': 'HONZA HAUZR',
        'eyebrow': 'VÍTEJ VE VLASTNÍ REŽII', 'serif': True,
        'prah': True, 'tmavy_blok': True, 'tmava_paticka': True,
        'blok': '#0d141e', 'blok_text': '#6bb5ff', 'paticka': '#0a0a0f',
    },
    'tema_editorial': {
        'stranka': '#efe7d8', 'karta': '#f4efe6', 'linka': '#e3d9c8',
        'grafit': '#23211d', 'akcent': '#a06a37', 'sede': '#ddd4c4',
        'tlacitko': '#a06a37', 'znacka': 'VLASTNÍ REŽIE',
        'eyebrow': 'TVŮJ TAH · PO VÝZVĚ', 'serif': True,
        'prah': True, 'tmavy_blok': True, 'tmava_paticka': True,
    },
}

for jmeno, navrh in NAVRHY.items():
    nahled(navrh, *MALY, '/tmp/%s_small.png' % jmeno)
    nahled(navrh, *VELKY, '/tmp/%s_large.png' % jmeno)
    print('hotovo:', jmeno)
