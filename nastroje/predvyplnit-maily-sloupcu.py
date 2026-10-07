# -*- coding: utf-8 -*-
"""Predvyplni e-maily u sloupcu CRM.

Texty jsou zaklad k prepsani - tonem i obsahem vychazeji z webu.
Zapinaji se jen ty zpravy, ktere se nebijou s tim, co uz odesila
kod sam:

  - Den 2 a Den 3 vyzvy rozesila nocni ukol (_hh_vyzva_rozeslat),
  - potvrzeni rezervace posila sam termin (_hh_ohlasit_rezervaci).

Tam jsou texty vyplnene, ale vypnute, aby clovek nedostal dve
zpravy o tomtez. Kdyz je nekdo zapne, musi se druhy zdroj vypnout.
"""

# Jmeno se doplnuje jen kdyz nejake je a kdyz to neni adresa.
# Kdo ho ve formulari nevyplni, dostane kontakt pojmenovany podle
# e-mailu a contact_name se z nej dopocita - bez teto pojistky by
# e-mail zacinal "Ahoj petr@seznam.cz,".
OSLOVENI = (
    "Ahoj{{ ' ' + object.contact_name"
    " if object.contact_name and '@' not in object.contact_name"
    " else '' }},"
)
ZAKLAD = "{{ object.env['ir.config_parameter'].sudo().get_param('web.base.url') }}"
PODPIS = '<p>Honza Hauzr<br/><span style="color:#777">Mentor pro muže · Vlastní režie</span></p>'


def p(text):
    return '<p>%s</p>' % text


NASTAVENI = {
    'Chci odebírat': {
        1: {
            'zapnuto': True,
            'predmet': 'Jsi v tom',
            'telo': (
                p(OSLOVENI)
                + p('díky, že chceš číst, co píšu.')
                + p('Nebudu ti psát každý týden. Ozvu se, když budu mít co '
                    'říct &#8212; něco z praxe, z vlastních chyb nebo z toho, '
                    'co vidím u chlapů, se kterými pracuju. Žádné motivační '
                    'citáty, žádné návody na jediný správný život.')
                + p('Kdyby ti to nedávalo smysl, odhlásíš se jedním klikem '
                    'dole v každém e-mailu.')
                + PODPIS
            ),
        },
        2: {
            'zapnuto': True,
            'po': 3,
            'predmet': 'Tři dny, tři videa, tři kroky',
            'telo': (
                p(OSLOVENI)
                + p('než ti začnu posílat delší věci, dám ti něco '
                    'konkrétního k vyzkoušení.')
                + p('Mám 3denní výzvu <b>Z autopilota zpět do života</b>. '
                    'Tři krátká videa a u každého jeden krok, který uděláš '
                    'ten den. Zadarmo.')
                + p('Za tři dny budeš vědět, kde se zasekáváš a co s tím '
                    'uděláš jako první.')
                + p('<a href="%s/zpet-do-zivota">Chci do výzvy</a>' % ZAKLAD)
                + PODPIS
            ),
        },
        3: {
            'zapnuto': True,
            'po': 10,
            'predmet': 'Proč to většinou nevydrží',
            'telo': (
                p(OSLOVENI)
                + p('většina lidí nezkrachuje na tom, že by nevěděli, co mají '
                    'dělat. Zkrachují na tom, že si to nikdy nepřiznali '
                    'nahlas.')
                + p('Rozhodnutí vydrží tehdy, když stojí na něčem tvém &#8212; '
                    'ne na tom, co se čeká. Proto nezačínám plánem, ale tím, '
                    'že si pojmenuješ, kde doopravdy jsi.')
                + p('Kdyby sis to chtěl zkusit, výzva je pořád otevřená: '
                    '<a href="%s/zpet-do-zivota">Z autopilota zpět do '
                    'života</a>' % ZAKLAD)
                + PODPIS
            ),
        },
    },
    '3denní výzva': {
        1: {
            'zapnuto': True,
            'predmet': 'Den 1 je pro tebe připravený',
            'telo': (
                p(OSLOVENI)
                + p('jsi ve výzvě <b>Z autopilota zpět do života</b>. První '
                    'den na tebe čeká hned teď.')
                + p('<b>Den 1 &#8212; Zrcadlo a pravda.</b> Uvidíš, kde dnes '
                    'stojíš, a vybereš si jednu oblast, kterou už nechceš '
                    'obcházet.')
                + p('<a href="{{ object.hh_vyzva_odkaz }}">Otevřít výzvu</a>')
                + p('Zítra ve stejnou dobu se ti na téže stránce odemkne '
                    'Den 2. Dám ti vědět.')
                + PODPIS
            ),
        },
        2: {
            'zapnuto': False,
            'po': 1,
            'predmet': 'Den 2 je odemčený',
            'telo': (
                p(OSLOVENI)
                + p('<b>Den 2 &#8212; Důkaz.</b> Dnes si určíš jeden malý '
                    'konkrétní závazek, kterým začneš obnovovat respekt '
                    'k sobě. Malý schválně &#8212; má se dodržet, ne '
                    'odložit.')
                + p('<a href="{{ object.hh_vyzva_odkaz }}">Otevřít Den 2</a>')
                + PODPIS
            ),
        },
        3: {
            'zapnuto': False,
            'po': 2,
            'predmet': 'Den 3 je odemčený',
            'telo': (
                p(OSLOVENI)
                + p('<b>Den 3 &#8212; Tvůj tah.</b> Pojmenuješ autopilota, '
                    'který tě drží na místě, a uvidíš, co je tvůj další '
                    'krok.')
                + p('<a href="{{ object.hh_vyzva_odkaz }}">Otevřít Den 3</a>')
                + p('Na stránce se ti zároveň otevře kalendář. Jestli budeš '
                    'chtít probrat, co ti z výzvy vyšlo, vyber si čas na '
                    'nezávazný hovor.')
                + PODPIS
            ),
        },
    },
    'Rezervace': {
        1: {
            'zapnuto': False,
            'predmet': 'Úvodní hovor je domluvený',
            'telo': (
                p(OSLOVENI)
                + p('mám tvůj čas zapsaný a těším se.')
                + p('Kdyby se ti termín nehodil, napiš mi a domluvíme jiný.')
                + PODPIS
            ),
        },
        2: {
            'zapnuto': True,
            'po': 1,
            'predmet': 'Než spolu budeme mluvit',
            'telo': (
                p(OSLOVENI)
                + p('na hovor se nemusíš nijak chystat. Ale jestli z toho '
                    'chceš vytěžit víc, promysli si tyhle tři věci:')
                + '<ul>'
                  '<li>Co tě vedlo k tomu, že sis hovor domluvil?</li>'
                  '<li>Co by mělo být za rok jinak?</li>'
                  '<li>Co jsi už zkoušel a nezabralo to?</li>'
                  '</ul>'
                + p('Nemusíš mít odpovědi. Stačí, když o tom chvíli '
                    'přemýšlíš.')
                + PODPIS
            ),
        },
        3: {
            'zapnuto': False,
            'po': 7,
            'predmet': 'Jak to šlo?',
            'telo': (
                p(OSLOVENI)
                + p('je to týden od našeho hovoru. Zkusil jsi ten krok, '
                    'na kterém jsme se shodli?')
                + p('Jestli ano, napiš mi, jak to dopadlo. Jestli ne, taky '
                    'napiš &#8212; to je většinou zajímavější.')
                + PODPIS
            ),
        },
    },
    'Placené': {
        1: {
            'zapnuto': True,
            'predmet': 'Vítej ve Vlastní režii',
            'telo': (
                p(OSLOVENI)
                + p('jsi uvnitř. Díky za důvěru.')
                + p('Všechno podstatné ti pošlu zvlášť &#8212; přístupy, '
                    'termíny a první krok. Kdybys cokoliv potřeboval, '
                    'stačí odpovědět na tenhle e-mail.')
                + p('Jedna věc na začátek: tohle není kurz, který se '
                    'prokliká. Posune tě jen to, co převedeš do reality.')
                + PODPIS
            ),
        },
        2: {
            'zapnuto': True,
            'po': 3,
            'predmet': 'Jak jsi na tom?',
            'telo': (
                p(OSLOVENI)
                + p('jsou to tři dny. Nepíšu kontrolovat, ale připomenout '
                    'jednu věc.')
                + p('Nejde o to stihnout všechno. Jde o to udělat jeden '
                    'krok, který je opravdu tvůj &#8212; a ten pak '
                    'zopakovat.')
                + p('Kdyby ses někde zasekl, napiš mi.')
                + PODPIS
            ),
        },
        3: {
            'zapnuto': True,
            'po': 14,
            'predmet': 'Dva týdny zpátky',
            'telo': (
                p(OSLOVENI)
                + p('dva týdny jsou dost na to, aby bylo vidět, co drží '
                    'a co ne.')
                + p('Zkus si odpovědět: co z toho, co jsi začal, děláš '
                    'pořád? A co odpadlo hned první týden?')
                + p('Odpad není selhání. Je to informace o tom, že ten krok '
                    'nebyl tvůj, ale převzatý. Napiš mi, co ti vyšlo.')
                + PODPIS
            ),
        },
    },
}


zapnuto_celkem = 0
vyplneno_celkem = 0

for nazev, zpravy in NASTAVENI.items():
    stupen = env['crm.stage'].sudo().search([('name', '=', nazev)], limit=1)
    if not stupen:
        print('  !! sloupec nenalezen:', nazev)
        continue

    hodnoty = {}
    for cislo, z in zpravy.items():
        pr = '' if cislo == 1 else str(cislo)
        hodnoty['hh_mail%s_enabled' % pr] = z['zapnuto']
        hodnoty['hh_mail%s_subject' % pr] = z['predmet']
        hodnoty['hh_mail%s_body' % pr] = z['telo']
        if cislo != 1:
            hodnoty['hh_mail%s_po' % pr] = z['po']
        vyplneno_celkem += 1
        if z['zapnuto']:
            zapnuto_celkem += 1

    stupen.write(hodnoty)
    stav = ', '.join(
        '%s:%s' % (c, 'ZAP' if z['zapnuto'] else 'vyp')
        for c, z in sorted(zpravy.items())
    )
    print('  %-16s %s' % (nazev, stav))

env.cr.commit()
print()
print('vyplneno zprav:', vyplneno_celkem, '| z toho zapnutych:', zapnuto_celkem)

# ----------------------------------------------------------------------
# Jak to spustit
#
#   docker exec -i <kontejner-web> python3 odoo-bin shell \
#       -c /etc/odoo/odoo.conf --addons-path=... \
#       -r odoo -w <heslo> --db_host <db> -d odoo --no-http \
#       < nastroje/predvyplnit-maily-sloupcu.py
#
# Spusteni PREPISE texty u vsech ctyr sloupcu. Kdyz uz si je nekdo
# upravil, prijde o ne - proto se pousti jen pri zakladani noveho
# prostredi, ne na uz rozjetem webu.
# ----------------------------------------------------------------------
