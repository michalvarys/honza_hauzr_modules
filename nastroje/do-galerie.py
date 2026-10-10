# -*- coding: utf-8 -*-
"""Zaregistruje nase navrhy do galerie editoru.

Galerie v editoru nenabizi jen temata Odoo, ale i "oblibene" - to
jsou zaznamy mailing.mailing s favorite=True. Editor si je tahne
pres action_fetch_favorites a necha videt jen ty, ktere maji stejny
model jako prave otevrena zprava (u nas crm.lead).
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

model = env['ir.model'].sudo().search([('model', '=', 'crm.lead')], limit=1)
Mailing = env['mailing.mailing'].sudo()

NAVRHY = [
    ('Vlastní režie — Den 1', '/tmp/den1.html'),
    ('Vlastní režie — Den 2', '/tmp/den2.html'),
    ('Vlastní režie — Den 3', '/tmp/den3.html'),
]

for nazev, cesta in NAVRHY:
    telo = KOSTRA % io.open(cesta, encoding='utf-8').read()
    m = Mailing.with_context(active_test=False).search([('subject', '=', nazev)], limit=1)
    hodnoty = {
        'subject': nazev,
        'body_arch': telo,
        'body_html': telo,
        'favorite': True,
        'mailing_model_id': model.id,
        'mailing_type': 'mail',
    }
    if m:
        m.write(hodnoty)
        print('%-26s aktualizovan (id=%s)' % (nazev, m.id))
    else:
        m = Mailing.create(hodnoty)
        print('%-26s zalozen (id=%s)' % (nazev, m.id))

env.cr.commit()
print('oblibenych pro crm.lead: %s' % Mailing.with_context(active_test=False).search_count(
    [('favorite', '=', True), ('mailing_model_id', '=', model.id)]))
