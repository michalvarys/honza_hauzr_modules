# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmStage(models.Model):
    """Ke kazdemu stupni se da napsat e-mail, ktery se sam odesle.

    Text se pise primo sem, ne pres samostatne sablony - Honza si
    jednou vyplni predmet a telo u kazdeho stupne (Nove, Prijate,
    Neplacene, Placene) a dal uz jen pretahuje karty. Stejne to ma
    Jarda Kotlar na boardu objednavek.
    """

    _inherit = 'crm.stage'

    # Napoveda schvalne cela v help, ne jako odstavce ve formulari.
    # Formular se otevira v dialogu a kazdy radek navic tlaci tlacitka
    # Ulozit a Zrusit pod spodni okraj obrazovky.
    hh_mail_enabled = fields.Boolean(
        string='Poslat e-mail zájemci',
        help='Když příležitost vstoupí do tohoto sloupce, odejde na adresu '
             'z formuláře e-mail s předmětem a textem níže.\n\n'
             'E-mail odejde jen jednou. Když kartu vrátíš o sloupec zpět '
             'a zase sem, podruhé už se neposílá.\n\n'
             'Vypni, když má být sloupec jen tvůj interní krok bez e-mailu.',
    )
    hh_mail_subject = fields.Char(
        string='Předmět e-mailu',
        translate=True,
        help='Zástupné texty, které se vyplní samy:\n'
             '{{ object.contact_name }} = jméno\n'
             '{{ object.email_from }} = e-mailová adresa\n'
             '{{ object.name }} = název příležitosti',
    )
    hh_mail_body = fields.Html(
        string='Text e-mailu',
        translate=True,
        sanitize=False,
        help='Text zprávy. Zástupné texty, které se vyplní samy:\n'
             '{{ object.contact_name }} = jméno\n'
             '{{ object.email_from }} = e-mailová adresa\n'
             '{{ object.name }} = název příležitosti',
    )

    # ------------------------------------------------------------------
    # navazujici e-maily
    # ------------------------------------------------------------------
    #
    # Tridenni vyzva potrebuje tri zpravy za sebou, ne jednu: prvni den
    # odkaz na video, druhy a treti den pripomenuti dalsiho dilu. Jeden
    # e-mail na sloupec by znamenal delat tri sloupce a kazdy den karty
    # rucne pretahovat.
    #
    # Odpocet bezi od okamziku, kdy karta do sloupce vstoupila, zvlast
    # za kazdou prilezitost - kdo se prihlasi v poledne, dostane druhy
    # den take kolem poledne.

    hh_mail2_enabled = fields.Boolean(
        string='Poslat druhý e-mail',
        help='Navazující zpráva, která odejde s odstupem po tom prvním.',
    )
    hh_mail2_po = fields.Integer(
        string='Druhý e-mail po (dnech)',
        default=1,
        help='Kolik dní po vstupu do sloupce zpráva odejde. 1 = další den.',
    )
    hh_mail2_subject = fields.Char(string='Předmět druhého e-mailu', translate=True)
    hh_mail2_body = fields.Html(
        string='Text druhého e-mailu', translate=True, sanitize=False)

    hh_mail3_enabled = fields.Boolean(
        string='Poslat třetí e-mail',
        help='Poslední zpráva v řadě.',
    )
    hh_mail3_po = fields.Integer(
        string='Třetí e-mail po (dnech)',
        default=2,
        help='Kolik dní po vstupu do sloupce zpráva odejde. 2 = třetí den.',
    )
    hh_mail3_subject = fields.Char(string='Předmět třetího e-mailu', translate=True)
    hh_mail3_body = fields.Html(
        string='Text třetího e-mailu', translate=True, sanitize=False)

    def hh_mail_cast(self, cislo):
        """Predmet, telo a odstup pro zadanou zpravu v rade (1, 2, 3)."""
        self.ensure_one()
        if cislo == 1:
            return {
                'zapnuto': self.hh_mail_enabled,
                'predmet': self.hh_mail_subject,
                'telo': self.hh_mail_body,
                # Prvni zprava odchazi hned pri vstupu do sloupce.
                'po_dnech': 0,
            }
        if cislo == 2:
            return {
                'zapnuto': self.hh_mail2_enabled,
                'predmet': self.hh_mail2_subject,
                'telo': self.hh_mail2_body,
                'po_dnech': max(0, self.hh_mail2_po or 0),
            }
        return {
            'zapnuto': self.hh_mail3_enabled,
            'predmet': self.hh_mail3_subject,
            'telo': self.hh_mail3_body,
            'po_dnech': max(0, self.hh_mail3_po or 0),
        }
