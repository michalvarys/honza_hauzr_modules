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
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_tag_data.xml',
        'data/mailing_list_data.xml',
        'data/website_form_data.xml',
        'data/sekce_doplneni.xml',
        'data/sekce_odhlaseno.xml',
        'data/sekvence_po_vyzve.xml',
        'data/ir_cron_data.xml',
        'views/hh_mail_sablona_views.xml',
        'views/mail_tema.xml',
        'views/crm_stage_views.xml',
        'views/hh_vyzva_sledovani_views.xml',
        # Menu az za akcemi - polozky na ne odkazuji.
        'views/menu.xml',
        'views/crm_lead_views.xml',
        'views/hh_termin_views.xml',
        'views/rezervace_templates.xml',
        # Snippet az za sablonami - registrace do panelu odkazuje
        # na sablonu snippetu, takze uz musi existovat.
        'views/rezervace_snippet.xml',
        'views/vyzva_obsah_templates.xml',
        'views/odhlaseni_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    # Styl a skript rezervacni stranky. Oboji je zanorene pod .hhr,
    # takze i kdyz se to nacita pro celou instanci, na cizi weby to
    # nemuze dosahnout - zadny obecny selektor tam neni.
    'assets': {
        'web.assets_frontend': [
            'honzahauzr_crm/static/src/css/rezervace.scss',
            'honzahauzr_crm/static/src/css/vyzva_obsah.scss',
            'honzahauzr_crm/static/src/js/rezervace.js',
            'honzahauzr_crm/static/src/js/rezervace_snippet.js',
            'honzahauzr_crm/static/src/js/vyzva_odpocet.js',
            'honzahauzr_crm/static/src/js/vyzva_sledovani.js',
        ],
        # Strop pro editor textu e-mailu, aby dialog sloupce nerostl
        # s delkou zpravy. Visi na vlastni tride, takze na nic jineho
        # v Odoo nedosahne.
        'web.assets_backend': [
            'honzahauzr_crm/static/src/css/stupen.scss',
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
