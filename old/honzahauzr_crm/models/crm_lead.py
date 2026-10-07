# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

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
    hh_stupen_maily = fields.Char(
        string='Odeslané zprávy sloupce',
        copy=False,
        readonly=True,
        help='Cisla uz odeslanych zprav z rady, oddelena carkou.',
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

        stitek = self.env.ref(self.HH_STITKY.get(zdroj, ''),
                              raise_if_not_found=False)
        if stitek and stitek not in self.tag_ids:
            zapis['tag_ids'] = [(4, stitek.id)]

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

        zdroj = self.hh_zdroj or self._hh_uhodnout_zdroj()
        if not zdroj:
            return

        stitek = self.env.ref(self.HH_STITKY.get(zdroj, ''),
                              raise_if_not_found=False)
        if not stitek:
            return

        hodnoty = {}
        # Kdyz zdroj prisel jen z nazvu, dopise se i do pole, aby se
        # priste uz nehadal a dal se podle nej filtrovat.
        if not self.hh_zdroj:
            hodnoty['hh_zdroj'] = zdroj
        if stitek not in self.tag_ids:
            hodnoty['tag_ids'] = [(4, stitek.id)]
        if hodnoty:
            self.write(hodnoty)

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
        """Zahaji radu e-maily napsanou u stupne.

        Prvni zprava odejde hned, druha a treti az s odstupem - o ty se
        stara nocni, respektive hodinovy ukol _hh_rozeslat_navazujici.
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
            'hh_stupen_maily': '',
            'hh_odeslane_stupne_ids': [(4, stupen.id)],
        })

        self._hh_poslat_cast_rady(1)

    def _hh_poslat_cast_rady(self, cislo):
        """Odesle jednu zpravu z rady a poznamena si ji."""
        self.ensure_one()

        stupen = self.stage_id
        if not stupen:
            return False

        cast = stupen.hh_mail_cast(cislo)
        if not cast['zapnuto']:
            return False

        if str(cislo) in self._hh_odeslane_casti():
            return False

        prijemce = self.email_from or self.partner_id.email
        if not prijemce:
            return False

        if not self._hh_poslat_email_stupne(stupen, prijemce, cast):
            return False

        odeslane = self._hh_odeslane_casti() | {str(cislo)}
        self.sudo().hh_stupen_maily = ','.join(sorted(odeslane))
        return True

    def _hh_odeslane_casti(self):
        self.ensure_one()
        return {c for c in (self.hh_stupen_maily or '').split(',') if c}

    @api.model
    def _hh_rozeslat_navazujici(self):
        """Hodinovy ukol: rozesle druhou a treti zpravu, az prijde jejich cas.

        Po hodinach, ne jednou za noc: odpocet je navazany na okamzik,
        kdy karta do sloupce vstoupila, zvlast za kazdeho cloveka. Kdo
        se prihlasil v poledne, ma dalsi den dostat take kolem poledne.
        """
        ted = fields.Datetime.now()
        odeslano = 0

        for cislo in (2, 3):
            stupne = self.env['crm.stage'].search([
                ('hh_mail%s_enabled' % cislo, '=', True),
            ])
            if not stupne:
                continue

            leady = self.sudo().search([
                ('stage_id', 'in', stupne.ids),
                ('hh_stupen_od', '!=', False),
                ('active', '=', True),
            ])
            for lead in leady:
                cast = lead.stage_id.hh_mail_cast(cislo)
                kdy = lead.hh_stupen_od + timedelta(days=cast['po_dnech'])
                if ted < kdy:
                    continue
                if lead._hh_poslat_cast_rady(cislo):
                    odeslano += 1

        if odeslano:
            _logger.info(
                'Honza Hauzr CRM: rozeslano %s navazujicich zprav.', odeslano)
        return True

    def _hh_poslat_email_stupne(self, stupen, prijemce, cast=None):
        if cast is None:
            cast = stupen.hh_mail_cast(1)
        try:
            sablona = self.env['mail.render.mixin'].sudo()
            predmet = sablona._render_template(
                cast['predmet'] or '', 'crm.lead', [self.id],
                engine='inline_template',
            )[self.id]
            telo = sablona._render_template(
                cast['telo'] or '', 'crm.lead', [self.id],
                engine='inline_template',
            )[self.id]

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
                'Honza Hauzr CRM: e-mail stupne %s se nepodarilo odeslat: %s',
                stupen.name, chyba)
            return False
