"""Smaže dvojníky, kteří po tématu zůstanou v databázi.

Téma se při aplikaci kopíruje: z theme.ir.asset vznikne ir.asset,
z theme.ir.ui.view ir.ui.view. Když se kopírování proběhne víckrát
(přeinstalace tématu, obnova kopií, upgrade po změně závislostí),
vzniknou vedle sebe dva stejné záznamy.

U šablon to jen mate. U assetů to web **shodí**: záznam s direktivou
"remove" odebere soubor ze svazku, druhý stejný už nemá co odebrat
a Odoo skončí chybou

    ValueError: File(s) [...] not found in bundle web.assets_frontend_lazy

a stránka vrátí 500. Stalo se na devu 13. 10. 2026 po přidání
závislosti tématu na honzahauzr_crm.

Z každé skupiny stejných záznamů zůstane jeden, přednost má ten bez
vazby na konkrétní web - platí pro obě domény.

Pouští se přes odoo shell:
    docker compose -p hauzr exec -T odoo odoo shell -d hauzr --no-http \
        < nastroje/sjednotit-kopie-tematu.py
"""


def klic_assetu(a):
    return (a.name, a.bundle, a.path or '', a.directive, a.target or '',
            a.sequence)


Asset = env['ir.asset'].sudo().with_context(active_test=False)
vsechny = Asset.search([('path', 'like', 'theme_honzahauzr%')])

skupiny = {}
for a in vsechny:
    skupiny.setdefault(klic_assetu(a), []).append(a)

smazano = 0
for klic, zaznamy in skupiny.items():
    if len(zaznamy) < 2:
        continue
    # Bez vazby na web napred - ten plati pro vsechny domeny.
    zaznamy.sort(key=lambda a: (bool(a.website_id), a.id))
    zustava, pryc = zaznamy[0], zaznamy[1:]
    print('dvojnik: %-48s zustava id=%s, mazu %s' % (
        klic[0][:48], zustava.id, [a.id for a in pryc]))
    for a in pryc:
        a.unlink()
        smazano += 1

env.cr.commit()
print('SMAZANO DVOJNIKU:', smazano)
print('ZBYVA ZAZNAMU:', Asset.search_count([('path', 'like', 'theme_honzahauzr%')]))
