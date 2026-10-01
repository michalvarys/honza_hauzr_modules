# -*- coding: utf-8 -*-
"""Nahravani videa po kouscich.

Odoo nahrava soubor jednim pozadavkem: cele video zakodovane do
base64 v jednom JSON. Na mistnim stroji to funguje, na ostrem webu
ne - pred Odoo stoji WAF, ktery pozadavek nad zhruba pul megabajtu
utne a vrati HTML chybovou stranku. Odoo misto odpovedi dostane
necekany text, upload tise skonci a clovek v editoru jen kouka, proc
se nic nedeje. Pres Cloudflare navic vede strop 100 MB na pozadavek.

Tenhle controller to obchazi tim, ze video prijima po kouscich.
Kazdy kousek je dost maly, aby prosel, takze na zadny z tech stropu
nenarazi - ani na ten Cloudflare, protoze velky pozadavek uz zadny
neni. Kousky se skladaji do docasneho souboru a teprve z hotoveho
celku vznikne priloha.

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

_logger = logging.getLogger(__name__)

# Nad timhle uz WAF pozadavek utina. Merenim proslo 300 kB souboru,
# 600 kB uz ne; 200 kB necha pohodlnou rezervu i po zakodovani do
# base64, ktere objem zvedne o tretinu.
KOUSEK = 200 * 1024

# Strop pro cele video. Stejny jako web.max_file_upload_size, ktery
# nastavuje honzahauzr_crm - tady se hlida znovu, protoze tudy
# pozadavek Odoo kontrolu velikosti vubec neprochazi.
STROP = 512 * 1024 * 1024

POVOLENE_TYPY = {
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

    def _slozka(self):
        """Docasna slozka davky, jedna na prihlaseni.

        Lezi pod data_dir, aby po sobe neco nezustavalo v /tmp a aby
        to slo pri uklidu najit.
        """
        zaklad = os.path.join(
            config.filestore(request.env.cr.dbname), 'hh_nahravani')
        # Klic sezeni je dost dlouhy a nahodny; bere se z nej jen cast,
        # aby se cely netocil po disku.
        otisk = re.sub(r'[^A-Za-z0-9]', '', request.session.sid or '')[:24]
        return os.path.join(zaklad, otisk or 'bez-sezeni')

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
    def kousek(self, nazev=None, poradi=0, celkem=0, data=None, **kw):
        """Prijme jeden kousek videa a pripise ho do docasneho souboru.

        Kousky chodi popore. Prvni (poradi 0) zalozi soubor, kazdy
        dalsi se pripise na konec. Hotovo se nehlasi tady - az
        /hh/nahravani/dokonci.
        """
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}

        pripona = self._pripona(nazev)
        if pripona not in POVOLENE_TYPY:
            return {'chyba': 'Tenhle typ souboru nejde nahrát. '
                             'Povolené jsou: %s.'
                             % ', '.join(sorted(POVOLENE_TYPY))}

        try:
            syrove = base64.b64decode(data or '', validate=True)
        except Exception:
            return {'chyba': 'Kousek souboru dorazil poškozený.'}

        slozka = self._slozka()
        os.makedirs(slozka, exist_ok=True)
        cesta = os.path.join(slozka, self._bezpecny_nazev(nazev))

        # Prvni kousek zacina od nuly - kdyby se predchozi pokus
        # nedokoncil, zbytek po nem by se jinak pripsal dopredu.
        rezim = 'wb' if int(poradi or 0) == 0 else 'ab'
        if rezim == 'ab' and not os.path.exists(cesta):
            return {'chyba': 'Rozdělané nahrávání se ztratilo, '
                             'zkus to prosím znovu.'}

        if os.path.exists(cesta) and rezim == 'ab':
            if os.path.getsize(cesta) + len(syrove) > STROP:
                self._zahod(cesta)
                return {'chyba': 'Video je větší než povolených 512 MB.'}

        with open(cesta, rezim) as soubor:
            soubor.write(syrove)

        return {'ok': True, 'prijato': os.path.getsize(cesta)}

    @http.route('/hh/nahravani/dokonci', type='json', auth='user',
                methods=['POST'], website=True)
    def dokonci(self, nazev=None, **kw):
        """Z hotoveho docasneho souboru udela prilohu a vrati adresu.

        Priloha musi byt verejna, jinak by ji navstevnik webu nestahl.
        """
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}

        pripona = self._pripona(nazev)
        if pripona not in POVOLENE_TYPY:
            return {'chyba': 'Tenhle typ souboru nejde nahrát.'}

        cesta = os.path.join(self._slozka(), self._bezpecny_nazev(nazev))
        if not os.path.exists(cesta):
            return {'chyba': 'Nahrané video se nenašlo, zkus to znovu.'}

        try:
            with open(cesta, 'rb') as soubor:
                obsah = soubor.read()
            priloha = request.env['ir.attachment'].create({
                'name': os.path.basename(cesta),
                'raw': obsah,
                'mimetype': POVOLENE_TYPY[pripona],
                'public': True,
                'res_model': 'ir.ui.view',
            })
        finally:
            self._zahod(cesta)

        return {
            'ok': True,
            'adresa': '/web/content/%s?unique=%s' % (
                priloha.id, priloha.checksum),
            'nazev': priloha.name,
        }

    @http.route('/hh/nahravani/zrus', type='json', auth='user',
                methods=['POST'], website=True)
    def zrus(self, nazev=None, **kw):
        """Uklidi rozdelanou davku, kdyz nahravani nekdo prerusi."""
        if not self._smi_nahravat():
            return {'chyba': 'Na tohle nemáš oprávnění.'}
        self._zahod(os.path.join(
            self._slozka(), self._bezpecny_nazev(nazev)))
        return {'ok': True}

    # ------------------------------------------------------------------
    # uklid
    # ------------------------------------------------------------------

    def _zahod(self, cesta):
        try:
            if os.path.exists(cesta):
                os.remove(cesta)
            slozka = os.path.dirname(cesta)
            if os.path.isdir(slozka) and not os.listdir(slozka):
                shutil.rmtree(slozka, ignore_errors=True)
        except OSError:
            _logger.warning('Nepodarilo se uklidit %s', cesta, exc_info=True)
