# -*- coding: utf-8 -*-
{
    'name': 'Honza Hauzr - sběr kontaktů',
    'summary': 'Každý e-mail z webu založí i kontakt v Zákaznících',
    'description': """
Z webu chodí e-maily přes formuláře do CRM jako příležitosti. Samy o sobě
ale nezakládají kontakt, takže se adresy nikde nehromadí a nedá se jim
později poslat hromadný e-mail.

Tenhle modul to doplňuje: jakmile vznikne příležitost s e-mailem,
najde se podle něj kontakt, a když žádný není, založí se nový. Kontakt
se pak k příležitosti připojí, takže je v CRM vidět, s kým se jedná.

Záměrně je to modul, ne pravidlo v databázi - nastavení v databázi by se
muselo po nasazení na server dělat znovu, kód se nasadí sám.
""",
    'category': 'Sales/CRM',
    'version': '18.0.1.5.0',
    'author': 'Michal Varys',
    'license': 'LGPL-3',
    'depends': [
        # Kvuli editoru e-mailu: bloky, obrazky a hotove
        # predlohy, ktere Odoo pouziva v Email Marketingu.
        'mass_mailing',
        'crm',
        'website',
        # Formulare na webu zakladaji prilezitosti pres nej. Je
        # v zavislostech kvuli poradi nacitani: bez toho se nase
        # uprava website_form_input_filter nemusi dostat na radu
        # a puvod navstevnika by prebil obecny kanal "Website".
        'website_crm',
        # Dava do galerie editoru jedenact dalsich navrhu. Je
        # v zavislostech, protoze je z galerie schovavame - bez nej
        # by se xpath na ne nenaslo a upgrade by spadl.
        'mass_mailing_themes',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_tag_data.xml',
        'data/mailing_list_data.xml',
        'data/website_form_data.xml',
        'data/sekce_odhlaseno.xml',
        # Pred obema datovymi soubory se zpravami: zahodi ty, ktere
        # jsou jeste psane v tabulkach, aby se o kousek niz zalozily
        # znovu v blocich editoru.
        'data/predlohy_do_bloku.xml',
        'data/sekvence_po_vyzve.xml',
        # Az za sloupci, ktere si modul zaklada sam (Odhlaseno,
        # Po vyzve). Nastenka adoptuje, co uz je, a dodela zbytek;
        # kdyby bezela driv, zalozila by sloupec Po vyzve sama
        # i s radou a datovy soubor by pak spadl na duplicitni
        # nazev rady. Overeno instalaci na ciste databazi.
        #
        # Zaroven pred predlohami: ty si radu hledaji podle jmena
        # ("Chci odebirat", "Rezervace"), takze uz musi existovat.
        'data/sekce_doplneni.xml',
        'data/predlohy_dalsi.xml',
        # Az za predlohami: presouva zpravu mezi radami, ktere
        # obe musi uz existovat.
        'data/stitek_rezervace.xml',
        # Az za obema: dny vyzvy i srovnani sablon uvnitr doplnuji
        # paticku, takze musi bezet, kdyz uz jsou vsechny zpravy
        # zalozene. Driv to bylo obracene a sedm novych zprav na
        # cerstve databazi zustalo bez odhlaseni.
        'data/vyzva_den3.xml',
        'data/puvod_navstevniku.xml',
        'data/videa_oznaceni.xml',
        'data/ir_cron_data.xml',
        'views/hh_mail_sablona_views.xml',
        'views/mail_tema.xml',
        'views/crm_stage_views.xml',
        'views/hh_vyzva_sledovani_views.xml',
        'views/hh_web_klik_views.xml',
        'views/hh_video_views.xml',
        'views/crm_lead_zdroje_views.xml',
        # Menu az za akcemi - polozky na ne odkazuji.
        'views/menu.xml',
        'views/crm_lead_views.xml',
        'views/hh_termin_views.xml',
        'views/rezervace_templates.xml',
        # Snippet az za sablonami - registrace do panelu odkazuje
        # na sablonu snippetu, takze uz musi existovat.
        'views/rezervace_snippet.xml',
        # Az za snippetem rezervace - stranka pouziva tentyz blok.
        'views/stranka_hovor.xml',
        'views/vyzva_obsah_templates.xml',
        'views/odhlaseni_templates.xml',
        'views/res_config_settings_views.xml',
        # Uplne nakonec: srovnani nabidek pod aplikaci Honza Admin
        # saha i na polozky z hh_termin_views.xml.
        'data/presun_menu.xml',
    ],
    # Styl a skript rezervacni stranky. Oboji je zanorene pod .hhr,
    # takze i kdyz se to nacita pro celou instanci, na cizi weby to
    # nemuze dosahnout - zadny obecny selektor tam neni.
    'assets': {
        'web.assets_frontend': [
            'honzahauzr_crm/static/src/css/rezervace.scss',
            'honzahauzr_crm/static/src/css/vyzva_obsah.scss',
            'honzahauzr_crm/static/src/css/odhlaseni.scss',
            'honzahauzr_crm/static/src/js/rezervace.js',
            'honzahauzr_crm/static/src/js/rezervace_snippet.js',
            'honzahauzr_crm/static/src/js/vyzva_odpocet.js',
            'honzahauzr_crm/static/src/js/vyzva_sledovani.js',
            'honzahauzr_crm/static/src/js/web_klik.js',
            'honzahauzr_crm/static/src/js/hh_video.js',
        ],
        # Strop pro editor textu e-mailu, aby dialog sloupce nerostl
        # s delkou zpravy. Visi na vlastni tride, takze na nic jineho
        # v Odoo nedosahne.
        'web.assets_backend': [
            'honzahauzr_crm/static/src/css/stupen.scss',
            'honzahauzr_crm/static/src/css/nastenka.scss',
            'honzahauzr_crm/static/src/css/terminy_kalendar.scss',
            'honzahauzr_crm/static/src/js/terminy_kalendar.js',
            'honzahauzr_crm/static/src/xml/terminy_kalendar.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
