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
