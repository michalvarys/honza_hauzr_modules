# -*- coding: utf-8 -*-
"""Jak lidé koukají na videa — na všech stránkách webu.

Vedle tohohle existuje ještě "Zhlédnutí videí" (hh.vyzva.sledovani).
Každé odpovídá na jinou otázku a obě jsou potřeba:

  Zhlédnutí videí   kdo konkrétně kam došel ve třídenní výzvě.
                    Záznam za člověka, protože Honza podle něj
                    posouvá karty na nástěnce.

  Videa na webu     jak funguje které video, ať je kdekoliv.
                    Záznam za video, ne za návštěvníka - na
                    stránkách mimo výzvu nikdo přihlášený není
                    a jméno bychom stejně neměli.

Vede se **jeden řádek na jedno video na jedné stránce**. Stejně jako
u kliknutí: tabulka zůstane malá a neukládá se nic o tom, kdo koukal.

Průměr zhlédnuté části se počítá z posledního hlášení každého
přehrání - ne z průběžných, těch chodí za jedno video několik a
průměr by se jimi stáhl dolů.
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Od kolika procent se video počítá za dokoukané. Závěrečné vteřiny
# nikdo nesleduje a přehrávač hlásí o kousek míň, než video má.
DOKOUKANO_OD = 90


class HhVideo(models.Model):
    _name = 'hh.video'
    _description = 'Video na webu'
    _order = 'spusteni desc, stranka'
    _rec_name = 'nazev'

    stranka = fields.Char(
        string='Stránka',
        required=True,
        index=True,
        help='Adresa stránky bez domény, například /zpet-do-zivota.',
    )
    video = fields.Char(
        string='Označení videa',
        required=True,
        index=True,
        help='Kód videa na YouTube, nebo název souboru u videa '
             'nahraného přímo na web. Podle něj se pozná, že jde '
             'pořád o totéž video.',
    )
    nazev = fields.Char(
        string='Video',
        help='Název, jak ho hlásí přehrávač. U YouTube je to titulek '
             'videa.',
    )
    delka = fields.Integer(
        string='Délka (s)',
        help='Jak je video dlouhé. Hlásí ho přehrávač.',
    )

    spusteni = fields.Integer(string='Spuštění', default=0, index=True)
    dokoukani = fields.Integer(string='Dokoukání', default=0)

    # Z techhle dvou se pocita prumer. Drzi se zvlast, aby se dal
    # dopocitat bez uchovavani jednotlivych prehrani.
    soucet_procent = fields.Integer(string='Součet procent', default=0)
    mereni = fields.Integer(string='Změřených přehrání', default=0)

    prumer = fields.Integer(
        string='Průměrně zhlédnuto',
        compute='_compute_prumer',
        store=True,
        help='Kolik procent videa lidé v průměru viděli.',
    )
    podil_dokoukani = fields.Integer(
        string='Dokoukalo',
        compute='_compute_prumer',
        store=True,
        help='Kolik procent těch, co video spustili, ho dokoukalo '
             'do konce.',
    )

    poprve = fields.Datetime(string='Poprvé')
    naposledy = fields.Datetime(string='Naposledy')

    _sql_constraints = [
        ('jedno_video_na_strance', 'UNIQUE(stranka, video)',
         'Tohle video už na té stránce evidujeme.'),
    ]

    @api.depends('soucet_procent', 'mereni', 'spusteni', 'dokoukani')
    def _compute_prumer(self):
        for radek in self:
            radek.prumer = (
                round(radek.soucet_procent / radek.mereni)
                if radek.mereni else 0)
            radek.podil_dokoukani = (
                round(100 * radek.dokoukani / radek.spusteni)
                if radek.spusteni else 0)

    @api.model
    def _hh_radek(self, stranka, video, nazev=None, delka=0):
        """Najde řádek pro video na stránce, nebo ho založí."""
        stranka = (stranka or '').strip()[:200] or '/'
        video = (video or '').strip()[:120]
        if not video:
            return self.browse()

        radek = self.sudo().search([
            ('stranka', '=', stranka), ('video', '=', video)], limit=1)
        if not radek:
            ted = fields.Datetime.now()
            radek = self.sudo().create({
                'stranka': stranka, 'video': video,
                'nazev': (nazev or '').strip()[:200] or video,
                'delka': int(delka or 0),
                'poprve': ted, 'naposledy': ted,
            })
            return radek

        # Nazev a delku hlasi az prehravac, takze u prvniho hlaseni
        # chybet mohou. Doplni se, jakmile dorazi.
        zmeny = {}
        if nazev and (not radek.nazev or radek.nazev == radek.video):
            zmeny['nazev'] = nazev.strip()[:200]
        if delka and not radek.delka:
            zmeny['delka'] = int(delka)
        if zmeny:
            radek.write(zmeny)
        return radek

    @api.model
    def _hh_spusteno(self, stranka, video, nazev=None, delka=0):
        """Někdo video pustil."""
        radek = self._hh_radek(stranka, video, nazev, delka)
        if not radek:
            return False
        radek.write({
            'spusteni': radek.spusteni + 1,
            'naposledy': fields.Datetime.now(),
        })
        return radek.id

    @api.model
    def _hh_dokoukano(self, stranka, video, procento, nazev=None, delka=0):
        """Konec jednoho přehrání: kolik z videa člověk viděl.

        Posílá se jednou za přehrání - při pauze, na konci videa nebo
        když člověk zavře stránku.
        """
        radek = self._hh_radek(stranka, video, nazev, delka)
        if not radek:
            return False

        procento = max(0, min(100, int(procento or 0)))
        zmeny = {
            'soucet_procent': radek.soucet_procent + procento,
            'mereni': radek.mereni + 1,
            'naposledy': fields.Datetime.now(),
        }
        if procento >= DOKOUKANO_OD:
            zmeny['dokoukani'] = radek.dokoukani + 1
        radek.write(zmeny)
        return radek.id

    @api.model
    def _hh_z_osobnich(self, stranka, video, nazev=None, delka=0):
        """Spočítá souhrn u videa, které se měří i po lidech.

        Týká se tří videí výzvy. Tam chodí hlášení o postupu každých
        pár vteřin a přičítat za každé jedno přehrání by čísla
        nafouklo. Záznam u člověka přitom drží nejdál dosažený bod,
        takže je přesnější - souhrn se z něj proto rovnou přepočítá.

        Spuštění tím znamená "kolik lidí video pustilo", ne "kolikrát
        se pustilo". U videa, které má jeden člověk vidět jednou, to
        vyjde nastejno.
        """
        radek = self._hh_radek(stranka, video, nazev, delka)
        if not radek:
            return False

        zaznamy = self.env['hh.vyzva.sledovani'].sudo().search([
            ('video', '=', radek.video), ('spusteno', '!=', False)])
        radek.write({
            'spusteni': len(zaznamy),
            'dokoukani': len(zaznamy.filtered('dokoukano')),
            'soucet_procent': sum(zaznamy.mapped('procento')),
            'mereni': len(zaznamy),
            'naposledy': fields.Datetime.now(),
        })
        return radek.id
