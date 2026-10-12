# -*- coding: utf-8 -*-
"""Odkud člověk přišel: Google, Instagram, Facebook, TikTok, YouTube.

Odoo tohle v základu umí: crm.lead dědí utm.mixin, takže má pole
Zdroj / Kanál / Kampaň, a modul utm si parametry z adresy ukládá do
cookie. Jsou tu ale dvě díry, kvůli kterým by čísla byla jen
přibližná:

**Cookie lišta.** Odoo ukládá UTM jako cookie typu "optional". Dokud
je lišta se souhlasem vypnutá, projde to. Jakmile se zapne - a před
spuštěním na ostro se zapne - přestane se bez souhlasu ukládat
a část lidí přijde bez zdroje. Pamatujeme si to proto vedle toho
v relaci, která je technicky nutná a na souhlasu nezávisí.

**Netagované odkazy.** Odkaz v popisku na Instagramu nebo výsledek
z Googlu žádné utm_ parametry nenese. Takový člověk by zůstal bez
zdroje, i když se dá poznat z hlavičky Referer. Doplňujeme ho tedy
z odkazovače - jen když UTM opravdu chybí, aby ručně otagovaná
kampaň měla vždycky přednost.

Co se zapisuje, se drží první návštěvy: kdo přišel z Instagramu
a vrátil se za týden přímo, zůstává u Instagramu. Zajímá nás,
odkud se o Honzovi dozvěděl, ne kudy chodí potom.
"""
import logging
from urllib.parse import urlparse

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Pod timhle klicem sedi puvod v relaci navstevnika.
KLIC_RELACE = 'hh_puvod'

# Pod timhle klicem si relace drzi, ciji je. Diky tomu jde prehrane
# video priradit konkretnimu cloveku i na strankach, kde zadny
# osobni odkaz neni - treba kdyz se nekdo prihlasi do vyzvy a pak
# si projde zbytek webu.
KLIC_CLOVEKA = 'hh_lead'

POLE = (
    ('utm_source', 'source_id', 'utm.source'),
    ('utm_medium', 'medium_id', 'utm.medium'),
    ('utm_campaign', 'campaign_id', 'utm.campaign'),
)

# Domeny odkazovacu. Hleda se zprava, takze "l.instagram.com"
# i "instagram.com" spadnou pod Instagram.
ODKAZOVACE = (
    ('Instagram', ('instagram.com', 'ig.me')),
    ('Facebook', ('facebook.com', 'fb.com', 'fb.me', 'messenger.com')),
    ('TikTok', ('tiktok.com',)),
    ('YouTube', ('youtube.com', 'youtu.be')),
    ('LinkedIn', ('linkedin.com', 'lnkd.in')),
    ('Google', ('google.com', 'google.cz', 'googleusercontent.com')),
    ('Seznam', ('seznam.cz',)),
    ('Bing', ('bing.com',)),
    ('X', ('twitter.com', 'x.com', 't.co')),
    ('WhatsApp', ('whatsapp.com',)),
)

# Jak se pisou zname zdroje, at kolac necte "instagram", "Instagram"
# a "IG" jako tri ruzne vecí. Klic je hodnota z adresy, malymi.
SROVNANI = {
    'instagram': 'Instagram', 'ig': 'Instagram',
    'facebook': 'Facebook', 'fb': 'Facebook', 'meta': 'Facebook',
    'tiktok': 'TikTok', 'tt': 'TikTok',
    'youtube': 'YouTube', 'yt': 'YouTube',
    'google': 'Google', 'adwords': 'Google', 'google_ads': 'Google',
    'seznam': 'Seznam', 'sklik': 'Seznam',
    'linkedin': 'LinkedIn',
    'bing': 'Bing',
    'twitter': 'X', 'x': 'X',
    'email': 'E-mail', 'mail': 'E-mail', 'newsletter': 'E-mail',
    'whatsapp': 'WhatsApp',
}

# Kanal u zdroje poznaneho z odkazovace. Cesky, protoze to cte Honza,
# ne analyticky nastroj.
SOCIALNI = 'Sociální sítě'
VYHLEDAVANI = 'Vyhledávání'
ODKAZ = 'Odkaz z webu'

KANALY = {
    'Google': VYHLEDAVANI, 'Seznam': VYHLEDAVANI, 'Bing': VYHLEDAVANI,
    'Instagram': SOCIALNI, 'Facebook': SOCIALNI, 'TikTok': SOCIALNI,
    'YouTube': SOCIALNI, 'LinkedIn': SOCIALNI, 'X': SOCIALNI,
    'WhatsApp': SOCIALNI,
}

# Totez pro kanal zapsany v adrese. Hodnoty jako "social" nebo "cpc"
# jsou zvyklost analytickych nastroju; v nabidce u karty by nikomu
# nic nerekly.
KANALY_NAZVY = {
    'social': SOCIALNI, 'social-media': SOCIALNI, 'socialni': SOCIALNI,
    'organic': VYHLEDAVANI, 'search': VYHLEDAVANI, 'seo': VYHLEDAVANI,
    'referral': ODKAZ, 'odkaz': ODKAZ,
    'email': 'E-mail', 'mail': 'E-mail', 'newsletter': 'E-mail',
    'cpc': 'Placená reklama', 'ppc': 'Placená reklama',
    'paid': 'Placená reklama', 'ads': 'Placená reklama',
    'sms': 'SMS',
}

# Obecny kanal, ktery k formulari pridava samo Odoo. Rika jen "prisel
# z webu", coz plati o kazdem - kdyz vime konkretneji, prepiseme ho.
OBECNY_KANAL = 'website'

# Zdroj pro toho, kdo prisel bez stopy - adresu si napsal sam nebo
# kliknul v aplikaci, ktera odkazovac neposila.
PRIMO = 'Přímo'

# Karty z doby, nez se puvod zacal merit. Prazdno by v kolaci
# vypadalo jako chyba mereni.
PRED_MERENIM = 'Před měřením'
PARAMETR_OD = 'honzahauzr_crm.puvod_meren_od'


def srovnat(hodnota, prevod=None):
    """Zná-li se hodnota, vrátí její ustálený zápis.

    Bez toho by koláč četl "instagram", "Instagram" a "IG" jako tři
    různé zdroje - každá hodnota z adresy se píše jinak.
    """
    text = (hodnota or '').strip()
    if not text:
        return ''
    return (prevod if prevod is not None else SROVNANI).get(text.lower(), text)


# Ktery prevod platí pro ktery seznam.
PREVODY = {
    'utm.source': SROVNANI,
    'utm.medium': KANALY_NAZVY,
}


def zdroj_z_odkazovace(odkaz, vlastni_domeny=()):
    """Z hlavičky Referer pozná známou síť nebo vyhledávač.

    Vrací dvojici (zdroj, kanál), nebo (None, None) u prázdného
    odkazovače a u přechodu v rámci vlastního webu.
    """
    if not odkaz:
        return None, None
    try:
        domena = (urlparse(odkaz).hostname or '').lower()
    except ValueError:
        return None, None
    if not domena:
        return None, None
    if any(domena == d or domena.endswith('.' + d)
           for d in vlastni_domeny if d):
        return None, None

    for nazev, domeny in ODKAZOVACE:
        if any(domena == d or domena.endswith('.' + d) for d in domeny):
            return nazev, KANALY.get(nazev, 'referral')

    # Neznámý web. Jméno domény je pořád lepší než prázdno - Honza
    # aspoň uvidí, že odněkud chodí lidé, a může to otagovat.
    return domena.removeprefix('www.'), 'referral'


class IrHttpPuvod(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _hh_zapamatovat_puvod(cls):
        """Uloží původ návštěvníka do relace. Volá se při každém požadavku."""
        try:
            if not request or not request.session:
                return
            cesta = request.httprequest.path
            # Jen stránky webu. Požadavky administrace, obrázků
            # a assetů s příchodem návštěvníka nesouvisí a jen by
            # relaci zbytečně přepisovaly.
            if cesta.startswith(('/web/', '/odoo', '/my', '/mail/',
                                 '/longpolling', '/websocket', '/@')):
                return

            udaje = dict(request.session.get(KLIC_RELACE) or {})
            puvodni = dict(udaje)

            for parametr, _pole, _model in POLE:
                hodnota = request.params.get(parametr)
                if hodnota and isinstance(hodnota, str):
                    udaje[parametr] = hodnota.strip()[:100]

            # Odkazovač jen jako záloha, a jen jednou: ručně
            # otagovaná kampaň i první poznaná síť mají přednost.
            if not udaje.get('utm_source'):
                zdroj, kanal = zdroj_z_odkazovace(
                    request.httprequest.referrer, cls._hh_vlastni_domeny())
                if zdroj:
                    udaje['utm_source'] = zdroj
                    udaje.setdefault('utm_medium', kanal)

            if udaje != puvodni:
                request.session[KLIC_RELACE] = udaje
        except Exception:
            # Zapamatování původu nesmí nikdy shodit stránku.
            _logger.exception(
                'Honza Hauzr CRM: zapamatovani puvodu navstevnika selhalo.')

    @classmethod
    def _hh_vlastni_domeny(cls):
        """Domény, ze kterých přechod není příchod zvenčí."""
        domeny = {(request.httprequest.host or '').split(':')[0].lower()}
        try:
            for web in request.env['website'].sudo().search([]):
                hostitel = urlparse(web.domain or '').hostname
                if hostitel:
                    domeny.add(hostitel.lower())
        except Exception:
            pass
        return tuple(d for d in domeny if d)


class UtmMixinPuvod(models.AbstractModel):
    """Jednotný zápis názvů v seznamech Zdroj a Kanál.

    Sem vede každé zakládání hodnoty — naše i to, které si Odoo dělá
    samo z cookie. Bez toho by v koláči stál vedle sebe "instagram"
    z neotagovaného odkazu a "Instagram" od nás jako dva různé zdroje.
    """

    _inherit = 'utm.mixin'

    def _find_or_create_record(self, model_name, name):
        prevod = PREVODY.get(model_name)
        if prevod is not None:
            name = srovnat(name, prevod)
        return super()._find_or_create_record(model_name, name)

    @api.model
    def _hh_srovnat_nazvy_puvodu(self):
        """Srovná názvy, které v seznamech vznikly dřív.

        Hledání záznamu nerozlišuje velikost písmen, takže jednou
        založený "instagram" si drží své malé i, i když už bychom ho
        zakládali jako "Instagram". Tohle to přejmenuje; a kdyby
        v seznamu mezitím ležely obě podoby, karty se přepnou na tu
        správnou a druhá se smaže.

        Pouští se při každém upgradu a podruhé už nic nezmění.
        """
        prejmenovano, slouceno = 0, 0
        for model, prevod in PREVODY.items():
            Seznam = self.env[model].sudo().with_context(active_test=False)
            pole = 'source_id' if model == 'utm.source' else 'medium_id'
            for zaznam in Seznam.search([]):
                spravny = srovnat(zaznam.name, prevod)
                if not spravny or spravny == zaznam.name:
                    continue
                dvojce = Seznam.search(
                    [('name', '=', spravny), ('id', '!=', zaznam.id)], limit=1)
                if dvojce:
                    self.env['crm.lead'].sudo().with_context(
                        active_test=False).search(
                            [(pole, '=', zaznam.id)]).write({pole: dvojce.id})
                    zaznam.unlink()
                    slouceno += 1
                else:
                    zaznam.name = spravny
                    prejmenovano += 1

        if prejmenovano or slouceno:
            _logger.info(
                'Honza Hauzr CRM: nazvy puvodu - prejmenovano %s, '
                'slouceno %s.', prejmenovano, slouceno)

        self._hh_oznacit_karty_pred_merenim()
        return prejmenovano, slouceno

    @api.model
    def _hh_oznacit_karty_pred_merenim(self):
        """Označí karty, které vznikly dřív, než se původ měřil.

        Bez toho by u nich zůstalo prázdno a v koláči by to vypadalo
        jako chyba měření - přitom je to prostě doba, kdy se nic
        neměřilo.

        Okamžik, odkud měření platí, se zapíše při prvním spuštění
        a dál se nemění. Kdyby se bral "teď", posouval by se při
        každém upgradu a postupně by pohltil i karty, u kterých zdroj
        chybí z jiného důvodu.
        """
        Parametry = self.env['ir.config_parameter'].sudo()
        od = Parametry.get_param(PARAMETR_OD)
        if not od:
            od = fields.Datetime.to_string(fields.Datetime.now())
            Parametry.set_param(PARAMETR_OD, od)

        stare = self.env['crm.lead'].sudo().with_context(
            active_test=False).search([
                ('source_id', '=', False),
                ('create_date', '<', od),
            ])
        if not stare:
            return 0

        zdroj = self.env['utm.mixin'].sudo()._find_or_create_record(
            'utm.source', PRED_MERENIM)
        stare.write({'source_id': zdroj.id})
        _logger.info('Honza Hauzr CRM: %s karet oznaceno "%s".',
                     len(stare), PRED_MERENIM)
        return len(stare)


class CrmLeadPuvod(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def _hh_puvod_z_relace(self):
        """Hodnoty pro Zdroj / Kanál / Kampaň podle relace návštěvníka."""
        if not request:
            return {}
        udaje = request.session.get(KLIC_RELACE) or {}
        if not udaje:
            return {}

        hodnoty = {}
        for parametr, pole, model in POLE:
            nazev = (udaje.get(parametr) or '').strip()
            if not nazev:
                continue
            zaznam = self.env['utm.mixin'].sudo()._find_or_create_record(
                model, nazev)
            if zaznam:
                hodnoty[pole] = zaznam.id
        return hodnoty

    def website_form_input_filter(self, request, values):
        """Doplní původ dřív, než se z formuláře založí karta.

        Až v create() by to bylo pozdě u kanálu: website_crm sem
        nejdřív dosadí obecné "Website", a ten by pak naši hodnotu
        přebil. "Website" přitom platí o každém, kdo formulář
        odeslal, takže se nedá k ničemu použít — když víme, že
        člověk přišel ze sociální sítě nebo z vyhledávače, přepíšeme
        ho.
        """
        values = super().website_form_input_filter(request, values)
        z_relace = self._hh_puvod_z_relace()
        for pole, hodnota in z_relace.items():
            if not values.get(pole):
                values[pole] = hodnota
            elif pole == 'medium_id' and self._hh_je_obecny_kanal(
                    values[pole]):
                values[pole] = hodnota

        # Kdo nepřišel odnikud poznatelného, napsal si adresu sám
        # nebo kliknul v aplikaci, která odkazovač neposílá. Je to
        # pořád odpověď na otázku "odkud" — prázdný řádek v koláči
        # by jen vypadal jako chyba měření.
        if not values.get('source_id'):
            values['source_id'] = self.env['utm.mixin'].sudo(
                )._find_or_create_record('utm.source', PRIMO).id
        return values

    @api.model
    def _hh_je_obecny_kanal(self, medium_id):
        nazev = self.env['utm.medium'].sudo().browse(medium_id).name or ''
        return nazev.strip().lower() == OBECNY_KANAL

    def _hh_doplnit_puvod(self, hodnoty=None):
        """Doplní prázdný původ. Co už je vyplněné, nechává být.

        Drží se první návštěvy: kdo přišel z Instagramu a za týden
        se vrátil přímo, zůstává u Instagramu.
        """
        z_relace = hodnoty if hodnoty is not None else self._hh_puvod_z_relace()
        if not z_relace:
            return
        for lead in self:
            chybi = {pole: hodnota for pole, hodnota in z_relace.items()
                     if not lead[pole]}
            if chybi:
                lead.write(chybi)

    @api.model_create_multi
    def create(self, vals_list):
        """Nová karta si původ odnese z relace.

        Odoo sice plní tahle pole samo z cookie (utm.mixin), ale jen
        dokud je vypnutá lišta se souhlasem - viz vysvětlení nahoře.
        Tohle doplní, co tam po ní chybí.
        """
        z_relace = self._hh_puvod_z_relace()
        if z_relace:
            for hodnoty in vals_list:
                for pole, hodnota in z_relace.items():
                    hodnoty.setdefault(pole, hodnota)
        leady = super().create(vals_list)
        # Karta, kterou create() místo zalozeni nasel a jen doplnil,
        # muze byt starsi a bez puvodu - treba z doby, nez tohle
        # existovalo. Dovyplni se ted.
        if z_relace:
            leady._hh_doplnit_puvod(z_relace)
        if leady:
            leady[0]._hh_zapamatovat_cloveka()
        return leady

    def _hh_zapamatovat_cloveka(self):
        """Poznamená si do relace, čí je.

        Od téhle chvíle se dá přehrané video přiřadit konkrétnímu
        člověku i na stránkách, kde žádný osobní odkaz není.
        """
        if not request or not self:
            return
        try:
            request.session[KLIC_CLOVEKA] = self[0].id
        except Exception:
            _logger.exception(
                'Honza Hauzr CRM: zapamatovani cloveka do relace selhalo.')

    @api.model
    def _hh_clovek_z_relace(self):
        """Karta, ke které relace patří, nebo prázdná sada."""
        if not request:
            return self.browse()
        try:
            cislo = request.session.get(KLIC_CLOVEKA)
        except Exception:
            return self.browse()
        if not cislo:
            return self.browse()
        return self.sudo().browse(cislo).exists()
