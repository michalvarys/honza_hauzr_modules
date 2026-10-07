# -*- coding: utf-8 -*-
"""Vycisti CRM do prazdna, aby slo zkouset od zacatku.

Smaze vsechny prilezitosti, kontakty vznikle z webu, frontu posty
a uvolni zabrane terminy hovoru.

Kontakty se nemazou vsechny. Systemove zaznamy - spolecnost sama,
kontakty prihlasovacich uctu a jejich nadrizene firmy - zustavaji.
Bez nich se instance rozbije: admin by prisel o vlastni kontakt
a Odoo by nenabehlo.
"""

Lead = env['crm.lead'].sudo()
Partner = env['res.partner'].sudo()
Termin = env['hh.termin'].sudo()

# --- co se nesmi smazat ----------------------------------------------
chranene = set()
for spolecnost in env['res.company'].sudo().search([]):
    chranene.add(spolecnost.partner_id.id)
    chranene.update(spolecnost.partner_id.child_ids.ids)
for uzivatel in env['res.users'].sudo().with_context(active_test=False).search([]):
    chranene.add(uzivatel.partner_id.id)
    if uzivatel.partner_id.parent_id:
        chranene.add(uzivatel.partner_id.parent_id.id)

# --- prilezitosti -----------------------------------------------------
leady = Lead.with_context(active_test=False).search([])
print('prilezitosti ke smazani:', len(leady))
for l in leady:
    print('   -', (l.contact_name or l.name or '-')[:34], '|', l.email_from or '-')

# --- terminy zpatky na volne -----------------------------------------
zabrane = Termin.search([('stav', '=', 'rezervovany')])
if zabrane:
    zabrane.write({
        'stav': 'volny', 'lead_id': False, 'partner_id': False,
        'jmeno': False, 'email': False, 'telefon': False,
        'poznamka': False, 'zrusovaci_klic': False,
    })
print('uvolnenych terminu:', len(zabrane))

# --- fronta posty -----------------------------------------------------
posta = env['mail.mail'].sudo().with_context(active_test=False).search([])
print('e-mailu ve fronte:', len(posta))
posta.unlink()

leady.unlink()

# --- kontakty ---------------------------------------------------------
kandidati = Partner.with_context(active_test=False).search(
    [('id', 'not in', list(chranene))])
print('kontaktu ke smazani:', len(kandidati))
smazano = 0
for k in kandidati:
    try:
        jmeno = k.name
        k.unlink()
        smazano += 1
    except Exception as chyba:
        # Kontakt drzi jiny zaznam (faktura, objednavka). Mazat na silu
        # nema smysl - pro zkouseni prekazet nebude.
        print('   ponechan %s: %s' % (jmeno, str(chyba)[:50]))

env.cr.commit()
print()
print('--- po uklidu ---')
print('prilezitosti:', Lead.with_context(active_test=False).search_count([]))
print('kontaktu celkem:', Partner.with_context(active_test=False).search_count([]))
print('  (z toho chranenych systemovych: %s)' % len(chranene))
print('zabranych terminu:', Termin.search_count([('stav', '=', 'rezervovany')]))
print('volnych terminu:', Termin.search_count([('stav', '=', 'volny')]))
print('e-mailu ve fronte:', env['mail.mail'].sudo().search_count([]))
