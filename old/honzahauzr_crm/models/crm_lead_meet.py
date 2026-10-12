# -*- coding: utf-8 -*-
"""Odkaz na Google Meet, který Honza pošle těsně před hovorem.

Hovor se vede přes Google Meet, jenže odkaz na schůzku vzniká až ve
chvíli, kdy ji Honza v kalendáři založí - v potvrzení rezervace tedy
být nemůže. Proto dvě zprávy: potvrzení slíbí, že odkaz přijde, a
tahle ho doručí.

Odesílá se ručně, ne odstupem ve dnech: schůzka může vzniknout den
předem i deset minut před hovorem a žádný odstup to netrefí. Honza
otevře kartu, vloží odkaz, klikne na Odeslat.

Text zprávy je v knihovně jako každý jiný, takže si ho může přepsat.
Do tlačítka se odkaz doplní sám přes {{ object.hh_meet_odkaz }}.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Predloha, kterou tlacitko posila. Odkaz na modul, ne jmeno: jmeno
# si Honza muze prepsat a tlacitko by pak zpravu nenaslo.
PREDLOHA = 'honzahauzr_crm.hh_predloha_meet'


class CrmLeadMeet(models.Model):
    _inherit = 'crm.lead'

    hh_meet_odkaz = fields.Char(
        string='Odkaz na Google Meet',
        help='Odkaz na schůzku, který se doplní do tlačítka ve '
             'zprávě. V textu zprávy se píše jako '
             '{{ object.hh_meet_odkaz }}.',
        tracking=True,
    )
    hh_meet_odeslano = fields.Datetime(
        string='Odkaz odeslán',
        readonly=True,
        copy=False,
        help='Kdy odkaz naposledy odešel. Poslat se dá i znovu - '
             'třeba když se schůzka přeloží a odkaz se změní.',
    )

    hh_meet_mozny = fields.Boolean(
        string='Jde poslat odkaz na hovor',
        compute='_compute_hh_meet_mozny',
        help='Podle toho se na kartě ukazuje políčko s odkazem.',
    )

    @api.depends('stage_id', 'hh_termin_kdy')
    def _compute_hh_meet_mozny(self):
        """Komu má smysl posílat odkaz na hovor.

        Nestačí ptát se na termín: na nástěnce končí ve sloupci
        Rezervace i karty, za kterými žádný termín není - hovor se
        domluvil mimo web, nebo slot mezitím zmizel. Honza by u nich
        políčko neviděl, přestože hovor proběhne.

        Proto se bere i sloupec: když se z něj posílá řada, do které
        ta zpráva patří, políčko je na místě. Podle řady, ne podle
        jména sloupce - jméno si Honza může přepsat.
        """
        zprava = self.env.ref(PREDLOHA, raise_if_not_found=False)
        stitek = zprava.stitek_id if zprava else False
        for lead in self:
            lead.hh_meet_mozny = bool(
                lead.hh_termin_kdy
                or (stitek and stitek in lead.stage_id.hh_stitek_ids))

    hh_stav_barva = fields.Char(
        string='Barva karty',
        compute='_compute_hh_stav_barva',
        help='Podle čeho se karta na nástěnce obarví. Zelená = '
             'odkaz na hovor odešel, červená = člověk si hovor '
             'zrušil.',
    )

    @api.depends('hh_meet_odeslano', 'tag_ids')
    def _compute_hh_stav_barva(self):
        """Obarvi kartu podle toho, co se s hovorem stalo.

        Na nástěnce je u sloupce Rezervace víc karet pod sebou
        a jediné, čím se liší, je jméno. Barva řekne stav dřív,
        než Honza stihne kartu otevřít.

        Zrušení přebíjí odeslaný odkaz: když si člověk hovor zruší
        potom, co mu odkaz přišel, je podstatné to zrušení.
        """
        zruseny = self.env.ref('honzahauzr_crm.tag_zruseny_hovor',
                               raise_if_not_found=False)
        for lead in self:
            if zruseny and zruseny in lead.tag_ids:
                lead.hh_stav_barva = 'cervena'
            elif lead.hh_meet_odeslano:
                lead.hh_stav_barva = 'zelena'
            else:
                lead.hh_stav_barva = ''

    def action_hh_poslat_meet(self):
        """Pošle člověku odkaz na hovor.

        Chyby hlásí nahlas, ne do logu: Honza mačká tlačítko a čeká
        na odpověď. Když se zpráva nepošle, musí to vědět hned - ne
        se to dozvědět od zákazníka, který se na hovor nedostal.
        """
        self.ensure_one()

        odkaz = (self.hh_meet_odkaz or '').strip()
        if not odkaz:
            raise UserError(_(
                'Nejdřív vlož odkaz na Google Meet. Bez něj by '
                'tlačítko ve zprávě nikam nevedlo.'))
        if not odkaz.lower().startswith(('http://', 'https://')):
            raise UserError(_(
                'Odkaz musí začínat https:// - takhle by ho pošta '
                'neudělala klikací. Zkopíruj ho z Google Meetu celý.'))

        prijemce = self.email_from or self.partner_id.email
        if not prijemce:
            raise UserError(_(
                'Tahle karta nemá e-mail, takže není kam poslat.'))

        zprava = self.env.ref(PREDLOHA, raise_if_not_found=False)
        if not zprava:
            raise UserError(_(
                'V knihovně chybí zpráva s odkazem na hovor. '
                'Založí se sama při aktualizaci modulu.'))

        # Mezery na okrajich by v odkazu zustaly a tlacitko by
        # vedlo na adresu s %20 na konci.
        if odkaz != self.hh_meet_odkaz:
            self.hh_meet_odkaz = odkaz

        if not self._hh_poslat_email_stupne(self.stage_id, prijemce, zprava):
            raise UserError(_(
                'Zprávu se nepodařilo odeslat. Zkus to znovu; když to '
                'nepůjde ani podruhé, bude chyba v nastavení pošty.'))

        self.sudo().hh_meet_odeslano = fields.Datetime.now()
        self.message_post(body=_(
            'Odkaz na hovor odeslán na %(adresa)s: %(odkaz)s',
            adresa=prijemce, odkaz=odkaz))
        return True

    @api.model
    def _hh_oznacit_meet_jako_rucni(self):
        """Zajistí, že zprávu s odkazem nerozešle řada sama.

        Předloha se zakládá datovým souborem s noupdate, takže
        v databázi, kde vznikla dřív než příznak, by zůstala jako
        běžná zpráva řady - a odešla by všem, kdo přijdou do sloupce
        Rezervace, s prázdným tlačítkem.

        Pouští se při každé aktualizaci a podruhé nemá co dělat.
        """
        zprava = self.env.ref(PREDLOHA, raise_if_not_found=False)
        if zprava and not zprava.rucni:
            zprava.sudo().rucni = True
            _logger.info(
                'Honza Hauzr CRM: zprava s odkazem na hovor oznacena '
                'jako rucni.')
        return True
