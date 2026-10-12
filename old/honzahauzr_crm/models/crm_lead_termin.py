# -*- coding: utf-8 -*-
"""Údaje o domluveném hovoru pro e-mailové předlohy.

Potvrzení rezervace se dosud skládalo natvrdo v kódu. Aby si ho
Honza mohl napsat a upravit v editoru jako ostatní zprávy, musí se
termín dostat na kartu příležitosti - texty v knihovně se vyhodnocují
nad ní ({{ object.neco }}), o termínu samotném nevědí.

Bere se nejbližší budoucí domluvený hovor. Když žádný není, pole
zůstanou prázdná a zpráva s nimi nemá co dělat - proto ji odesílač
pouští jen při přesunu do sloupce Rezervace, kdy termín vždycky je.
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmLeadTermin(models.Model):
    _inherit = 'crm.lead'

    hh_termin_ids = fields.One2many(
        'hh.termin', 'lead_id',
        string='Termíny hovorů',
        help='Hovory domluvené touhle kartou. Drží se tu kvůli '
             'přepočtu: bez vazby zpátky by karta o změně termínu '
             'nevěděla.',
    )
    hh_hovor_kdy = fields.Datetime(
        string='Kdy je hovor',
        compute='_compute_hh_hovor_kdy',
        store=True,
        help='Začátek nejbližšího domluveného hovoru. Podle něj se '
             'karty na nástěnce řadí - kdo má hovor dřív, je výš.',
    )

    @api.depends('hh_termin_ids.zacatek', 'hh_termin_ids.stav')
    def _compute_hh_hovor_kdy(self):
        """Kdy má člověk hovor, aby se podle toho dalo řadit.

        hh_termin_kdy je text pro e-maily ("úterý 20.10.2026 v 10:45")
        a navíc se nikam neukládá, takže se podle něj řadit nedá.
        Tohle je totéž jako datum.

        Bere se nejbližší budoucí hovor. Po proběhlém hovoru zůstane
        poslední, aby karta nevyskočila na začátek sloupce.
        """
        ted = fields.Datetime.now()
        for lead in self:
            domluvene = lead.hh_termin_ids.filtered(
                lambda t: t.stav == 'rezervovany')
            budouci = domluvene.filtered(lambda t: t.zacatek >= ted)
            vybrany = (min(budouci, key=lambda t: t.zacatek) if budouci
                       else max(domluvene, key=lambda t: t.zacatek)
                       if domluvene else None)
            lead.hh_hovor_kdy = vybrany.zacatek if vybrany else False

    hh_termin_kdy = fields.Char(
        string='Kdy je hovor',
        compute='_compute_hh_termin',
        help='Datum a čas nejbližšího domluveného hovoru, česky '
             'a v pásmu firmy. V textu zprávy se píše jako '
             '{{ object.hh_termin_kdy }}.',
    )
    hh_termin_delka = fields.Char(
        string='Jak dlouho hovor trvá',
        compute='_compute_hh_termin',
        help='Například „30 minut“. V textu zprávy se píše jako '
             '{{ object.hh_termin_delka }}.',
    )
    hh_termin_zruseni = fields.Char(
        string='Odkaz na zrušení hovoru',
        compute='_compute_hh_termin',
        help='Osobní odkaz, kterým si člověk termín zruší. '
             'V textu zprávy se píše jako '
             '{{ object.hh_termin_zruseni }}.',
    )

    @api.depends('email_from')
    def _compute_hh_termin(self):
        Termin = self.env['hh.termin'].sudo()
        ted = fields.Datetime.now()
        for lead in self:
            termin = Termin.search([
                ('lead_id', '=', lead.id),
                ('stav', '=', 'rezervovany'),
                ('zacatek', '>=', ted),
            ], order='zacatek', limit=1)
            # Kdyz uz hovor probehl, bere se posledni - zprava se
            # muze posilat i zpetne a prazdne misto v textu vypada
            # jako chyba.
            if not termin:
                termin = Termin.search([
                    ('lead_id', '=', lead.id),
                    ('stav', '=', 'rezervovany'),
                ], order='zacatek desc', limit=1)

            lead.hh_termin_kdy = termin._hh_cas(termin.zacatek) if termin else ''
            lead.hh_termin_delka = (
                '%s minut' % int(round((termin.delka or 0) * 60))
                if termin else '')
            lead.hh_termin_zruseni = (
                termin._hh_odkaz_na_zruseni() or '') if termin else ''

    def unlink(self):
        """Se smazanou kartou se uvolni i jeji budouci hovor."""
        self._hh_uvolnit_terminy()
        return super().unlink()

    def write(self, vals):
        vysledek = super().write(vals)
        # Archivovana karta na nastence taky neni, takze plati totez
        # jako pro smazanou.
        if not vals.get('active', True):
            self._hh_uvolnit_terminy()
        return vysledek

    def _hh_uvolnit_terminy(self):
        """Vrátí mezi volné hovory, které už nemají svou kartu.

        Vazba termínu na kartu se při smazání jen vynuluje, takže
        termín zůstával v kalendáři obsazený - ale na nástěnce po něm
        nebyla ani stopa. Honza o tom hovoru nevěděl a slot zároveň
        nemohl nabídnout nikomu dalšímu.

        Minulé hovory zůstávají: jsou záznam o tom, co se stalo,
        a kalendář už neblokují.
        """
        Termin = self.env['hh.termin'].sudo()
        terminy = Termin.search([
            ('lead_id', 'in', self.ids),
            ('stav', '=', 'rezervovany'),
            ('zacatek', '>=', fields.Datetime.now()),
        ])
        if not terminy:
            return False
        _logger.info(
            'Honza Hauzr CRM: karta mizi, uvolnuji %s domluvenych hovoru: '
            '%s', len(terminy),
            ', '.join('%s %s' % (t.zacatek, t.email or '') for t in terminy))
        terminy._hh_uvolnit()
        return True

    @api.model
    def _hh_uvolnit_osirele_terminy(self):
        """Úklid po kartách smazaných dřív, než se to začalo hlídat.

        V kalendáři po nich zůstal obsazený termín bez karty: Honza
        o tom hovoru nevěděl a slot zároveň nikomu nemohl nabídnout.
        Hledá se podle chybějící vazby, ne podle data smazání - to se
        nikde nedrží.

        Jen budoucí. Minulé jsou záznam o tom, co bylo, a kalendář
        už neblokují.

        Pouští se při každé aktualizaci a podruhé nemá co dělat.
        """
        Termin = self.env['hh.termin'].sudo()
        osirele = Termin.search([
            ('lead_id', '=', False),
            ('stav', '=', 'rezervovany'),
            ('zacatek', '>=', fields.Datetime.now()),
        ])
        if not osirele:
            return False
        _logger.info(
            'Honza Hauzr CRM: uvolnuji %s rezervaci bez karty: %s',
            len(osirele),
            ', '.join('%s %s' % (t.zacatek, t.email or '') for t in osirele))
        osirele._hh_uvolnit()
        return True
