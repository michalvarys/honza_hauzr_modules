# -*- coding: utf-8 -*-
"""Podklady pro vlastni administraci.

Obrazovka si rada data v jednom dotazu, ne v peti. Duvod je
praktický: kazdy dotaz z prohlizece je jedno kolo tam a zpet, a pri
prepnuti zalozky by se jich jinak poslalo nekolik za sebou a cisla
by naskakovala postupne.

Nic se tu nepocita znovu - jen se cte to, co uz v databazi je.
"""

from datetime import timedelta

from odoo import api, fields, models


class HhAdmin(models.AbstractModel):
    _name = 'hh.admin'
    _description = 'Podklady pro vlastní administraci'

    # ------------------------------------------------------------------
    # cisla do karet
    # ------------------------------------------------------------------

    @api.model
    def hh_cisla(self):
        """Ctyri cisla do karet nahore."""
        Lead = self.env['crm.lead'].sudo()
        Termin = self.env['hh.termin'].sudo()
        ted = fields.Datetime.now()

        stupen_vyzva = self.env['crm.stage'].sudo().search(
            [('name', 'ilike', 'výzv')], limit=1)

        # Odeslane zpravy se nepocitaji z posty, ale z toho, co ma
        # kazdy clovek u sebe poznamenane - posta se maze, poznamka
        # zustava.
        self.env.cr.execute("SELECT count(*) FROM hh_lead_odeslany_mail_rel")
        odeslano = self.env.cr.fetchone()[0]

        return {
            'lidi': Lead.search_count([('active', '=', True)]),
            'vyzva': Lead.search_count([
                ('active', '=', True),
                ('stage_id', '=', stupen_vyzva.id),
            ]) if stupen_vyzva else 0,
            'hovory': Termin.search_count([
                ('stav', '=', 'rezervovany'),
                ('zacatek', '>=', ted),
            ]),
            'maily': odeslano,
        }

    # ------------------------------------------------------------------
    # zalozka Nastenka
    # ------------------------------------------------------------------

    @api.model
    def hh_nastenka(self, limit=60):
        """Sloupce a karty v nich - totez, co ukazuje nastenka Odoo.

        Prehazovani karet se dela beznym zapisem do stage_id, takze
        plati stejna pravidla jako doted: presun do sloupce spusti
        e-maily navazane na jeho stitky.
        """
        Lead = self.env['crm.lead'].sudo()
        stupne = self.env['crm.stage'].sudo().search([], order='sequence, id')

        out = []
        for s in stupne:
            leady = Lead.search_read(
                [('active', '=', True), ('stage_id', '=', s.id)],
                ['name', 'contact_name', 'email_from', 'phone', 'tag_ids',
                 'create_date', 'expected_revenue'],
                limit=limit, order='create_date desc')
            out.append({
                'id': s.id,
                'nazev': s.name,
                'karty': leady,
                'celkem': Lead.search_count(
                    [('active', '=', True), ('stage_id', '=', s.id)]),
            })

        # Nazvy stitku najednou, at se na ne nechodi po jedne karte.
        ids = set()
        for sl in out:
            for k in sl['karty']:
                ids.update(k['tag_ids'])
        stitky = {t['id']: t['name'] for t in self.env['crm.tag'].sudo()
                  .search_read([('id', 'in', list(ids))], ['name'])}
        for sl in out:
            for k in sl['karty']:
                k['stitky'] = [stitky.get(i, '') for i in k['tag_ids']]
                k['kdy'] = fields.Datetime.context_timestamp(
                    self, k['create_date']).strftime('%d.%m.%Y')

        return out

    @api.model
    def hh_pridat_sekci(self, nazev):
        """Zalozi sekci z nastenky.

        Jde toutez cestou jako sekce zalozena formularem z webu, takze
        vznikne sloupec i oba stitky a jsou spolu svazane. Dve ruzne
        cesty k temuz by znamenaly, ze rucne zalozeny sloupec nema
        radu e-mailu a nikdo nevi proc.
        """
        stupen = self.env['crm.lead']._hh_zajistit_sekci(nazev)
        return stupen.id if stupen else False

    @api.model
    def hh_prejmenovat_sekci(self, stupen_id, nazev):
        """Prejmenuje sloupec. Stitky si nazev nechavaji.

        Prejmenovat s nim i stitky by znamenalo prepsat je i u lidi,
        kteri uz timhle sloupcem davno prosli - a v jejich historii
        by pak stalo neco, co tam nikdy nebylo.
        """
        nazev = (nazev or '').strip()
        if not nazev:
            return False
        self.env['crm.stage'].sudo().browse(stupen_id).name = nazev
        return True

    @api.model
    def hh_smazat_sekci(self, stupen_id):
        """Smaze sloupec, ale jen prazdny.

        Se smazanim sloupce, ve kterem nekdo stoji, by ti lide zmizeli
        z nastenky - Odoo je nikam neprerazuje. Stitky zustavaji:
        visi na nich rada e-mailu a muzou patrit i jinam.
        """
        stupen = self.env['crm.stage'].sudo().browse(stupen_id)
        if not stupen.exists():
            return {'ok': False, 'duvod': 'Sekce už neexistuje.'}
        pocet = self.env['crm.lead'].sudo().search_count(
            [('stage_id', '=', stupen.id), ('active', '=', True)])
        if pocet:
            return {'ok': False,
                    'duvod': 'V sekci je %s lidí. Nejdřív je přesuň jinam.' % pocet}
        stupen.unlink()
        return {'ok': True}

    # ------------------------------------------------------------------
    # zalozka Lide
    # ------------------------------------------------------------------

    @api.model
    def hh_lide(self, hledani='', stupen_id=None, limit=80):
        domena = [('active', '=', True)]
        if stupen_id:
            domena.append(('stage_id', '=', stupen_id))
        if hledani:
            domena += ['|', '|', '|',
                       ('contact_name', 'ilike', hledani),
                       ('name', 'ilike', hledani),
                       ('email_from', 'ilike', hledani),
                       ('phone', 'ilike', hledani)]

        Lead = self.env['crm.lead'].sudo()
        zaznamy = Lead.search_read(
            domena,
            ['contact_name', 'name', 'email_from', 'phone', 'stage_id',
             'tag_ids', 'hh_zdroj', 'hh_web', 'create_date'],
            limit=limit, order='create_date desc')

        # Nazvy stitku najednou, at se na ne nechodi po jednom.
        ids = set()
        for z in zaznamy:
            ids.update(z['tag_ids'])
        stitky = {s['id']: s['name'] for s in self.env['crm.tag'].sudo()
                  .search_read([('id', 'in', list(ids))], ['name'])}

        zdroje = dict(Lead._fields['hh_zdroj'].selection)
        weby = dict(Lead._fields['hh_web'].selection)

        for z in zaznamy:
            z['stitky'] = [stitky.get(i, '') for i in z['tag_ids']]
            z['zdroj'] = zdroje.get(z['hh_zdroj'], '')
            z['web'] = weby.get(z['hh_web'], '')
            z['stupen'] = z['stage_id'][1] if z['stage_id'] else ''

        stupne = self.env['crm.stage'].sudo().search_read(
            [], ['name'], order='sequence, id')

        return {'lide': zaznamy, 'stupne': stupne,
                'celkem': Lead.search_count(domena)}

    # ------------------------------------------------------------------
    # zalozka Vyzva
    # ------------------------------------------------------------------

    @api.model
    def hh_vyzva(self, limit=80):
        """Kdo je ve vyzve a jak daleko je."""
        stupen = self.env['crm.stage'].sudo().search(
            [('name', 'ilike', 'výzv')], limit=1)
        if not stupen:
            return {'lide': [], 'stupen': ''}

        leady = self.env['crm.lead'].sudo().search(
            [('active', '=', True), ('stage_id', '=', stupen.id)],
            limit=limit, order='hh_stupen_od desc, create_date desc')

        out = []
        for lead in leady:
            dny = lead.hh_vyzva_stav() if lead.hh_vyzva_klic else []
            out.append({
                'id': lead.id,
                'jmeno': lead.contact_name or lead.name,
                'email': lead.email_from or '',
                'odkaz': lead.hh_vyzva_odkaz,
                'maKlic': bool(lead.hh_vyzva_klic),
                'od': (lead.hh_stupen_od or lead.create_date).strftime('%d.%m.%Y')
                      if (lead.hh_stupen_od or lead.create_date) else '',
                'dny': [{'cislo': d['cislo'],
                         'odemceno': d['odemceno'],
                         'zbyva': d['zbyva_hodin']} for d in dny],
            })
        return {'lide': out, 'stupen': stupen.name}

    # ------------------------------------------------------------------
    # zalozka Hovory
    # ------------------------------------------------------------------

    @api.model
    def hh_hovory(self, limit=60):
        ted = fields.Datetime.now()
        Termin = self.env['hh.termin'].sudo()

        rezervovane = Termin.search_read(
            [('stav', '=', 'rezervovany'), ('zacatek', '>=', ted)],
            ['zacatek', 'jmeno', 'email', 'telefon', 'poznamka'],
            limit=limit, order='zacatek')

        for r in rezervovane:
            r['kdy'] = fields.Datetime.context_timestamp(
                self, r['zacatek']).strftime('%d.%m.%Y %H:%M')

        # Kolik volnych terminu je jeste pred nami, po dnech.
        #
        # Seskupuje se podle zacatku, ne podle hh_datum: to je pocitane
        # pole bez store, takze podle nej nejde ani seskupovat, ani
        # filtrovat. Totez plati pro hh_nabizet - a neni ho tu treba,
        # protoze se odvozuje prave ze stavu, na ktery se ptam.
        volne = Termin.read_group(
            [('stav', '=', 'volny'),
             ('zacatek', '>=', ted), ('zacatek', '<=', ted + timedelta(days=21))],
            ['id'], ['zacatek:day'])

        return {
            'rezervovane': rezervovane,
            'volne': [{'den': v['zacatek:day'], 'pocet': v['zacatek_count']}
                      for v in volne if v.get('zacatek:day')],
        }

    # ------------------------------------------------------------------
    # obrazovka Sekvence
    # ------------------------------------------------------------------

    @api.model
    def hh_sekvence(self):
        """Stitky a pod nimi jejich zpravy, serazene podle odstupu."""
        stitky = self.env['hh.mail.stitek'].sudo().search_read(
            [], ['name'], order='name')
        zpravy = self.env['hh.mail.sablona'].sudo().search_read(
            [], ['name', 'predmet', 'po_dnech', 'zapnuto', 'stitek_id'],
            order='po_dnech, id')

        podle = {}
        for z in zpravy:
            podle.setdefault(z['stitek_id'][0] if z['stitek_id'] else 0, []).append(z)

        out = [dict(s, zpravy=podle.get(s['id'], [])) for s in stitky]

        # Zpravy bez stitku by jinak zmizely ze sveta - nikde jinde
        # uz se neukazuji.
        if podle.get(0):
            out.append({'id': 0, 'name': 'Bez štítku', 'zpravy': podle[0]})
        return out

    # ------------------------------------------------------------------
    # obrazovka Stitky
    # ------------------------------------------------------------------

    @api.model
    def hh_stitky(self):
        """Stitky s tim, kolik zprav na nich visi a kolik sloupcu je
        pouziva. Bez toho druheho cisla nejde poznat, jestli se stitek
        da smazat."""
        Stitek = self.env['hh.mail.stitek'].sudo()
        out = []
        for s in Stitek.search([], order='name'):
            sloupce = self.env['crm.stage'].sudo().search(
                [('hh_stitek_ids', 'in', s.id)])
            out.append({
                'id': s.id,
                'name': s.name,
                'zprav': len(s.mail_ids),
                'zapnutych': len(s.mail_ids.filtered('zapnuto')),
                'sloupce': sloupce.mapped('name'),
            })
        return out

    # ------------------------------------------------------------------
    # zalozka Statistiky
    # ------------------------------------------------------------------

    @api.model
    def hh_statistiky(self):
        Lead = self.env['crm.lead'].sudo()

        # Kolik lidi sedi v kterem sloupci.
        podle_stupne = Lead.read_group(
            [('active', '=', True)], ['id'], ['stage_id'])
        stupne = [{'nazev': s['stage_id'][1] if s['stage_id'] else 'Bez fáze',
                   'pocet': s['stage_id_count']} for s in podle_stupne]

        # Odkud lide chodi.
        zdroje_popis = dict(Lead._fields['hh_zdroj'].selection)
        podle_zdroje = Lead.read_group(
            [('active', '=', True)], ['id'], ['hh_zdroj'])
        zdroje = [{'nazev': zdroje_popis.get(z['hh_zdroj'], 'Neuvedeno'),
                   'pocet': z['hh_zdroj_count']} for z in podle_zdroje]

        # Prirustek za poslednich sest tydnu.
        ted = fields.Datetime.now()
        tydny = []
        for i in range(5, -1, -1):
            od = ted - timedelta(days=7 * (i + 1))
            do = ted - timedelta(days=7 * i)
            tydny.append({
                'popis': do.strftime('%d.%m.'),
                'pocet': Lead.search_count([
                    ('create_date', '>=', od), ('create_date', '<', do)]),
            })

        return {'stupne': stupne, 'zdroje': zdroje, 'tydny': tydny}
