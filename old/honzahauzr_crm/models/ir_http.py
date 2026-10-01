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


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

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
