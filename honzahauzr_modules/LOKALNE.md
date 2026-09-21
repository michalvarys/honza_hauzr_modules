# Honza Hauzr - lokalni Odoo 18

## Spusteni

```bash
docker compose up -d
```

Web:   http://localhost:8078/
WIP:   http://localhost:8078/wip
Admin: http://localhost:8078/odoo   (admin / admin)

## Co kde je

| Vec | Hodnota |
|---|---|
| Kontejnery | `hauzr-odoo`, `hauzr-db` |
| Port | 8078 |
| Databaze | `hauzr` |
| Modul | `theme_honzahauzr` |
| addons_path | `/mnt/modules` |

Slozka `honzahauzr_modules/` je namountovana do `/mnt/modules` pro zapis, Odoo bezi s
`--dev=xml,qweb` - zmeny v XML sablonach se projevi po refreshi bez restartu.

## Upgrade po zmene Python/XML

```bash
docker exec hauzr-odoo odoo -d hauzr -u theme_honzahauzr --stop-after-init
docker compose restart odoo
```

## Po zmene SCSS / JS

Odoo si drzi zkompilovany bundle v `ir_attachment`, samotny upgrade nestaci:

```bash
docker exec hauzr-db psql -U odoo -d hauzr -c \
  "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';"
docker compose restart odoo
```

Pak nacist http://localhost:8078/?debug=assets

## Po zmene stranek (pages.xml)

`theme_*` modul kopiruje `theme.website.page` -> `website.page` jen pri
prvni aplikaci tematu. Upgrade zdrojovy zaznam zmeni, kopii ne. Je potreba
kopii smazat a nechat vyrobit znovu:

```bash
docker exec -i hauzr-odoo odoo shell -d hauzr --no-http <<'PY'
env['website.page'].search([('url', '=', '/')]).unlink()
env.cr.commit()
PY
docker exec hauzr-odoo odoo -d hauzr -u theme_honzahauzr --stop-after-init
docker compose restart odoo
```

## Logy

```bash
docker logs -f --tail 200 hauzr-odoo
```

## Reset databaze od nuly

```bash
docker compose stop odoo
docker exec hauzr-db psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS hauzr;"
docker exec hauzr-odoo odoo -d hauzr -i theme_honzahauzr --without-demo=all --stop-after-init
docker compose start odoo
```

Pak znovu priradit tema k webu (viz nize).

## Priradit tema k webu

Instalace modulu sama o sobe nic nezobrazi. Tema se musi aplikovat na web
a pote smazat prazdna `website.homepage`, ktera jinak na `/` vyhraje:

```bash
docker exec -i hauzr-odoo odoo shell -d hauzr --no-http <<'PY'
w = env['website'].search([], limit=1)
t = env['ir.module.module'].search([('name', '=', 'theme_honzahauzr')], limit=1)
w.theme_id = t.id
env.cr.commit()
t._theme_load(w)
env.cr.commit()
dead = env['website.page'].search([('url', '=', '/')]).filtered(
    lambda p: p.view_id.key == 'website.homepage')
dead.unlink()
env.cr.commit()
PY
docker compose restart odoo
```

## Zmeny proti puvodnimu repu

- Ze zavislosti modulu odstranen `theme_common` - v odoo:18 community image
  neexistuje (je v repu odoo/design-themes) a modul ho stejne nikde nepouzival,
  vse jede pres `website.*`.
