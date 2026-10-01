# -*- coding: utf-8 -*-
import logging

from datetime import datetime, timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class HhTermin(models.Model):
    """Jeden termin na uvodni hovor - volny, nebo uz zabrany.

    Proc vlastni model a ne modul Schuzky od Odoo: ten je jen
    v Enterprise, v Community se nainstalovat neda. Kalendar se
    schvalnymi terminy je pritom cela podstata veci, takze je to
    postavene tady a drzi se to zamerne jednoduche:

      * Honza si v kalendari naklika volne terminy,
      * zakaznik na webu vidi, co je volne, a jeden si vezme,
      * v kalendari v adminu pak Honza termin presune mysi jinam
        a zakaznikovi o tom prijde e-mail.

    Zabrany termin se uz na webu nenabizi, protoze se filtruje
    podle stavu.
    """

    _name = 'hh.termin'
    _description = 'Termín úvodního hovoru'
    _order = 'zacatek'
    # Chat a ukoly primo na terminu - at je u nej videt, co se dohodlo.
    _inherit = ['mail.thread']

    # Zamerne neulozene: nazev se sklada ze stavu a jmena, obojí uz
    # v tabulce je. Kdyby se ukladal, zustaval by po zmene vzorce
    # viset stary text u vsech drivejsich terminu.
    name = fields.Char(
        string='Termín',
        compute='_compute_name',
    )

    zacatek = fields.Datetime(
        string='Začátek',
        required=True,
        tracking=True,
        default=lambda self: fields.Datetime.now().replace(
            minute=0, second=0, microsecond=0) + timedelta(days=1),
    )

    delka = fields.Float(
        string='Délka (hodiny)',
        default=lambda self: self._hh_vychozi_delka(),
        required=True,
        help='Jak dlouho hovor trva. 0.75 je 45 minut. Vychozi hodnota '
             'se bere z rozvrhu v nastaveni CRM.',
    )

    # Kalendarovy pohled Odoo potrebuje konec jako ulozene pole, jinak
    # se udalost neda chytit mysi a protahnout.
    konec = fields.Datetime(
        string='Konec',
        compute='_compute_konec',
        inverse='_inverse_konec',
        store=True,
    )

    stav = fields.Selection(
        selection=[
            ('volny', 'Volný'),
            ('rezervovany', 'Rezervovaný'),
            ('zablokovany', 'Přeškrtnutý'),
            ('zruseny', 'Zrušený'),
        ],
        string='Stav',
        default='volny',
        required=True,
        tracking=True,
    )

    # Datum a hodina zvlast. Ve formulari se totiz termin nejcasteji
    # zaklada kliknutim na den v kalendari - datum uz je tim padem dane
    # a prepisovat cely datum a cas dokola je zbytecna prace. Obe pole
    # jsou jen jiny pohled na zacatek, v databazi nic nepribyva.
    hh_datum = fields.Date(
        string='Datum',
        compute='_compute_hh_cast',
        inverse='_inverse_hh_cast',
    )
    hh_hodina = fields.Selection(
        selection='_hh_hodiny',
        string='Hodina',
        compute='_compute_hh_cast',
        inverse='_inverse_hh_cast',
    )

    # Prepinac do seznamu, aby se termin dal preskrtnout jednim kliknutim
    # a nemusel se kvuli tomu otevirat. Rezervovany termin se prepnout
    # neda - to uz je domluva s konkretnim clovekem.
    hh_nabizet = fields.Boolean(
        string='Nabízet',
        compute='_compute_hh_nabizet',
        inverse='_inverse_hh_nabizet',
        help='Vypni, když se ti termín zrovna nehodí. Ze stránky '
             's rezervacemi zmizí, ale zůstane ti tu, takže ho můžeš '
             'kdykoliv vrátit zpátky.',
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Příležitost',
        ondelete='set null',
        tracking=True,
        index=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Kontakt',
        ondelete='set null',
    )

    jmeno = fields.Char(string='Jméno', tracking=True)
    email = fields.Char(string='E-mail', tracking=True)
    telefon = fields.Char(string='Telefon')
    poznamka = fields.Text(string='Poznámka od zákazníka')

    # Nahodny retezec v odkazu, kterym zakaznik termin zrusi. Bez nej
    # by stacilo hadat cislo a rusit cizi rezervace.
    zrusovaci_klic = fields.Char(string='Rušící klíč', copy=False, index=True)

    # ------------------------------------------------------------------
    # dopocitavana pole
    # ------------------------------------------------------------------

    @api.depends('zacatek', 'delka')
    def _compute_konec(self):
        for termin in self:
            if termin.zacatek:
                termin.konec = termin.zacatek + timedelta(
                    hours=termin.delka or 0.0)
            else:
                termin.konec = False

    @api.model
    def _hh_vychozi_delka(self):
        return (self._hh_rozvrh()['delka_min'] or 45) / 60.0

    def _inverse_konec(self):
        """Protazeni udalosti mysi v kalendari meni delku, ne zacatek.

        Strop na ctyri hodiny je tu kvuli zakladani z kalendare Odoo:
        kliknuti na prazdny den v mesicnim pohledu posle jako konec
        cely den, z ceho by vysel dvanactihodinovy hovor. Takova delka
        neni protazeni mysi, ale nedorozumeni - bere se proto delka
        z rozvrhu.
        """
        for termin in self:
            if not termin.zacatek or not termin.konec:
                continue
            hodin = (termin.konec - termin.zacatek).total_seconds() / 3600.0
            termin.delka = hodin if 0 < hodin < 4 else self._hh_vychozi_delka()

    @api.model
    def _hh_hodiny(self):
        """Nabidka hodin do vyberu ve formulari.

        Zaklad jsou hodiny podle rozvrhu (10:00, 10:45, ...), aby
        v seznamu byly presne ty casy, ktere se doopravdy nabizeji.
        K nim se primicha ctvrthodinova mrizka pres cely den, aby
        slo zalozit i termin mimo rozvrh a aby se u stavajiciho
        terminu vzdycky nasla jeho vlastni hodina.
        """
        minuty = set()

        rozvrh = self._hh_rozvrh()
        if rozvrh['do'] > rozvrh['od']:
            krok = rozvrh['delka_min'] or 45
            cas = int(round(rozvrh['od'] * 60))
            konec = int(round(rozvrh['do'] * 60))
            while cas <= konec:
                minuty.add(cas)
                cas += krok

        for cas in range(0, 24 * 60, 15):
            minuty.add(cas)

        return [
            ('%02d:%02d' % (m // 60, m % 60), '%02d:%02d' % (m // 60, m % 60))
            for m in sorted(minuty)
            if m < 24 * 60
        ]

    @api.depends('zacatek')
    def _compute_hh_cast(self):
        pasmo = self._hh_pasmo()
        for termin in self:
            if termin.zacatek:
                mistni = pytz.utc.localize(termin.zacatek).astimezone(pasmo)
                termin.hh_datum = mistni.date()
                termin.hh_hodina = mistni.strftime('%H:%M')
            else:
                termin.hh_datum = False
                termin.hh_hodina = False

    def _inverse_hh_cast(self):
        pasmo = self._hh_pasmo()
        for termin in self:
            if not termin.hh_datum or not termin.hh_hodina:
                continue
            hodina, minuta = (int(c) for c in termin.hh_hodina.split(':'))
            naivni = datetime(
                termin.hh_datum.year, termin.hh_datum.month,
                termin.hh_datum.day, hodina, minuta,
            )
            # localize, ne replace(tzinfo=...) - jen tak sedi letni cas
            mistni = pasmo.localize(naivni, is_dst=None)
            termin.zacatek = mistni.astimezone(pytz.utc).replace(tzinfo=None)

    @api.depends('stav')
    def _compute_hh_nabizet(self):
        for termin in self:
            termin.hh_nabizet = termin.stav in ('volny', 'rezervovany')

    def _inverse_hh_nabizet(self):
        for termin in self:
            if termin.stav == 'rezervovany':
                # Domluveny hovor se preskrtnout neda - musel by se
                # nejdriv zrusit, at o tom clovek vi.
                continue
            termin.stav = 'volny' if termin.hh_nabizet else 'zablokovany'

    @api.depends('stav', 'jmeno')
    def _compute_name(self):
        """Nazev zamerne bez data a casu.

        Kalendar i seznam ukazuji zacatek zvlast, takze by se cas
        opakoval dvakrat vedle sebe. Hlavne ale: nazev je ulozene
        pole a cas by se do nej zapsal v pasmu toho, kdo zaznam
        prave uklada. Zapsal by ho tedy jinak web (prazska hodina)
        a jinak sprava (pasmo prihlaseneho cloveka) a v kalendari
        by pak svitily dva ruzne casy u tehoz terminu.
        """
        for termin in self:
            if termin.stav == 'rezervovany':
                termin.name = termin.jmeno or _('Rezervováno')
            elif termin.stav == 'zablokovany':
                termin.name = _('Přeškrtnuto')
            elif termin.stav == 'zruseny':
                termin.name = _('Zrušeno')
            else:
                termin.name = _('Volný termín')

    # ------------------------------------------------------------------
    # preskrtavani z formulare a ze seznamu
    # ------------------------------------------------------------------

    def hh_preskrtnout(self):
        """Termin zmizi ze stranky s rezervacemi, ale zustane v prehledu."""
        self.filtered(lambda t: t.stav == 'volny').stav = 'zablokovany'

    def hh_uvolnit(self):
        self.filtered(lambda t: t.stav == 'zablokovany').stav = 'volny'

    # ------------------------------------------------------------------
    # kontroly
    # ------------------------------------------------------------------

    @api.constrains('delka')
    def _check_delka(self):
        for termin in self:
            if termin.delka <= 0:
                raise UserError(_('Délka termínu musí být větší než nula.'))

    # ------------------------------------------------------------------
    # presun terminu v kalendari
    # ------------------------------------------------------------------

    def write(self, vals):
        # Puvodni casy si drzim pred zapisem - potrebuju je do e-mailu,
        # aby zakaznik videl, odkud kam se hovor posunul.
        puvodni = {t.id: t.zacatek for t in self} if 'zacatek' in vals else {}

        vysledek = super().write(vals)

        if 'zacatek' in vals:
            for termin in self:
                if termin.stav != 'rezervovany':
                    continue
                if puvodni.get(termin.id) == termin.zacatek:
                    continue
                termin._hh_ohlasit_presun(puvodni.get(termin.id))

        return vysledek

    def _hh_ohlasit_presun(self, stary_zacatek):
        """Da zakaznikovi vedet, ze se jeho hovor presunul."""
        self.ensure_one()

        prijemce = self.email or self.lead_id.email_from
        if not prijemce:
            return

        telo = [
            '<p>Ahoj%s,</p>' % ((' ' + self.jmeno) if self.jmeno else ''),
            '<p>musel jsem posunout náš úvodní hovor.</p>',
        ]
        if stary_zacatek:
            telo.append('<p><b>Původně:</b> %s</p>' % self._hh_cas(stary_zacatek))
        telo.append('<p><b>Nově:</b> %s</p>' % self._hh_cas(self.zacatek))
        telo.append('<p>Kdyby se ti nový čas nehodil, napiš mi a domluvíme jiný.</p>')
        telo.append('<p>Honza Hauzr</p>')

        self._hh_poslat(prijemce, 'Úvodní hovor se přesunul', ''.join(telo))

    # ------------------------------------------------------------------
    # rezervace z webu
    # ------------------------------------------------------------------

    def hh_rezervovat(self, jmeno, email, telefon=None, poznamka=None):
        """Zabere termin pro konkretniho cloveka.

        Vraci True, kdyz se to povedlo. Kdyz uz termin nekdo zabral
        mezitim, vraci False - dva lide muzou kliknout na stejny cas
        v tentyz okamzik.
        """
        self.ensure_one()

        if self.stav != 'volny':
            return False

        # Zamek na radku: druhy soubezny pozadavek na stejny termin
        # pocka, a az se dostane ke slovu, uvidi uz stav rezervovany.
        self.env.cr.execute(
            'SELECT stav FROM hh_termin WHERE id = %s FOR UPDATE', (self.id,))
        radek = self.env.cr.fetchone()
        if not radek or radek[0] != 'volny':
            return False

        lead = self._hh_najit_lead(jmeno, email, telefon, poznamka)

        self.write({
            'stav': 'rezervovany',
            'jmeno': jmeno,
            'email': email,
            'telefon': telefon,
            'poznamka': poznamka,
            'lead_id': lead.id if lead else False,
            'partner_id': lead.partner_id.id if lead and lead.partner_id else False,
            'zrusovaci_klic': self._hh_novy_klic(),
        })

        self._hh_potvrdit()
        self._hh_upozornit_honzu()
        return True

    def _hh_najit_lead(self, jmeno, email, telefon, poznamka):
        """Pripoji rezervaci k existujici prilezitosti, nebo zalozi novou.

        Hleda se podle e-mailu mezi otevrenymi prilezitostmi - clovek,
        ktery prosel tridenni vyzvou, uz v CRM je a nema smysl zakladat
        mu druhy zaznam.
        """
        Lead = self.env['crm.lead'].sudo()

        lead = Lead.search([
            ('email_from', '=ilike', email),
            ('active', '=', True),
        ], order='create_date desc', limit=1)

        stitek = self.env.ref('honzahauzr_crm.tag_rezervace',
                              raise_if_not_found=False)

        if lead:
            hodnoty = {}
            if stitek and stitek not in lead.tag_ids:
                hodnoty['tag_ids'] = [(4, stitek.id)]
            if not lead.phone and telefon:
                hodnoty['phone'] = telefon
            if hodnoty:
                lead.write(hodnoty)
            self._hh_do_sloupce_rezervaci(lead)
            return lead

        hodnoty = {
            'name': 'Rezervace úvodního hovoru',
            'contact_name': jmeno,
            'email_from': email,
            'phone': telefon,
            'description': poznamka,
            'hh_zdroj': 'rezervace',
        }
        return Lead.create(hodnoty)

    def _hh_do_sloupce_rezervaci(self, lead):
        """Presune prilezitost do sloupce s rezervacemi hovoru.

        Kdo si domluvil hovor, uz neni v tridenni vyzve - patri mezi
        lidi, se kterymi se mluvi. Bez toho by zustal viset tam, kde
        byl, a Honza by ho musel pretahovat rucne.

        Novou prilezitost sem tahat nemusime, ta do sloupce spadne uz
        pri zalozeni podle zdroje 'rezervace'.
        """
        if not lead:
            return

        stupen = self.env.ref('crm.stage_lead3', raise_if_not_found=False)
        if not stupen or lead.stage_id == stupen:
            return

        # Pres write, ne primym zapisem do pole - na presunu stupne visi
        # odeslani e-mailu napsaneho u sloupce a to ma probehnout i tady.
        lead.write({'stage_id': stupen.id})

    def hh_zrusit_zakaznikem(self):
        """Uvolni termin zpatky. Vola se z odkazu v potvrzovacim e-mailu."""
        self.ensure_one()

        if self.stav != 'rezervovany':
            return False

        jmeno = self.jmeno
        kdy = self._hh_cas(self.zacatek)

        self.write({
            'stav': 'volny',
            'jmeno': False,
            'email': False,
            'telefon': False,
            'poznamka': False,
            'partner_id': False,
            'zrusovaci_klic': False,
        })

        adresa = self.env['ir.config_parameter'].sudo().get_param(
            'honzahauzr_crm.notify_email')
        if adresa:
            self._hh_poslat(
                adresa,
                'Zrušená rezervace: %s' % kdy,
                '<p><b>%s</b> zrušil(a) úvodní hovor na %s.</p>'
                '<p>Termín je zase volný.</p>' % (jmeno or '-', kdy),
            )
        return True

    # ------------------------------------------------------------------
    # e-maily
    # ------------------------------------------------------------------

    def _hh_potvrdit(self):
        self.ensure_one()
        if not self.email:
            return

        odkaz = self._hh_odkaz_na_zruseni()
        telo = (
            '<p>Ahoj%s,</p>'
            '<p>termín máme domluvený.</p>'
            '<p><b>Kdy:</b> %s<br/><b>Jak dlouho:</b> %s minut</p>'
            '<p>Ozvu se ti na uvedené spojení. Kdyby ti to nevyšlo, '
            'dej mi prosím vědět předem.</p>'
            '%s'
            '<p>Honza Hauzr</p>'
        ) % (
            (' ' + self.jmeno) if self.jmeno else '',
            self._hh_cas(self.zacatek),
            int(round((self.delka or 0) * 60)),
            ('<p><a href="%s">Zrušit termín</a></p>' % odkaz) if odkaz else '',
        )
        self._hh_poslat(self.email, 'Úvodní hovor je domluvený', telo)

    def _hh_upozornit_honzu(self):
        self.ensure_one()

        adresa = self.env['ir.config_parameter'].sudo().get_param(
            'honzahauzr_crm.notify_email')
        if not adresa:
            return

        radky = [
            ('Kdy', self._hh_cas(self.zacatek)),
            ('Jméno', self.jmeno or '-'),
            ('E-mail', self.email or '-'),
            ('Telefon', self.telefon or '-'),
        ]
        telo = ''.join('<p><b>%s:</b> %s</p>' % r for r in radky)
        if self.poznamka:
            telo += '<p><b>Poznámka:</b> %s</p>' % self.poznamka

        self._hh_poslat(adresa, 'Nová rezervace úvodního hovoru', telo,
                        odpovedet=self.email)

    def _hh_poslat(self, prijemce, predmet, telo, odpovedet=None):
        """Odeslani nesmi nikdy shodit rezervaci - proto to try/except.

        Kdyz posta nevyjde, zapise se to do logu; termin uz je zabrany
        a v CRM vidi Honza vsechno i bez e-mailu.
        """
        try:
            self.env['mail.mail'].sudo().create({
                'subject': predmet,
                'body_html': telo,
                'email_from': (self.env.company.email_formatted
                               or self.env.user.email_formatted),
                'email_to': prijemce,
                'reply_to': odpovedet or None,
                'model': 'hh.termin',
                'res_id': self.id,
                'auto_delete': False,
            }).send()
        except Exception as chyba:
            _logger.warning(
                'Honza Hauzr: e-mail k terminu %s se nepodarilo odeslat: %s',
                self.id, chyba)

    # ------------------------------------------------------------------
    # pomocne
    # ------------------------------------------------------------------

    def _hh_cas(self, kdy):
        """Datum a cas v pasmu firmy, ne v UTC a ne podle prihlaseneho.

        Zamerne se nebere pasmo toho, kdo akci spustil: hovor presouva
        sprava a e-mail cte zakaznik. Kdyby Michal sedel v jinem pasmu
        nez Honza, prisel by zakaznikovi cas posunuty o par hodin.
        """
        if not kdy:
            return '-'
        pasmo = self.env.company.sudo().partner_id.tz or 'Europe/Prague'
        mistni = fields.Datetime.context_timestamp(
            self.with_context(tz=pasmo), kdy)
        dny = ('pondělí', 'úterý', 'středa', 'čtvrtek', 'pátek',
               'sobota', 'neděle')
        return '%s %s' % (dny[mistni.weekday()],
                          mistni.strftime('%d.%m.%Y v %H:%M'))

    @api.model
    def _hh_novy_klic(self):
        import secrets
        return secrets.token_urlsafe(24)

    def _hh_odkaz_na_zruseni(self):
        self.ensure_one()
        if not self.zrusovaci_klic:
            return ''
        zaklad = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '')
        return '%s/rezervace/zrusit/%s/%s' % (
            zaklad.rstrip('/'), self.id, self.zrusovaci_klic)

    # ------------------------------------------------------------------
    # pro web
    # ------------------------------------------------------------------

    @api.model
    def hh_volne_terminy(self, dnu=None):
        """Volne terminy od ted do zadaneho poctu dnu dopredu."""
        ted = fields.Datetime.now()
        if dnu is None:
            dnu = self._hh_rozvrh()['dopredu']
        return self.sudo().search([
            ('stav', '=', 'volny'),
            ('zacatek', '>=', ted),
            ('zacatek', '<=', ted + timedelta(days=dnu)),
        ], order='zacatek')

    # ------------------------------------------------------------------
    # vyroba terminu podle rozvrhu
    # ------------------------------------------------------------------

    @api.model
    def _hh_rozvrh(self):
        """Nacte rozvrh z nastaveni CRM.

        Vsechno ma rozumnou zalozni hodnotu, aby generovani fungovalo
        i na cerstve nainstalovanem modulu, kde jeste nikdo nic nenastavil.
        """
        param = self.env['ir.config_parameter'].sudo()

        def cislo(klic, zaloha):
            try:
                return float(param.get_param('honzahauzr_crm.%s' % klic) or zaloha)
            except (TypeError, ValueError):
                return zaloha

        def zapnuto(klic, zaloha):
            hodnota = param.get_param('honzahauzr_crm.%s' % klic)
            if hodnota is False or hodnota is None or hodnota == '':
                return zaloha
            return hodnota not in ('False', 'false', '0')

        # Poradi odpovida datetime.weekday(): 0 = pondeli ... 6 = nedele
        dny = [
            zapnuto('rez_po', True),
            zapnuto('rez_ut', True),
            zapnuto('rez_st', True),
            zapnuto('rez_ct', True),
            zapnuto('rez_pa', True),
            zapnuto('rez_so', False),
            zapnuto('rez_ne', False),
        ]

        delka = int(cislo('rez_delka', 45)) or 45

        return {
            'od': cislo('rez_od', 10.0),
            'do': cislo('rez_do', 20.0),
            'delka_min': delka,
            'dopredu': int(cislo('rez_dopredu', 30)) or 30,
            'dny': dny,
        }

    @api.model
    def _hh_pasmo(self):
        """Pasmo, ve kterem se rozvrh cte.

        Hodiny v nastaveni jsou mistni ("od desiti do osmi"), zatimco
        v databazi se uklada UTC. Bez prevodu by se v lete a v zime
        terminy rozjely o hodinu.
        """
        nazev = self.env.company.sudo().partner_id.tz or 'Europe/Prague'
        try:
            return pytz.timezone(nazev)
        except pytz.UnknownTimeZoneError:
            return pytz.timezone('Europe/Prague')

    @api.model
    def hh_vygenerovat(self):
        """Doplni terminy podle rozvrhu az do konce nabizeneho okna.

        Vola se z nocniho ukolu i z tlacitka v nastaveni. Je zamerne
        idempotentni - co uz existuje, nechá být, takze opakovane
        spusteni nic nezdvoji ani neprepise preskrtnute terminy.
        """
        rozvrh = self._hh_rozvrh()
        pasmo = self._hh_pasmo()

        if rozvrh['do'] <= rozvrh['od']:
            _logger.warning(
                'Honza Hauzr: rozvrh terminu ma konec driv nez zacatek '
                '(%s - %s), nic se nevyrobi.', rozvrh['od'], rozvrh['do'])
            return 0

        ted = fields.Datetime.now()
        dnes_mistni = pytz.utc.localize(ted).astimezone(pasmo).date()

        # Co uz v okne existuje, at se nezaklada podruhe. Staci mnozina
        # zacatku - jine udaje nas pri porovnavani nezajimaji.
        hranice = ted + timedelta(days=rozvrh['dopredu'] + 1)
        existujici = set(self.sudo().search([
            ('zacatek', '>=', ted - timedelta(days=1)),
            ('zacatek', '<=', hranice),
        ]).mapped('zacatek'))

        krok = timedelta(minutes=rozvrh['delka_min'])
        delka_hodin = rozvrh['delka_min'] / 60.0
        nove = []

        for posun in range(rozvrh['dopredu'] + 1):
            den = dnes_mistni + timedelta(days=posun)
            if not rozvrh['dny'][den.weekday()]:
                continue

            hodina = rozvrh['od']
            while hodina + delka_hodin <= rozvrh['do'] + 1e-9:
                cele = int(hodina)
                minuty = int(round((hodina - cele) * 60))
                naivni = datetime(den.year, den.month, den.day, cele, minuty)

                # localize, ne replace(tzinfo=...) - jen tak se spravne
                # chytne letni cas a den, kdy se posouvaji hodiny.
                mistni = pasmo.localize(naivni, is_dst=None)
                v_utc = mistni.astimezone(pytz.utc).replace(tzinfo=None)

                hodina += delka_hodin

                # Terminy, ktere uz jsou za nami, nema smysl nabizet.
                if v_utc <= ted:
                    continue
                if v_utc in existujici:
                    continue

                existujici.add(v_utc)
                nove.append({
                    'zacatek': v_utc,
                    'delka': delka_hodin,
                    'stav': 'volny',
                })

        if nove:
            self.sudo().create(nove)

        return len(nove)

    @api.model
    def _hh_nocni_uklid(self):
        """Nocni ukol: doplni terminy a zahodi stare volne.

        Preskrtnute a rezervovane terminy zustavaji - jsou to zaznamy
        o tom, co se dohodlo, a maji cenu i zpetne.
        """
        vyrobeno = self.hh_vygenerovat()

        stare = self.sudo().search([
            ('stav', '=', 'volny'),
            ('zacatek', '<', fields.Datetime.now() - timedelta(days=1)),
        ])
        smazano = len(stare)
        stare.unlink()

        _logger.info('Honza Hauzr: vyrobeno %s terminu, smazano %s starych.',
                     vyrobeno, smazano)
        return True

    # ------------------------------------------------------------------
    # rozvrh a rucni rezervace z kalendare v adminu
    # ------------------------------------------------------------------
    #
    # Kalendar v adminu je jedine misto, kde se terminy spravuji. Cte
    # a zapisuje rozvrh temito metodami, aby nemusel znat vnitrnosti
    # systemovych parametru ani poradi dnu v tydnu.

    HH_DNY_KLICE = ('rez_po', 'rez_ut', 'rez_st', 'rez_ct', 'rez_pa',
                    'rez_so', 'rez_ne')

    @api.model
    def hh_nacist_rozvrh(self):
        """Rozvrh pro nastaveni pod kalendarem."""
        rozvrh = self._hh_rozvrh()
        return {
            'od': rozvrh['od'],
            'do': rozvrh['do'],
            'delka': rozvrh['delka_min'],
            'dopredu': rozvrh['dopredu'],
            'dny': rozvrh['dny'],
            # Pasmo, ve kterem se terminy vyrabeji. Kalendar v nem musi
            # i kreslit - jinak si Honza nastavi "od osmi do devíti"
            # a v mrizce mu vyskoci jine hodiny podle toho, z jakeho
            # pasma se na ni zrovna diva.
            'pasmo': self._hh_pasmo().zone,
        }

    @api.model
    def hh_ulozit_rozvrh(self, rozvrh):
        """Ulozi rozvrh a hned ho promitne do uz vyrobenych terminu.

        Samotne ulozeni parametru by se projevilo az u terminu, ktere
        teprve vzniknou - ty uz vyrobene by zustaly viset. Proto se
        po ulozeni jeste zahodi volne a preskrtnute terminy, ktere do
        noveho rozvrhu nepatri, a doplni se chybejici.

        Rezervovane terminy se nikdy nemazou. Kdyz nektery vypadne
        z rozvrhu, vrati se jejich seznam, aby se na ne dalo upozornit -
        je to domluveny hovor s konkretnim clovekem.
        """
        param = self.env['ir.config_parameter'].sudo()

        od = float(rozvrh.get('od', 8.0))
        do = float(rozvrh.get('do', 21.0))
        delka = int(rozvrh.get('delka', 45)) or 45
        dopredu = int(rozvrh.get('dopredu', 30)) or 30
        dny = [bool(d) for d in (rozvrh.get('dny') or [])]
        dny = (dny + [False] * 7)[:7]

        if do <= od:
            raise UserError(_('Konec dne musí být později než začátek.'))
        if not any(dny):
            raise UserError(_('Aspoň jeden den v týdnu musí zůstat zapnutý.'))

        param.set_param('honzahauzr_crm.rez_od', str(od))
        param.set_param('honzahauzr_crm.rez_do', str(do))
        param.set_param('honzahauzr_crm.rez_delka', str(delka))
        param.set_param('honzahauzr_crm.rez_dopredu', str(dopredu))
        for klic, zapnuto in zip(self.HH_DNY_KLICE, dny):
            param.set_param('honzahauzr_crm.%s' % klic, str(bool(zapnuto)))

        kolidujici = self._hh_srovnat_s_rozvrhem()
        vyrobeno = self.hh_vygenerovat()

        return {
            'vyrobeno': vyrobeno,
            'rezervovane_mimo': kolidujici,
        }

    @api.model
    def _hh_srovnat_s_rozvrhem(self):
        """Zahodi budouci terminy, ktere uz do rozvrhu nepatri.

        Maze jen volne a preskrtnute - preskrtnuty termin je jen skryty
        volny, takze kdyz cely den z rozvrhu zmizi, nema co drzet.
        Rezervovane zustavaji vzdy a jen se vrati jejich popis.
        """
        rozvrh = self._hh_rozvrh()
        pasmo = self._hh_pasmo()
        ted = fields.Datetime.now()

        budouci = self.sudo().search([('zacatek', '>=', ted)])

        k_smazani = self.browse()
        rezervovane_mimo = []

        krok = rozvrh['delka_min'] / 60.0

        for termin in budouci:
            mistni = pytz.utc.localize(termin.zacatek).astimezone(pasmo)
            hodina = mistni.hour + mistni.minute / 60.0

            # Sedi na mrizku noveho rozvrhu? Nestaci hlidat jen okno dne:
            # kdyz se zmeni delka hovoru, stary raster v okne zustane
            # a s novym se prekryva - v dni pak stoji 10:00 z hodinove
            # mrizky vedle 10:15 ze ctyricetipetiminutove.
            odsazeni = (hodina - rozvrh['od']) / krok if krok else -1
            na_mrizce = abs(odsazeni - round(odsazeni)) < 1e-6

            sedi = (
                rozvrh['dny'][mistni.weekday()]
                and hodina >= rozvrh['od'] - 1e-9
                and hodina + krok <= rozvrh['do'] + 1e-9
                and na_mrizce
                and abs(termin.delka - krok) < 1e-6
            )
            if sedi:
                continue

            if termin.stav == 'rezervovany':
                rezervovane_mimo.append({
                    'id': termin.id,
                    'kdy': mistni.strftime('%d.%m.%Y %H:%M'),
                    'jmeno': termin.jmeno or '',
                })
            else:
                k_smazani |= termin

        if k_smazani:
            k_smazani.unlink()

        return rezervovane_mimo

    @api.model
    def hh_rezervovat_rucne(self, termin_id, udaje):
        """Zapise, ze si termin nekdo domluvil mimo web.

        Prochazi to stejnou cestou jako rezervace z webu, takze se
        zaroven zalozi nebo dohleda prilezitost v CRM. Potvrzovaci
        e-mail se ale neposila - hovor uz je domluveny primo a druha
        zprava by pusobila zmatecne.
        """
        termin = self.browse(termin_id)
        termin.check_access('write')

        jmeno = (udaje.get('jmeno') or '').strip()
        email = (udaje.get('email') or '').strip()
        if not jmeno:
            raise UserError(_('Bez jména nevím, s kým ten hovor je.'))

        if termin.stav == 'rezervovany':
            # Uprava uz zapsane rezervace - jen se prepisi udaje.
            termin.write({
                'jmeno': jmeno,
                'email': email,
                'telefon': (udaje.get('telefon') or '').strip(),
                'poznamka': udaje.get('poznamka') or False,
            })
            return True

        if termin.stav not in ('volny', 'zablokovany'):
            raise UserError(_('Tenhle termín se rezervovat nedá.'))

        lead = termin._hh_najit_lead(
            jmeno, email, (udaje.get('telefon') or '').strip(),
            udaje.get('poznamka'))

        termin.write({
            'stav': 'rezervovany',
            'jmeno': jmeno,
            'email': email,
            'telefon': (udaje.get('telefon') or '').strip(),
            'poznamka': udaje.get('poznamka') or False,
            'lead_id': lead.id if lead else False,
            'partner_id': lead.partner_id.id if lead and lead.partner_id else False,
            'zrusovaci_klic': termin._hh_novy_klic(),
        })
        return True

    @api.model
    def hh_zrusit_rucne(self, termin_id):
        """Vrati rezervovany termin zpatky mezi volne."""
        termin = self.browse(termin_id)
        termin.check_access('write')
        termin.write({
            'stav': 'volny',
            'jmeno': False,
            'email': False,
            'telefon': False,
            'poznamka': False,
            'lead_id': False,
            'partner_id': False,
            'zrusovaci_klic': False,
        })
        return True
