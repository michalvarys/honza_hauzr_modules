# -*- coding: utf-8 -*-
"""Zalozi zkusebni rezervace, aby bylo videt, jak sloupec vypada.

Prilezitosti se zakladaji se zdrojem "rezervace", takze spadnou rovnou
do sveho sloupce a dostanou stitek. Ke kazde se obsadi nejblizsi volny
termin, aby sedelo i to, co je videt v Terminech hovoru.

Upozorneni Honzovi se neposila - jsou to vymyslena data, ne skutecni
lide.

Poznaji se podle adresy koncici na .zkouska, aby sly hromadne smazat.
"""

from datetime import timedelta
from odoo import fields

LIDE = [
    ('Petr Dvořák', 'petr.dvorak@example.zkouska', '+420 602 118 240',
     'Chci probrat, co mi z výzvy vyšlo. Zasekl jsem se u druhého dne.'),
    ('Martin Kolář', 'martin.kolar@example.zkouska', '+420 777 304 915',
     'Prošel jsem celou výzvu. Zajímá mě program Tvůj tah.'),
    ('Jakub Beneš', 'jakub.benes@example.zkouska', '+420 721 660 183',
     ''),
]

Lead = env['crm.lead'].sudo()
Termin = env['hh.termin'].sudo()

# Uklid po predchozim spusteni, aby se data nehromadila.
stare = Lead.search([('email_from', 'like', '%.zkouska')])
if stare:
    Termin.search([('lead_id', 'in', stare.ids)]).write({
        'stav': 'volny', 'lead_id': False, 'partner_id': False,
        'jmeno': False, 'email': False, 'telefon': False,
    })
    env['res.partner'].sudo().search([('email', 'like', '%.zkouska')]).unlink()
    stare.unlink()
    print('uklizeno po minulem spusteni:', len(stare))

volne = Termin.search(
    [('stav', '=', 'volny'), ('zacatek', '>=', fields.Datetime.now())],
    order='zacatek', limit=len(LIDE) * 4)

if len(volne) < len(LIDE):
    print('!! volnych terminu je jen', len(volne))

print('zakladam:')
for poradi, (jmeno, email, telefon, poznamka) in enumerate(LIDE):
    lead = Lead.with_context(hh_bez_upozorneni=True).create({
        'name': 'Rezervace hovoru — %s' % jmeno,
        'contact_name': jmeno,
        'email_from': email,
        'phone': telefon,
        'description': poznamka or False,
        'hh_zdroj': 'rezervace',
    })

    # Kazdemu jiny den, at to v kalendari nevypada jako jeden blok.
    termin = volne[poradi * 2] if len(volne) > poradi * 2 else None
    if termin:
        termin.write({
            'stav': 'rezervovany',
            'lead_id': lead.id,
            'partner_id': lead.partner_id.id or False,
            'jmeno': jmeno,
            'email': email,
            'telefon': telefon,
        })
        kdy = fields.Datetime.context_timestamp(termin, termin.zacatek)
        kdy = kdy.strftime('%d.%m. %H:%M')
    else:
        kdy = 'bez termínu'

    print('  %-16s %-14s sloupec: %-12s termin: %s'
          % (jmeno, telefon, lead.stage_id.name, kdy))

env.cr.commit()
print()
print('prilezitosti v Rezervacich:',
      Lead.search_count([('stage_id.name', '=', 'Rezervace')]))
print('obsazenych terminu:', Termin.search_count([('stav', '=', 'rezervovany')]))
