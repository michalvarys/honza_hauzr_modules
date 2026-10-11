# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)

# Editor z Email Marketingu hleda tuhle kostru. Bez ni bere zpravu
# jako prazdnou a misto textu nabidne galerii predloh.
KOSTRA_EDITORU = """<div class="o_layout oe_styling_vr">
  <div class="container o_mail_wrapper o_mail_wrapper_td">
    <div class="col o_mail_no_options o_mail_wrapper_td oe_structure o_editable">
%s
    </div>
  </div>
</div>"""


class HhMailStitek(models.Model):
    """Stitek, ktery drzi pohromade jednu radu e-mailu.

    Stitek je cela rada: "Tridenni vyzva", "Po rezervaci", "Po
    nakupu". U sloupce se pak uz nevybiraji jednotlive zpravy, jen
    se k nemu prihodi stitek - a odejde vsechno, co pod nej patri.

    Nejsou to stitky prilezitosti (crm.tag) schvalne: ty rikaji,
    odkud clovek prisel, a michat mezi ne nazvy e-mailovych rad by
    ten seznam zneprehlednilo.
    """

    _name = 'hh.mail.stitek'
    _description = 'Štítek e-mailů'
    _order = 'name'

    name = fields.Char(string='Název', required=True, translate=True)
    color = fields.Integer(string='Barva')

    prodejni = fields.Boolean(
        string='Prodejní řada',
        help='Nabídka, ne provozní zpráva. U takové se před každým '
             'odesláním navíc ověří, jestli to má ještě smysl:\n\n'
             '• kdo má domluvený hovor, další nabídku nedostane\n'
             '• zaškrtnuté „Pozastavit prodejní e-maily“ na kartě '
             'řadu zastaví, dokud to nevyřídíš\n'
             '• vypnuté „Rezervace jsou otevřené“ v nastavení ji '
             'pozastaví celou, ať nikomu nechodí pozvánka na '
             'zavřený kalendář\n\n'
             'Provozních řad (dny výzvy, uvítání, potvrzení '
             'rezervace) se to netýká — ty musí dojít vždycky. '
             'Odhlášení platí pro všechny bez ohledu na tenhle '
             'přepínač.',
    )

    mail_ids = fields.One2many(
        'hh.mail.sablona', 'stitek_id', string='E-maily')
    mail_count = fields.Integer(
        string='Počet e-mailů', compute='_compute_mail_count')

    @api.depends('mail_ids.zapnuto')
    def _compute_mail_count(self):
        for stitek in self:
            stitek.mail_count = len(stitek.mail_ids.filtered('zapnuto'))

    _sql_constraints = [
        ('nazev_jedinecny', 'UNIQUE(name)', 'Takový štítek už existuje.'),
    ]


class HhMailSablona(models.Model):
    """Jeden pripraveny e-mail: co se posila, pod jakym stitkem a kdy.

    Driv se predmet a telo psaly primo u sloupce, a to ve trech
    pevnych trojicich poli. Vic nez tri zpravy nesly a stejny text
    ve dvou radach se musel psat dvakrat.

    Odpocet "po kolika dnech" bezi od okamziku, kdy karta do sloupce
    vstoupila, zvlast za kazdeho cloveka. Kdo se prihlasi v poledne,
    dostane dalsi zpravu take kolem poledne - kazdy si jede vlastni
    radu od sveho vlastniho zacatku, ne podle spolecneho kalendare.

    Zamerne to neni mail.template z Odoo: ten ma pres tricet poli
    (model, jazyk, server, pravidla mazani) a schovava se v technickem
    nastaveni. Tady staci nazev, stitek, kdy, predmet a text.
    """

    _name = 'hh.mail.sablona'
    _description = 'E-mail'
    # Pod sebou tak, jak chodi: nejdriv podle rady, uvnitr ni podle dne.
    _order = 'stitek_id, po_dnech, id'

    name = fields.Char(
        string='Název',
        required=True,
        translate=True,
        help='Jen pro tebe, ať e-mail najdeš v seznamu. '
             'Příjemci se neukáže.',
    )
    stitek_id = fields.Many2one(
        'hh.mail.stitek',
        string='Štítek',
        required=True,
        ondelete='restrict',
        index=True,
        # Bez group_expand ukazuje seskupeny seznam jen rady, ve
        # kterych uz nejaka zprava je. Prazdna rada se v knihovne
        # vubec neobjevila, takze nebylo poznat, ze existuje a ze
        # se do ni da psat.
        group_expand='_hh_vsechny_stitky',
        help='Řada, do které zpráva patří. U sloupce pak stačí '
             'přihodit tenhle štítek a odejde všechno, co pod něj spadá.',
    )

    def action_hh_zmenit_sablonu(self):
        """Vyprazdni telo, aby sel vybrat jiny vzhled.

        Galerii predloh ukazuje editor z Email Marketingu jen tehdy,
        kdyz je zprava prazdna - jina cesta, jak uz zvolenou predlohu
        vymenit, v nem neni.

        Maze se i preklad. Obycejny zapis prepise jen zakladni jazyk
        a v ceske administraci by se dal ukazoval puvodni text, takze
        by se galerie neobjevila.
        """
        self.ensure_one()
        jazyky = [l.code for l in self.env['res.lang'].sudo().search([('active', '=', True)])]
        self.write({'body_arch': False, 'body_html': False})
        for pole in ('body_arch', 'body_html'):
            self.update_field_translations(pole, {k: '' for k in jazyky})
        # Formular se musi nacist znovu, jinak editor drzi stary obsah.
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def _hh_vsechny_stitky(self, stitky, domena):
        return self.env['hh.mail.stitek'].search([], order='name')

    def _hh_text_pro(self, lead=None):
        """Text zprávy v jazyce, ve kterém opravdu něco je.

        Text i předmět jsou překládaná pole. Zprávu ale nepíše nikdo
        v angličtině - Honza ji napíše česky a anglická verze zůstane
        prázdná. Hodinová úloha přitom běží v základním jazyce, takže
        by si sáhla právě pro to prázdno a odeslala prázdný e-mail.
        Stalo se to u uvítací zprávy Dne 1, která má 20 tisíc znaků
        v češtině a v angličtině nic.

        Bere se proto první jazyk, ve kterém text opravdu je: jazyk
        příjemce, pak jazyk firmy, pak zbytek.
        """
        self.ensure_one()

        poradi = []
        if lead is not None and lead.partner_id.lang:
            poradi.append(lead.partner_id.lang)
        poradi.append(self.env.company.partner_id.lang)
        poradi.append(self.env.lang)
        poradi += [l.code for l in self.env['res.lang'].sudo().search(
            [('active', '=', True)])]

        videne = set()
        for jazyk in [j for j in poradi if j]:
            if jazyk in videne:
                continue
            videne.add(jazyk)
            zprava = self.with_context(lang=jazyk)
            # Posila se verze se styly prepsanymi do znacek, kterou
            # vyrobil editor. Kdyz chybi, vezme se text z editoru.
            for pole in ('body_html', 'body_arch'):
                text = zprava[pole]
                if text and text.strip():
                    return text
        return ''

    @api.model
    def _hh_srovnat_sablony(self):
        """Doplní do zpráv patičku a vyhodí záložní odkaz pod tlačítkem.

        **Patička** se dřív skládala až při odesílání, takže ji Honza
        v editoru neviděl a nemohl si ověřit, že tam je. Teď stojí
        rovnou v textu zprávy. Odesílač ji přidává dál, ale jen když
        ve zprávě chybí - pojistka pro nově psané zprávy.

        **Záložní odkaz** pod tlačítkem začínal větou "Kdyby tlačítko
        nefungovalo". Tlačítko je obyčejný odkaz v tabulce a vykreslí
        ho i Outlook; ta věta jen podkopávala důvěru v něco, co
        funguje. Jedna výzva k akci ostatně odpovídá i zadání.

        Pouští se při každém upgradu a dělá jen to, co ještě není
        udělané - dá se to spustit opakovaně.
        """
        from .crm_lead_maily import PATICKA, DUVOD_VYZVA, ma_odhlaseni

        paticka = PATICKA % {
            'odesilatel': '{{ object.hh_paticka_odesilatel }}',
            'duvod': DUVOD_VYZVA,
            'odhlaseni': '{{ object.hh_odkaz_odhlaseni }}',
        }

        jazyky = [l.code for l in self.env['res.lang'].sudo().search(
            [('active', '=', True)])]
        doplneno, oriznuto = 0, 0

        for zprava in self.sudo().with_context(active_test=False).search([]):
            for pole in ('body_html', 'body_arch'):
                nove = {}
                for jazyk in jazyky:
                    # Cte se po jazycich prez kontext, ne pres
                    # get_field_translations: ten vraci u prekladaneho
                    # pole zdrojovy termin, a kde je zakladni jazyk
                    # prazdny, vratil by prazdno a zprava by se
                    # preskocila.
                    # str() je nutne: pole Html vraci Markup a ten by
                    # pri spojeni s obycejnym retezcem druhou stranu
                    # zaescapoval - paticka by se do zpravy vypsala
                    # jako zdrojovy kod misto odkazu.
                    text = str(zprava.with_context(lang=jazyk)[pole] or '')
                    if not text:
                        continue
                    puvodni = text
                    text = self._hh_bez_escapovane_paticky(text)
                    text = self._hh_bez_zalozniho_odkazu(text)
                    # Adresy kalendare a vyzvy jsou pro vsechny
                    # stejne, takze zastupny text nema co resit -
                    # v editoru jen zakryval, kam tlacitko vede.
                    # Odkaz do vyzvy s osobnim klicem
                    # ({{ object.hh_vyzva_odkaz }}) ani odhlaseni se
                    # tohle netyka, ty se u kazdeho lisi.
                    text = text.replace(
                        '{{ object.hh_odkaz_rezervace }}', '/uvodni-hovor')
                    text = text.replace(
                        '{{ object.hh_vyzva_zaklad }}/zpet-do-zivota',
                        '/zpet-do-zivota')
                    if text != puvodni:
                        oriznuto += 1
                    if not ma_odhlaseni(text):
                        text = text + paticka
                        doplneno += 1
                    if text != puvodni:
                        nove[jazyk] = text
                if nove:
                    # Jen preklady, zadny write na pole: ten by
                    # u zpravy s prazdnym zakladnim jazykem prepsal
                    # ceskou verzi prazdnem.
                    zprava.update_field_translations(pole, nove)

        if doplneno or oriznuto:
            _logger.info(
                'Honza Hauzr CRM: paticka doplnena %sx, zalozni odkaz '
                'odstranen %sx.', doplneno, oriznuto)
        return doplneno, oriznuto

    @api.model
    def _hh_bez_escapovane_paticky(self, text):
        """Uklid po patickce, ktera se ulozila jako zdrojovy kod.

        Pole Html vraci Markup a ten pri spojeni s obycejnym
        retezcem druhou stranu zaescapuje. Nez se to chytlo, stihla
        se takova paticka ulozit - ve zprave by se misto odkazu
        vypsaly znacky. Pozna se podle escapovaneho zacatku tabulky,
        za kterym nekde dal lezi zastupny text odhlaseni.
        """
        ZACATEK = '&lt;table role=&#34;presentation&#34;'
        i = text.find(ZACATEK)
        if i == -1 or 'hh_odkaz_odhlaseni' not in text[i:]:
            return text
        return text[:i]

    @api.model
    def _hh_bez_zalozniho_odkazu(self, text):
        """Vyhodi radek tabulky se zalozním odkazem pod tlacitkem.

        Pracuje nad retezcem, ne nad rozebranym HTML: pretazeni
        dokumentu pres parser by prepsalo cely zbytek zpravy
        a u Honzovy predlohy z galerie to nestoji za riziko.
        Nasi sablony maji ten odkaz v jednom <tr>, takze se najde
        veta a odstrani se radek, ve kterem lezi.
        """
        VETA = 'Kdyby tlačítko nefungovalo'
        while VETA in text:
            i = text.find(VETA)
            zacatek = text.rfind('<tr', 0, i)
            konec = text.find('</tr>', i)
            if zacatek == -1 or konec == -1:
                break
            text = text[:zacatek] + text[konec + len('</tr>'):]
        return text

    @api.model
    def _hh_stitek_vyzvy(self):
        """Řada e-mailů třídenní výzvy, ať se jmenuje jakkoliv.

        Na lokále je štítek "3denní výzva", na devu "3 denni vyzva".
        Hledat ho podle přesného názvu proto nestačí - tam by se
        třetí den tiše nedoplnil a nikdo by se to nedozvěděl.

        Jde se přes sloupec: ten se na obou místech jmenuje stejně
        a svou řadu si drží. Když ani tak nic, zkusí se štítek podle
        názvu bez diakritiky a mezer.
        """
        def klic(text):
            prevod = {'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
                      'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
                      'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z'}
            return ''.join(
                prevod.get(z, z) for z in (text or '').lower() if z != ' ')

        HLEDANE = klic('3denní výzva')

        for stupen in self.env['crm.stage'].sudo().search([]):
            if klic(stupen.name) == HLEDANE and stupen.hh_stitek_ids:
                return stupen.hh_stitek_ids[0]

        for stitek in self.env['hh.mail.stitek'].sudo().search([]):
            if klic(stitek.name) == HLEDANE:
                return stitek

        return self.env['hh.mail.stitek'].browse()

    @api.model
    def _hh_doplnit_den3(self):
        """Doplní do řady třídenní výzvy chybějící zprávu ke třetímu dni.

        Dny 1 a 2 v řadě byly, třetí ne - původní mechanismus, který
        ho měl natvrdo v kódu, je vypnutý. Člověk tedy dostal "Den 2
        je odemčený" a pak ticho, přestože se mu třetí den po
        48 hodinách na stránce odemkl.

        Pouští se při každém upgradu, ale zakládá jen jednou: když
        u řady nějaká zpráva s odstupem dvou dnů už je, nechá se být.
        Honza si text může přepsat a tohle mu ho nepřepíše zpátky.
        """
        stitek = self._hh_stitek_vyzvy()
        if not stitek:
            return False

        if self.sudo().with_context(active_test=False).search_count([
                ('stitek_id', '=', stitek.id), ('po_dnech', '=', 2)]):
            return False

        # Bez 'rb' a rucniho dekodovani by se soubor precetl
        # v kodovani systemu a ceska diakritika by se rozsypala.
        with tools.file_open(
                'honzahauzr_crm/data/mail_vyzva_den3.html',
                mode='rb') as soubor:
            telo = soubor.read().decode('utf-8')

        zprava = self.sudo().create({
            'name': 'vyzva den 3',
            'stitek_id': stitek.id,
            'po_dnech': 2,
            'predmet': 'Den 3 je odemčený',
            'body_html': telo,
            'body_arch': KOSTRA_EDITORU % telo,
        })
        # Prekladana pole: obycejny zapis plni jen zakladni jazyk
        # a ceska administrace by ukazovala prazdnou zpravu.
        jazyky = [l.code for l in self.env['res.lang'].sudo().search(
            [('active', '=', True)])]
        for pole, hodnota in (('body_html', telo),
                              ('body_arch', KOSTRA_EDITORU % telo)):
            zprava.update_field_translations(
                pole, {k: hodnota for k in jazyky})
        return zprava.id
    po_dnech = fields.Integer(
        string='Po (dnech)',
        default=1,
        required=True,
        help='Kolik dní po vstupu do sloupce zpráva odejde.\n'
             '0 = hned, jakmile tam karta přijde.\n'
             '1 = další den, 2 = třetí den a tak dál.\n\n'
             'Počítá se zvlášť u každého člověka, od chvíle, kdy '
             'jeho karta do sloupce vstoupila.',
    )
    zapnuto = fields.Boolean(
        string='Odesílat',
        default=True,
        help='Vypnutá zpráva zůstane v řadě, jen se nikomu nepošle. '
             'Hodí se, když ji chceš dočasně vynechat a nechtěl bys '
             'ji psát znovu.',
    )

    predmet = fields.Char(
        string='Předmět',
        required=True,
        translate=True,
        help='Co uvidí příjemce v poště jako předmět zprávy.',
    )
    preheader = fields.Char(
        string='Náhledový text',
        translate=True,
        help='Řádek, který schránka ukáže ve výpisu hned za '
             'předmětem. Když se nevyplní, vezme si schránka první '
             'slova ze zprávy - u nás popisek loga.\n\n'
             'Do zprávy se nevkládá viditelně, doplní se sám při '
             'odeslání. Zatím jen u prodejních řad.',
    )
    # Dve pole na jeden text, stejne jako to ma Email Marketing.
    # V telo_arch se zprava sklada - jsou v nem bloky, tridy a styly
    # editoru. Pri ulozeni z nej editor vyrobi telo: tytez bloky, ale
    # se styly prepsanymi primo do znacek. Posta totiz externi styly
    # zahazuje a bez toho by zprava dorazila rozsypana.
    # Nazvy poli jsou anglicke zamerne. Editor z Email Marketingu
    # si pole body_html hleda podle jmena primo v kodu widgetu
    # (fieldDependencies), takze pod jinym nazvem formular spadne
    # na "Invalid field 'body_html'".
    body_arch = fields.Html(
        string='Text',
        translate=True,
        sanitize=False,
        help='Zástupné texty, které se vyplní samy:\n'
             '{{ object.contact_name }} = jméno\n'
             '{{ object.email_from }} = e-mailová adresa\n'
             '{{ object.hh_vyzva_odkaz }} = osobní odkaz do výzvy',
    )
    body_html = fields.Html(
        string='Text pro odeslání',
        translate=True,
        sanitize=False,
        help='Verze, která opravdu odejde. Vyrobí ji editor sám '
             'při uložení, ručně se do ní nepíše.',
    )

    # Editor z Email Marketingu si sahne na mailing_model_id a cte
    # z nej rovnou druhou polozku (nazev modelu) bez kontroly, jestli
    # vubec neco je. Bez tohohle pole spadne formular na
    # "Cannot read properties of undefined". Nic jineho ho nepouziva -
    # zpravy se vzdycky posilaji prilezitosti.
    mailing_model_id = fields.Many2one(
        'ir.model',
        string='Model',
        readonly=True,
        default=lambda self: self.env['ir.model']._get_id('crm.lead'),
    )

    active = fields.Boolean(
        string='Aktivní',
        default=True,
        help='Archivovaná zpráva se přestane posílat a zmizí ze seznamu.',
    )

    kdy_popis = fields.Char(string='Kdy', compute='_compute_kdy_popis')

    @api.depends('po_dnech')
    def _compute_kdy_popis(self):
        for mail in self:
            mail.kdy_popis = 'hned' if not mail.po_dnech else (
                '%s. den' % mail.po_dnech)

    @api.depends('name', 'po_dnech')
    def _compute_display_name(self):
        for mail in self:
            kdy = 'hned' if not mail.po_dnech else '%s. den' % mail.po_dnech
            mail.display_name = '%s · %s' % (kdy, mail.name or '')

    _sql_constraints = [
        ('po_dnech_nezaporne', 'CHECK (po_dnech >= 0)',
         'Odstup zprávy nemůže být záporný.'),
    ]
