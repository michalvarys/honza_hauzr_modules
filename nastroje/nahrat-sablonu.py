# -*- coding: utf-8 -*-
"""Nahraje HTML do zpravy v Knihovne e-mailu.

Pouziti (z adresare projektu):

    docker cp nastroje/mail-den1.html hauzr-odoo:/tmp/telo.html
    docker cp nastroje/nahrat-sablonu.py hauzr-odoo:/tmp/n.py
    docker exec hauzr-odoo sh -c "odoo shell -d hauzr --no-http < /tmp/n.py"

Nazev zpravy a cestu k souboru uprav v seznamu PLAN dole.

Dve veci, na ktere se tu naráží a ktere nejsou videt:

1. Editor z Email Marketingu hleda svou kostru - obal .o_layout a
   v nem sloupec .oe_structure. Kdyz ji nenajde, povazuje zpravu za
   prazdnou a misto obsahu nabidne galerii temat. Kostru proto
   doplnuje tenhle skript.

2. body_arch i body_html jsou prekladana pole. Obycejny write()
   prepise jen zakladni jazyk a v administraci se dal ukazuje stary
   cesky preklad. Meni se proto i pres update_field_translations.

Obrazky se v HTML pisou relativne (/theme_honzahauzr/...). Absolutni
adresu pred ne doplni _replace_local_links pri odeslani.
"""
import io

KOSTRA = (
    '<div class="o_layout oe_unremovable oe_unmovable bg-200 o_default_theme" '
    'data-name="Mailing">'
    '<div class="container o_mail_wrapper o_mail_regular oe_unremovable">'
    '<div class="row">'
    '<div class="col o_mail_no_options o_mail_wrapper_td bg-white oe_structure o_editable">'
    '%s'
    '</div></div></div></div>'
)

# (nazev zpravy v knihovne, soubor s telem, predmet)
PLAN = [
    ('3denní výzva – hned', '/tmp/telo.html', 'Den 1 je pro tebe připravený'),
]

M = env['hh.mail.sablona'].sudo()
jazyky = [l.code for l in env['res.lang'].sudo().search([('active', '=', True)])]

for nazev, cesta, predmet in PLAN:
    s = M.search([('name', '=', nazev)], limit=1)
    if not s:
        print('%-26s NENALEZENA' % nazev)
        continue
    telo = io.open(cesta, encoding='utf-8').read()
    arch = KOSTRA % telo
    s.write({'body_arch': arch, 'body_html': telo, 'predmet': predmet})
    s.update_field_translations('body_arch', {k: arch for k in jazyky})
    s.update_field_translations('body_html', {k: telo for k in jazyky})
    s.update_field_translations('predmet', {k: predmet for k in jazyky})
    print('%-26s nahrano (%s znaku)' % (nazev, len(telo)))

env.cr.commit()
