# -*- coding: utf-8 -*-
"""Kdo kolik z kterého videa opravdu viděl.

Honza potřebuje vědět víc než "poslal jsem mu e-mail". Zajímá ho,
jestli člověk video vůbec pustil, kam se v něm dostal a jestli ho
dokoukal - a jestli vůbec došel na druhý a třetí den.

Jeden záznam = jeden člověk a jedno video. Píše do něj stránka,
na které video běží - kterákoliv, ne jen výzva. U třídenní výzvy
je navíc vyplněný den, takže se podle něj dá dál řadit a filtrovat.

Že za přehráváním stojí konkrétní člověk, se pozná z relace: jakmile
někdo odešle formulář nebo otevře svůj osobní odkaz, drží si ji web
dál. Kdo se nikdy nepředstavil, zůstává jen v souhrnu za video
(hh.video) a tady nemá nic.

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
        string='Den výzvy',
        index=True,
        help='Vyplněné jen u tří videí třídenní výzvy. U ostatních '
             'videí na webu zůstává prázdné.',
    )

    # Oznaceni videa. Klic zaznamu: jeden clovek muze mit u jednoho
    # videa jen jeden radek, at ho pousti kolikrat chce.
    video = fields.Char(
        string='Označení videa',
        index=True,
        help='Kód videa na YouTube, nebo název souboru u videa '
             'nahraného přímo na web.\n\n'
             'Prázdné zůstane jen u záznamů z doby, kdy se '
             'sledovala pouze tři videa výzvy a označení se '
             'nevedlo.',
    )
    nazev = fields.Char(
        string='Video',
        help='Název, jak ho hlásí přehrávač.',
    )
    stranka = fields.Char(
        string='Stránka',
        help='Kde to video člověk pustil.',
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

    @api.depends('lead_id', 'den', 'nazev', 'video', 'procento')
    def _compute_display_name(self):
        for z in self:
            kdo = z.lead_id.contact_name or z.lead_id.email_from or '?'
            co = ('den %s' % z.den) if z.den else (z.nazev or z.video)
            z.display_name = '%s · %s · %s %%' % (kdo, co, z.procento)

    _sql_constraints = [
        ('jeden_zaznam_na_video', 'UNIQUE(lead_id, video)',
         'Sledování se u každého videa vede jen jednou.'),
    ]

    # ------------------------------------------------------------------
    # zapis ze stranky
    # ------------------------------------------------------------------

    @api.model
    def _hh_zapsat(self, lead, video, den=None, sekund=None, delka=None,
                   spustil=False, nazev=None, stranka=None):
        """Založí nebo doplní záznam. Vrací ho.

        Volá se z webu u veřejného návštěvníka, proto sudo. Zapisuje
        se jen dopředu: nejdál dosažená vteřina nikdy neklesne, takže
        opakované přehrání ani přetáčení dozadu statistiku nesmaže.

        Klíčem je video, ne den: tentýž člověk může koukat i na videa
        mimo výzvu a u těch žádný den není.
        """
        video = (video or '').strip()[:120]
        if not lead or not video:
            return self.browse()

        ted = fields.Datetime.now()
        zaznam = self.sudo().search(
            [('lead_id', '=', lead.id), ('video', '=', video)], limit=1)
        if not zaznam:
            zaznam = self.sudo().create({
                'lead_id': lead.id, 'video': video, 'otevreno': ted})

        zapis = {'naposledy': ted}
        if not zaznam.otevreno:
            zapis['otevreno'] = ted
        if spustil and not zaznam.spusteno:
            zapis['spusteno'] = ted
        if delka and int(delka) > 0:
            zapis['delka'] = int(delka)
        if sekund and int(sekund) > zaznam.nejdale:
            zapis['nejdale'] = int(sekund)
        if den in ('1', '2', '3') and zaznam.den != den:
            zapis['den'] = den
        if stranka and not zaznam.stranka:
            zapis['stranka'] = stranka.strip()[:200]
        if not zaznam.nazev:
            zapis['nazev'] = self._hh_nazev(
                nazev, den or zaznam.den, stranka or zaznam.stranka, video)

        zaznam.sudo().write(zapis)
        return zaznam


    @api.model
    def _hh_nazev(self, nazev, den, stranka, video):
        """Jméno videa do seznamu. Nikdy prázdné.

        Přehrávač titulek hlásí, ale ne vždycky - u videa nahraného
        přímo na web žádný není a YouTube ho při prvním hlášení
        ještě nemusí stihnout. Bez náhrady by se takový řádek
        v seskupení schoval do skupiny "Žádné", která nikomu nic
        neřekne.
        """
        if nazev and nazev.strip():
            return nazev.strip()[:200]
        if den in ('1', '2', '3'):
            return 'Výzva – den %s' % den
        if stranka:
            return 'Video na %s' % stranka.strip()[:180]
        return (video or 'Video')[:200]

    @api.model
    def _hh_doplnit_oznaceni(self):
        """Doplní označení videa u záznamů z doby, kdy se nevedlo.

        Tehdy se sledovala jen tři videa výzvy a klíčem byl den.
        Dnes je klíčem video, protože se měří i videa na ostatních
        stránkách. Starým řádkům se proto dosadí zástupné označení
        podle dne - číslo je zachované, jen dostane jméno.

        Pouští se při každém upgradu a podruhé už nic nezmění.
        """
        stare = self.sudo().search([('video', '=', False)])
        for zaznam in stare:
            zaznam.video = 'vyzva-den-%s' % (zaznam.den or '0')

        # Jmeno do seznamu. Tyka se i radku, ktere oznaceni uz maji,
        # ale vznikly driv, nez se jmeno vedlo.
        bezejmenne = self.sudo().search([('nazev', '=', False)])
        for zaznam in bezejmenne:
            zaznam.nazev = self._hh_nazev(
                None, zaznam.den, zaznam.stranka, zaznam.video)

        if stare or bezejmenne:
            _logger.info(
                'Honza Hauzr CRM: sledovani - oznaceni doplneno %sx, '
                'jmeno %sx.', len(stare), len(bezejmenne))
        return len(stare), len(bezejmenne)


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
