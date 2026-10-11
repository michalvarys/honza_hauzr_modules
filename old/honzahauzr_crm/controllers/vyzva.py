# -*- coding: utf-8 -*-
"""Tridenni vyzva - data pro snippet a obnoveni pristupu.

Samotnou stranku /zpet-do-zivota/vyzva uz zadna routa neobsluhuje.
Je to bezna website.page s oe_structure, takze ji jde upravovat
v editoru jako kazdou jinou. Driv to byla routa v kodu a kvuli tomu
se stranka neobjevila v seznamu stranek, snippety u ni byly sede
a sekce nesly mazat.

Obsah tri dnu do stranky doplnuje snippet az pres tuhle routu.
Zamcene video se do prohlizece nedostane - adresu vraci server jen
u dnu, ktere jsou opravdu odemcene.
"""
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

CIL = '/zpet-do-zivota/vyzva'


class HhVyzva(http.Controller):

    @http.route(CIL + '/stav', type='json', auth='public', website=True)
    def stav(self, k=None, **kw):
        """Stav dnu pro prihlaseneho ucastnika.

        Klic z odkazu v e-mailu prichazi az odsud: stranka je staticka
        a adresu s ?k=... cte az skript, ktery ji preda sem. Bez toho
        by odkaz z e-mailu prestal fungovat - pri vykresleni stranky
        uz ho nikdo necte.

        Kdyz ucastnika nepoznáme, vrati se vsechny dny zamcene bez
        odpoctu a stranka nabidne zadani e-mailu.
        """
        lead = request.env['crm.lead']._hh_vyzva_ucastnik(k or None)

        # Prihlasenemu spravci se u prazdneho dne pripise, kde se adresa
        # videa zadava. Navstevnikovi se takova hlaska ukazat nesmi.
        spravce = request.env.user.has_group('base.group_user')

        # Nahled "odemceno" ukazuje stranku tak, jak vypada po trech
        # dnech - bez odpoctu a bez vyzvy k zadani e-mailu. Protejsek
        # "zamceno" se tu neresi: ten uz zaridilo rozpoznani ucastnika,
        # ktere v takovem pripade nikoho nevrati.
        if request.env['crm.lead']._hh_nahled() == 'odemceno':
            return {
                'zname': True,
                'spravce': spravce,
                'jmeno': '',
                'dny': [{'cislo': c, 'odemceno': True, 'zbyva_hodin': 0,
                         'odemkne_se': '', 'video': ''} for c in (1, 2, 3)],
            }

        if not lead:
            return {
                'zname': False,
                'spravce': spravce,
                'jmeno': '',
                'dny': [{'cislo': c, 'odemceno': False, 'zbyva_hodin': 0,
                         'odemkne_se': '', 'video': ''} for c in (1, 2, 3)],
            }

        return {
            'zname': True,
            'spravce': spravce,
            'jmeno': (lead.contact_name or '').strip(),
            'dny': lead.hh_vyzva_stav(),
        }

    @http.route(CIL + '/sledovani', type='json', auth='public', website=True)
    def sledovani(self, k=None, den=None, sekund=None, delka=None,
                  spustil=False, **kw):
        """Postup v přehrávači. Hlásí ho stránka, když video běží.

        Zapisuje se jen u dnů, které má člověk opravdu odemčené -
        jinak by si šlo poslat postup u zamčeného dne a Honza by
        v přehledu viděl, že ho někdo viděl dřív, než mohl.

        Mlčí i při chybě: statistika nesmí ničím rušit přehrávání.
        """
        lead = request.env['crm.lead']._hh_vyzva_ucastnik(k or None)
        if not lead or str(den) not in ('1', '2', '3'):
            return {'zapsano': False}

        dny = {str(d['cislo']): d for d in lead.hh_vyzva_stav()}
        if not dny.get(str(den), {}).get('odemceno'):
            return {'zapsano': False}

        try:
            request.env['hh.vyzva.sledovani'].sudo()._hh_zapsat(
                lead, str(den),
                sekund=int(sekund or 0), delka=int(delka or 0),
                spustil=bool(spustil))
        except Exception as chyba:
            _logger.warning(
                'Honza Hauzr CRM: sledovani dne %s se nezapsalo: %s',
                den, chyba)
            return {'zapsano': False}
        return {'zapsano': True}

    @http.route(CIL + '/dokonceno', type='json', auth='public', website=True)
    def dokonceno(self, k=None, **kw):
        """Ucastnik potvrdil, ze vyzvu dokoncil.

        Tohle je jedina spolehliva evidence dokonceni, kterou mame.
        Zhlednuti videa ani otevreni e-mailu nic nedokladaji - clovek
        muze video pustit a odejit - a odeslani posledni lekce uz
        vubec. Proto se Honza na konci treti lekce zepta a teprve
        potvrzeni spusti navaznou radu e-mailu.

        Potvrzuje se jednou. Druhe kliknuti uz jen rekne, ze to mame.
        """
        lead = request.env['crm.lead']._hh_vyzva_ucastnik(k or None)
        if not lead:
            return {'zname': False, 'potvrzeno': False}

        # Treti den musi byt odemceny, jinak by si slo dokonceni
        # odkliknout hned po prihlaseni a prodejni rada by zacala
        # chodit cloveku, ktery vyzvu ani nevidel.
        dny = lead.hh_vyzva_stav()
        if not dny or not dny[-1].get('odemceno'):
            return {'zname': True, 'potvrzeno': False, 'brzy': True}

        lead.sudo()._hh_vyzva_dokoncil()
        return {'zname': True, 'potvrzeno': True}

    @http.route(CIL + '/nahled', type='http', auth='public',
                website=True, sitemap=False)
    def nahled(self, strana=None, **kw):
        """Prepne nahled stranky mezi zamcenou a odemcenou podobou.

        Slouzi k ukazovani rozdelane prace - jde si projit obe strany
        bez cekani na e-maily. Volba se drzi v relaci, ne v adrese:
        kalendar i stav dnu si o data rikaji zvlast a do techto
        pozadavku by se parametr z adresy stranky nedostal.

        Kdyz prepinac neni zapnuty systemovym parametrem, routa jen
        odvede zpatky na stranku a nic nenastavi.
        """
        Lead = request.env['crm.lead'].sudo()
        if Lead._hh_nahled_povolen():
            if strana in ('odemceno', 'zamceno', 'odpocet'):
                request.session[Lead.HH_NAHLED_RELACE] = strana
                if strana == 'odpocet':
                    # Zkusebni ucastnik s cerstvym zacatkem. Spousti se
                    # pri kazdem prepnuti, takze odpocet zacina znovu
                    # a ukazku jde opakovat.
                    Lead._hh_nahled_spustit_odpocet()
            else:
                request.session.pop(Lead.HH_NAHLED_RELACE, None)
        return request.redirect(CIL)

    @http.route(CIL + '/obnovit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True, sitemap=False)
    def obnovit(self, email=None, **kw):
        """Najde ucastnika podle e-mailu a zapamatuje si ho v prohlizeci.

        Zalozni cesta pro cloveka, ktery prijde z jineho zarizeni
        a odkaz z e-mailu nema po ruce. Vraci se zpatky na stranku
        vyzvy - bud uz s odemcenymi dny, nebo s hlaskou.
        """
        lead = request.env['crm.lead']._hh_vyzva_podle_emailu(email)
        if not lead:
            return request.redirect(CIL + '?chyba=1')
        return request.redirect(CIL)

    # ------------------------------------------------------------------
    # video nahrane primo na web
    # ------------------------------------------------------------------
    #
    # Videa vyzvy jsou tajna, takze se nesmi dat najit drive, nez na ne
    # clovek ma narok. Prilozeny soubor v Odoo tuhle vlastnost sam
    # o sobe nema: prilohy maji poradova cisla, takze by stacilo
    # zkouset /web/content/124, 125 a videa si vytahnout predem.
    #
    # Soubor se proto uklada jako neverejna priloha a ven se dostane
    # jen pres tuhle routu, ktera se u kazdeho pozadavku zepta, kdo se
    # pta a jestli uz ten den ma odemceny. Kdo narok nema, dostane
    # odmitnuti - i kdyz adresu zna. Tim se zaroven zavira sdileni:
    # ucastnik muze odkaz poslat dal, ale cizimu cloveku se video
    # neprehraje.
    #
    # Ktery soubor patri kteremu dni, drzi systemovy parametr
    # honzahauzr_crm.vyzva_soubor_<den>. Nastavuje ho tlacitko
    # v editoru, rucne se do nej nesaha.

    @staticmethod
    def _hh_parametr_souboru(den):
        return 'honzahauzr_crm.vyzva_soubor_%s' % den

    @staticmethod
    def _hh_je_spravce():
        """Kdo web upravuje, vidi vsechny dny.

        Jinak by si Honza k dnum 2 a 3 nemel jak video vlozit - ani
        zkontrolovat, ze se nahralo to spravne.
        """
        return request.env.user.has_group(
            'website.group_website_restricted_editor')

    @http.route(CIL + '/video/<int:den>', type='http', auth='public',
                website=True, sitemap=False)
    def video(self, den, k=None, **kw):
        if den not in (1, 2, 3):
            return request.not_found()

        if not self._hh_je_spravce():
            lead = request.env['crm.lead']._hh_vyzva_ucastnik(k or None)
            if not lead:
                return request.not_found()
            stav = {d['cislo']: d for d in lead.hh_vyzva_stav()}
            if not (stav.get(den) or {}).get('odemceno'):
                return request.not_found()

        param = request.env['ir.config_parameter'].sudo()
        try:
            priloha_id = int(param.get_param(self._hh_parametr_souboru(den), 0))
        except (TypeError, ValueError):
            priloha_id = 0
        if not priloha_id:
            return request.not_found()

        priloha = request.env['ir.attachment'].sudo().browse(priloha_id)
        if not priloha.exists():
            return request.not_found()

        # conditional=True zapina castecne pozadavky. Bez nich by
        # prehravac musel pokazde stahnout cely soubor od zacatku
        # a preskakovani v case by nefungovalo.
        return request.env['ir.binary']._get_stream_from(
            priloha, 'raw').get_response(
                as_attachment=False, conditional=True,
                content_security_policy=None)
