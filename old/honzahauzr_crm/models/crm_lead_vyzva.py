# -*- coding: utf-8 -*-
"""Tridenni vyzva: postupne odemykani dnu a e-maily k nim.

Vsechna tri videa lezi na jedne strance /zpet-do-zivota/vyzva. Den 1
je dostupny hned po registraci, Den 2 po 24 hodinach a Den 3 po 48
hodinach - odpocet se pocita od okamziku registrace konkretniho
cloveka, ne od prvniho otevreni stranky v prohlizeci.

Proto ma kazdy ucastnik svuj klic. Odkaz v e-mailu ho nese s sebou,
takze odemykani funguje i na jinem zarizeni. Adresy videi se navic
vykresluji az na serveru a jen pro odemcene dny - do zdrojoveho kodu
stranky se tak zamcene video vubec nedostane.
"""
import logging
import math
import secrets

from datetime import timedelta

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Po kolika hodinach se ktery den odemyka
ODEMCENI = {1: 0, 2: 24, 3: 48}


class CrmLeadVyzva(models.Model):
    _inherit = 'crm.lead'

    hh_vyzva_klic = fields.Char(
        string='Klíč k výzvě',
        copy=False,
        index=True,
        help='Nahodny retezec v odkazu, pod kterym ucastnik vidi svoje '
             'odemcene dny. Bez nej by se dny nedaly navazat na konkretniho '
             'cloveka, kdyz otevre odkaz na jinem zarizeni.',
    )

    # Kazdy e-mail odejde jen jednou. Bez techhle prepinacu by nocni
    # ukol posilal totez porad dokola.
    hh_vyzva_mail1 = fields.Boolean(string='Odeslán e-mail Den 1', copy=False)
    hh_vyzva_mail2 = fields.Boolean(string='Odeslán e-mail Den 2', copy=False)
    hh_vyzva_mail3 = fields.Boolean(string='Odeslán e-mail Den 3', copy=False)

    # ------------------------------------------------------------------
    # registrace
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        leady = super().create(vals_list)
        for lead in leady:
            if lead.hh_zdroj != 'vyzva':
                continue
            lead.hh_vyzva_klic = secrets.token_urlsafe(24)
            # Aby clovek po odeslani formulare rovnou videl Den 1, i kdyz
            # se k e-mailu jeste nedostal.
            try:
                if request:
                    request.session['hh_vyzva_lead'] = lead.id
            except Exception:
                # Mimo webovy pozadavek (import, shell) zadna relace neni.
                pass
            # E-mail se zamerne neposila. Honza si po registraci sam
            # rozhodne, co a kdy clovek dostane - stejne jako u odberu
            # novinek. Kdyby odesel automaticky, prisel by lidem odkaz
            # na video driv, nez se na nej Honza vubec podival.
            #
            # Odesilani samo zustava: lead._hh_vyzva_poslat_den(1..3)
            # se da kdykoliv spustit rucne a stranka s videi funguje
            # dal, jakmile clovek dostane odkaz.
        return leady

    # ------------------------------------------------------------------
    # stav dnu
    # ------------------------------------------------------------------

    def hh_vyzva_zacatek(self):
        """Okamzik, od ktereho bezi odpocet dnu.

        Pocita se od vstupu do sloupce (hh_stupen_od), ne od registrace.
        Na stejnych hodinach bezi i rada e-mailu u sloupce, takze kdyz
        clovek dostane "Den 2 je odemceny", video na strance uz opravdu
        pusti. Kdyby stranka pocitala od registrace a Honza kartu
        presunul az za dva dny, mel by odemceno vsechno jeste driv,
        nez mu prvni e-mail vubec prisel.

        Nez karta do sloupce dojde, drzi se registrace - jinak by prvni
        den nesel otevrit vubec.
        """
        self.ensure_one()
        ted = fields.Datetime.now()
        # Mikrosekundy pryc: fields.Datetime.now() je zahazuje, zatimco
        # create_date si je necha. Bez srovnani vychazi zbyvajici cas
        # o hodinu vic - z rovnych 24 hodin se stane 25.
        return (self.hh_stupen_od or self.create_date or ted).replace(
            microsecond=0)

    def hh_vyzva_stav(self):
        """Vrati pro kazdy den, jestli uz je odemceny a za jak dlouho bude."""
        self.ensure_one()
        ted = fields.Datetime.now()
        od = self.hh_vyzva_zacatek()

        dny = []
        for cislo in (1, 2, 3):
            hodin = ODEMCENI[cislo]
            kdy = od + timedelta(hours=hodin)

            # Den 1 nema zadnou cekaci dobu, takze se neporovnava vubec.
            # fields.Datetime.now() zahazuje mikrosekundy, kdezto
            # create_date si je necha - registrace tim vychazi o zlomek
            # vteriny "v budoucnu" a prvni den by zustal zamceny.
            odemceno = hodin == 0 or ted >= kdy

            # Zaokrouhluje se nahoru, ale bez pricitani cele hodiny -
            # driv z 24 hodin vychazelo 25.
            zbyva = 0
            if not odemceno:
                zbyva = max(1, math.ceil((kdy - ted).total_seconds() / 3600))
            dny.append({
                'cislo': cislo,
                'odemceno': odemceno,
                'zbyva_hodin': zbyva,
                # Presny okamzik odemceni pro odpocet, ktery na strance
                # tika. Pouhe "zbyva 7 hodin" by po nacteni zamrzlo.
                #
                # Zakonceni Z je nutne: v databazi je cas v UTC, ale
                # bez nej by ho prohlizec vzal jako mistni a odpocet
                # by byl posunuty o cely casovy rozdil.
                'odemkne_se': kdy.isoformat() + 'Z' if not odemceno else '',
            })
        return dny

    # Odkaz jako pole, aby se dal napsat primo do e-mailu u sloupce -
    # tam se text vyhodnocuje pres {{ object.neco }} a metoda se do
    # nej dostat neda. Kazdy clovek ma vlastni klic, takze odkaz
    # otevre jeho vlastni stranku s prave odemcenymi dny.
    hh_vyzva_odkaz = fields.Char(
        string='Odkaz na výzvu',
        compute='_compute_hh_vyzva_odkaz',
        help='Osobní odkaz na stránku s videi. V e-mailu u sloupce se '
             'píše jako {{ object.hh_vyzva_odkaz }}.',
    )

    def _compute_hh_vyzva_odkaz(self):
        for lead in self:
            lead.hh_vyzva_odkaz = lead._hh_vyzva_odkaz()

    def _hh_vyzva_odkaz(self):
        self.ensure_one()
        zaklad = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '').rstrip('/')
        if not self.hh_vyzva_klic:
            return '%s/zpet-do-zivota/vyzva' % zaklad
        return '%s/zpet-do-zivota/vyzva?k=%s' % (zaklad, self.hh_vyzva_klic)

    # ------------------------------------------------------------------
    # e-maily ke dnum
    # ------------------------------------------------------------------

    def _hh_vyzva_poslat_den(self, cislo):
        """Posle e-mail k danemu dni. Kazdy jen jednou."""
        self.ensure_one()

        pole = 'hh_vyzva_mail%s' % cislo
        if self[pole]:
            return
        prijemce = self.email_from or self.partner_id.email
        if not prijemce:
            return

        jmeno = (self.contact_name or '').strip()
        osloveni = ('Ahoj %s,' % jmeno) if jmeno else 'Ahoj,'
        odkaz = self._hh_vyzva_odkaz()

        texty = {
            1: (
                'Den 1 je pro tebe připravený',
                '<p>%s</p>'
                '<p>jsi ve výzvě <b>Z autopilota zpět do života</b>. '
                'První den na tebe čeká hned teď.</p>'
                '<p><b>Den 1 &#8211; Zrcadlo a pravda.</b> Uvidíš, kde dnes '
                'stojíš, a vybereš oblast, kterou už nechceš ignorovat.</p>'
                '<p><a href="%s">Otevřít výzvu</a></p>'
                '<p>Zítra ve stejnou dobu se ti na téže stránce odemkne '
                'Den 2.</p>'
                '<p>Honza Hauzr</p>' % (osloveni, odkaz)
            ),
            2: (
                'Den 2 je odemčený',
                '<p>%s</p>'
                '<p><b>Den 2 &#8211; Důkaz.</b> Definuješ malý konkrétní '
                'závazek, kterým začneš obnovovat respekt k sobě.</p>'
                '<p><a href="%s">Otevřít výzvu</a></p>'
                '<p>Honza Hauzr</p>' % (osloveni, odkaz)
            ),
            3: (
                'Den 3 je odemčený',
                '<p>%s</p>'
                '<p><b>Den 3 &#8211; Tvůj tah.</b> Pojmenuješ autopilota, '
                'který tě drží na místě, a uvidíš svůj další krok.</p>'
                '<p><a href="%s">Otevřít výzvu</a></p>'
                '<p>Honza Hauzr</p>' % (osloveni, odkaz)
            ),
        }
        predmet, telo = texty[cislo]

        try:
            # Kdyz uz zprava k tomuhle dni lezi ve fronte po nepovedenem
            # pokusu, zkusi se znovu ona. Jinak by kazda hodinova uloha
            # zalozila dalsi kus a ve fronte by se hromadily kopie.
            zprava = self.env['mail.mail'].sudo().search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', self.id),
                ('subject', '=', predmet),
                ('state', '=', 'exception'),
            ], limit=1)
            if not zprava:
                zprava = self.env['mail.mail'].sudo().create({
                    'subject': predmet,
                    'body_html': telo,
                    'email_from': (self.company_id.email_formatted
                                   or self.env.company.email_formatted
                                   or self.env.user.email_formatted),
                    'email_to': prijemce,
                    'model': 'crm.lead',
                    'res_id': self.id,
                    'auto_delete': False,
                })
            zprava.send()

            # Priznak az kdyz zprava opravdu odesla. Drive se nastavoval
            # vzdycky - i kdyz posta prave nejela a zprava skoncila ve
            # stavu "exception". Takovy den uz se nikdy nerozeslal
            # a clovek se o nem nedozvedel.
            if zprava.state != 'exception':
                self[pole] = True
            else:
                _logger.warning(
                    'Honza Hauzr: e-mail Den %s pro lead %s neodesel '
                    '(%s), zkusi se znovu pri dalsim behu.',
                    cislo, self.id, (zprava.failure_reason or '').strip()[:120])
        except Exception as chyba:
            # E-mail nesmi shodit registraci ani nocni ukol.
            _logger.warning(
                'Honza Hauzr: e-mail Den %s pro lead %s se nepodaril: %s',
                cislo, self.id, chyba)

    @api.model
    def _hh_vyzva_rozeslat(self):
        """Nocni ukol: rozesle e-maily ke Dni 2 a Dni 3.

        Bere se cas registrace kazdeho cloveka zvlast, takze kdo se
        prihlasil v poledne, dostane druhy den take v poledne.
        """
        ted = fields.Datetime.now()
        for cislo in (2, 3):
            hranice = ted - timedelta(hours=ODEMCENI[cislo])

            # Stejny okamzik, od ktereho odemyka stranka - viz
            # hh_vyzva_zacatek(). Tedy vstup do sloupce, a dokud karta
            # do sloupce nedosla, registrace.
            #
            # Drive se tu hledalo jen podle create_date. Kdyz Honza
            # kartu presunul pozdeji nez v okamziku registrace, obojí
            # se rozeslo: na strance byl Den 2 jeste zamceny, ale
            # e-mail uz tvrdil, ze je odemceny - nebo naopak clovek
            # mel den odemceny a zadnou zpravu nedostal.
            leady = self.sudo().search([
                ('hh_zdroj', '=', 'vyzva'),
                ('hh_vyzva_mail%s' % cislo, '=', False),
                ('active', '=', True),
                '|',
                    '&', ('hh_stupen_od', '!=', False),
                         ('hh_stupen_od', '<=', hranice),
                    '&', ('hh_stupen_od', '=', False),
                         ('create_date', '<=', hranice),
            ])
            for lead in leady:
                lead._hh_vyzva_poslat_den(cislo)
            if leady:
                _logger.info('Honza Hauzr: rozeslan Den %s na %s adres.',
                             cislo, len(leady))
        return True

    # ------------------------------------------------------------------
    # rozpoznani ucastnika na webu
    # ------------------------------------------------------------------

    # Jak dlouho si prohlizec pamatuje, kdo je. Rok: vyzva trva tri dny,
    # ale lidi se k videim vraceji i pozdeji a nikdo nechce znovu hledat
    # e-mail s odkazem.
    HH_COOKIE = 'hh_vyzva_klic'
    HH_COOKIE_DOBA = 365 * 24 * 60 * 60

    @api.model
    def _hh_vyzva_ucastnik(self, klic=None):
        """Najde ucastnika, ktery si stranku prave otevrel.

        Zkousi se tri zdroje v tomhle poradi:
          1. klic v adrese (?k=...) - nese ho odkaz z e-mailu a funguje
             na jakemkoliv zarizeni,
          2. susenka v prohlizeci - clovek se vrati i bez odkazu,
          3. relace - hned po odeslani formulare, nez prijde e-mail.

        Jakmile je clovek rozpoznan, klic se ulozi do susenky, takze
        priste uz odkaz hledat nemusi.
        """
        if not request:
            return self.browse()

        # Nahled "zamceno" znamena divat se na stranku ocima cloveka,
        # ktery jeste nedostal zadny e-mail. Staci proto zapomenout,
        # koho zname - zbytek stranky uz se podle toho zaridi sam,
        # vcetne hlasky "Nevim, kdo jsi" i zamceneho kalendare.
        if self._hh_nahled() == 'zamceno':
            return self.browse()

        # Snippet se na ucastnika pta u kazdeho ze tri dnu zvlast.
        # Bez teto pameti by to znamenalo tri stejne dotazy do databaze
        # pri kazdem nacteni stranky.
        if klic is None and hasattr(request, 'hh_vyzva_ucastnik'):
            return request.hh_vyzva_ucastnik

        Lead = self.sudo()
        klic = klic or request.params.get('k') or request.httprequest.cookies.get(
            self.HH_COOKIE)

        nalezeny = Lead.browse()

        if klic:
            lead = Lead.search([('hh_vyzva_klic', '=', klic)], limit=1)
            if lead:
                nalezeny = lead

        if not nalezeny:
            lead_id = request.session.get('hh_vyzva_lead')
            if lead_id:
                lead = Lead.browse(lead_id).exists()
                if lead and lead.hh_zdroj == 'vyzva':
                    nalezeny = lead

        if nalezeny:
            self._hh_vyzva_zapamatovat(nalezeny)

        request.hh_vyzva_ucastnik = nalezeny
        return nalezeny


    # ------------------------------------------------------------------
    # nahled pro kontrolu stranky
    # ------------------------------------------------------------------

    # Prepinac, kterym jde stranku vyzvy prohlednout z obou stran -
    # zamcenou tak, jak ji vidi clovek pred prvnim e-mailem, i celou
    # odemcenou s videi a kalendarem. Je to nastroj na ukazovani
    # rozdelane prace, ne soucast webu.
    #
    # Zapina se systemovym parametrem honzahauzr_crm.nahled_vyzvy.
    # Bez nej se prepinac nezobrazi a volba v relaci se ignoruje,
    # takze na ostrem webu nejde videa odemknout ani tim, ze by nekdo
    # adresu uhodl. Pred spustenim na ostro staci parametr nezakladat.
    HH_NAHLED_PARAMETR = 'honzahauzr_crm.nahled_vyzvy'
    HH_NAHLED_RELACE = 'hh_nahled'

    @api.model
    def _hh_nahled_povolen(self):
        """Je prepinac nahledu na tomhle webu vubec zapnuty?"""
        if not request:
            return False
        hodnota = self.env['ir.config_parameter'].sudo().get_param(
            self.HH_NAHLED_PARAMETR, '')
        return str(hodnota).strip().lower() not in ('', '0', 'false')

    @api.model
    def _hh_nahled(self):
        """Zvolena strana nahledu: 'odemceno', 'zamceno', 'odpocet',
        nebo None.

        None znamena bezne chovani - stranka se ridi tim, koho pozna.
        """
        if not self._hh_nahled_povolen():
            return None
        volba = request.session.get(self.HH_NAHLED_RELACE)
        return volba if volba in ('odemceno', 'zamceno', 'odpocet') else None

    # Poznavaci znamka zkusebnich karet z nahledu. V adrese se za ni
    # pridava nahodny kousek, takze kazdy prohlizec ma vlastni kartu
    # a lide si navzajem neprepisuji odpocet.
    HH_NAHLED_DOMENA = '@nahled.vlastni-rezie.invalid'
    HH_NAHLED_KARTA = 'hh_nahled_karta'

    @api.model
    def _hh_nahled_spustit_odpocet(self):
        """Udela z navstevnika cerstve prihlaseneho ucastnika vyzvy.

        Zalozi zkusebni kartu, nastavi jeji zacatek na ted a prihlasi
        ji do relace. Stranka se od te chvile chova presne tak, jak ji
        vidi clovek hned po odeslani formulare - Den 1 otevreny, Den 2
        a Den 3 s tikajicim odpoctem.

        Kazdy prohlizec dostane vlastni kartu, drzenou v relaci. Kdyby
        se sdilela jedna, dva lide by si pri soucasne ukazce navzajem
        posouvali odpocet na nulu. Pri opakovanem spusteni se karta
        z relace recykluje, takze v CRM nepribyva donekonecna.
        """
        if not request:
            return self.browse()

        Lead = self.sudo()

        lead = Lead.browse()
        ulozena = request.session.get(self.HH_NAHLED_KARTA)
        if ulozena:
            lead = Lead.browse(ulozena).exists()

        if not lead:
            # with_context kvuli tomu, aby zalozeni zkusebni karty
            # neposilalo Honzovi upozorneni na novou registraci.
            lead = Lead.with_context(hh_bez_upozorneni=True).create({
                'name': 'Náhled výzvy (zkušební)',
                'contact_name': 'Náhled',
                'email_from': secrets.token_hex(6) + self.HH_NAHLED_DOMENA,
                'hh_zdroj': 'vyzva',
            })
            request.session[self.HH_NAHLED_KARTA] = lead.id

        lead.write({
            'hh_stupen_od': fields.Datetime.now(),
            # Priznaky odeslanych e-mailu se mazou taky, jinak by
            # opakovana ukazka uz zadny e-mail neposlala.
            'hh_vyzva_mail1': False,
            'hh_vyzva_mail2': False,
            'hh_vyzva_mail3': False,
        })
        if not lead.hh_vyzva_klic:
            lead.hh_vyzva_klic = secrets.token_urlsafe(24)

        request.session['hh_vyzva_lead'] = lead.id
        return lead
    @api.model
    def _hh_vyzva_zapamatovat(self, lead):
        """Ulozi ucastnika do relace i do susenky."""
        if not request or not lead:
            return
        request.session['hh_vyzva_lead'] = lead.id
        if lead.hh_vyzva_klic:
            # set_cookie na odpovedi, ktera se teprve odesila - Odoo
            # ji drzi v request.future_response.
            request.future_response.set_cookie(
                self.HH_COOKIE, lead.hh_vyzva_klic,
                max_age=self.HH_COOKIE_DOBA, samesite='Lax')

    @api.model
    def _hh_vyzva_podle_emailu(self, email):
        """Zalozni cesta: clovek zada e-mail, kterym se prihlasil.

        Pouziva se, kdyz prijde z jineho zarizeni a odkaz z e-mailu
        nema po ruce. Hleda se jen mezi ucastniky vyzvy, takze se
        timhle zpusobem nedá dostat k nicemu jinemu.
        """
        email = (email or '').strip().lower()
        if not email:
            return self.browse()

        lead = self.sudo().search([
            ('hh_zdroj', '=', 'vyzva'),
            ('email_normalized', '=', email),
        ], order='create_date desc', limit=1)

        if lead:
            if not lead.hh_vyzva_klic:
                lead.hh_vyzva_klic = secrets.token_urlsafe(24)
            self._hh_vyzva_zapamatovat(lead)
            request.hh_vyzva_ucastnik = lead
        return lead
