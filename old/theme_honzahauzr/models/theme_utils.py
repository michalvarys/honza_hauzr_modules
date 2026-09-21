from odoo import models


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
        ):
            self.disable_view(pohled)
