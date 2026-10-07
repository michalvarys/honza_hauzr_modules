# -*- coding: utf-8 -*-
"""Rozdeli agendu mezi dva weby.

Honza Hauzr   -> jen odber novinek ("Chci odebírat")
Vlastni rezie -> jen 3denni vyzva a rezervace hovoru

Sloupce se mazou. Archivovat je nejde - crm.stage v Odoo 18 pole
active vubec nema. Pred smazanim se prilezitosti z rusenych sloupcu
prevedou do prvniho ponechaneho, aby se zadna neztratila.

Zarazovani podle zdroje stoji na odkazech crm.stage_lead1..3
(HH_STUPNE v crm_lead.py). Kdyz cilovy sloupec na danem webu
neexistuje, _hh_zaradit_do_stupne proste nic neudela a prilezitost
zustane v prvnim sloupci - nic nespadne.

Spousti se s promennou HH_ROLE: "novinky" nebo "vyzva".
"""

import os

ROLE = os.environ.get('HH_ROLE', '')
assert ROLE in ('novinky', 'vyzva'), 'nastav HH_ROLE na novinky nebo vyzva'

PONECHAT = {
    'novinky': ['Chci odebírat'],
    'vyzva': ['3denní výzva', 'Rezervace'],
}[ROLE]

# "rozeslat navazující e-maily sloupců" zustava vzdy - na nem visi
# druha a treti zprava u KAZDEHO sloupce, tedy i u odberu novinek.
VYPNOUT_UKOLY = {
    'novinky': ['rozeslat dny výzvy', 'doplnit termíny hovorů'],
    'vyzva': [],
}[ROLE]

SMAZAT_STRANKY = {
    'novinky': ['/zpet-do-zivota', '/zpet-do-zivota/vyzva'],
    'vyzva': [],
}[ROLE]

print('=== role: %s ===' % ROLE)

Stage = env['crm.stage'].sudo()
Lead = env['crm.lead'].sudo()

zustavaji = Stage.search([('name', 'in', PONECHAT)], order='sequence')
rusene = Stage.search([('name', 'not in', PONECHAT)])

if not zustavaji:
    raise Exception('zadny z ponechanych sloupcu neexistuje: %s' % PONECHAT)

# --- prilezitosti z rusenych sloupcu ----------------------------------
cil = zustavaji[0]
for stupen in rusene:
    leady = Lead.with_context(active_test=False).search([('stage_id', '=', stupen.id)])
    if leady:
        leady.write({'stage_id': cil.id})
        print('  presunuto %s prilezitosti z "%s" do "%s"'
              % (len(leady), stupen.name, cil.name))

# --- sloupce ----------------------------------------------------------
print('sloupce:')
for stupen in zustavaji:
    print('  %-16s zustava' % stupen.name)
for stupen in rusene:
    nazev = stupen.name
    stupen.unlink()
    print('  %-16s smazan' % nazev)

# --- planovane ukoly --------------------------------------------------
print('planovane ukoly:')
for ukol in env['ir.cron'].sudo().with_context(active_test=False).search(
        [('name', 'ilike', 'Honza Hauzr')]):
    vypnout = any(k in ukol.name for k in VYPNOUT_UKOLY)
    if ukol.active == vypnout:
        ukol.active = not vypnout
    print('  %-46s %s' % (ukol.name, 'vypnut' if vypnout else 'bezi'))

# --- menu terminu hovoru ----------------------------------------------
menu = env.ref('honzahauzr_crm.hh_termin_menu', raise_if_not_found=False)
if menu:
    chceme = (ROLE == 'vyzva')
    menu.active = chceme
    print('menu Termíny hovorů:', 'zustava' if chceme else 'schovano')

# --- stranky ----------------------------------------------------------
if SMAZAT_STRANKY:
    print('stranky:')
    for url in SMAZAT_STRANKY:
        stranka = env['website.page'].sudo().search([('url', '=', url)])
        if stranka:
            stranka.unlink()
            print('  smazana', url)
        else:
            print('  neni', url)

env.cr.commit()
print('hotovo')
