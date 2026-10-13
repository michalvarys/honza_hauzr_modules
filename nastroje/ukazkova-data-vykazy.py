"""Naplní Výkazy ukázkovými daty, aby nebyly prázdné.

Prázdná tabulka neřekne nic o tom, jak bude vypadat plná: nejde
poznat, jestli je filtr k něčemu, jestli se čísla vejdou do sloupce
ani co bude na první pohled vidět. Tenhle skript proto vyrobí
několik lidí a k nim zhlédnutí videí a kliknutí na webu.

Data jsou poznat na první pohled: e-maily končí na @test.local
a jména jsou obyčejná česká, ne "Lorem Ipsum". Smažou se příkazem
na konci souboru.

Pouští se přes odoo shell:
    docker compose -p hauzr exec -T odoo odoo shell -d hauzr --no-http \
        < nastroje/ukazkova-data-vykazy.py
"""

import random
from datetime import timedelta

from odoo import fields

random.seed(20261013)   # at vypada stejne po kazdem spusteni

ted = fields.Datetime.now()

# ---------------------------------------------------------------- #
# lide                                                              #
# ---------------------------------------------------------------- #

LIDE = [
    # jmeno, odkud prisel, jak daleko doshel ve vyzve (procenta po dnech)
    ('Petr Dvořák', 'Instagram', [100, 100, 100]),
    ('Martin Novák', 'Facebook', [100, 92, 0]),
    ('Jakub Svoboda', 'YouTube', [100, 45, 0]),
    ('Tomáš Procházka', 'Instagram', [78, 0, 0]),
    ('Lukáš Černý', 'Google', [100, 100, 61]),
    ('Ondřej Veselý', 'TikTok', [34, 0, 0]),
    ('David Horák', 'Seznam', [100, 100, 100]),
    ('Michal Kučera', 'Přímo', [0, 0, 0]),
]

# Videa vyzvy. Klic je to, co se ulozi do pole video.
VIDEA_VYZVY = {
    '1': ('vyzva-den-1', 'Den 1: Kde ti utíká čas', 612),
    '2': ('vyzva-den-2', 'Den 2: Jeden malý důkaz', 548),
    '3': ('vyzva-den-3', 'Den 3: Co s tím dál', 703),
}

# Videa mimo vyzvu - ta se meri taky, u kazde stranky zvlast.
VIDEA_WEBU = [
    ('/', 'uvod-honza', 'Kdo jsem a pro koho to dělám', 184),
    ('/tvuj-tah', 'tvuj-tah-program', 'Jak vypadá Tvůj tah', 421),
    ('/tvuj-tah', 'tvuj-tah-reference', 'Co říkají ti, co to prošli', 236),
]

Lead = env['crm.lead'].sudo()
Sledovani = env['hh.vyzva.sledovani'].sudo()
Video = env['hh.video'].sudo()
Klik = env['hh.web.klik'].sudo()
Zdroj = env['utm.mixin'].sudo()

stupen = env['crm.stage'].sudo().search([('name', '=', '3denní výzva')], limit=1)
stitek = env.ref('honzahauzr_crm.tag_vyzva', raise_if_not_found=False)

zalozeno_lidi, zalozeno_radku = 0, 0

for poradi, (jmeno, odkud, procenta) in enumerate(LIDE):
    email = '%s@test.local' % jmeno.split()[0].lower().translate(
        str.maketrans('áčďéěíňóřšťúůýž', 'acdeeinorstuuyz'))
    lead = Lead.search([('email_from', '=', email)], limit=1)
    if not lead:
        lead = Lead.with_context(hh_bez_rady=True).create({
            'name': 'Výzva: Z autopilota zpět do života',
            'contact_name': jmeno,
            'email_from': email,
            'stage_id': stupen.id if stupen else False,
            'tag_ids': [(4, stitek.id)] if stitek else False,
            'hh_zdroj': 'vyzva',
            'source_id': Zdroj._find_or_create_record('utm.source', odkud).id,
            'hh_souhlas': True,
            'hh_souhlas_kdy': ted - timedelta(days=9 - poradi),
        })
        zalozeno_lidi += 1

    # Zhlednuti videi vyzvy. Den, ktery clovek nepustil, nema radek -
    # presne jako ve skutecnosti.
    for den, procento in zip(('1', '2', '3'), procenta):
        if not procento:
            continue
        klic, nazev, delka = VIDEA_VYZVY[den]
        if Sledovani.search_count([('lead_id', '=', lead.id),
                                   ('video', '=', klic)]):
            continue
        kdy = ted - timedelta(days=9 - poradi - int(den), hours=random.randint(0, 9))
        Sledovani.create({
            'lead_id': lead.id,
            'den': den,
            'video': klic,
            'nazev': nazev,
            'stranka': '/zpet-do-zivota',
            'otevreno': kdy,
            'spusteno': kdy + timedelta(minutes=1),
            'naposledy': kdy + timedelta(minutes=2),
            'delka': delka,
            'nejdale': int(delka * procento / 100),
            'procento': procento,
            'dokoukano': procento >= 90,
        })
        zalozeno_radku += 1

    # Nekdo si pustil i video mimo vyzvu.
    if poradi % 3 == 0:
        stranka, klic, nazev, delka = VIDEA_WEBU[poradi % len(VIDEA_WEBU)]
        if not Sledovani.search_count([('lead_id', '=', lead.id),
                                       ('video', '=', klic)]):
            procento = random.choice((100, 88, 52, 31))
            kdy = ted - timedelta(days=3, hours=poradi)
            Sledovani.create({
                'lead_id': lead.id,
                'video': klic,
                'nazev': nazev,
                'stranka': stranka,
                'otevreno': kdy,
                'spusteno': kdy,
                'naposledy': kdy + timedelta(minutes=3),
                'delka': delka,
                'nejdale': int(delka * procento / 100),
                'procento': procento,
                'dokoukano': procento >= 90,
            })
            zalozeno_radku += 1

# ---------------------------------------------------------------- #
# videa na webu - souhrn za vsechny navstevniky                     #
# ---------------------------------------------------------------- #

SOUHRNY = [
    ('/zpet-do-zivota', 'vyzva-den-1', 'Den 1: Kde ti utíká čas', 612, 47, 31),
    ('/zpet-do-zivota', 'vyzva-den-2', 'Den 2: Jeden malý důkaz', 548, 29, 18),
    ('/zpet-do-zivota', 'vyzva-den-3', 'Den 3: Co s tím dál', 703, 16, 11),
    ('/', 'uvod-honza', 'Kdo jsem a pro koho to dělám', 184, 162, 96),
    ('/tvuj-tah', 'tvuj-tah-program', 'Jak vypadá Tvůj tah', 421, 58, 24),
    ('/tvuj-tah', 'tvuj-tah-reference', 'Co říkají ti, co to prošli', 236, 41, 0),
]

zalozeno_videi = 0
for stranka, klic, nazev, delka, spusteni, dokoukani in SOUHRNY:
    if Video.search_count([('video', '=', klic), ('stranka', '=', stranka)]):
        continue
    prumer = int(dokoukani / spusteni * 100) if spusteni else 0
    Video.create({
        'stranka': stranka,
        'video': klic,
        'nazev': nazev,
        'delka': delka,
        'spusteni': spusteni,
        'dokoukani': dokoukani,
        'mereni': spusteni,
        # Prumer je vys nez podil dokoukani: vetsina lidi video
        # nedokouka, ale kus ho videt.
        'soucet_procent': spusteni * min(100, prumer + 28),
        'poprve': ted - timedelta(days=21),
        'naposledy': ted - timedelta(hours=random.randint(1, 40)),
    })
    zalozeno_videi += 1

# ---------------------------------------------------------------- #
# kam lide klikaji                                                  #
# ---------------------------------------------------------------- #

KLIKY = [
    ('/', 'Začni zde zdarma', '/zpet-do-zivota', 214),
    ('/', 'Chci odebírat', '#newsletter', 96),
    ('/zpet-do-zivota', 'Chci vstoupit do výzvy zdarma', '#registrace', 183),
    ('/zpet-do-zivota', 'Pustit si video', '#video', 74),
    ('/tvuj-tah', 'Domluvit si úvodní hovor', '/uvodni-hovor', 61),
    ('/uvodni-hovor', 'Rezervovat termín', '#rezervace', 38),
    ('/', 'Můj příběh', '#pribeh', 142),
    ('/', 'Jak pracuji', '#jak-pracuji', 118),
    ('/tvuj-tah', 'Co je v ceně', '#cena', 52),
    ('/zpet-do-zivota', 'Co bude po třetím dni?', '#faq', 29),
]

zalozeno_kliku = 0
for stranka, popis, cil, pocet in KLIKY:
    if Klik.search_count([('stranka', '=', stranka), ('popis', '=', popis)]):
        continue
    Klik.create({
        'stranka': stranka,
        'popis': popis,
        'cil': cil,
        'pocet': pocet,
        'poprve': ted - timedelta(days=24),
        'naposledy': ted - timedelta(hours=random.randint(1, 30)),
    })
    zalozeno_kliku += 1

env.cr.commit()

print('ZALOZENO LIDI:   ', zalozeno_lidi)
print('ZHLEDNUTI VIDEI: ', zalozeno_radku)
print('VIDEI NA WEBU:   ', zalozeno_videi)
print('KLIKU:           ', zalozeno_kliku)
print()
print('Smazani ukazkovych dat:')
print("    env['crm.lead'].search([('email_from','like','%@test.local')]).unlink()")
print("    env['hh.video'].search([('video','like','vyzva-den-%')]).unlink()")
print("    env['hh.web.klik'].search([]).unlink()")
