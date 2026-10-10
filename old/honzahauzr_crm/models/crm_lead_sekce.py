# -*- coding: utf-8 -*-
"""Nová sekce na webu si sama založí, co k ní patří.

Doted platilo, ze kazdy formular musel mit svuj klic v hh_zdroj
a k nemu rucne zalozeny sloupec, stitek i rada e-mailu. Kdyz Honza
pridal na web novou sekci - treba "20denni vyzva" - lide z ni padali
do prvniho sloupce bez stitku a nikdo o tom nevedel.

Formular proto muze poslat pole hh_sekce s nazvem sekce. Kdyz pro ni
jeste nic neexistuje, zalozi se:

    sloupec na nastence  (crm.stage, na konec rady)
    stitek na kartu      (crm.tag)
    stitek na e-maily    (hh.mail.stitek, navazany na ten sloupec)

a clovek se do te sekce rovnou zaradi. Zprav v rade zadna nevznika -
ty si Honza napise sam, az bude chtit. Prazdna rada nic neposila,
takze nehrozi, ze by nekomu odesel nedodelany text.

Puvodni zarazovani podle hh_zdroj zustava beze zmeny. Tohle se
pridava az nad nim a jen tehdy, kdyz hh_sekce opravdu prijde.
"""

from odoo import api, fields, models


class CrmLeadSekce(models.Model):
    _inherit = 'crm.lead'

    hh_sekce = fields.Char(
        string='Sekce z webu',
        help='Název sekce, ze které člověk přišel. Když pro ni ještě '
             'není sloupec na nástěnce, založí se i se štítky sám.',
    )

    # ------------------------------------------------------------------
    # zalozeni sekce
    # ------------------------------------------------------------------

    @api.model
    def _hh_zajistit_sekci(self, nazev):
        """Vrati sloupec pro sekci; co chybi, zalozi.

        Hleda se podle nazvu bez ohledu na velikost pismen, aby
        "20denní výzva" a "20denní Výzva" neskoncily jako dva
        sloupce vedle sebe.
        """
        nazev = (nazev or '').strip()
        if not nazev:
            return self.env['crm.stage'].browse()

        Stage = self.env['crm.stage'].sudo()
        Tag = self.env['crm.tag'].sudo()
        Stitek = self.env['hh.mail.stitek'].sudo()

        stupen = Stage.search([('name', '=ilike', nazev)], limit=1)
        if not stupen:
            # Na konec rady, at novy sloupec nerozhodi poradi, na ktere
            # je Honza zvykly. Presunout si ho muze sam.
            posledni = Stage.search([], order='sequence desc, id desc', limit=1)
            stupen = Stage.create({
                'name': nazev,
                'sequence': (posledni.sequence or 0) + 1,
            })

        stitek_karty = Tag.search([('name', '=ilike', nazev)], limit=1)
        if not stitek_karty:
            stitek_karty = Tag.create({'name': nazev})

        stitek_mailu = Stitek.search([('name', '=ilike', nazev)], limit=1)
        if not stitek_mailu:
            stitek_mailu = Stitek.create({'name': nazev})

        # Bez tohohle by rada e-mailu u sloupce visela ve vzduchu:
        # stitek by existoval, ale sloupec by o nem nevedel.
        if stitek_mailu not in stupen.hh_stitek_ids:
            stupen.hh_stitek_ids = [(4, stitek_mailu.id)]

        return stupen

    def _hh_zaradit_do_sekce(self):
        """Posune kartu do sekce, kterou poslal formular."""
        self.ensure_one()
        if not self.hh_sekce:
            return

        stupen = self._hh_zajistit_sekci(self.hh_sekce)
        if not stupen:
            return

        zapis = {}

        stitek = self.env['crm.tag'].sudo().search(
            [('name', '=ilike', self.hh_sekce.strip())], limit=1)
        if stitek and stitek not in self.tag_ids:
            zapis['tag_ids'] = [(4, stitek.id)]

        # Posouva se jen dopredu, stejne jako u hh_zdroj. Kdo uz ma
        # domluveny hovor, nema spadnout zpatky mezi odberatele jen
        # proto, ze si jeste neco stahl.
        if not self.stage_id or stupen.sequence > self.stage_id.sequence:
            zapis['stage_id'] = stupen.id

        if zapis:
            # Pres write kvuli rade e-mailu navazane na presun sloupce.
            self.sudo().write(zapis)
