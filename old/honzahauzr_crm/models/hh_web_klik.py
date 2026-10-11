# -*- coding: utf-8 -*-
"""Kam lidé na webu klikají.

Honza se ptá, co na stránce funguje: které tlačítko lidi mačkají
a které si nikdo nevšimne. Z CRM to nevyčte - tam se objeví až ten,
kdo formulář opravdu odeslal, a o zbytku návštěvníků se nedozví nic.

Vede se **počet kliknutí na jeden prvek jedné stránky**, ne záznam
za každého návštěvníka. Dva důvody:

  - stačí to na otázku "co lidi mačkají" a tabulka zůstane malá;
    při tisíci návštěvách přibude pár desítek řádků, ne tisíce,
  - neukládá se nic o tom, kdo klikal, takže se tu nehromadí
    osobní údaje, které bychom museli hlídat.

Co to neumí: cestu jednoho člověka po webu ani pořadí kliknutí.
Na to by bylo potřeba vést záznam za návštěvu, a to je jiná věc
než tohle.
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HhWebKlik(models.Model):
    _name = 'hh.web.klik'
    _description = 'Kliknutí na webu'
    _order = 'pocet desc, stranka'
    _rec_name = 'popis'

    stranka = fields.Char(
        string='Stránka',
        required=True,
        index=True,
        help='Adresa stránky bez domény, například /zpet-do-zivota.',
    )
    popis = fields.Char(
        string='Na co klikl',
        required=True,
        help='Text tlačítka nebo odkazu tak, jak ho člověk viděl.',
    )
    cil = fields.Char(
        string='Kam to vede',
        help='Adresa, na kterou odkaz míří. U tlačítek bez odkazu '
             'zůstává prázdné.',
    )

    pocet = fields.Integer(string='Kliknutí', default=0, index=True)
    poprve = fields.Datetime(string='Poprvé')
    naposledy = fields.Datetime(string='Naposledy')

    _sql_constraints = [
        ('jeden_radek_na_prvek', 'UNIQUE(stranka, popis, cil)',
         'Tenhle prvek už na té stránce evidujeme.'),
    ]

    @api.model
    def _hh_zapsat(self, stranka, popis, cil=None):
        """Přičte kliknutí. Volá se z webu, proto sudo.

        Delší texty se krátí: popisek tlačítka má pár slov, ale
        kliknout jde i na odstavec s odkazem a z toho by byl
        nepřehledný román.
        """
        stranka = (stranka or '').strip()[:200]
        popis = ' '.join((popis or '').split())[:120]
        cil = (cil or '').strip()[:300]
        if not stranka or not popis:
            return False

        ted = fields.Datetime.now()
        radek = self.sudo().search([
            ('stranka', '=', stranka),
            ('popis', '=', popis),
            ('cil', '=', cil),
        ], limit=1)

        if radek:
            radek.write({'pocet': radek.pocet + 1, 'naposledy': ted})
        else:
            radek = self.sudo().create({
                'stranka': stranka, 'popis': popis, 'cil': cil,
                'pocet': 1, 'poprve': ted, 'naposledy': ted,
            })
        return radek.id
