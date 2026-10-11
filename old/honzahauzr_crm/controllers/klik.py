# -*- coding: utf-8 -*-
"""Sběr kliknutí z webu.

Jediná routa, která přijme hlášení od stránky a přičte jedničku.
Nic nevrací a při chybě mlčí - měření nesmí nikdy stát v cestě tomu,
kvůli čemu člověk na stránku přišel.

Záměrně se nepřijímá nic o návštěvníkovi: jen adresa stránky, popis
prvku a kam vede. Není co chránit a není co mazat.
"""

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HhKlik(http.Controller):

    # Stranky, ktere nejsou web pro navstevniky: administrace,
    # prihlaseni, technicke adresy. Kliknuti na nich o nicem
    # nevypovida a v prehledu by jen prekazela.
    MIMO = ('/web', '/odoo', '/my', '/@', '/mail')

    @http.route('/hh/klik', type='json', auth='public', website=True,
                sitemap=False)
    def klik(self, stranka=None, popis=None, cil=None, **kw):
        # Prihlaseny spravce si web prohlizi a upravuje; jeho kliknuti
        # by cisla rozhodila a vypadalo by to, ze tlacitko funguje.
        if request.env.user.has_group('base.group_user'):
            return {'zapsano': False}

        cesta = (stranka or '').strip()
        if any(cesta == m or cesta.startswith(m + '/') for m in self.MIMO):
            return {'zapsano': False}

        try:
            request.env['hh.web.klik'].sudo()._hh_zapsat(
                stranka=stranka, popis=popis, cil=cil)
        except Exception as chyba:
            _logger.warning(
                'Honza Hauzr CRM: kliknuti se nezapsalo: %s', chyba)
            return {'zapsano': False}
        return {'zapsano': True}
