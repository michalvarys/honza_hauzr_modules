# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adresa, na kterou chodi upozorneni na novou zpravu z webu.

    Drzi se v systemovem parametru, takze se da kdykoliv prepsat
    v nastaveni CRM - neni potreba sahat do kodu ani nasazovat znovu.
    """

    _inherit = 'res.config.settings'

    hh_notify_email = fields.Char(
        string='Upozornění na nové zprávy posílat na',
        config_parameter='honzahauzr_crm.notify_email',
        help='Kdykoliv někdo odešle formulář na webu, přijde na tuhle '
             'adresu e-mail s tím, kdo psal a co chce. Zpráva se zároveň '
             'uloží do nástěnky mezi příležitosti. Když pole necháte '
             'prázdné, žádné upozornění se neposílá.',
    )

    # ------------------------------------------------------------------
    # rozvrh terminu na uvodni hovor
    # ------------------------------------------------------------------
    #
    # Podle tohohle rozvrhu si kazdou noc vyrobi termin sam sebe - Honza
    # uz je jen odskrtava tam, kde se mu zrovna nehodi. Drive se kazdy
    # termin musel naklikat rucne, coz je pri deseti hodinach denne
    # neunosne.

    hh_rez_od = fields.Float(
        string='Termíny nabízet od',
        config_parameter='honzahauzr_crm.rez_od',
        default=10.0,
        help='První hodina dne, ve které se dá hovor domluvit.',
    )
    hh_rez_do = fields.Float(
        string='Termíny nabízet do',
        config_parameter='honzahauzr_crm.rez_do',
        default=20.0,
        help='Poslední hodina dne. Termín, který by za ni přesáhl, '
             'se už nenabídne.',
    )
    # Druhe az ctvrte pasmo jsou nepovinna. Nula na obou stranach
    # znamena "nepouziva se" - kdo bere hovory cely den v kuse,
    # vyplni jen prvni. Diky nim jde vynechat poledne nebo podvecer,
    # coz s jedinym rozsahem neslo.
    hh_rez_od2 = fields.Float(
        string="Druhé pásmo od",
        config_parameter="honzahauzr_crm.rez_od2",
        default=0.0,
        help="Nepovinné. Nech na nule, pokud druhé pásmo nepotřebuješ.",
    )
    hh_rez_do2 = fields.Float(
        string="Druhé pásmo do",
        config_parameter="honzahauzr_crm.rez_do2",
        default=0.0,
    )
    hh_rez_od3 = fields.Float(
        string="Třetí pásmo od",
        config_parameter="honzahauzr_crm.rez_od3",
        default=0.0,
        help="Nepovinné. Nech na nule, pokud třetí pásmo nepotřebuješ.",
    )
    hh_rez_do3 = fields.Float(
        string="Třetí pásmo do",
        config_parameter="honzahauzr_crm.rez_do3",
        default=0.0,
    )
    hh_rez_od4 = fields.Float(
        string="Čtvrté pásmo od",
        config_parameter="honzahauzr_crm.rez_od4",
        default=0.0,
        help="Nepovinné. Nech na nule, pokud čtvrté pásmo nepotřebuješ.",
    )
    hh_rez_do4 = fields.Float(
        string="Čtvrté pásmo do",
        config_parameter="honzahauzr_crm.rez_do4",
        default=0.0,
    )
    hh_rez_delka = fields.Integer(
        string='Délka hovoru (minuty)',
        config_parameter='honzahauzr_crm.rez_delka',
        default=45,
        help='Podle téhle délky se den rozseká na jednotlivé termíny.',
    )
    hh_rez_dopredu = fields.Integer(
        string='Nabízet dopředu (dnů)',
        config_parameter='honzahauzr_crm.rez_dopredu',
        default=30,
        help='Jak daleko dopředu se zákazníkovi ukazují volné termíny.',
    )

    hh_rez_po = fields.Boolean(string='Pondělí', config_parameter='honzahauzr_crm.rez_po', default=True)
    hh_rez_ut = fields.Boolean(string='Úterý', config_parameter='honzahauzr_crm.rez_ut', default=True)
    hh_rez_st = fields.Boolean(string='Středa', config_parameter='honzahauzr_crm.rez_st', default=True)
    hh_rez_ct = fields.Boolean(string='Čtvrtek', config_parameter='honzahauzr_crm.rez_ct', default=True)
    hh_rez_pa = fields.Boolean(string='Pátek', config_parameter='honzahauzr_crm.rez_pa', default=True)
    hh_rez_so = fields.Boolean(string='Sobota', config_parameter='honzahauzr_crm.rez_so', default=False)
    hh_rez_ne = fields.Boolean(string='Neděle', config_parameter='honzahauzr_crm.rez_ne', default=False)


    def hh_vygenerovat_terminy(self):
        """Tlacitko v nastaveni - vyrobi terminy hned, bez cekani na noc."""
        self.ensure_one()
        # Nastaveni se uklada az po stisku Ulozit; tohle tlacitko na nej
        # navazuje, takze uz cte ulozene hodnoty.
        self.env['hh.termin'].hh_vygenerovat()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
