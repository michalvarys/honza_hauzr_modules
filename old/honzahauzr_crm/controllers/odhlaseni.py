# -*- coding: utf-8 -*-
"""Odhlášení z e-mailů a cesta zpátky.

Každá zpráva má v patičce odkaz na tuhle adresu. Klíč je náhodný
řetězec u karty, ne její číslo - podle čísel by šlo odhlásit cizího
člověka pouhým zkoušením.

Odhlášení je jedno kliknutí bez potvrzování. Když po člověku chceme
ještě něco vyplnit, obvykle místo toho označí zprávu jako spam, a to
poškodí doručování všem ostatním.

Návrat je naopak tlačítko ve formuláři, tedy POST. Odkaz si firemní
antispam sám proklikne a přihlásil by člověka zpátky, aniž by o tom
věděl.
"""

from odoo import http
from odoo.http import request


class HhOdhlaseni(http.Controller):

    @http.route('/maily/odhlasit/<string:klic>', type='http', auth='public',
                website=True, sitemap=False)
    def odhlasit(self, klic, **kw):
        lead = self._hh_podle_klice(klic)

        if lead and not lead.hh_odhlaseno:
            lead.write({'hh_odhlaseno': True})
            # Do seznamu zablokovanych taky, at se adresa neobjevi
            # v zadne jine rozesilce z Odoo.
            adresa = (lead.email_from or lead.partner_id.email or '').strip()
            if adresa:
                request.env['mail.blacklist'].sudo()._add(adresa)

        return request.render('honzahauzr_crm.hh_odhlaseni_hotovo', {
            'nalezen': bool(lead),
            'vraceno': False,
            'klic': klic if lead else '',
            'adresa': (lead.email_from or '') if lead else '',
        })

    @http.route('/maily/odhlasit/<string:klic>/zpet', type='http',
                auth='public', website=True, methods=['POST'], csrf=True,
                sitemap=False)
    def zpet(self, klic, **kw):
        """Rozmyslel si to - odhlášení se ruší a řada jede od začátku."""
        lead = self._hh_podle_klice(klic)
        if lead:
            lead._hh_vratit_se()

        return request.render('honzahauzr_crm.hh_odhlaseni_hotovo', {
            'nalezen': bool(lead),
            'vraceno': bool(lead),
            'klic': '',
            'adresa': (lead.email_from or '') if lead else '',
        })

    @staticmethod
    def _hh_podle_klice(klic):
        return request.env['crm.lead'].sudo().search(
            [('hh_odhlaseni_klic', '=', klic)], limit=1)
