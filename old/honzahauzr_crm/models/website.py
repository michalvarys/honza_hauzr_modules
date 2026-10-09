# -*- coding: utf-8 -*-
from odoo import fields, models


class Website(models.Model):
    """Weby bezi z jedne databaze, administrace ale patri jen jednomu.

    Nastenka, knihovna e-mailu i terminy hovoru jsou spolecne - cokoli
    se odesle z druhe domeny, spadne do teze nastenky. Otevirat kvuli
    tomu administraci i na druhe domene nema duvod: byla by to tataz
    administrace na dvou adresach a clovek by netusel, kde vlastne je.
    """

    _inherit = 'website'

    hh_admin_jinde = fields.Boolean(
        string='Administrace je na jiném webu',
        help='Na tomhle webu se administrace neotevře a odkaz do ní '
             'přesměruje na web, kam patří. Obsah webu jde dál '
             'upravovat v editoru, jen se k němu nedostaneš přes '
             'nástěnku.',
    )

    hh_kod = fields.Selection(
        selection=[
            ('honzahauzr', 'Honza Hauzr'),
            ('vlastni_rezie', 'Vlastní režie'),
        ],
        string='Odkud přišel',
        default='honzahauzr',
        required=True,
        help='Co se zapíše příležitosti do pole „Z jakého webu". '
             'Podle něj dostane štítek – třeba „Newsletter VR".',
    )

    def hh_web_s_adminem(self):
        """Web, na kterem administrace bydli."""
        return self.sudo().search(
            [('hh_admin_jinde', '=', False)], order='id', limit=1)
