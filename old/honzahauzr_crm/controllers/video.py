# -*- coding: utf-8 -*-
"""Sběr přehrávání videí z webu.

Jediná routa pro všechna videa na všech stránkách. Nic nevrací a při
chybě mlčí - měření nesmí nikdy stát v cestě tomu, kvůli čemu člověk
na stránku přišel.

Záměrně se nepřijímá nic o návštěvníkovi: jen adresa stránky, označení
videa a kolik z něj viděl. Není co chránit a není co mazat.
"""

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HhVideo(http.Controller):

    # Stranky, ktere nejsou web pro navstevniky. Prehrani v nahledu
    # administrace o nicem nevypovida.
    MIMO = ('/web', '/odoo', '/my', '/@', '/mail')

    @http.route('/hh/video', type='json', auth='public', website=True,
                sitemap=False)
    def video(self, stranka=None, video=None, nazev=None, delka=None,
              procento=None, spustil=False, **kw):
        # Prihlaseny spravce si web prohlizi a upravuje; jeho
        # prehravani by cisla rozhodilo.
        if request.env.user.has_group('base.group_user'):
            return {'zapsano': False}

        cesta = (stranka or '').strip()
        if any(cesta == m or cesta.startswith(m + '/') for m in self.MIMO):
            return {'zapsano': False}
        if not video:
            return {'zapsano': False}

        Videa = request.env['hh.video'].sudo()
        try:
            if spustil:
                Videa._hh_spusteno(cesta, video, nazev, delka)
            else:
                Videa._hh_dokoukano(cesta, video, procento, nazev, delka)
        except Exception as chyba:
            _logger.warning(
                'Honza Hauzr CRM: prehrani videa se nezapsalo: %s', chyba)
            return {'zapsano': False}

        self._hh_pripsat_cloveku(cesta, video, nazev, delka, procento,
                                 spustil, kw.get('sekund'))
        return {'zapsano': True}

    def _hh_pripsat_cloveku(self, cesta, video, nazev, delka, procento,
                            spustil, sekund=None):
        """Když víme, čí je relace, zapíše se přehrání i na jeho kartu.

        Honza se u konkrétního člověka ptá "na co koukal a kolik
        toho viděl". Souhrn za video na to neodpoví - ten je o videu,
        ne o lidech.

        Kdo se nikdy nepředstavil, zůstane jen v souhrnu. Mlčí se
        i při chybě: do měření za video už se zapsalo a ztratit kvůli
        tomuhle celé hlášení by byla škoda.
        """
        try:
            lead = request.env['crm.lead'].sudo()._hh_clovek_z_relace()
            if not lead:
                return
            # Prehravac hlasi vterinu, procento si model dopocita
            # z delky sam. Kdyz prijde jen procento, vterina se
            # z nej odvodi - jinak by radek zustal na nule.
            dosud = int(sekund or 0)
            if not dosud and procento and delka:
                dosud = round(int(delka) * int(procento) / 100.0)
            request.env['hh.vyzva.sledovani'].sudo()._hh_zapsat(
                lead, video, sekund=dosud, delka=int(delka or 0),
                spustil=bool(spustil), nazev=nazev, stranka=cesta)
        except Exception as chyba:
            _logger.warning(
                'Honza Hauzr CRM: prehrani se neprispalo cloveku: %s',
                chyba)
