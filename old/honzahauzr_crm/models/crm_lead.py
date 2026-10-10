# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo.http import request
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    """Prilezitosti z webovych formularu: kontakt a e-mail podle stupne.

    Dve veci navic proti beznemu CRM:

    1. Formulare na webu posilaji e-mail do crm.lead. Tim ale vznikne
       jen prilezitost - adresa nikde nezustane jako kontakt, takze se
       kontakty nehromadi a neda se jim pozdeji poslat hromadny e-mail.
       Proto se po vzniku prilezitosti podle e-mailu dohleda kontakt,
       a kdyz zadny neexistuje, zalozi se novy.

    2. Kdyz prilezitost prejde do stupne, ktery ma vyplneny e-mail,
       odesle se. Text je primo na stupni (viz crm_stage.py).
    """

    _inherit = 'crm.lead'

    # Klic zdroje -> XML id stitku, ktery se prilezitosti nasadi.
    # Hodnoty klicu posilaji formulare na webu ve skrytem poli hh_zdroj.
    HH_STITKY = {
        'vyzva': 'honzahauzr_crm.tag_vyzva',
        'newsletter': 'honzahauzr_crm.tag_newsletter',
        'hovor': 'honzahauzr_crm.tag_hovor',
        'pdf': 'honzahauzr_crm.tag_pdf',
        'poptavka': 'honzahauzr_crm.tag_poptavka',
        'rezervace': 'honzahauzr_crm.tag_rezervace',
    }

    # Klic zdroje -> XML id seznamu adres v Email Marketingu.
    # Prihlaska nepada jen do nastenky, ale i sem: odtud se pak posila
    # hromadna zprava, aniz by se adresy musely vypisovat rucne nebo
    # exportovat z CRM.
    HH_SEZNAMY = {
        'newsletter': 'honzahauzr_crm.seznam_newsletter',
        'vyzva': 'honzahauzr_crm.seznam_vyzva',
        'hovor': 'honzahauzr_crm.seznam_hovor',
        'rezervace': 'honzahauzr_crm.seznam_rezervace',
        'pdf': 'honzahauzr_crm.seznam_pdf',
        'poptavka': 'honzahauzr_crm.seznam_poptavka',
    }

    # Zkratka webu, ktera se pripina k nazvu stitku. Odber novinek
    # vede z obou domen do jedne schranky, takze samotny "Newsletter"
    # na karte nerekne, odkud clovek prisel. Dva stitky vedle sebe to
    # rikaly taky, ale na karte se cetly hur nez jeden: "Newsletter HH".
    HH_ZKRATKY_WEBU = {
        'honzahauzr': 'HH',
        'vlastni_rezie': 'VR',
    }

    # Zalozni rozpoznani podle nazvu prilezitosti. Slouzi jen pro
    # prilezitosti, ktere prisly bez vyplneneho hh_zdroj - treba ze
    # starsiho formulare nebo z bloku poskladaneho v editoru Odoo.
    HH_PODLE_NAZVU = (
        ('výzva', 'vyzva'),
        ('newsletter', 'newsletter'),
        ('úvodní hovor', 'hovor'),
        ('rezervace', 'rezervace'),
        ('pdf', 'pdf'),
        ('poptávka', 'poptavka'),
    )

    hh_zdroj = fields.Selection(
        selection=[
            ('vyzva', '3denní výzva'),
            ('newsletter', 'Newsletter'),
            ('hovor', 'Úvodní hovor'),
            ('pdf', 'Stažení PDF'),
            ('poptavka', 'Poptávka z webu'),
            ('rezervace', 'Rezervace hovoru'),
        ],
        string='Odkud přišel',
        help='Ktery formular na webu prilezitost zalozil. Vyplnuje se '
             'automaticky ze skryteho pole ve formulari.',
    )

    hh_web = fields.Selection(
        selection=[
            ('honzahauzr', 'Honza Hauzr'),
            ('vlastni_rezie', 'Vlastní režie'),
        ],
        string='Z jakého webu',
        help='Ze ktereho webu clovek prisel. Odber novinek vede '
             'z obou do jedne schranky, takze bez tohohle pole by '
             'se nepoznaly od sebe. Vyplnuje se automaticky ze '
             'skryteho pole ve formulari.',
    )

    hh_odeslane_stupne_ids = fields.Many2many(
        'crm.stage',
        'hh_lead_odeslany_stupen_rel',
        'lead_id',
        'stage_id',
        string='Stupně, ze kterých už e-mail odešel',
        copy=False,
        help='Slouzi k tomu, aby tataz rada e-mailu nezacala znovu, kdyz '
             'se karta vrati o stupen zpet a zase dopredu.',
    )

    # Odkdy se pocita odstup navazujicich zprav. Nastavuje se pri vstupu
    # do sloupce, ne pri zalozeni prilezitosti - kdyz Honza kartu presune
    # az za tyden, ma rada zacit tehdy, ne zpetne.
    hh_stupen_od = fields.Datetime(
        string='Ve sloupci od',
        copy=False,
        readonly=True,
    )
    hh_odeslane_maily_ids = fields.Many2many(
        'hh.mail.sablona',
        'hh_lead_odeslany_mail_rel',
        'lead_id',
        'mail_id',
        string='Zprávy řady, které už odešly',
        copy=False,
        help='Pojistka proti dvojímu odeslání. Maže se při vstupu '
             'do nového sloupce, kdy řada začíná znovu.',
    )


    # ------------------------------------------------------------------
    # kontakt z e-mailu
    # ------------------------------------------------------------------

    # Kam prilezitost rovnou spadne podle toho, odkud prisla. Klice jsou
    # XML id stupnu z modulu crm, ne nazvy - Honza si sloupce v nastence
    # prejmenoval ("Chci odebirat", "3denni vyzva") a podle nazvu by to
    # po kazdem prejmenovani prestalo platit.
    HH_STUPNE = {
        'newsletter': 'crm.stage_lead1',
        'vyzva': 'crm.stage_lead2',
        # Kdo si rovnou domluvil hovor, patri mezi rezervace.
        'rezervace': 'crm.stage_lead3',
    }

    @api.model_create_multi
    def create(self, vals_list):
        # Kdo uz v boardu je, nedostane druhou kartu. Misto zalozeni
        # kopie se najde ta jeho, posune se do sloupce podle noveho
        # kroku a pribude stitek. Jeden clovek = jedna karta, stitky
        # drzi cestu, kterou k Honzovi prisel.
        #
        # Stejne se uz chova rezervace hovoru, viz hh_termin.py. Tohle
        # to same delaji i formulare na webu.
        zbyle = []
        nalezene = self.browse()
        for hodnoty in vals_list:
            lead = self._hh_najit_stavajici(hodnoty)
            if lead:
                lead._hh_prijmout_dalsi_krok(hodnoty)
                nalezene |= lead
            else:
                zbyle.append(hodnoty)

        leady = super().create(zbyle) if zbyle else self.browse()
        for lead in leady:
            lead._hh_oznacit_zdroj()
            lead._hh_zaradit_do_stupne()
            # Az po zarazeni podle hh_zdroj: kdyz formular posle
            # i nazev sekce, ma prednost a sloupec se pro ni
            # v pripade potreby zalozi.
            lead._hh_zaradit_do_sekce()
            lead._hh_doplnit_kontakt()
            lead._hh_upozornit()
        return nalezene | leady

    @api.model
    def _hh_najit_stavajici(self, hodnoty):
        """Karta stejneho cloveka, kdyz uz nejaka je.

        Hleda se jen u prilezitosti z webovych formularu - ty jedine
        posilaji hh_zdroj. Zaznam zalozeny rucne v CRM nebo importem
        se tim nedotkne: tam muze mit jeden clovek vic prilezitosti
        zamerne.
        """
        if not hodnoty.get('hh_zdroj'):
            return self.browse()
        email = (hodnoty.get('email_from') or '').strip()
        if not email:
            return self.browse()
        return self.sudo().search([
            ('email_from', '=ilike', email),
            ('active', '=', True),
        ], order='create_date desc', limit=1)

    def _hh_prijmout_dalsi_krok(self, hodnoty):
        """Prida stitek noveho kroku a posune kartu do jeho sloupce."""
        self.ensure_one()
        zdroj = hodnoty.get('hh_zdroj')

        zapis = {}

        # Clovek uz kartu ma. Kdyz se ted ozval z druhe domeny,
        # pribude dalsi stitek vedle toho puvodniho - at je videt,
        # odkud vsude prisel.
        # Zamerne se nebere self.hh_web: ten rika, odkud clovek prisel
        # poprve. Tenhle krok udelal tam, kde je prave ted.
        web = hodnoty.get('hh_web') or self._hh_web_ze_stranky()
        stitek = self._hh_stitek_pro(zdroj, web)
        if stitek and stitek not in self.tag_ids:
            zapis['tag_ids'] = [(4, stitek.id)]
        if not self.hh_web and hodnoty.get('hh_web'):
            zapis['hh_web'] = hodnoty['hh_web']

        self._hh_zaradit_do_seznamu(zdroj)

        # Chybejici udaje se doplni, vyplnene se neprepisuji - to, co
        # clovek napsal poprve, je stejne dobre jako to nove.
        for pole in ('contact_name', 'phone'):
            if hodnoty.get(pole) and not self[pole]:
                zapis[pole] = hodnoty[pole]

        # Posouva se jen dopredu. Kdo uz ma domluveny hovor a pak si
        # jeste zapne odber novinek, nema spadnout zpatky mezi odberatele.
        novy = self._hh_stupen_zdroje(zdroj)
        if novy and (not self.stage_id
                     or novy.sequence > self.stage_id.sequence):
            zapis['stage_id'] = novy.id

        if zapis:
            # Pres write kvuli e-mailu navazanemu na presun sloupce.
            self.sudo().write(zapis)

        # Clovek, ktery uz v nastence je a prijde pres novou sekci.
        # Sloupec pro ni jeste existovat nemusi.
        if hodnoty.get('hh_sekce'):
            self.sudo().hh_sekce = hodnoty['hh_sekce']
            self.sudo()._hh_zaradit_do_sekce()

    @api.model
    def _hh_stupen_zdroje(self, zdroj):
        xmlid = self.HH_STUPNE.get(zdroj)
        if not xmlid:
            return self.env['crm.stage']
        return self.env.ref(xmlid, raise_if_not_found=False) \
            or self.env['crm.stage']

    def _hh_zaradit_do_stupne(self):
        """Posune prilezitost rovnou do sloupce, ktery jejimu zdroji patri.

        Bez toho spadne vsechno do prvniho sloupce a Honza to musi
        pretahovat rucne, i kdyz je z formulare dopredu jasne, kam to
        ma jit.

        Kdyz uz prilezitost ve spravnem sloupci je, rada e-mailu se
        presto zahaji. Drive se nezahajila: rada visi na zmene
        stage_id a ta se u prvniho sloupce nekona, protoze tam karta
        vznikne rovnou. Na webu Honzy Hauzra, kde je prvnim sloupcem
        odber novinek, by tim padem uvitaci zprava neodesla vubec.
        """
        self.ensure_one()

        xmlid = self.HH_STUPNE.get(self.hh_zdroj)
        if not xmlid:
            return

        stupen = self.env.ref(xmlid, raise_if_not_found=False)
        if not stupen:
            return

        if self.stage_id == stupen:
            # Uz je na miste - presouvat neni co, ale radu e-mailu
            # je potreba zahajit rucne. Sama se spousti az pri zmene
            # stage_id, ke ktere tady nedojde.
            self._hh_ohlasit_stupen()
            return

        # Pres write, ne primym zapisem do pole - na presunu stupne visi
        # odesilani e-mailu napsaneho u sloupce a to se ma spustit i tady.
        self.write({'stage_id': stupen.id})

    # ------------------------------------------------------------------
    # stitek podle toho, odkud prilezitost prisla
    # ------------------------------------------------------------------

    def _hh_oznacit_zdroj(self):
        """Nasadi stitek podle formulare, ze ktereho prilezitost prisla.

        Bez nej se v CRM nepozna, jestli clovek prisel z tridenni vyzvy,
        z odberu novinek nebo z poptavky - vsechno vypada stejne a neda
        se to filtrovat ani na to navazat jinou komunikaci.
        """
        self.ensure_one()

        # Hada se jen tehdy, kdyz zarazeni neni dane odjinud. Kdyz
        # formular poslal nazev sekce, hadat se nema z ceho - nazev
        # "20denní výzva" obsahuje slovo vyzva a karta by k svemu
        # stitku dostala i stitek tridenni vyzvy.
        zdroj = self.hh_zdroj
        if not zdroj and not self.hh_sekce:
            zdroj = self._hh_uhodnout_zdroj()
        if not zdroj:
            return

        web = self.hh_web or self._hh_web_ze_stranky()
        stitek = self._hh_stitek_pro(zdroj, web)
        if not stitek:
            return

        hodnoty = {}
        if web and not self.hh_web:
            hodnoty['hh_web'] = web
        # Kdyz zdroj prisel jen z nazvu, dopise se i do pole, aby se
        # priste uz nehadal a dal se podle nej filtrovat.
        if not self.hh_zdroj:
            hodnoty['hh_zdroj'] = zdroj
        if stitek not in self.tag_ids:
            hodnoty['tag_ids'] = [(4, stitek.id)]
        if hodnoty:
            self.write(hodnoty)

        self._hh_zaradit_do_seznamu(zdroj)

    def _hh_zaradit_do_seznamu(self, zdroj):
        """Prida adresu do seznamu v Email Marketingu.

        Kontakt je jeden na adresu, at se clovek prihlasil kamkoliv -
        jen se mu pribaluji dalsi seznamy. Odhlaseni a blacklist si
        Email Marketing hlida sam, tohle do nich nesaha.
        """
        self.ensure_one()
        try:
            seznam = self.env.ref(self.HH_SEZNAMY.get(zdroj or '', ''),
                                  raise_if_not_found=False)
            adresa = (self.email_from or '').strip()
            if not seznam or not adresa:
                return

            Kontakt = self.env['mailing.contact'].sudo()
            kontakt = Kontakt.search([('email', '=ilike', adresa)], limit=1)
            if not kontakt:
                kontakt = Kontakt.create({
                    'name': self.contact_name or adresa,
                    'email': adresa,
                    'list_ids': [(4, seznam.id)],
                })
                return

            # Jmeno se doplni, az kdyz ho clovek nekde vyplnil -
            # u odberu novinek formular jmeno nema a prepsat uz znamy
            # nazev adresou by byl krok zpatky.
            if self.contact_name and kontakt.name != self.contact_name:
                if not kontakt.name or kontakt.name == adresa:
                    kontakt.name = self.contact_name

            if seznam not in kontakt.list_ids:
                kontakt.list_ids = [(4, seznam.id)]
        except Exception:
            # Zarazeni do seznamu nesmi nikdy shodit zalozeni
            # prilezitosti - ta je dulezitejsi.
            _logger.warning(
                'Honza Hauzr CRM: adresu %s se nepodarilo zaradit do '
                'seznamu (%s).', self.email_from, zdroj, exc_info=True)

    @api.model
    def _hh_web_ze_stranky(self):
        """Web, na kterem clovek prave ted formular odeslal.

        Bere se z pozadavku, ne z karty. Kdo uz je v CRM z newsletteru
        od Honzy Hauzra a pak se prihlasi do vyzvy na Vlastni rezii,
        ma u teto prihlasky dostat VR - rozhoduje misto, kde se
        prihlasil, ne historie karty.

        Mimo pozadavek (nocni ukol, rucne zalozena karta) vraci
        prazdno, aby se web nehadal.
        """
        try:
            if not request:
                return False
            web = getattr(request, 'website', None)
            return web.hh_kod if web else False
        except Exception:
            return False

    @api.model
    def _hh_stitek_pro(self, zdroj, web):
        """Stitek pro dvojici formular + web, treba "Newsletter HH".

        Zaklad je pripraveny stitek formulare. Kdyz je znamy i web,
        hleda se stitek s pripnutou zkratkou - a kdyz jeste neni,
        zalozi se, aby se barva i nazev daly v CRM prepsat.
        """
        zaklad = self.env.ref(self.HH_STITKY.get(zdroj or '', ''),
                              raise_if_not_found=False)
        if not zaklad:
            return self.env['crm.tag']

        zkratka = self.HH_ZKRATKY_WEBU.get(web or '')
        if not zkratka:
            return zaklad

        nazev = '%s %s' % (zaklad.name, zkratka)
        Stitek = self.env['crm.tag'].sudo()
        stitek = Stitek.search([('name', '=', nazev)], limit=1)
        if not stitek:
            stitek = Stitek.create({'name': nazev, 'color': zaklad.color})
        return stitek

    def _hh_uhodnout_zdroj(self):
        nazev = (self.name or '').lower()
        for kousek, zdroj in self.HH_PODLE_NAZVU:
            if kousek in nazev:
                return zdroj
        return False

    # ------------------------------------------------------------------
    # upozorneni na novou zpravu
    # ------------------------------------------------------------------

    def _hh_popis_zdroje(self):
        """Cesky nazev zdroje, stejny jako na stitku prilezitosti."""
        self.ensure_one()
        if not self.hh_zdroj:
            return ''
        popisky = dict(self._fields['hh_zdroj']._description_selection(self.env))
        return popisky.get(self.hh_zdroj, '')

    def _hh_upozornit(self):
        """Posle na nastavenou adresu upozorneni, ze nekdo projevil zajem.

        Adresa se zadava v CRM > Konfigurace > Nastaveni. Kdyz je prazdna,
        neposila se nic - zprava jen spadne do nastenky jako dosud.

        V predmetu i v tele je videt zdroj - tedy tentyz udaj, ktery nese
        barevny stitek na karte. Bez nej by z upozorneni nebylo poznat,
        jestli slo o registraci do vyzvy nebo o odber novinek, a muselo
        by se to pokazde dohledavat v CRM.
        """
        self.ensure_one()

        # Zkusebni karta z nahledu vyzvy se zaklada znovu pri kazde
        # ukazce - upozorneni na ni by Honzovi jen zaplnovalo schranku.
        if self.env.context.get('hh_bez_upozorneni'):
            return

        adresa = self.env['ir.config_parameter'].sudo().get_param(
            'honzahauzr_crm.notify_email')
        if not adresa:
            return

        zdroj = self._hh_popis_zdroje()
        kdo = self.contact_name or self.partner_name or self.email_from or 'neznámý'
        predmet = '%s: %s' % (zdroj or 'Nový zájem z webu', kdo)

        radky = [
            ('Odkud přišel', zdroj or self.name or '-'),
            ('Jméno', self.contact_name or self.partner_name or '-'),
            ('E-mail', self.email_from or '-'),
            ('Telefon', self.phone or '-'),
            ('Přišlo', fields.Datetime.context_timestamp(
                self, self.create_date or fields.Datetime.now()
            ).strftime('%d.%m.%Y %H:%M')),
        ]

        telo = (
            '<p style="font-size:15px"><b>%s</b> projevil zájem.</p>'
            % kdo
        )
        if zdroj:
            # Obdoba barevneho stitku z nastenky - at je zdroj videt hned,
            # jeste nez se clovek pusti do cteni udaju.
            telo += (
                '<p><span style="display:inline-block;padding:4px 12px;'
                'border-radius:999px;background:#8a5a2b;color:#fff;'
                'font-size:13px;font-weight:bold">%s</span></p>' % zdroj
            )
        telo += '<table cellpadding="4">%s</table>' % ''.join(
            '<tr><td><b>%s:</b></td><td>%s</td></tr>' % (popisek, hodnota)
            for popisek, hodnota in radky
        )
        if self.description:
            telo += '<p><b>Zpráva:</b></p>%s' % self.description

        odkaz = self._hh_odkaz_do_crm()
        if odkaz:
            telo += '<p><a href="%s">Otevřít v CRM</a></p>' % odkaz

        # Odpovedet na upozorneni ma jit rovnou tomu, kdo psal, ne sobe.
        try:
            self.env['mail.mail'].sudo().create({
                'subject': predmet,
                'body_html': telo,
                'email_from': (self.env.company.email_formatted
                               or self.env.user.email_formatted),
                'email_to': adresa,
                'reply_to': self.email_from or adresa,
                'model': 'crm.lead',
                'res_id': self.id,
                'auto_delete': False,
            }).send()
        except Exception as chyba:
            # Upozorneni nesmi shodit odeslani formulare na webu - kdyz
            # se neposle, navstevnik to nepozna a zprava v CRM zustane.
            _logger.warning(
                'Honza Hauzr CRM: upozorneni na novou zpravu se nepodarilo '
                'odeslat: %s', chyba)

    def _hh_odkaz_do_crm(self):
        zaklad = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not zaklad:
            return ''
        return '%s/odoo/crm/%s' % (zaklad.rstrip('/'), self.id)

    def _hh_doplnit_kontakt(self):
        self.ensure_one()

        # Kdyz uz kontakt ma, neni co resit. Bez e-mailu nemame podle
        # ceho hledat - takovou prilezitost necham byt.
        if self.partner_id or not self.email_from:
            return

        # email_normalized dopocitava Odoo samo a ma z adresy vytazenou
        # jen tu cast za spicatymi zavorkami. Kdyz je prazdny, adresa
        # neprosla kontrolou tvaru a kontakt z ni zakladat nebudeme.
        email = self.email_normalized
        if not email:
            return

        Kontakt = self.env['res.partner']
        kontakt = Kontakt.search([('email_normalized', '=', email)], limit=1)

        if not kontakt:
            hodnoty = {
                # Jmeno z formulare zname jen nekdy - jinak slouzi
                # jako nazev adresa, at kontakt neni bezejmenny.
                'name': self.contact_name or self.partner_name or email,
                'email': email,
            }
            # customer_rank pridavaji az moduly prodeje. Kdyz nainstalovane
            # nejsou, pole neexistuje a zapis by spadl - proto ta kontrola.
            # S nimi se kontakt objevi i v Prodej > Zakaznici.
            if 'customer_rank' in Kontakt._fields:
                hodnoty['customer_rank'] = 1
            kontakt = Kontakt.create(hodnoty)

        self.partner_id = kontakt

    # ------------------------------------------------------------------
    # e-mail podle stupne
    # ------------------------------------------------------------------

    def write(self, vals):
        vysledek = super().write(vals)
        if 'stage_id' in vals:
            for lead in self:
                lead._hh_ohlasit_stupen()
        return vysledek

    def _hh_ohlasit_stupen(self):
        """Zahaji radu e-mailu zarazenych u stupne.

        Zpravy s odstupem 0 odejdou hned, zbytek si vezme hodinovy
        ukol _hh_rozeslat_navazujici. Hned, a ne az pri nejakem behu
        ukolu: uvitaci zprava ma prijit v okamziku prihlaseni, ne
        treba o padesat minut pozdeji.
        """
        self.ensure_one()

        stupen = self.stage_id
        if not stupen:
            return

        # Kdyz uz rada z tohohle stupne jednou bezela, podruhe se
        # nezahajuje - jinak by prijemci chodila porad dokola pri
        # kazdem vraceni karty tam a zpet.
        if stupen in self.hh_odeslane_stupne_ids:
            return

        # Odpocet navazujicich zprav bezi od vstupu do sloupce.
        self.sudo().write({
            'hh_stupen_od': fields.Datetime.now(),
            'hh_odeslane_maily_ids': [(5, 0, 0)],
            'hh_odeslane_stupne_ids': [(4, stupen.id)],
        })

        for zprava in stupen.hh_maily_k_odeslani():
            if not zprava.po_dnech:
                self._hh_poslat_zpravu(zprava)
            else:
                # Serazene podle odstupu, takze dal uz jsou jen
                # zpravy do budoucna - o ty se postara hodinovy ukol.
                break

    def _hh_poslat_zpravu(self, zprava):
        """Odesle jednu zpravu z rady a poznamena si ji."""
        self.ensure_one()

        if not zprava.zapnuto:
            return False

        # Kazda zprava jen jednou. Bez tohohle by hodinovy ukol poslal
        # tutez zpravu pri kazdem behu, dokud je karta ve sloupci.
        if zprava in self.hh_odeslane_maily_ids:
            return False

        prijemce = self.email_from or self.partner_id.email
        if not prijemce:
            return False

        # Osobni odkaz na vyzvu ({{ object.hh_vyzva_odkaz }}) potrebuje
        # klic. Kdo prisel jinudy nez pres formular vyzvy, zadny nema -
        # bez tohohle by mu v e-mailu odesla adresa bez ?k=.
        self._hh_zajistit_klic()

        if not self._hh_poslat_email_stupne(self.stage_id, prijemce, zprava):
            return False

        self.sudo().hh_odeslane_maily_ids = [(4, zprava.id)]
        return True

    @api.model
    def _hh_rozeslat_navazujici(self):
        """Hodinovy ukol: rozesle zpravy rady, az prijde jejich cas.

        Po hodinach, ne jednou za noc: odpocet je navazany na okamzik,
        kdy karta do sloupce vstoupila, zvlast za kazdeho cloveka. Kdo
        se prihlasil v poledne, ma dalsi den dostat take kolem poledne.

        Zpravy s odstupem 0 uz odesly pri vstupu do sloupce, takze se
        tady preskakuji - jinak by se poslaly podruhe tem, kdo do
        sloupce prisli jeste pred tim, nez je Honza zaradil.
        """
        ted = fields.Datetime.now()
        odeslano = 0

        stupne = self.env['crm.stage'].search([('hh_stitek_ids', '!=', False)])
        for stupen in stupne:
            zpravy = stupen.hh_maily_k_odeslani().filtered('po_dnech')
            if not zpravy:
                continue

            leady = self.sudo().search([
                ('stage_id', '=', stupen.id),
                ('hh_stupen_od', '!=', False),
                ('active', '=', True),
            ])
            for lead in leady:
                for zprava in zpravy:
                    kdy = lead.hh_stupen_od + timedelta(days=zprava.po_dnech)
                    if ted < kdy:
                        # Zpravy jsou serazene podle odstupu, takze
                        # dalsi uz je jeste dal v budoucnu.
                        break
                    if lead._hh_poslat_zpravu(zprava):
                        odeslano += 1

        if odeslano:
            _logger.info(
                'Honza Hauzr CRM: rozeslano %s zprav z rad sloupcu.', odeslano)
        return True

    def _hh_poslat_email_stupne(self, stupen, prijemce, sablona_mailu):
        try:
            sablona = self.env['mail.render.mixin'].sudo()
            predmet = sablona._render_template(
                sablona_mailu.predmet or '', 'crm.lead', [self.id],
                engine='inline_template',
            )[self.id]
            # Posila se verze se styly prepsanymi do znacek, kterou
            # vyrobil editor. Kdyz zprava vznikla jinudy a ta verze
            # chybi, vezme se rovnou text z editoru.
            telo = sablona._render_template(
                sablona_mailu.body_html or sablona_mailu.body_arch or '',
                'crm.lead', [self.id],
                engine='inline_template',
            )[self.id]
            # Obrazky a odkazy se v editoru vkladaji relativne
            # (/theme_honzahauzr/...). V e-mailu by takova adresa nikam
            # nevedla, posta nema vuci cemu ji doplnit. Odoo na to ma
            # _replace_local_links, ktery pred ne doplni adresu webu.
            telo = sablona._replace_local_links(
                telo, base_url=self._hh_zaklad_vyzvy())

            posta = self.env['mail.mail'].sudo().create({
                'subject': predmet,
                'body_html': telo,
                'email_from': (self.company_id.email_formatted
                               or self.env.user.email_formatted),
                'email_to': prijemce,
                'model': 'crm.lead',
                'res_id': self.id,
                'auto_delete': False,
            })
            posta.send()
            return True
        except Exception as chyba:
            # E-mail nesmi nikdy shodit presun karty - kdyz se neodesle,
            # jen se to zapise do logu a prilezitost dojede do stupne.
            _logger.warning(
                'Honza Hauzr CRM: e-mail "%s" ze sloupce %s se nepodarilo '
                'odeslat: %s', sablona_mailu.name, stupen.name, chyba)
            return False
