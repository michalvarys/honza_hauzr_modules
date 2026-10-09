# -*- coding: utf-8 -*-
"""Vyriznuti zamcenych videi z hotove stranky.

Dny tridenni vyzvy jsou bezne editovatelne bloky - video se do nich
vklada v editoru jako kdekoliv jinde, vcetne souboru nahraneho primo
na web. Video je tim padem ulozene ve strance, tedy i u dnu, ktere
jeste nejsou odemcene.

Aby zamek nebyl jen na oko, vyrizne se obsah zamcenych dnu az tady,
z uz vykreslene odpovedi, tesne nez odejde do prohlizece. Do zdrojoveho
kodu stranky se tak zamcene video vubec nedostane a nejde ho pustit
drive - ani zobrazenim zdroje, ani ze site.

Proc az na odpovedi a ne v sablone: jakmile Odoo najde v sekci
dynamicke QWeb direktivy, vyradi ji z editovatelneho stromu a prestane
jit oznacit, presunout i smazat. Presne to se u teto stranky drive
delo.
"""
import logging

from lxml import html

from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Znacka, kterou nese obal videa v kazdem dni.
ZNACKA = 'data-hhd-video'

ZAMEK_IKONA = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"'
    ' stroke="currentColor" stroke-width="1.8" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<rect x="4" y="10.5" width="16" height="10" rx="2"/>'
    '<path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/></svg>'
)


# Adresy administrace. Nepatri sem /web/assets, /web/image ani
# /web/content - z tech zije i verejny web a odstrihnout je by
# znamenalo stranku bez stylu a obrazku. Prihlaseni (/web/login)
# zustava taky: bez nej by na druhe domene neslo otevrit editor
# a obsah by se tam nedal upravovat.
ADRESY_ADMINU = ('/odoo', '/web/dashboard')


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls, endpoint):
        odbocka = cls._hh_admin_patri_jinam()
        if odbocka is not None:
            return odbocka
        return super()._dispatch(endpoint)

    @classmethod
    def _hh_admin_patri_jinam(cls):
        """Na webu bez administrace posle zpatky tam, kam patri.

        Weby bezi z jedne databaze a nastenka je spolecna, takze
        administrace na druhe domene by byla tatáž administrace na
        druhe adrese - jen by se v tom clovek ztratil.
        """
        try:
            # Web se hleda podle domeny, ne pres request.website:
            # u adres administrace zadny "aktualni web" neni, takze
            # by odbocka nikdy nenaskocila.
            web = cls._hh_web_podle_domeny()
            if not web or not web.hh_admin_jinde:
                return None

            cesta = request.httprequest.path
            if not (cesta == '/web'
                    or any(cesta == a or cesta.startswith(a + '/')
                           for a in ADRESY_ADMINU)):
                return None

            domu = web.hh_web_s_adminem()
            if not domu or not domu.domain:
                return None

            cil = domu.domain.rstrip('/') + cesta
            if request.httprequest.query_string:
                cil += '?' + request.httprequest.query_string.decode()
            return request.redirect(cil, code=302, local=False)
        except Exception:
            # Odbocka nesmi nikdy shodit samotnou stranku.
            _logger.exception(
                'Honza Hauzr CRM: presmerovani administrace selhalo.')
            return None

    @classmethod
    def _hh_web_podle_domeny(cls):
        """Web podle adresy, na kterou prohlizec klepl."""
        hostitel = (request.httprequest.host or '').split(':')[0].lower()
        if not hostitel:
            return None
        for web in request.env['website'].sudo().search([]):
            if web.domain and hostitel in web.domain.lower():
                return web
        return None

    @classmethod
    def _post_dispatch(cls, response):
        try:
            cls._hh_vyrizni_zamcena_videa(response)
        except Exception:
            # Uprava odpovedi nesmi nikdy shodit stranku. Kdyz se
            # nepovede, radeji se nevyrizne nic - to je videt hned,
            # zatimco rozbita stranka by mohla projit bez povsimnuti.
            _logger.exception(
                'Honza Hauzr: zamcena videa se nepodarilo vyriznout.')
        try:
            cls._hh_vloz_prepinac_nahledu(response)
        except Exception:
            _logger.exception(
                'Honza Hauzr: prepinac nahledu se nepodarilo vlozit.')
        return super()._post_dispatch(response)

    @classmethod
    def _hh_vyrizni_zamcena_videa(cls, response):
        if not request or not response:
            return

        # Levny odfiltrovani drtive vetsiny pozadavku - znacku nese
        # jen stranka s vyzvou.
        # Stream (soubor, obrazek, svazek stylu) nema telo v pameti
        # a sahnuti na response.data u nej vyhodi vyjimku. Takovych
        # odpovedi chodi drtiva vetsina - stranka s vyzvou je HTML.
        if getattr(response, 'direct_passthrough', False):
            return
        if 'html' not in (response.headers.get('Content-Type') or ''):
            return

        data = getattr(response, 'data', None)
        if not data or ZNACKA.encode() not in data:
            return

        # Kdo web upravuje, musi videt vsechny tri dny - jinak by si
        # k dnum 2 a 3 nemel jak video vlozit. Zamek se proto tyka jen
        # navstevniku.
        if request.env.user.has_group(
                'website.group_website_restricted_editor'):
            return

        # Nahled "odemceno" necha videa ve strance, at je videt, jak
        # vypada hotova vyzva. Protejsek "zamceno" se tu neresi - ten
        # uz zaridilo rozpoznani ucastnika, ktere nikoho nevrati,
        # a bez ucastnika se vyrizne vsechno.
        if request.env['crm.lead']._hh_nahled() == 'odemceno':
            return

        lead = request.env['crm.lead']._hh_vyzva_ucastnik()
        stav = {d['cislo']: d for d in lead.hh_vyzva_stav()} if lead else {}

        strom = html.fromstring(data.decode('utf-8'))
        obaly = strom.xpath('//*[@%s]' % ZNACKA)
        if not obaly:
            return

        zmeneno = False
        for obal in obaly:
            try:
                cislo = int(obal.get(ZNACKA))
            except (TypeError, ValueError):
                continue

            den = stav.get(cislo)
            if den and den.get('odemceno'):
                continue

            # Zamceno (nebo ucastnika vubec nezname) - obsah pryc
            # a misto nej zamek s odpoctem.
            for dite in list(obal):
                obal.remove(dite)
            obal.text = None
            obal.append(html.fragment_fromstring(
                cls._hh_zamek_html(den)))
            zmeneno = True

        if zmeneno:
            response.data = html.tostring(
                strom, encoding='utf-8', doctype='<!DOCTYPE html>')

    @classmethod
    def _hh_zamek_html(cls, den):
        if not den:
            popis = 'Zamčeno'
            kdy = ''
        else:
            hodin = den.get('zbyva_hodin') or 0
            if hodin == 1:
                popis = 'Odemkne se za 1 hodinu'
            elif hodin < 5:
                popis = 'Odemkne se za %s hodiny' % hodin
            else:
                popis = 'Odemkne se za %s hodin' % hodin
            kdy = den.get('odemkne_se') or ''

        return (
            '<div class="hhd-zamek" data-odemkne-se="%s">'
            '<div class="hhd-zamek__ikona">%s</div>'
            '<p class="hhd-zamek__text">%s</p>'
            '<p class="hhd-micro">Dám ti vědět e-mailem, jakmile bude '
            'připravený.</p>'
            '</div>' % (kdy, ZAMEK_IKONA, popis)
        )

    # ------------------------------------------------------------------
    # prepinac nahledu
    # ------------------------------------------------------------------

    @classmethod
    def _hh_vloz_prepinac_nahledu(cls, response):
        """Prida na stranku vyzvy prepinac mezi zamcenou a odemcenou
        podobou.

        Vklada se az sem, do hotove odpovedi, a ne do sablony stranky.
        Obsah stranky je ulozeny v databazi, takze pridani do sablony
        by se na uz zalozenych strankach neprojevilo - a hlavne by
        prepinac zustal v obsahu i potom, co ho nekdo vypne.

        Zobrazuje se jen pri zapnutem systemovem parametru
        honzahauzr_crm.nahled_vyzvy. Na ostrem webu parametr nebude,
        takze stranka zustane bez nej.
        """
        if not request or not response:
            return
        if getattr(response, 'direct_passthrough', False):
            return
        if 'html' not in (response.headers.get('Content-Type') or ''):
            return

        data = getattr(response, 'data', None)
        if not data or ZNACKA.encode() not in data:
            return

        Lead = request.env['crm.lead'].sudo()
        if not Lead._hh_nahled_povolen():
            return

        strom = html.fromstring(data.decode('utf-8'))
        telo = strom.find('body')
        if telo is None:
            return

        # Dokud si clovek nevybere, zvyrazni se "Pred registraci" - za
        # predpokladu, ze stranka nikoho nepozna, coz je presne ten
        # stav, ktery prave vidi. Kdyz ucastnika pozna, je to stav
        # "po registraci".
        volba = Lead._hh_nahled()
        if not volba:
            volba = 'odpocet' if Lead._hh_vyzva_ucastnik() else 'zamceno'

        telo.append(html.fragment_fromstring(cls._hh_prepinac_html(volba)))
        response.data = html.tostring(
            strom, encoding='utf-8', doctype='<!DOCTYPE html>')

    @classmethod
    def _hh_prepinac_html(cls, volba):
        cil = '/zpet-do-zivota/vyzva/nahled?strana=%s'
        tlacitka = []
        for strana, popisek in (('zamceno', 'Před registrací'),
                                ('odpocet', 'Po registraci'),
                                ('odemceno', 'Vše odemčené')):
            tridy = 'hhd-nahled__tl'
            if volba == strana:
                tridy += ' hhd-nahled__tl--aktivni'
            tlacitka.append(
                '<a class="%s" href="%s">%s</a>' % (
                    tridy, cil % strana, popisek))

        return (
            '<div class="hhd-nahled" role="group" aria-label="Náhled stránky">'
            '<span class="hhd-nahled__popis">Náhled</span>'
            '<div class="hhd-nahled__tlacitka">%s</div>'
            '<span class="hhd-nahled__pozn">Jen pro kontrolu — na ostrém '
            'webu tenhle přepínač nebude.</span>'
            '</div>' % ''.join(tlacitka)
        )
