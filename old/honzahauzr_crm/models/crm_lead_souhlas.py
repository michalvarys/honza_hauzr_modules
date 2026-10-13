# -*- coding: utf-8 -*-
"""Souhlas se zpracováním osobních údajů u formulářů na webu.

Zaškrtávátko v šabloně má required, jenže na to se spolehnout nedá:
tlačítko „Odeslat nezávaznou přihlášku" na starší stránce je odkaz,
ne odesílací tlačítko, takže prohlížeč formulář nevaliduje vůbec,
a kdokoliv si může políčko v nástrojích pro vývojáře odškrtnout.
Odesílalo se tedy i bez souhlasu.

Kontrola proto stojí na serveru: bez souhlasu se karta nezaloží.
Zároveň se souhlas ukládá i s časem - GDPR po správci chce, aby
doložil, že souhlas dostal, a k tomu je potřeba vědět kdy.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Hodnoty, kterymi prohlizec posila zaskrtnute policko.
ZASKRTNUTO = ('on', '1', 'true', 'ano', 'yes', 'True')

# Odkud karta prisla bez formulare, takze souhlas chybet smi:
# rucni zapis rezervace v kalendari (hovor domluveny napr. po
# telefonu) a karty zalozene v administraci.
BEZ_FORMULARE = ('rucne',)


class CrmLeadSouhlas(models.Model):
    _inherit = 'crm.lead'

    hh_souhlas = fields.Boolean(
        string='Souhlas se zpracováním údajů',
        readonly=True,
        copy=False,
        help='Zaškrtl souhlas ve formuláři na webu.',
    )
    hh_souhlas_kdy = fields.Datetime(
        string='Souhlas udělen',
        readonly=True,
        copy=False,
        help='Kdy souhlas přišel. Bez data by se nedal doložit.',
    )

    def website_form_input_filter(self, request, values):
        """Bez souhlasu se z formuláře karta nezaloží.

        Běží dřív, než vznikne záznam, takže se nestane, že by karta
        vznikla a souhlas se řešil až potom.

        Políčko nemá v šabloně name schválně - Odoo zapisuje do
        modelu jen pojmenovaná pole a neznámý název by zápis shodil.
        Posílá se proto pod vlastním názvem, který tady vyzvedneme
        a do hodnot dosadíme sami.
        """
        values = super().website_form_input_filter(request, values)

        syrove = (request.params.get('hh_souhlas')
                  or values.pop('hh_souhlas', None))
        souhlasil = str(syrove) in ZASKRTNUTO if syrove is not None else False

        if not souhlasil:
            _logger.info(
                'Honza Hauzr CRM: formular odmitnut, chybi souhlas se '
                'zpracovanim udaju (%s).', values.get('email_from') or '?')
            raise ValidationError(_(
                'Bez souhlasu se zpracováním osobních údajů to '
                'odeslat nejde. Zaškrtni prosím políčko pod '
                'formulářem.'))

        values['hh_souhlas'] = True
        values['hh_souhlas_kdy'] = fields.Datetime.now()
        return values

    @api.model
    def _hh_zapsat_souhlas(self, lead):
        """Poznamená souhlas u karty, která nevznikla formulářem.

        Rezervace hovoru nejde přes website_form, ale přes vlastní
        volání - souhlas se u ní hlídá v controlleru a sem se jen
        zapíše, aby se dal doložit stejně jako u ostatních.
        """
        if not lead or lead.hh_souhlas:
            return False
        lead.sudo().write({
            'hh_souhlas': True,
            'hh_souhlas_kdy': fields.Datetime.now(),
        })
        return True
