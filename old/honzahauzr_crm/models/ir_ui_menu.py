import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Kam ktera nabidka patri. Klic i hodnota jsou nazvy zaznamu
# (xmlid) bez nazvu modulu - vsechny jsou nase.
#
# Stejne rozlozeni popisuje views/menu.xml. Tady stoji podruhe
# kvuli databazim, kde uz modul bezel: cast nabidek ma v
# ir.model.data priznak noupdate a novy rodic z XML by se na ne
# neuplatnil.
KAM_PATRI = {
    'hh_termin_menu': 'menu_hh_admin',
    'menu_hh_maily': 'menu_hh_admin',
    'menu_hh_vykazy': 'menu_hh_admin',
    'menu_hh_nastaveni': 'menu_hh_admin',

    'hh_termin_menu_kalendar': 'hh_termin_menu',
    'hh_termin_menu_rezervace': 'hh_termin_menu',

    'menu_hh_mail_sablona': 'menu_hh_maily',
    'menu_hh_mail_stitek': 'menu_hh_maily',

    'menu_hh_vyzva_sledovani': 'menu_hh_vykazy',
    'menu_hh_zdroje': 'menu_hh_vykazy',
    'menu_hh_web_klik': 'menu_hh_vykazy',

    'menu_stupne_crm': 'menu_hh_nastaveni',
    'menu_hh_nastaveni_crm': 'menu_hh_nastaveni',
}

# Korenova nabidka z davno vraceneho pokusu o vlastni administraci
# (commit 598de3c, vraceno v f2c508b). Zaznam v databazi prezil,
# protoze mel noupdate, a od te doby v nabidce aplikaci visi
# dlazdice "Honza Hauzr", ktera vede na akci, ktera uz neexistuje.
ZBYTEK_PO_POKUSU = 'menu_hh_admin_root'


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _hh_nase(self, nazev):
        """Nabidka podle nazvu zaznamu, nebo prazdna sada."""
        return self.env.ref('honzahauzr_crm.' + nazev, raise_if_not_found=False)

    @api.model
    def _hh_prestehovat_do_admina(self):
        """Dorovna rodice nabidek podle KAM_PATRI.

        Pousti se z data/presun_menu.xml pri kazde aktualizaci. Co uz
        sedi, nechava byt - takze kdyz si Honza nekdy neco presune
        rucne, vrati se to na misto, ale nic se nerozbije.
        """
        for nazev, rodic_nazev in KAM_PATRI.items():
            nabidka = self._hh_nase(nazev)
            rodic = self._hh_nase(rodic_nazev)
            if not nabidka or not rodic or nabidka.parent_id == rodic:
                continue
            nabidka.parent_id = rodic
            _logger.info('Nabidka %s presunuta pod %s.', nazev, rodic_nazev)

        # Priznak noupdate pryc, at se pristi zmena rozlozeni da
        # udelat uz jen v XML a tahle funkce nemusi rust.
        zaznamy = self.env['ir.model.data'].search([
            ('module', '=', 'honzahauzr_crm'),
            ('model', '=', 'ir.ui.menu'),
            ('name', 'in', list(KAM_PATRI)),
            ('noupdate', '=', True),
        ])
        if zaznamy:
            zaznamy.noupdate = False

        self._hh_uklidit_zbytek()

    def _hh_uklidit_zbytek(self):
        zbytek = self._hh_nase(ZBYTEK_PO_POKUSU)
        if not zbytek:
            return
        _logger.info('Mazu zbylou dlazdici "%s" po vracene administraci.',
                     zbytek.name)
        zbytek.unlink()
