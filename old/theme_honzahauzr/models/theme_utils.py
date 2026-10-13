import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ThemeUtils(models.AbstractModel):
    _inherit = "theme.utils"

    def _theme_honzahauzr_post_copy(self, mod):
        """Vypne demo prvky, ktere Odoo dava do hlavicky.

        Bez tohohle se v liste objevi telefon +1 555-555-5556, lupa,
        Prihlasit se a tlacitko Kontaktujte nas. Nic z toho na webu
        nema byt - v hlavicce ma byt jen logo a polozky menu.

        Odoo hleda metodu podle nazvu modulu (_post_copy v theme.utils
        sestavi '_%s_post_copy' % mod.name a zavola ji, kdyz existuje).
        Zadna rodicovska metoda tedy neexistuje a super() by spadlo.
        """
        for pohled in (
            "website.header_text_element",        # demo telefon
            "website.header_call_to_action",      # tlacitko Kontaktujte nas
            "website.header_search_box",          # lupa
            "portal.user_sign_in",                # Prihlasit se
            # Vychozi demo paticka Odoo - Uzitecne odkazy, O nas,
            # telefon +1 555-555-5556 a info@yourcompany.example.com.
            # Nasi paticku vklada theme_honzahauzr.hh_layout_paticka,
            # takze tahle by se pod ni jen zdvojila.
            "website.footer_custom",
        ):
            self.disable_view(pohled)

        self._hh_smazat_dvojniky_assetu()

    def _hh_smazat_dvojniky_assetu(self):
        """Uklidí dvojníky, které po sobě nechá kopírování tématu.

        Z theme.ir.asset vzniká při každé aktualizaci nový ir.asset,
        aniž by Odoo poznalo, že tam stejný záznam už je. U šablon to
        jen mate, u assetů to web **shodí**: záznam s direktivou
        "remove" odebere soubor ze svazku, druhý stejný už nemá co
        odebrat a stránka vrátí 500

            ValueError: File(s) [...] not found in bundle
            web.assets_frontend_lazy

        Dělo se to po každém upgradu tématu a muselo se to uklízet
        ručně, než na to někdo přišel. Běží tedy rovnou tady, hned po
        kopírování.

        Z každé skupiny stejných záznamů zůstane jeden, přednost má
        ten bez vazby na konkrétní web - platí pro obě domény.
        """
        Asset = self.env["ir.asset"].sudo().with_context(active_test=False)
        vsechny = Asset.search([("path", "like", "theme_honzahauzr%")])

        skupiny = {}
        for a in vsechny:
            klic = (a.name, a.bundle, a.path or "", a.directive,
                    a.target or "", a.sequence)
            skupiny.setdefault(klic, []).append(a)

        smazano = 0
        for zaznamy in skupiny.values():
            if len(zaznamy) < 2:
                continue
            zaznamy.sort(key=lambda a: (bool(a.website_id), a.id))
            for a in zaznamy[1:]:
                a.unlink()
                smazano += 1

        if smazano:
            _logger.info(
                "Honza Hauzr: po kopirovani tematu smazano %s dvojniku "
                "v ir.asset.", smazano)
        return smazano
