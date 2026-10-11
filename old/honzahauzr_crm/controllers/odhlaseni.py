# -*- coding: utf-8 -*-
"""Odhlášení z prodejních e-mailů.

Každá prodejní zpráva má v patičce odkaz na tuhle adresu. Klíč je
náhodný řetězec u karty, ne její číslo - podle čísel by šlo odhlásit
cizího člověka pouhým zkoušením.

Odhlášení je jedno kliknutí bez potvrzování. Když po člověku chceme
ještě něco vyplnit, obvykle místo toho označí zprávu jako spam, a to
poškodí doručování všem ostatním.
"""

from odoo import http
from odoo.http import request


class HhOdhlaseni(http.Controller):

    @http.route('/maily/odhlasit/<string:klic>', type='http', auth='public',
                website=True, sitemap=False)
    def odhlasit(self, klic, **kw):
        lead = request.env['crm.lead'].sudo().search(
            [('hh_odhlaseni_klic', '=', klic)], limit=1)

        if lead and not lead.hh_odhlaseno:
            lead.write({'hh_odhlaseno': True})
            # Do seznamu zablokovanych taky, at se adresa neobjevi
            # v zadne jine rozesilce z Odoo.
            adresa = (lead.email_from or lead.partner_id.email or '').strip()
            if adresa:
                request.env['mail.blacklist'].sudo()._add(adresa)

        return request.render('honzahauzr_crm.hh_odhlaseni_hotovo', {
            'nalezen': bool(lead),
            'adresa': (lead.email_from or '') if lead else '',
        })
