{
    'name': 'Theme Honza Hauzr',
    'version': '18.0.1.0.0',
    'category': 'Theme/Creative',
    'summary': 'Osobni rozvoj landing page theme pro HonzaHauzr.cz',
    'description': """
Theme Honza Hauzr
=================

Tema a sablony pro web HonzaHauzr.cz — osobni rozvoj, koucink, mentoring.

Obsahuje:
- Landing page sablonu s funnel strukturou
- Work in Progress stranku
- Vlastni styly (warm orange/sunset gradients)
- CRM kontaktni formular
- Snippets pro website builder
    """,
    'author': 'VaryShop',
    'website': 'https://honzahauzr.cz',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_crm',
    ],
    'data': [
        'data/generate_primary_template.xml',
        'data/ir_asset.xml',

        'views/snippets/s_hh_hero.xml',
        'views/snippets/s_hh_vision_strip.xml',
        'views/snippets/s_hh_pain.xml',
        'views/snippets/s_hh_transform.xml',
        'views/snippets/s_hh_offer.xml',
        'views/snippets/s_hh_process.xml',
        'views/snippets/s_hh_testimonials.xml',
        'views/snippets/s_hh_cta_form.xml',
        'views/snippets/s_hh_footer.xml',
        'views/snippets/s_hh_sticky_cta.xml',
        'views/snippets/s_hh_wip.xml',
        'views/snippets/s_hh_google_fonts.xml',
        'views/snippets/snippets_registry.xml',

        'views/pages.xml',
    ],
    'images': [
        'static/description/cover.png',
    ],
    'configurator_snippets': {
        'homepage': ['s_hh_hero', 's_hh_vision_strip', 's_hh_pain', 's_hh_transform', 's_hh_offer', 's_hh_process', 's_hh_testimonials', 's_hh_cta_form'],
    },
    'assets': {
        'web.assets_frontend': [
            'theme_honzahauzr/static/src/css/honzahauzr.scss',
            'theme_honzahauzr/static/src/js/honzahauzr.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
