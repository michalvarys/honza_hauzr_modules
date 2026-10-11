# -*- coding: utf-8 -*-
"""Kdo kolik z videa výzvy opravdu viděl.

Honza potřebuje vědět víc než "poslal jsem mu e-mail". Zajímá ho,
jestli člověk video vůbec pustil, kam se v něm dostal a jestli ho
dokoukal - a jestli vůbec došel na druhý a třetí den.

Jeden záznam = jeden člověk a jeden den. Píše do něj stránka výzvy,
když video běží.

Co se měří a co ne
------------------
Měří se **nejdál dosažená vteřina**, ne součet přehraného času.
Kdyby se sčítalo, vyšlo by z přetáčení sem a tam víc, než má video
minut. Takhle číslo roste jen tehdy, když se člověk dostane dál,
než kde kdy byl.

Přeskakování se tím nepozná - kdo video přetáhne na konec, bude mít
sto procent. Na to by byla potřeba mapa zhlédnutých úseků, což je
na tenhle účel složitost navíc. Honza se ptá "došel až na konec?",
ne "neošidil mě?".

Čísla posílá prohlížeč, takže se dají podvrhnout. Pro rozhodování,
komu zavolat, to stačí; jako důkaz o plnění ne.
"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Od kolika procent se video bere jako dokoukané. Ne sto: skoro nikdo
# nedojede závěrečné titulky a konec videa se často odklikne pár
# vteřin před úplným dohráním.
DOKOUKANO_OD = 90


class HhVyzvaSledovani(models.Model):
    _name = 'hh.vyzva.sledovani'
    _description = 'Sledování videa výzvy'
    _order = 'lead_id, den'
    _rec_name = 'display_name'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Příležitost',
        required=True,
        ondelete='cascade',
        index=True,
    )
    den = fields.Selection(
        selection=[('1', 'Den 1'), ('2', 'Den 2'), ('3', 'Den 3')],
        string='Den',
        required=True,
        index=True,
    )

    otevreno = fields.Datetime(
        string='Poprvé otevřel',
        help='Kdy se mu stránka s tímhle dnem poprvé načetla '
             'odemčená.',
    )
    spusteno = fields.Datetime(
        string='Poprvé spustil',
        help='Kdy poprvé zmáčkl přehrát. Prázdné = stránku viděl, '
             'ale video nepustil.',
    )
    naposledy = fields.Datetime(string='Naposledy sledoval')

    nejdale = fields.Integer(
        string='Nejdál (s)',
        default=0,
        help='Nejdál dosažená vteřina videa. Neroste přetáčením '
             'dozadu ani opakovaným přehráním.',
    )
    delka = fields.Integer(
        string='Délka videa (s)',
        default=0,
        help='Hlásí ji přehrávač. Bez ní nejde spočítat procento.',
    )

    procento = fields.Integer(
        string='Zhlédnuto',
        compute='_compute_procento',
        store=True,
        help='Kolik procent videa má za sebou.',
    )
    dokoukano = fields.Boolean(
        string='Dokoukal',
        compute='_compute_procento',
        store=True,
        help='Od %s %% výš. Posledních pár vteřin skoro nikdo '
             'nedojede.' % DOKOUKANO_OD,
    )

    @api.depends('nejdale', 'delka')
    def _compute_procento(self):
        for z in self:
            if z.delka > 0:
                # Zastropovane na sto: prehravac u kratkych videi
                # obcas ohlasi cas o zlomek vetsi nez delku.
                z.procento = min(100, round(100.0 * z.nejdale / z.delka))
            else:
                z.procento = 0
            z.dokoukano = z.procento >= DOKOUKANO_OD

    @api.depends('lead_id', 'den', 'procento')
    def _compute_display_name(self):
        for z in self:
            z.display_name = '%s · den %s · %s %%' % (
                z.lead_id.contact_name or z.lead_id.email_from or '?',
                z.den or '?', z.procento)

    _sql_constraints = [
        ('jeden_zaznam_na_den', 'UNIQUE(lead_id, den)',
         'Sledování se u každého dne vede jen jednou.'),
    ]

    # ------------------------------------------------------------------
    # zapis ze stranky
    # ------------------------------------------------------------------

    @api.model
    def _hh_zapsat(self, lead, den, sekund=None, delka=None, spustil=False):
        """Založí nebo doplní záznam. Vrací ho.

        Volá se z webu u veřejného návštěvníka, proto sudo. Zapisuje
        se jen dopředu: nejdál dosažená vteřina nikdy neklesne, takže
        opakované přehrání ani přetáčení dozadu statistiku nesmaže.
        """
        if not lead or den not in ('1', '2', '3'):
            return self.browse()

        ted = fields.Datetime.now()
        zaznam = self.sudo().search(
            [('lead_id', '=', lead.id), ('den', '=', den)], limit=1)
        if not zaznam:
            zaznam = self.sudo().create({
                'lead_id': lead.id, 'den': den, 'otevreno': ted})

        zapis = {'naposledy': ted}
        if not zaznam.otevreno:
            zapis['otevreno'] = ted
        if spustil and not zaznam.spusteno:
            zapis['spusteno'] = ted
        if delka and delka > 0:
            zapis['delka'] = int(delka)
        if sekund and int(sekund) > zaznam.nejdale:
            zapis['nejdale'] = int(sekund)

        zaznam.sudo().write(zapis)
        return zaznam


class CrmLeadSledovani(models.Model):
    """Přehled sledování na kartě, ať to Honza nemusí nikde hledat."""

    _inherit = 'crm.lead'

    hh_sledovani_ids = fields.One2many(
        'hh.vyzva.sledovani', 'lead_id', string='Sledování videí')

    hh_videa_souhrn = fields.Char(
        string='Videa výzvy',
        compute='_compute_hh_videa_souhrn',
        help='Kolik procent má člověk za sebou u jednotlivých dnů.',
    )

    @api.depends('hh_sledovani_ids.procento')
    def _compute_hh_videa_souhrn(self):
        for lead in self:
            podle_dne = {z.den: z for z in lead.hh_sledovani_ids}
            kusy = []
            for den in ('1', '2', '3'):
                z = podle_dne.get(den)
                if not z:
                    kusy.append('%s. –' % den)
                elif not z.spusteno:
                    kusy.append('%s. otevřel' % den)
                else:
                    kusy.append('%s. %s %%%s' % (
                        den, z.procento, ' ✓' if z.dokoukano else ''))
            lead.hh_videa_souhrn = '  ·  '.join(kusy)
