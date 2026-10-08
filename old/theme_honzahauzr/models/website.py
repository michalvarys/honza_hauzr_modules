# -*- coding: utf-8 -*-
"""Logo v liste - vlozene primo do stranky, ne stahovane zvlast.

Odoo posila logo jako samostatny obrazek. Lista se proto vykresli
prazdna a logo do ni doskoci, az obrazek dorazi po siti - pusobi to
jako bliknuti. Atribut loading="eager" to jen zrychli, cekani
neodstrani.

Logo se proto vklada rovnou do HTML jako data URI. Prijde se strankou
v jednom kuse, takze se vykresli spolu s listou a neblikne nic.

Zaroven se zmensuje. Nahrane logo je 720x394 a skoro 50 kB, zatimco
v liste je videt na 73x40 - vkladat do kazde stranky petinasobek toho,
co je potreba, nema smysl.

Zmenseni dela primo Pillow, ne image_process z Odoo. Odoo pri startu
zakaze Pillow donacitat dalsi formaty nez ty predpripravene a webp
mezi nimi neni, takze image_process logo odmitne. Import
WebPImagePlugin ten format zaregistruje zpatky.

Vysledek se drzi v pameti, aby se nepocital pri kazdem nacteni
stranky. Klicem je datum posledni zmeny webu, takze po vymene loga
se spocita znovu.
"""
import base64
import io
import logging

# WebPImagePlugin se importuje naschval. Odoo pri startu zavola
# Image.preinit() a nastavi Image._initialized = 2, cimz Pillow
# zakaze donacitat dalsi formaty. Webp mezi predpripravene nepatri,
# takze by ho Pillow uvnitr Odoo neotevrel - a logo je prave webp.
# Import modulu format zaregistruje bez ohledu na to nastaveni.
from PIL import Image
from PIL import WebPImagePlugin  # noqa: F401

from odoo import api, models, tools

_logger = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    # Dvojnasobek zobrazene velikosti, aby logo zustalo ostre i na
    # displejich s vyssi hustotou bodu.
    HH_LOGO_ROZMER = (190, 104)

    def hh_logo_vlozene(self):
        """Logo jako data URI pro vlozeni primo do sablony."""
        self.ensure_one()
        if not self.logo:
            return ''
        vlozene = self._hh_logo_uri(self.id, self.write_date)
        # Kdyz se zmenseni nepovede, logo se jen stahne postaru -
        # lepsi nez prazdne misto v liste.
        return vlozene or '/web/image/website/%s/logo' % self.id

    @api.model
    @tools.ormcache('id_webu', 'zmeneno')
    def _hh_logo_uri(self, id_webu, zmeneno):
        web = self.sudo().browse(id_webu)
        if not web.logo:
            return ''

        # Vektorove logo se nezmensuje. Zmensovani ma usetrit bajty
        # u fotografie; SVG je male uz samo a hlavne ho knihovna na
        # obrazky vubec neotevre - skoncila by vyjimkou pri kazdem
        # nacteni stranky. Pozna se podle zacatku souboru, protoze
        # pripona tu neni k dispozici.
        try:
            zacatek = base64.b64decode(web.logo)[:200].lstrip()
            if zacatek[:5] == b'<?xml' or zacatek[:4] == b'<svg':
                return ''
        except Exception:
            return ''

        try:
            obrazek = Image.open(io.BytesIO(base64.b64decode(web.logo)))
            obrazek.thumbnail(self.HH_LOGO_ROZMER, Image.LANCZOS)
            pamet = io.BytesIO()
            obrazek.save(pamet, format='WEBP', quality=88, method=6)
            return 'data:image/webp;base64,' + base64.b64encode(
                pamet.getvalue()).decode()
        except Exception:
            _logger.exception(
                'Honza Hauzr: logo se nepodarilo zmensit pro vlozeni.')
            return ''
