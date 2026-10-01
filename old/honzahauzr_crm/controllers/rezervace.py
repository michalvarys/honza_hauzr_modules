# -*- coding: utf-8 -*-
"""Verejna stranka s rezervaci uvodniho hovoru.

Odkaz na ni dostane clovek po tretim dni vyzvy. Vybira ve dvou
krocich: nejdriv den, pak v nem konkretni hodinu. Jednostupnovy
seznam vsech hodin pres cely mesic byl neprehledny.
"""
import logging

import pytz

from collections import OrderedDict
from datetime import date, datetime, timedelta

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

DNY = ('pondělí', 'úterý', 'středa', 'čtvrtek', 'pátek', 'sobota', 'neděle')
DNY_ZKRATKA = ('po', 'út', 'st', 'čt', 'pá', 'so', 'ne')
MESICE = ('ledna', 'února', 'března', 'dubna', 'května', 'června',
          'července', 'srpna', 'září', 'října', 'listopadu', 'prosince')


class HhRezervace(http.Controller):

    # ------------------------------------------------------------------
    # pomocne
    # ------------------------------------------------------------------

    def _pasmo(self):
        """Casove pasmo, ve kterem se terminy ukazuji.

        Verejny navstevnik zadne nastavene nema, takze by se mu casy
        ukazaly v UTC a o dve hodiny by nesedely. Bere se proto pasmo
        firmy a kdyz ani to neni vyplnene, prazska hodina.
        """
        # sudo je nutne: verejny navstevnik nema pravo cist kontakt
        # firmy a bez nej by stranka skoncila na 403.
        firma = request.env.company.sudo()
        return firma.partner_id.tz or 'Europe/Prague'

    def _okno(self):
        """Kolik dnu dopredu se terminy nabizeji - podle rozvrhu v CRM."""
        return request.env['hh.termin'].sudo()._hh_rozvrh()['dopredu']

    def _terminy(self, jen_volne=True):
        ted = fields.Datetime.now()
        stavy = ('volny',) if jen_volne else ('volny', 'rezervovany')
        return request.env['hh.termin'].sudo().with_context(
            tz=self._pasmo()
        ).search([
            ('stav', 'in', stavy),
            ('zacatek', '>=', ted),
            ('zacatek', '<=', ted + timedelta(days=self._okno())),
        ], order='zacatek')

    def _popis_dne(self, den):
        return '%s %d. %s' % (DNY[den.weekday()], den.day,
                              MESICE[den.month - 1])

    def _seznam_dnu(self):
        """Vsechny dny v nabizenem okne, vcetne tech bez volneho casu.

        Driv se vypisovaly jen dny, ve kterych neco zbyvalo. Z rady
        karet pak nebylo poznat, jestli ve ctvrtek nic neni, nebo jestli
        se ctvrtky vubec neberou - a prazdna mista mezi datumy pusobila,
        ze se neco nenacetlo.

        Stav kazdeho dne:
          volno      - je z ceho vybirat
          plno       - pracovni den, ale nic nezbyva
          nepracovni - v rozvrhu se tenhle den hovory neberou
        """
        rozvrh = request.env['hh.termin'].sudo()._hh_rozvrh()
        pasmo = pytz.timezone(self._pasmo())
        # fields.Datetime.now() vraci naivni UTC. Bez prevodu do pasma
        # by se po mistni pulnoci jeste cely vecer nabizel vcerejsek.
        dnes = pytz.utc.localize(fields.Datetime.now()).astimezone(pasmo).date()

        # Volne hodiny po dnech - jednim dotazem, ne dotazem na kazdy den.
        volne = {}
        for termin in self._terminy():
            mistni = fields.Datetime.context_timestamp(termin, termin.zacatek)
            zaznam = volne.setdefault(mistni.date(), [])
            zaznam.append(mistni.strftime('%H:%M'))

        dny = []
        for posun in range(rozvrh['dopredu'] + 1):
            den = dnes + timedelta(days=posun)
            hodiny = volne.get(den, [])

            if hodiny:
                stav = 'volno'
            elif rozvrh['dny'][den.weekday()]:
                stav = 'plno'
            else:
                stav = 'nepracovni'

            dny.append({
                'datum': den.isoformat(),
                'den': DNY_ZKRATKA[den.weekday()],
                'cislo': den.day,
                'mesic': MESICE[den.month - 1],
                'popis': self._popis_dne(den),
                'stav': stav,
                'dnes': den == dnes,
                'pocet': len(hodiny),
                'prvni': hodiny[0] if hodiny else '',
                'posledni': hodiny[-1] if hodiny else '',
            })
        return dny

    # ------------------------------------------------------------------
    # 1. krok - prehled dnu
    # ------------------------------------------------------------------

    @http.route('/rezervace', type='http', auth='public', website=True,
                sitemap=False)
    def rezervace(self, **kw):
        # sitemap=False zamerne: stranka je pokracovanim vyzvy, nema
        # se na ni chodit z vyhledavace.
        dny = self._seznam_dnu()
        return request.render('honzahauzr_crm.stranka_rezervace_dny', {
            'dny': dny,
            'nic_volneho': not any(d['stav'] == 'volno' for d in dny),
            'chyba': kw.get('chyba'),
        })

    # ------------------------------------------------------------------
    # 2. krok - hodiny ve vybranem dni
    # ------------------------------------------------------------------

    @http.route('/rezervace/den/<string:datum>', type='http', auth='public',
                website=True, sitemap=False)
    def den(self, datum, **kw):
        try:
            vybrany = date.fromisoformat(datum)
        except ValueError:
            return request.redirect('/rezervace')

        # Ukazuji se i zabrane hodiny - clovek ma videt, co uz je pryc,
        # ne jen to, co zbyva. Preskrtnute terminy se sem nedostanou,
        # ty ve vyberu nemaji co delat.
        casy = []
        for termin in self._terminy(jen_volne=False):
            mistni = fields.Datetime.context_timestamp(termin, termin.zacatek)
            if mistni.date() != vybrany:
                continue
            casy.append({
                'id': termin.id,
                'cas': mistni.strftime('%H:%M'),
                'volny': termin.stav == 'volny',
                'minut': int(round((termin.delka or 0) * 60)),
            })

        if not casy:
            return request.redirect('/rezervace')

        return request.render('honzahauzr_crm.stranka_rezervace_den', {
            'datum': vybrany.isoformat(),
            'popis': self._popis_dne(vybrany),
            'casy': casy,
            'volnych': len([c for c in casy if c['volny']]),
            'chyba': kw.get('chyba'),
        })

    # ------------------------------------------------------------------
    # 3. krok - odeslani
    # ------------------------------------------------------------------

    @http.route('/rezervace/potvrdit', type='http', auth='public',
                methods=['POST'], website=True, csrf=True)
    def potvrdit(self, **post):
        termin_id = post.get('termin_id')
        datum = post.get('datum') or ''
        jmeno = (post.get('jmeno') or '').strip()
        email = (post.get('email') or '').strip()
        telefon = (post.get('telefon') or '').strip()
        poznamka = (post.get('poznamka') or '').strip()

        # Pri chybe se clovek vraci do dne, ze ktereho odesilal, ne na
        # zacatek - jinak by musel den hledat znovu.
        zpet = '/rezervace/den/%s' % datum if datum else '/rezervace'

        if not termin_id or not jmeno or not email:
            return request.redirect('%s?chyba=neuplne' % zpet)

        Termin = request.env['hh.termin'].sudo()
        try:
            termin = Termin.browse(int(termin_id)).exists()
        except (TypeError, ValueError):
            return request.redirect('%s?chyba=chyba' % zpet)

        if not termin or termin.stav != 'volny':
            # Nekdo byl rychlejsi - clovek se vrati na hodiny toho dne
            # a vybere si jinou.
            return request.redirect('%s?chyba=obsazeno' % zpet)

        try:
            povedlo_se = termin.hh_rezervovat(jmeno, email, telefon, poznamka)
        except Exception as chyba:
            _logger.exception('Rezervace terminu %s selhala: %s',
                              termin_id, chyba)
            return request.redirect('%s?chyba=chyba' % zpet)

        if not povedlo_se:
            return request.redirect('%s?chyba=obsazeno' % zpet)

        v_pasmu = termin.with_context(tz=self._pasmo())
        return request.render('honzahauzr_crm.stranka_rezervace_hotovo', {
            'termin': v_pasmu,
            'kdy': v_pasmu._hh_cas(termin.zacatek),
        })

    # ------------------------------------------------------------------
    # data pro snippet
    # ------------------------------------------------------------------
    #
    # Snippet se da pretahnout na libovolnou stranku, takze si obsah
    # nacita sam odsud. Diky tomu nemusi byt v ulozene strance zadny
    # seznam terminu - kdyby tam byl, zustal by v ni zamrzly ten, ktery
    # tam byl v okamziku ulozeni.

    @staticmethod
    def _hh_zamceno_do_dne(den):
        """Je kalendar na strance vyzvy jeste zamceny?

        Na samostatne strance /rezervace se nezamyka nic - tohle se
        tyka jen bloku, ktery si vyzada konkretni den vyzvy. Kalendar
        je videt porad, jen do te doby nejde kliknout.
        """
        try:
            den = int(den or 0)
        except (TypeError, ValueError):
            return False
        if den not in (1, 2, 3):
            return False

        # Kdo web upravuje, vidi kalendar odemceny - jinak by si
        # nemohl vyzkouset, jak se chova.
        if request.env.user.has_group('website.group_website_restricted_editor'):
            return False

        lead = request.env['crm.lead']._hh_vyzva_ucastnik()
        if not lead:
            return True
        stav = {d['cislo']: d for d in lead.hh_vyzva_stav()}
        return not (stav.get(den) or {}).get('odemceno')

    @http.route('/rezervace/data', type='json', auth='public', website=True)
    def data(self, odemkne_den=None, **kw):
        # Hodiny po dnech - do karty dne, na kterou se klikne.
        casy = OrderedDict()
        for termin in self._terminy(jen_volne=False):
            mistni = fields.Datetime.context_timestamp(termin, termin.zacatek)
            casy.setdefault(mistni.date(), []).append({
                'id': termin.id,
                'cas': mistni.strftime('%H:%M'),
                'volny': termin.stav == 'volny',
                'minut': int(round((termin.delka or 0) * 60)),
            })

        # Vypisuji se vsechny dny v okne, ne jen ty s volnym casem -
        # stejne jako v kalendari v adminu. Z rady karet je tak videt,
        # ve ktere dny se hovory vubec neberou, a mezi datumy nezustavaji
        # diry, ktere pusobily, ze se neco nenacetlo.
        dny = self._seznam_dnu()
        for den in dny:
            datum = date.fromisoformat(den['datum'])
            den['casy'] = casy.get(datum, [])
            den['volnych'] = len([c for c in den['casy'] if c['volny']])

        return {
            'dny': dny,
            'zamceno': self._hh_zamceno_do_dne(odemkne_den),
        }

    @http.route('/rezervace/data/rezervovat', type='json', auth='public',
                website=True)
    def data_rezervovat(self, termin_id=None, jmeno=None, email=None,
                        telefon=None, poznamka=None, **kw):
        jmeno = (jmeno or '').strip()
        email = (email or '').strip()

        if not termin_id or not jmeno or not email:
            return {'ok': False, 'chyba': 'neuplne'}

        Termin = request.env['hh.termin'].sudo()
        try:
            termin = Termin.browse(int(termin_id)).exists()
        except (TypeError, ValueError):
            return {'ok': False, 'chyba': 'chyba'}

        if not termin or termin.stav != 'volny':
            return {'ok': False, 'chyba': 'obsazeno'}

        try:
            povedlo_se = termin.hh_rezervovat(
                jmeno, email, (telefon or '').strip(), (poznamka or '').strip())
        except Exception as chyba:
            _logger.exception('Rezervace terminu %s selhala: %s',
                              termin_id, chyba)
            return {'ok': False, 'chyba': 'chyba'}

        if not povedlo_se:
            return {'ok': False, 'chyba': 'obsazeno'}

        v_pasmu = termin.with_context(tz=self._pasmo())
        return {'ok': True, 'kdy': v_pasmu._hh_cas(termin.zacatek)}

    # ------------------------------------------------------------------
    # zruseni z odkazu v e-mailu
    # ------------------------------------------------------------------

    @http.route('/rezervace/zrusit/<int:termin_id>/<string:klic>',
                type='http', auth='public', website=True, sitemap=False)
    def zrusit(self, termin_id, klic, **kw):
        termin = request.env['hh.termin'].sudo().browse(termin_id).exists()

        # Bez shody klice se nic nerusi - jinak by stacilo menit cislo
        # v adrese a rusit cizi rezervace.
        if not termin or not termin.zrusovaci_klic or termin.zrusovaci_klic != klic:
            return request.render('honzahauzr_crm.stranka_rezervace_zruseno', {
                'povedlo_se': False,
            })

        povedlo_se = termin.hh_zrusit_zakaznikem()
        return request.render('honzahauzr_crm.stranka_rezervace_zruseno', {
            'povedlo_se': povedlo_se,
        })
