import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Kam ktera nabidka patri a v jakem poradi. Klic je nazev zaznamu
# (xmlid) bez nazvu modulu - vsechny jsou nase.
#
# Stejne rozlozeni popisuje views/menu.xml. Tady stoji podruhe
# kvuli databazim, kde uz modul bezel: cast nabidek ma v
# ir.model.data priznak noupdate a rodic ani poradi z XML by se na
# ne neuplatnily.
KAM_PATRI = {
    'menu_hh_nastenka': ('menu_hh_admin', 5),
    'hh_termin_menu': ('menu_hh_admin', 10),
    'menu_hh_vykazy': ('menu_hh_admin', 30),
    'menu_hh_nastaveni': ('menu_hh_admin', 40),

    'hh_termin_menu_kalendar': ('hh_termin_menu', 10),
    'hh_termin_menu_rezervace': ('hh_termin_menu', 20),

    'menu_hh_vyzva_sledovani': ('menu_hh_vykazy', 10),
    'menu_hh_zdroje': ('menu_hh_vykazy', 20),
    'menu_hh_web_klik': ('menu_hh_vykazy', 30),

    'menu_stupne_crm': ('menu_hh_nastaveni', 10),
    'menu_hh_mail_sablona': ('menu_hh_nastaveni', 20),
    'menu_hh_mail_stitek': ('menu_hh_nastaveni', 30),
}

# Nabidky z kratkeho mezikroku, kdy e-maily mely vlastni sekci a
# v Nastaveni byla zkratka na nastaveni CRM. Honza chtel rozlozeni
# presne takove, jake bylo v CRM, takze obe pryc.
ZRUSENE = ['menu_hh_maily', 'menu_hh_nastaveni_crm']

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
        """Dorovna nabidky podle KAM_PATRI.

        Pousti se z data/presun_menu.xml pri kazde aktualizaci. Co uz
        sedi, nechava byt - na ciste databazi tedy neudela nic,
        protoze rozlozeni uz prislo z XML.
        """
        for nazev, (rodic_nazev, poradi) in KAM_PATRI.items():
            nabidka = self._hh_nase(nazev)
            rodic = self._hh_nase(rodic_nazev)
            if not nabidka or not rodic:
                continue
            zmeny = {}
            if nabidka.parent_id != rodic:
                zmeny['parent_id'] = rodic.id
            if nabidka.sequence != poradi:
                zmeny['sequence'] = poradi
            if zmeny:
                nabidka.write(zmeny)
                _logger.info('Nabidka %s srovnana: %s', nazev, zmeny)

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
        """Smaze nabidky, ktere uz v rozlozeni nemaji co delat.

        Odstraneni polozky z XML ji z databaze samo nesmaze, takze
        by v nabidce visela dal - prazdna, nebo s akci, ktera uz
        nikam nevede.
        """
        pryc = [ZBYTEK_PO_POKUSU] + ZRUSENE
        for nazev in pryc:
            nabidka = self._hh_nase(nazev)
            if not nabidka:
                continue
            if nabidka.child_id:
                # Pojistka: mazani nabidky vezme s sebou i to, co pod
                # ni visi. Deti uz mely byt prestehovane o kus vys,
                # a kdyz nejsou, je lepsi nechat nabidku byt nez
                # nekam zahodit polozku, na kterou se kliká.
                _logger.warning(
                    'Nabidku "%s" nemazu, porad pod ni neco visi: %s',
                    nabidka.name, nabidka.child_id.mapped('name'))
                continue
            _logger.info('Mazu nabidku "%s" (%s).', nabidka.name, nazev)
            nabidka.unlink()
