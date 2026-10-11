# -*- coding: utf-8 -*-
"""Patička, odhlášení a zádrže před odesláním.

Dvě vrstvy, které platí různě široko.

**Patička s odhlášením je v každém e-mailu, který jde zákazníkovi.**
Nejen u nabídek - i u zpráv ze tří dnů výzvy a u potvrzení hovoru.
Kdo nechce nic, musí mít možnost to zastavit v e-mailu, který zrovna
drží v ruce, a ne hledat, ve které zprávě ten odkaz byl. Jediné, kde
patička není, jsou upozornění pro Honzu - ta nejdou zákazníkovi.

Z odhlášení plyne **univerzální zádrž**: komu jsme přestali psát,
tomu nejde nic, ani provozní řada.

**Prodejní řada má zádrží víc.** Nabídka se nesmí poslat člověku,
který už si hovor domluvil nebo Honzovi osobně odepsal. Řada se
proto u štítku označí jako prodejní; některé zádrže ji ukončí
(odhlášení, domluvený hovor), jiné jen pozastaví (osobní odpověď,
zavřené rezervace). Jakmile důvod pomine, pokračuje se prvním
neodeslaným e-mailem - zameškané se nedoposílají, protože odesílač
si u každého člověka pamatuje, co už odešlo.
"""

import logging
import secrets

from markupsafe import Markup

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Patička a skrytý náhledový text se do zprávy vkládají až při
# odeslání, ne do textu v editoru. Honza tak nemá co omylem smazat
# a pod každou zprávou je identifikace odesílatele i odhlášení jistě.
PATICKA = (
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
    'width="100%%" style="background-color:#f4efe6;margin:0;padding:0;">'
    '<tr><td align="center" style="padding:0 10px 30px 10px;">'
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
    'width="100%%" style="width:100%%;max-width:600px;">'
    '<tr><td align="center" '
    'style="padding:16px 22px 0 22px;font-family:Helvetica,Arial,sans-serif;'
    'font-size:12px;line-height:1.7;color:#a89681;">'
    '%(odesilatel)s<br/>'
    'Tenhle e-mail ti přišel, protože %(duvod)s.<br/>'
    '<a href="%(odhlaseni)s" style="color:#8c8276;text-decoration:underline;">'
    'Nechceš ode mě další e-maily? Odhlas se.</a>'
    '</td></tr></table></td></tr></table>'
)

# Proc clovek zpravu dostal. Mel by to poznat i ten, kdo si uz
# nepamatuje, kde nam adresu nechal - jinak oznaci zpravu jako spam
# a poskodi tim dorucovani vsem ostatnim.
DUVOD_VYZVA = 'ses přihlásil do bezplatné výzvy Z autopilota zpět do života'
DUVOD_HOVOR = 'sis u mě domluvil úvodní hovor'

# Podle tohohle se pozná, jestli patička ve zprávě už je. Dvě
# podoby: v šabloně stojí zástupný text, v hotové zprávě už adresa.
ZNACKY_ODHLASENI = ('hh_odkaz_odhlaseni', 'maily/odhlasit')


def ma_odhlaseni(telo):
    return any(z in (telo or '') for z in ZNACKY_ODHLASENI)

# Schránky ukazují ve výpisu kus textu hned za předmětem. Když se
# nedoplní, vezmou si první slova ze zprávy - u nás popisek loga.
# Náhledový text je proto skrytý blok úplně na začátku, doplněný
# neviditelnými znaky, aby za něj schránka nenatáhla nic dalšího.
NAHLED = (
    '<div style="display:none;max-height:0;overflow:hidden;'
    'mso-hide:all;font-size:1px;line-height:1px;color:#ffffff;'
    'opacity:0;">%(text)s%(vypln)s</div>'
)
VYPLN = '&#847;&#160;' * 60


class CrmLeadProdejni(models.Model):
    _inherit = 'crm.lead'

    hh_serie_pozastavena = fields.Boolean(
        string='Pozastavit prodejní e-maily',
        copy=False,
        help='Zaškrtni, když ti člověk osobně odepsal a řešíš to s ním. '
             'Řada se zastaví a nic dalšího mu samo neodejde.\n\n'
             'Až to vyřídíš, odškrtni - pokračuje se prvním '
             'neodeslaným e-mailem, zameškané se nedoposílají.',
    )

    hh_odhlaseno = fields.Boolean(
        string='Odhlášen z e-mailů',
        copy=False,
        help='Nastaví se samo, když člověk klikne na odhlášení '
             'v patičce. Prodejní e-maily mu pak už nechodí.',
    )

    hh_odhlaseni_klic = fields.Char(
        string='Klíč pro odhlášení',
        copy=False,
        index=True,
        help='Náhodný řetězec v odkazu na odhlášení. Bez něj by '
             'stačilo hádat čísla a odhlásit cizího člověka.',
    )

    hh_odkaz_odhlaseni = fields.Char(
        string='Odkaz na odhlášení',
        compute='_compute_hh_odkaz_odhlaseni',
        help='Osobní odkaz, kterým se tenhle člověk odhlásí. '
             'V textu zprávy se píše jako '
             '{{ object.hh_odkaz_odhlaseni }}.',
    )
    hh_paticka_odesilatel = fields.Char(
        string='Odesílatel do patičky',
        compute='_compute_hh_paticka_odesilatel',
        help='Název firmy a adresa tak, jak se tisknou do patičky. '
             'V textu zprávy se píše jako '
             '{{ object.hh_paticka_odesilatel }}.',
    )

    def _compute_hh_odkaz_odhlaseni(self):
        for lead in self:
            lead.hh_odkaz_odhlaseni = lead._hh_odkaz_odhlaseni()

    def _compute_hh_paticka_odesilatel(self):
        for lead in self:
            nazev = (lead.company_id.name
                     or lead.env.company.name or 'Honza Hauzr')
            adresa = (lead.company_id.street or lead.env.company.street or '')
            lead.hh_paticka_odesilatel = (
                '%s · %s' % (nazev, adresa) if adresa else nazev)

    hh_odkaz_rezervace = fields.Char(
        string='Odkaz na rezervaci',
        compute='_compute_hh_odkaz_rezervace',
        help='Adresa, kam vedou tlačítka v prodejních e-mailech. '
             'V textu se píše jako {{ object.hh_odkaz_rezervace }}.',
    )

    ODKAZ_HOVORU = '/uvodni-hovor'

    @api.model
    def _hh_vychozi_odkaz_hovoru(self):
        """Nasměruje tlačítka na stránku s kalendářem, když nic není.

        Zapisuje jen do prázdného - co si Honza v nastavení zvolí,
        se nepřepisuje.
        """
        param = self.env['ir.config_parameter'].sudo()
        if (param.get_param('honzahauzr_crm.odkaz_rezervace') or '').strip():
            return False
        param.set_param('honzahauzr_crm.odkaz_rezervace', self.ODKAZ_HOVORU)
        return True

    def _compute_hh_odkaz_rezervace(self):
        param = self.env['ir.config_parameter'].sudo()
        nastaveny = (param.get_param('honzahauzr_crm.odkaz_rezervace') or '').strip()
        for lead in self:
            adresa = nastaveny or self.ODKAZ_HOVORU
            # Relativni adresu doplnime na uplnou. V e-mailu by sama
            # o sobe nikam nevedla - posta nema vuci cemu ji doplnit.
            if adresa.startswith('/'):
                adresa = lead._hh_zaklad_vyzvy().rstrip('/') + adresa
            lead.hh_odkaz_rezervace = adresa

    # ------------------------------------------------------------------
    # odhlaseni
    # ------------------------------------------------------------------

    def _hh_zajistit_odhlasovaci_klic(self):
        self.ensure_one()
        if not self.sudo().hh_odhlaseni_klic:
            self.sudo().hh_odhlaseni_klic = secrets.token_urlsafe(16)
        return self.sudo().hh_odhlaseni_klic

    def _hh_odkaz_odhlaseni(self):
        self.ensure_one()
        return '%s/maily/odhlasit/%s' % (
            self._hh_zaklad_vyzvy().rstrip('/'),
            self._hh_zajistit_odhlasovaci_klic())

    def _hh_paticka_emailu(self, duvod=None):
        """Patička pod každou zprávu, která jde zákazníkovi.

        Identifikace odesílatele, proč zprávu dostal, a odkaz na
        odhlášení. Skládá se až při odeslání, takže ji nejde omylem
        smazat v editoru ani zapomenout v nově psané zprávě.
        """
        self.ensure_one()

        nazev = (self.company_id.name
                 or self.env.company.name or 'Honza Hauzr')
        adresa = (self.company_id.street or self.env.company.street or '')
        odesilatel = (Markup('%s &#183; %s') % (nazev, adresa)
                      if adresa else Markup('%s') % nazev)

        return Markup(PATICKA) % {
            'odesilatel': odesilatel,
            'duvod': duvod or DUVOD_VYZVA,
            'odhlaseni': self._hh_odkaz_odhlaseni(),
        }

    # ------------------------------------------------------------------
    # zadrze pred odeslanim
    # ------------------------------------------------------------------

    def _hh_ma_hovor(self):
        """Domluvený hovor.

        Hledá se i tehdy, když karta ve sloupci zůstala - termín se
        dá zapsat ručně a na přesun sloupce se spoléhat nedá.
        """
        self.ensure_one()
        return bool(self.env['hh.termin'].sudo().search_count([
            ('lead_id', '=', self.id),
            ('stav', '=', 'rezervovany'),
        ]))

    @api.model
    def _hh_rezervace_otevrene(self):
        """Dá se vůbec hovor domluvit?

        Posílat nabídku s tlačítkem na zavřený kalendář je horší než
        neposlat nic - člověk klikne, nenajde termín a podruhé už
        neklikne.

        Nenastaveno znamená otevřeno. Jinak by se po nasazení
        přestalo posílat, aniž by o tom kdokoli věděl.
        """
        hodnota = self.env['ir.config_parameter'].sudo().get_param(
            'honzahauzr_crm.rezervace_otevrene')
        if hodnota in (None, False, ''):
            return True
        return str(hodnota).strip().lower() not in ('false', '0', 'off')

    def _hh_zadrz_emailu(self):
        """Platí pro každou zprávu: komu jsme přestali psát, tomu nepíšeme.

        Netýká se jen nabídek. Kdo klikne na odhlášení ve zprávě ze
        třídenní výzvy, nechce další díly - poslat mu je proto, že
        jde o "provozní" řadu, by bylo obejití jeho rozhodnutí.
        """
        self.ensure_one()

        if self.hh_odhlaseno:
            return 'odhlášen'

        prijemce = (self.email_from or self.partner_id.email or '').strip().lower()
        if prijemce and self.env['mail.blacklist'].sudo().search_count(
                [('email', '=', prijemce), ('active', '=', True)]):
            return 'adresa je na seznamu zablokovaných'

        return ''

    def _hh_prodejni_zadrz(self):
        """Vrátí důvod, proč prodejní zprávu neposlat, nebo prázdno."""
        self.ensure_one()

        duvod = self._hh_zadrz_emailu()
        if duvod:
            return duvod

        if self.hh_serie_pozastavena:
            return 'pozastaveno kvůli osobní odpovědi'
        if self._hh_ma_hovor():
            return 'má domluvený hovor'
        if not self._hh_rezervace_otevrene():
            return 'rezervace jsou zavřené'

        return ''

    def _hh_poslat_zpravu(self, zprava):
        """Před odesláním se ověří, že zpráva má komu a proč jít."""
        duvod = (self._hh_prodejni_zadrz() if zprava.stitek_id.prodejni
                 else self._hh_zadrz_emailu())
        if duvod:
            _logger.info(
                'Honza Hauzr CRM: zprava "%s" pro %s neodesla - %s.',
                zprava.name, self.email_from or self.id, duvod)
            return False
        return super()._hh_poslat_zpravu(zprava)

    # ------------------------------------------------------------------
    # nahledovy text a paticka
    # ------------------------------------------------------------------

    def _hh_telo_zpravy(self, sablona_mailu):
        """Každou zprávu z řady obalí náhledovým textem a patičkou.

        Pole Html vrací Markup. Ten při spojení s obyčejným řetězcem
        druhou stranu zaescapuje - bez obalení by se patička do
        zprávy vypsala jako zdrojový kód místo textu.
        """
        telo = super()._hh_telo_zpravy(sablona_mailu)

        nahled = (sablona_mailu.preheader or '').strip()
        if nahled:
            # Markup % escapuje dosazované hodnoty, takže Honzův text
            # projde bezpečně, a výplň z entit zůstane výplní.
            telo = Markup(NAHLED) % {
                'text': nahled, 'vypln': Markup(VYPLN)} + telo

        # Patička je u zpráv rovnou v textu, aby ji Honza viděl
        # v editoru. Tohle je pojistka pro případ, že ji smaže nebo
        # že napíše zprávu novou: bez odhlášení nesmí odejít nic.
        if not ma_odhlaseni(telo):
            telo = telo + self._hh_paticka_emailu()

        return telo

    # ------------------------------------------------------------------
    # sloupec Odhlaseno
    # ------------------------------------------------------------------

    @api.model
    def _hh_sekce_odhlaseno(self):
        return self.env.ref(
            'honzahauzr_crm.hh_stupen_odhlaseno', raise_if_not_found=False)

    def _hh_do_sloupce_odhlaseno(self):
        """Odhlášené karty přesune na nástěnce do sloupce Odhlášeno.

        Honza tak vidí rovnou na nástěnce, komu se přestalo psát,
        a nemusí to hledat po kartách.
        """
        stupen = self._hh_sekce_odhlaseno()
        if not stupen:
            return
        k_presunu = self.filtered(lambda l: l.stage_id != stupen)
        if k_presunu:
            k_presunu.sudo().write({'stage_id': stupen.id})

    def _hh_zrusit_odhlaseni(self):
        """Nové přihlášení z webu odhlášení ruší a řada jede od začátku.

        Bez tohohle byl člověk, který se jednou odhlásil, navždycky
        hluchý: formulář sice odeslal, karta se našla ta jeho - ale
        s odhlášením na ní mu nic neodešlo a nikomu se to nehlásilo.
        Přitom vyplněný formulář je jasný souhlas.

        Maže se i paměť odeslaného. "Jede znovu od začátku" znamená,
        že mu řada projde celá, ne že naváže tam, kde tenkrát
        přestal.
        """
        self.ensure_one()
        if not self.hh_odhlaseno:
            return False

        adresa = (self.email_from or self.partner_id.email or '').strip()
        if adresa:
            self.env['mail.blacklist'].sudo()._remove(adresa)

        self.sudo().write({
            'hh_odhlaseno': False,
            'hh_serie_pozastavena': False,
            'hh_odeslane_stupne_ids': [(5, 0, 0)],
            'hh_odeslane_maily_ids': [(5, 0, 0)],
        })
        return True

    def _hh_vratit_se(self):
        """Rozmyslel si odhlášení - zpátky do řady, od začátku.

        Karta visí ve sloupci Odhlášeno a ten je poslední, takže by
        ji dopředu nic neposunulo. Vrací se do sloupce, ze kterého
        člověk původně přišel; tím se mu řada rozjede znovu.
        """
        self.ensure_one()

        vratil_se = self._hh_zrusit_odhlaseni()
        if self.stage_id != self._hh_sekce_odhlaseno():
            return vratil_se

        stupen = self._hh_stupen_zdroje(self.hh_zdroj or 'vyzva')
        if stupen:
            self.sudo().write({'stage_id': stupen.id})
        return True

    def _hh_prijmout_dalsi_krok(self, hodnoty):
        """Opakované přihlášení: nejdřív ho pustit z bloku, pak zařadit."""
        self.ensure_one()

        if self._hh_zrusit_odhlaseni():
            # Odhlášeno je poslední sloupec v řadě a karta se posouvá
            # jen dopředu - odtud by ji nic nevytáhlo. Uvolní se tedy
            # ze sloupce a správný jí vzápětí přiřadí zařazení podle
            # zdroje formuláře.
            if self.stage_id == self._hh_sekce_odhlaseno():
                self.sudo().stage_id = False

        return super()._hh_prijmout_dalsi_krok(hodnoty)

    def write(self, vals):
        """Zaškrtnuté odhlášení kartu rovnou přesune.

        Visí to na poli, ne na odhlašovací stránce, takže to platí
        i když přepínač zaškrtne Honza ručně - třeba po telefonu.

        Zacyklit se to nemůže: přesun zapisuje jen stage_id, a na to
        se tahle větev neváže.
        """
        vysledek = super().write(vals)
        if vals.get('hh_odhlaseno'):
            self._hh_do_sloupce_odhlaseno()
        return vysledek
