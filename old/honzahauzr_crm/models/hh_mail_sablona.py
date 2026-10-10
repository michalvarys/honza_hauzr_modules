# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HhMailStitek(models.Model):
    """Stitek, ktery drzi pohromade jednu radu e-mailu.

    Stitek je cela rada: "Tridenni vyzva", "Po rezervaci", "Po
    nakupu". U sloupce se pak uz nevybiraji jednotlive zpravy, jen
    se k nemu prihodi stitek - a odejde vsechno, co pod nej patri.

    Nejsou to stitky prilezitosti (crm.tag) schvalne: ty rikaji,
    odkud clovek prisel, a michat mezi ne nazvy e-mailovych rad by
    ten seznam zneprehlednilo.
    """

    _name = 'hh.mail.stitek'
    _description = 'Štítek e-mailů'
    _order = 'name'

    name = fields.Char(string='Název', required=True, translate=True)
    color = fields.Integer(string='Barva')

    mail_ids = fields.One2many(
        'hh.mail.sablona', 'stitek_id', string='E-maily')
    mail_count = fields.Integer(
        string='Počet e-mailů', compute='_compute_mail_count')

    @api.depends('mail_ids.zapnuto')
    def _compute_mail_count(self):
        for stitek in self:
            stitek.mail_count = len(stitek.mail_ids.filtered('zapnuto'))

    _sql_constraints = [
        ('nazev_jedinecny', 'UNIQUE(name)', 'Takový štítek už existuje.'),
    ]


class HhMailSablona(models.Model):
    """Jeden pripraveny e-mail: co se posila, pod jakym stitkem a kdy.

    Driv se predmet a telo psaly primo u sloupce, a to ve trech
    pevnych trojicich poli. Vic nez tri zpravy nesly a stejny text
    ve dvou radach se musel psat dvakrat.

    Odpocet "po kolika dnech" bezi od okamziku, kdy karta do sloupce
    vstoupila, zvlast za kazdeho cloveka. Kdo se prihlasi v poledne,
    dostane dalsi zpravu take kolem poledne - kazdy si jede vlastni
    radu od sveho vlastniho zacatku, ne podle spolecneho kalendare.

    Zamerne to neni mail.template z Odoo: ten ma pres tricet poli
    (model, jazyk, server, pravidla mazani) a schovava se v technickem
    nastaveni. Tady staci nazev, stitek, kdy, predmet a text.
    """

    _name = 'hh.mail.sablona'
    _description = 'E-mail'
    # Pod sebou tak, jak chodi: nejdriv podle rady, uvnitr ni podle dne.
    _order = 'stitek_id, po_dnech, id'

    name = fields.Char(
        string='Název',
        required=True,
        translate=True,
        help='Jen pro tebe, ať e-mail najdeš v seznamu. '
             'Příjemci se neukáže.',
    )
    stitek_id = fields.Many2one(
        'hh.mail.stitek',
        string='Štítek',
        required=True,
        ondelete='restrict',
        index=True,
        # Bez group_expand ukazuje seskupeny seznam jen rady, ve
        # kterych uz nejaka zprava je. Prazdna rada se v knihovne
        # vubec neobjevila, takze nebylo poznat, ze existuje a ze
        # se do ni da psat.
        group_expand='_hh_vsechny_stitky',
        help='Řada, do které zpráva patří. U sloupce pak stačí '
             'přihodit tenhle štítek a odejde všechno, co pod něj spadá.',
    )

    @api.model
    def _hh_vsechny_stitky(self, stitky, domena):
        return self.env['hh.mail.stitek'].search([], order='name')
    po_dnech = fields.Integer(
        string='Po (dnech)',
        default=1,
        required=True,
        help='Kolik dní po vstupu do sloupce zpráva odejde.\n'
             '0 = hned, jakmile tam karta přijde.\n'
             '1 = další den, 2 = třetí den a tak dál.\n\n'
             'Počítá se zvlášť u každého člověka, od chvíle, kdy '
             'jeho karta do sloupce vstoupila.',
    )
    zapnuto = fields.Boolean(
        string='Odesílat',
        default=True,
        help='Vypnutá zpráva zůstane v řadě, jen se nikomu nepošle. '
             'Hodí se, když ji chceš dočasně vynechat a nechtěl bys '
             'ji psát znovu.',
    )

    predmet = fields.Char(
        string='Předmět',
        required=True,
        translate=True,
        help='Co uvidí příjemce v poště jako předmět zprávy.',
    )
    # Dve pole na jeden text, stejne jako to ma Email Marketing.
    # V telo_arch se zprava sklada - jsou v nem bloky, tridy a styly
    # editoru. Pri ulozeni z nej editor vyrobi telo: tytez bloky, ale
    # se styly prepsanymi primo do znacek. Posta totiz externi styly
    # zahazuje a bez toho by zprava dorazila rozsypana.
    # Nazvy poli jsou anglicke zamerne. Editor z Email Marketingu
    # si pole body_html hleda podle jmena primo v kodu widgetu
    # (fieldDependencies), takze pod jinym nazvem formular spadne
    # na "Invalid field 'body_html'".
    body_arch = fields.Html(
        string='Text',
        translate=True,
        sanitize=False,
        help='Zástupné texty, které se vyplní samy:\n'
             '{{ object.contact_name }} = jméno\n'
             '{{ object.email_from }} = e-mailová adresa\n'
             '{{ object.hh_vyzva_odkaz }} = osobní odkaz do výzvy',
    )
    body_html = fields.Html(
        string='Text pro odeslání',
        translate=True,
        sanitize=False,
        help='Verze, která opravdu odejde. Vyrobí ji editor sám '
             'při uložení, ručně se do ní nepíše.',
    )

    # Editor z Email Marketingu si sahne na mailing_model_id a cte
    # z nej rovnou druhou polozku (nazev modelu) bez kontroly, jestli
    # vubec neco je. Bez tohohle pole spadne formular na
    # "Cannot read properties of undefined". Nic jineho ho nepouziva -
    # zpravy se vzdycky posilaji prilezitosti.
    mailing_model_id = fields.Many2one(
        'ir.model',
        string='Model',
        readonly=True,
        default=lambda self: self.env['ir.model']._get_id('crm.lead'),
    )

    active = fields.Boolean(
        string='Aktivní',
        default=True,
        help='Archivovaná zpráva se přestane posílat a zmizí ze seznamu.',
    )

    kdy_popis = fields.Char(string='Kdy', compute='_compute_kdy_popis')

    @api.depends('po_dnech')
    def _compute_kdy_popis(self):
        for mail in self:
            mail.kdy_popis = 'hned' if not mail.po_dnech else (
                '%s. den' % mail.po_dnech)

    @api.depends('name', 'po_dnech')
    def _compute_display_name(self):
        for mail in self:
            kdy = 'hned' if not mail.po_dnech else '%s. den' % mail.po_dnech
            mail.display_name = '%s · %s' % (kdy, mail.name or '')

    _sql_constraints = [
        ('po_dnech_nezaporne', 'CHECK (po_dnech >= 0)',
         'Odstup zprávy nemůže být záporný.'),
    ]
