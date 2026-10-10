# -*- coding: utf-8 -*-
"""Slouceni seznamu adres, ktere uz v Email Marketingu byly.

Modul si zaklada seznam na kazdy formular. Kdyz ale stejne pojmenovany
seznam nekdo zalozil driv rucne - treba "Newsletter" - vznikly by
dva stejne vedle sebe a adresy by se delily mezi ne.

Prednost ma ten starsi: prevezmou se do nej kontakty z naseho, nas se
smaze a odkaz modulu se prepise na ten puvodni. Dal uz se tedy plni
seznam, ktery Honza zna.
"""
import logging

_logger = logging.getLogger(__name__)

XMLID = [
    'seznam_newsletter', 'seznam_vyzva', 'seznam_hovor',
    'seznam_rezervace', 'seznam_pdf', 'seznam_poptavka',
]


def migrate(cr, version):
    if not version:
        return

    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    Seznam = env['mailing.list'].sudo()
    slouceno = []

    for jmeno in XMLID:
        data = env['ir.model.data'].sudo().search([
            ('module', '=', 'honzahauzr_crm'),
            ('name', '=', jmeno),
            ('model', '=', 'mailing.list'),
        ], limit=1)
        if not data:
            continue

        nas = Seznam.browse(data.res_id)
        if not nas.exists():
            continue

        puvodni = Seznam.search([
            ('name', '=', nas.name),
            ('id', '!=', nas.id),
        ], order='id', limit=1)
        if not puvodni:
            continue

        # Kontakty z naseho seznamu prejdou do puvodniho.
        for kontakt in env['mailing.contact'].sudo().search(
                [('list_ids', 'in', nas.ids)]):
            kontakt.list_ids = [(4, puvodni.id), (3, nas.id)]

        data.res_id = puvodni.id
        nas.unlink()
        slouceno.append(puvodni.name)

    if slouceno:
        _logger.info(
            'Honza Hauzr CRM: slouceny seznamy adres: %s.',
            ', '.join(slouceno))
