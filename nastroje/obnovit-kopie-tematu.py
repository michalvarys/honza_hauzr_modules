"""Přepíše kopie šablon tématu ze zdroje v modulu.

Téma se při instalaci zkopíruje: z theme.ir.ui.view vznikne
ir.ui.view, se kterým pak pracuje editor. Upgrade modulu aktualizuje
jen zdroj, kopii nechá být - což je správně u stránek, do kterých
Honza něco napsal, ale u změn v kódu to znamená, že se na web vůbec
nedostanou.

Pozná se to tak, že změna je v souboru i ve zdroji, ale ne na webu.
Stalo se u souhlasu se zpracováním údajů: v šabloně byl odkaz na
zásady, na stránce výzvy pořád starý text bez něj.

Pouští se přes odoo shell:
    docker compose -p hauzr exec -T odoo odoo shell -d hauzr --no-http \
        < nastroje/obnovit-kopie-tematu.py

Přepíše jen šablony, jejichž jméno je v NAZVY - ne celé téma.
Zúžené schválně: kopie stránek nese Honzovy úpravy a plošné
přepsání by o ně přišlo.
"""

NAZVY = [
    'theme_honzahauzr.hh_page_vyzva',
    'theme_honzahauzr.s_hhv_registrace',
    'theme_honzahauzr.s_hhn_news',
    'theme_honzahauzr.s_hh_cta_form',
    'theme_honzahauzr.s_hh_pdf',
    'theme_honzahauzr.hh_page_novy',
    'theme_honzahauzr.hh_page_landing',
    'theme_honzahauzr.hh_page_landing_blue',
]

Zdroj = env['theme.ir.ui.view'].sudo()
Kopie = env['ir.ui.view'].sudo()

prepsano, chybi = 0, []
for klic in NAZVY:
    modul, jmeno = klic.split('.', 1)
    zdroj = Zdroj.search([('key', '=', klic)], limit=1)
    kopie = Kopie.with_context(active_test=False).search([('key', '=', klic)])
    if not zdroj or not kopie:
        chybi.append('%s (zdroj=%s, kopii=%s)' % (klic, bool(zdroj), len(kopie)))
        continue
    for k in kopie:
        if k.arch_db != zdroj.arch:
            k.write({'arch_db': zdroj.arch})
            prepsano += 1

env.cr.commit()
print('PREPSANO KOPII:', prepsano)
if chybi:
    print('NENALEZENO:', chybi)
