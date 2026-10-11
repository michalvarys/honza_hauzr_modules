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

from odoo import api, fields, models


class CrmLeadTermin(models.Model):
    _inherit = 'crm.lead'

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
