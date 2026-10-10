# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CrmStage(models.Model):
    """Sloupec nastenky a rady e-mailu, ktere se z nej posilaji.

    Sloupec je sekce, do ktere clovek prijde - Chci odebirat, 3denni
    vyzva, Rezervace. Jakmile v ni karta pristane, zacne jeho vlastni
    odpocet a podle nej odchazi jedna zprava za druhou.

    Texty ani predmety se tu nepisi a jednotlive zpravy se tu ani
    nevybiraji. Sloupec nese jen stitky - a odejde vsechno, co pod ne
    v knihovne spada. Co se v rade posila, kdy a jestli vubec, se
    nastavuje u e-mailu samotneho.
    """

    _inherit = 'crm.stage'

    hh_stitek_ids = fields.Many2many(
        'hh.mail.stitek',
        'hh_stage_mail_stitek_rel',
        'stage_id',
        'stitek_id',
        string='Řady e-mailů',
        help='Které řady se z tohohle sloupce posílají. Jednotlivé '
             'zprávy i jejich odstupy se nastavují v knihovně e-mailů.',
    )
    hh_maily_count = fields.Integer(
        string='Počet e-mailů',
        compute='_compute_hh_maily_count',
    )

    @api.depends('hh_stitek_ids.mail_count')
    def _compute_hh_maily_count(self):
        for stupen in self:
            stupen.hh_maily_count = sum(
                stupen.hh_stitek_ids.mapped('mail_count'))

    @api.model_create_multi
    def create(self, vals_list):
        """Novy sloupec dostane svou radu e-mailu rovnou.

        Honza prida sloupec na nastence a ocekava, ze si k nemu muze
        hned napsat zpravy. Bez toho by musel jit do stitku, zalozit
        stejnojmenny a prihodit ho zpatky ke sloupci - tri kroky
        navic a tri mista, kde se da zapomenout.
        """
        stupne = super().create(vals_list)
        stupne._hh_zajistit_vlastni_stitek()
        return stupne

    def _hh_zajistit_vlastni_stitek(self):
        """Prihodi sloupci radu e-mailu pojmenovanou jako on."""
        Stitek = self.env['hh.mail.stitek'].sudo()
        for stupen in self:
            if stupen.hh_stitek_ids:
                continue
            stitek = Stitek.search([('name', '=ilike', stupen.name)], limit=1)
            if not stitek:
                stitek = Stitek.create({'name': stupen.name})
            stupen.sudo().hh_stitek_ids = [(4, stitek.id)]

    @api.model
    def _hh_doplnit_stitky(self):
        """Kazdy sloupec dostane svou radu e-mailu.

        V knihovne se zpravy radi podle stitku a sloupec bez stitku
        se v ni vubec neukaze - Honza by pro nej musel stitek zakladat
        rucne a pamatovat si, ze se jmenuje stejne jako sloupec.

        Pousti se pri kazdem upgradu modulu, takze sloupce pridane
        pozdeji se doplni samy. Co uz stitek ma, se nechava byt -
        i kdyz se jmenuje jinak: nazev stitku je vec, kterou si Honza
        muze zmenit, a prepsat mu ji by bylo svevolne.
        """
        bez = self.sudo().search([('hh_stitek_ids', '=', False)])
        bez._hh_zajistit_vlastni_stitek()
        return bez.mapped('name')

    def hh_maily_k_odeslani(self):
        """Zapnute zpravy vsech rad sloupce, serazene podle odstupu."""
        self.ensure_one()
        if not self.hh_stitek_ids:
            return self.env['hh.mail.sablona']
        return self.env['hh.mail.sablona'].search([
            ('stitek_id', 'in', self.hh_stitek_ids.ids),
            ('zapnuto', '=', True),
        ], order='po_dnech, id')

    def action_hh_maily(self):
        """Otevre e-maily, ktere se z tohohle sloupce posilaji."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'E-maily sloupce %s' % self.name,
            'res_model': 'hh.mail.sablona',
            'view_mode': 'list,form',
            'domain': [('stitek_id', 'in', self.hh_stitek_ids.ids)],
            'context': {'search_default_podle_stitku': 1},
        }
