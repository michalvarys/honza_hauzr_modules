# -*- coding: utf-8 -*-
"""Nahravani videa po kouscich.

Odoo nahrava soubor jednim pozadavkem: cele video zakodovane do
base64 v jednom JSON. Na ostrem webu to neprojde - pred Odoo stoji
WAF, ktery pozadavek nad zhruba 400 kB utne a vrati HTML chybovou
stranku. Odoo misto odpovedi dostane necekany text, upload tise
skonci a v editoru to vypada, ze tlacitko nereaguje. Pres
Cloudflare navic vede strop 100 MB na pozadavek.

Video se proto kraji na kousky, ktere pod ten strop pohodlne
spadnou. Kazdy kousek se uklada zvlast pod svym poradim a teprve
na konci se z nich slozi priloha.

Proc zvlast a ne rovnou za sebe: kousky tak mohou chodit soucasne
a nemusi se cekat, nez dojde ten predchozi. U videa na 260 MB to
je rozdil mezi sedmnacti minutami a necelymi tremi - rezie
jednoho pozadavku (zhruba 0,7 s) prevazuje nad prenosem samotnych
dat, takze se vyplati poslat jich vic najednou.

Nahrava jen clovek, ktery smi upravovat web. Docasne soubory lezi
pod data_dir a jsou svazane s prihlasenim, takze se do rozdelane
davky nikdo jiny nemuze pripojit.
"""
import base64
import logging
import os
import re
import shutil

from odoo import http
from odoo.http import request
from odoo.tools import config

from . import faststart

_logger = logging.getLogger(__name__)

# Merenim na ostrem webu: 360 kB jeste projde, 420 kB uz WAF utne.
# 300 kB necha rezervu i potom, co base64 objem zvedne o tretinu.
KOUSEK = 300 * 1024

# Strop pro cele video. Stejny jako web.max_file_upload_size, ktery
# nastavuje honzahauzr_crm - tady se hlida znovu, protoze tudy
# pozadavek Odoo kontrolu velikosti vubec neprochazi.
STROP = 512 * 1024 * 1024

POVOLENE_TYPY = {
    # Titulky k videu. Jsou male, projdou v jednom kousku.
    'vtt': 'text/vtt',
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mov': 'video/quicktime',
    'm4v': 'video/x-m4v',
    'ogv': 'video/ogg',
}


class HhNahravani(http.Controller):

    # ------------------------------------------------------------------
    # pomocne
    # ------------------------------------------------------------------

    def _smi_nahravat(self):
        return request.env.user.has_group(
            'website.group_website_restricted_editor')

    def _slozka(self, davka):
        """Slozka jedne rozdelane davky.

        Lezi pod data_dir, aby po sobe neco nezustavalo v /tmp a aby
        to slo pri uklidu najit.

        Nazev davky si vymysli prohlizec a posila ho s kazdym
        kouskem. Driv se odvozoval z prihlaseni, jenze to se behem
        dlouheho nahravani obnovuje ("Session expired" v logu)
        a kousky pak padaly do jine slozky - z 953 jich doslo 371
        a zbytek se ztratil. Cislo uzivatele je v ceste proto, aby
        si dva lide nemohli lezt do stejne davky.
        """
        otisk = re.sub(r'[^A-Za-z0-9-]', '', str(davka or ''))[:40]
        return os.path.join(
            config.filestore(request.env.cr.dbname),
            'hh_nahravani',
            '%s-%s' % (request.env.uid, otisk or 'bez-nazvu'),
        )

    def _pripona(self, nazev):
        kus = (nazev or '').rsplit('.', 1)
        return kus[1].lower() if len(kus) == 2 else ''

    def _bezpecny_nazev(self, nazev):
        """Z nazvu od uzivatele udela neco, co jde bezpecne ulozit.

        Lomitka a tecky by jinak umoznily vylezt ze slozky ven.
        """
        nazev = os.path.basename(nazev or '')
        nazev = re.sub(r'[^A-Za-z0-9._-]', '_', nazev)
        nazev = nazev.lstrip('.') or 'video'
        return nazev[:120]

    # ------------------------------------------------------------------
    # verejne body
    # ------------------------------------------------------------------

    @http.route('/hh/nahravani/kousek', type='json', auth='user',
                methods=['POST'], website=True)
    def kousek(self, nazev=None, davka=None, poradi=0, celkem=0, data=None, **kw):
        """Ulozi jeden kousek videa pod jeho poradim.

        Kousky mohou chodit v libovolnem poradi i soucasne - kazdy
        ma vlastni soubor a sklada se az v /hh/nahravani/dokonci.
        """
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}

        if self._pripona(nazev) not in POVOLENE_TYPY:
            return {'chyba': 'Tenhle typ souboru nejde nahrát. '
                             'Povolené jsou: %s.'
                             % ', '.join(sorted(POVOLENE_TYPY))}

        try:
            poradi = int(poradi)
            celkem = int(celkem)
        except (TypeError, ValueError):
            return {'chyba': 'Pořadí kousku dorazilo poškozené.'}

        if poradi < 0 or celkem <= 0 or poradi >= celkem:
            return {'chyba': 'Pořadí kousku je mimo rozsah.'}

        if celkem * KOUSEK > STROP:
            return {'chyba': 'Video je větší než povolených 512 MB.'}

        try:
            syrove = base64.b64decode(data or '', validate=True)
        except Exception:
            return {'chyba': 'Kousek souboru dorazil poškozený.'}

        slozka = self._slozka(davka)
        os.makedirs(slozka, exist_ok=True)

        # Zapis pres docasny nazev a prejmenovani: kdyby spojeni
        # vypadlo uprostred, nezustane po nem napul zapsany kousek,
        # ktery by se tvaril jako hotovy.
        cil = os.path.join(slozka, str(poradi))
        rozdelany = cil + '.pul'
        with open(rozdelany, 'wb') as soubor:
            soubor.write(syrove)
        os.replace(rozdelany, cil)

        # Vraci se poradi a skutecne zapsana velikost, aby prohlizec
        # poznal ztraceny kousek hned, ne az na konci pri skladani.
        return {'ok': True, 'poradi': poradi, 'bajtu': len(syrove)}

    @http.route('/hh/nahravani/dokonci', type='json', auth='user',
                methods=['POST'], website=True)
    def dokonci(self, nazev=None, davka=None, celkem=0, **kw):
        """Slozi kousky dohromady a udela z nich prilohu.

        Priloha musi byt verejna, jinak by ji navstevnik webu
        nestahl.
        """
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}

        pripona = self._pripona(nazev)
        if pripona not in POVOLENE_TYPY:
            return {'chyba': 'Tenhle typ souboru nejde nahrát.'}

        try:
            celkem = int(celkem)
        except (TypeError, ValueError):
            celkem = 0
        if celkem <= 0:
            return {'chyba': 'Chybí počet kousků.'}

        slozka = self._slozka(davka)
        chybejici = [i for i in range(celkem)
                     if not os.path.exists(os.path.join(slozka, str(i)))]
        if chybejici:
            return {'chyba': 'Část videa se neuložila (%d z %d kousků '
                             'chybí). Zkus to prosím znovu.'
                             % (len(chybejici), celkem)}

        try:
            # Kousky se spojuji na disk, ne do pameti. U videa na
            # 300 MB by jinak server drzel ten objem dvakrat -
            # jednou slozeny soubor a jednou kopii pro prilohu.
            celek = os.path.join(slozka, '.celek')
            with open(celek, 'wb') as vystup:
                for i in range(celkem):
                    with open(os.path.join(slozka, str(i)), 'rb') as kus:
                        shutil.copyfileobj(kus, vystup, 4 * 1024 * 1024)

            if os.path.getsize(celek) > STROP:
                return {'chyba': 'Video je větší než povolených 512 MB.'}

            # Strihove programy zapisuji prehravaci hlavicku na konec
            # souboru. Prohlizec pak musi stahnout cele video, nez
            # vubec zacne hrat - u velkeho souboru to znamena, ze se
            # netoci nic a jen bezi kolecko. Tohle ji presune dopredu.
            if pripona in ('mp4', 'm4v', 'mov'):
                srovnany = celek + '.srovnany'
                try:
                    if faststart.prekopiruj_s_hlavickou_vepredu(celek, srovnany):
                        os.replace(srovnany, celek)
                    elif os.path.exists(srovnany):
                        os.remove(srovnany)
                except Exception:
                    # Kdyz se to nepovede, video se nahraje tak, jak
                    # prislo - radeji pomalejsi start nez zadne video.
                    _logger.warning('Nepodarilo se srovnat %s', nazev,
                                    exc_info=True)
                    if os.path.exists(srovnany):
                        os.remove(srovnany)

            with open(celek, 'rb') as hotovy:
                priloha = request.env['ir.attachment'].create({
                    'name': self._bezpecny_nazev(nazev),
                    'raw': hotovy.read(),
                    'mimetype': POVOLENE_TYPY[pripona],
                    'public': True,
                    'res_model': 'ir.ui.view',
                })
        finally:
            self._zahod(slozka)

        return {
            'ok': True,
            'adresa': '/web/content/%s?unique=%s' % (
                priloha.id, priloha.checksum),
            'nazev': priloha.name,
        }

    @http.route('/hh/nahravani/zrus', type='json', auth='user',
                methods=['POST'], website=True)
    def zrus(self, nazev=None, davka=None, **kw):
        """Uklidi rozdelanou davku, kdyz nahravani nekdo prerusi."""
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}
        self._zahod(self._slozka(davka))
        return {'ok': True}

    # ------------------------------------------------------------------
    # uklid
    # ------------------------------------------------------------------

    def _zahod(self, slozka):
        """Smaze slozku jedne davky.

        Spolecny koren hh_nahravani zustava - muze v nem prave bezet
        jine nahravani.
        """
        try:
            shutil.rmtree(slozka, ignore_errors=True)
        except OSError:
            _logger.warning('Nepodarilo se uklidit %s', slozka, exc_info=True)
