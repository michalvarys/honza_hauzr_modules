# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Nastenka tak, jak ma vypadat po instalaci. Poradi odpovida ceste
# zakaznika; srovnava ho _hh_srovnat_poradi.
#
# Proc to tu vubec je: tri z techhle sloupcu jsou na Honzove
# databazi prejmenovane vychozi sloupce Odoo (New, Qualified,
# Proposition). Prejmenoval je nekdo v administraci, takze na nove
# instalaci by se jmenovaly po staru - a nic by je nenaslo. Hledani
# rady tridenni vyzvy jde podle jmena, takze by se zpravy neposlaly
# vubec.
NASTENKA = (
    'Chci odebírat',
    '3denní výzva',
    'Po výzvě · Tvůj tah',
    'Rezervace',
    'Placené',
    '40denní výzva',
    'Odhlášeno',
)

# Vychozi sloupce Odoo se prejmenuji, misto aby se vedle nich
# zakladaly nase - jinak by na nastence zustaly viset "New"
# a "Qualified", do kterych nikdy nic nespadne.
VYCHOZI_ODOO = {
    'crm.stage_lead1': 'Chci odebírat',
    'crm.stage_lead2': '3denní výzva',
    'crm.stage_lead3': 'Rezervace',
    'crm.stage_lead4': 'Placené',
}

# Nastenka se sklada jen jednou. Pak uz si ji Honza prejmenovava
# a prerovnava sam a druhy beh by mu zalozil duplikaty.
PARAMETR_HOTOVO = 'honzahauzr_crm.nastenka_zalozena'


class CrmStage(models.Model):
    """Sloupec nastenky a rady e-mailu, ktere se z nej posilaji.

    Sloupec je sekce, do ktere clovek prijde - Chci odebirat, 3denni
    vyzva, Rezervace. Jakmile v ni karta pristane, zacne jeho vlastni
    odpocet a podle nej odchazi jedna zprava za druhou.

    Texty ani predmety se tu nepisi a jednotlive zpravy se tu ani
    nevybiraji. Sloupec nese jen stitky - a odejde vsechno, co pod ne
    v knihovne spada. Co se v rade posila, kdy a jestli vubec, se
    nastavuje u e-mailu samotneho.
    """

    _inherit = 'crm.stage'

    hh_stitek_ids = fields.Many2many(
        'hh.mail.stitek',
        'hh_stage_mail_stitek_rel',
        'stage_id',
        'stitek_id',
        string='Řady e-mailů',
        help='Které řady se z tohohle sloupce posílají. Jednotlivé '
             'zprávy i jejich odstupy se nastavují v knihovně e-mailů.',
    )
    hh_maily_count = fields.Integer(
        string='Počet e-mailů',
        compute='_compute_hh_maily_count',
    )

    @api.depends('hh_stitek_ids.mail_count')
    def _compute_hh_maily_count(self):
        for stupen in self:
            stupen.hh_maily_count = sum(
                stupen.hh_stitek_ids.mapped('mail_count'))

    @api.model_create_multi
    def create(self, vals_list):
        """Novy sloupec dostane svou radu e-mailu rovnou.

        Honza prida sloupec na nastence a ocekava, ze si k nemu muze
        hned napsat zpravy. Bez toho by musel jit do stitku, zalozit
        stejnojmenny a prihodit ho zpatky ke sloupci - tri kroky
        navic a tri mista, kde se da zapomenout.
        """
        stupne = super().create(vals_list)
        stupne._hh_zajistit_vlastni_stitek()
        return stupne

    def _hh_zajistit_vlastni_stitek(self):
        """Prihodi sloupci radu e-mailu pojmenovanou jako on."""
        Stitek = self.env['hh.mail.stitek'].sudo()
        for stupen in self:
            if stupen.hh_stitek_ids:
                continue
            stitek = Stitek.search([('name', '=ilike', stupen.name)], limit=1)
            if not stitek:
                stitek = Stitek.create({'name': stupen.name})
            stupen.sudo().hh_stitek_ids = [(4, stitek.id)]

    @api.model
    def _hh_doplnit_stitky(self):
        """Kazdy sloupec dostane svou radu e-mailu.

        V knihovne se zpravy radi podle stitku a sloupec bez stitku
        se v ni vubec neukaze - Honza by pro nej musel stitek zakladat
        rucne a pamatovat si, ze se jmenuje stejne jako sloupec.

        Pousti se pri kazdem upgradu modulu, takze sloupce pridane
        pozdeji se doplni samy. Co uz stitek ma, se nechava byt -
        i kdyz se jmenuje jinak: nazev stitku je vec, kterou si Honza
        muze zmenit, a prepsat mu ji by bylo svevolne.
        """
        bez = self.sudo().search([('hh_stitek_ids', '=', False)])
        bez._hh_zajistit_vlastni_stitek()
        return bez.mapped('name')

    @api.model
    def _hh_zajistit_nastenku(self):
        """Složí nástěnku, aby po instalaci stála celá.

        Co už je, se jen pojmenuje odkazem na modul (xmlid), ať se
        na to dá v kódu i v datech odkázat. Co chybí, se vezme
        z výchozích sloupců Odoo - a když ani ty nezbývají, založí.

        Skládá se jen jednou, pak si nástěnku Honza upravuje sám.
        Bez té pojistky by druhý běh po přejmenování sloupce založil
        vedle něj nový se starým jménem.
        """
        Parametry = self.env['ir.config_parameter'].sudo()
        poprve = not Parametry.get_param(PARAMETR_HOTOVO)

        prejmenovano = 0
        if poprve:
            prejmenovano = self._hh_prejmenovat_vychozi()

        vsechny = self.sudo().with_context(active_test=False).search([])

        def podle_jmena(nazev):
            najde = vsechny.filtered(
                lambda s, n=nazev: (s.name or '').strip().lower() == n.lower())
            return najde[0] if najde else None

        zalozeno, pojmenovano = 0, 0
        for poradi, nazev in enumerate(NASTENKA, start=1):
            stupen = podle_jmena(nazev)
            if not stupen and poprve:
                stupen = self.sudo().create(
                    {'name': nazev, 'sequence': poradi})
                zalozeno += 1
                vsechny |= stupen
            if not stupen:
                continue
            if self._hh_pojmenovat(stupen, nazev):
                pojmenovano += 1

        if poprve:
            Parametry.set_param(PARAMETR_HOTOVO, '1')
        if zalozeno or prejmenovano or pojmenovano:
            _logger.info(
                'Honza Hauzr CRM: nastenka - zalozeno %s, prejmenovano '
                '%s, odkazu na modul %s.',
                zalozeno, prejmenovano, pojmenovano)
        return zalozeno, prejmenovano

    @api.model
    def _hh_prejmenovat_vychozi(self):
        """Přejmenuje výchozí sloupce Odoo na naše.

        Dřív to dělal instalační hook, jenže ten běží až za datovými
        soubory - do té doby se sloupce jmenovaly po staru, nic je
        nenašlo a vedle nich vznikly naše duplikáty. Ověřeno
        instalací na čisté databázi.

        Názvy jsou překládané pole, takže se zapisují pro každý
        nainstalovaný jazyk; jinak by v tom druhém zůstal původní
        anglický název.
        """
        jazyky = [kod for kod, _ in self.env['res.lang'].get_installed()]
        zmeneno = 0
        for xmlid, cesky in VYCHOZI_ODOO.items():
            stupen = self.env.ref(xmlid, raise_if_not_found=False)
            if not stupen or (stupen.name or '').strip() == cesky:
                continue
            for jazyk in jazyky:
                stupen.sudo().with_context(lang=jazyk).name = cesky
            zmeneno += 1
        return zmeneno

    @api.model
    def _hh_pojmenovat(self, stupen, nazev):
        """Dá sloupci odkaz na modul, pokud ještě žádný nemá.

        Bez něj je sloupec jen řádek v databázi: nedá se na něj
        odkázat z datového souboru a při nasazení jinam o něm nikdo
        neví. Název odkazu se odvodí z názvu sloupce.
        """
        Data = self.env['ir.model.data'].sudo()
        if Data.search_count([('model', '=', 'crm.stage'),
                              ('res_id', '=', stupen.id)]):
            return False

        klic = 'hh_stupen_' + ''.join(
            z if z.isalnum() else '_'
            for z in self._hh_bez_diakritiky(nazev)).strip('_')
        if Data.search_count([('module', '=', 'honzahauzr_crm'),
                              ('name', '=', klic)]):
            klic = '%s_%s' % (klic, stupen.id)
        Data.create({
            'module': 'honzahauzr_crm', 'name': klic,
            'model': 'crm.stage', 'res_id': stupen.id,
            'noupdate': True,
        })
        return True

    @api.model
    def _hh_bez_diakritiky(self, text):
        prevod = {'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
                  'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
                  'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
                  '·': '_', ' ': '_'}
        return ''.join(prevod.get(z, z) for z in (text or '').lower())

    @api.model
    def _hh_srovnat_poradi(self):
        """Srovna poradi sloupcu na nastence podle cesty zakaznika.

        Novy sloupec vznika na konci rady - to je spravne u sekce,
        kterou si Honza zalozi sam, protoze nikdo nevi, kam patri.
        U "Po výzvě" to ale vime: stoji mezi vyzvou a rezervaci.

        Rovna se to podle jmen, ne podle cisel, a jen u sloupcu, ktere
        tu rozpoznam. Co neznam, zustava za nimi v poradi, v jakem to
        bylo. Da se to pustit opakovane - podruhe uz nic nezmeni.

        Na poradi zalezi i jinde nez na nastence: karta se posouva jen
        dopredu, a to se pozna prave podle cisla sloupce.
        """
        rada = [
            'Chci odebírat',
            '3denní výzva',
            'Po výzvě · Tvůj tah',
            'Rezervace',
            'Placené',
        ]
        # Odhlaseni je konecna, patri uplne na konec - i za sloupce,
        # ktere si Honza zalozil sam.
        POSLEDNI = 'Odhlášeno'

        vsechny = self.sudo().search([])

        def podle_jmena(nazev):
            najde = vsechny.filtered(
                lambda s, n=nazev: (s.name or '').strip().lower() == n.lower())
            return najde[0] if najde else None

        znama = [s for s in (podle_jmena(n) for n in rada) if s]
        konecna = podle_jmena(POSLEDNI)
        pevne = znama + ([konecna] if konecna else [])

        zbytek = [s for s in vsechny.sorted(lambda s: (s.sequence, s.id))
                  if s not in pevne]

        zmeneno = 0
        for poradi, stupen in enumerate(
                znama + zbytek + ([konecna] if konecna else []), start=1):
            if stupen.sequence != poradi:
                stupen.sequence = poradi
                zmeneno += 1
        return zmeneno

    def hh_maily_k_odeslani(self):
        """Zapnute zpravy vsech rad sloupce, serazene podle odstupu."""
        self.ensure_one()
        if not self.hh_stitek_ids:
            return self.env['hh.mail.sablona']
        return self.env['hh.mail.sablona'].search([
            ('stitek_id', 'in', self.hh_stitek_ids.ids),
            ('zapnuto', '=', True),
        ], order='po_dnech, id')

    def action_hh_maily(self):
        """Otevre e-maily, ktere se z tohohle sloupce posilaji."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'E-maily sloupce %s' % self.name,
            'res_model': 'hh.mail.sablona',
            'view_mode': 'list,form',
            'domain': [('stitek_id', 'in', self.hh_stitek_ids.ids)],
            'context': {'search_default_podle_stitku': 1},
        }
