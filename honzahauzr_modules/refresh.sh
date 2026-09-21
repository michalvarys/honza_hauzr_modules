#!/usr/bin/env bash
# Pregeneruje lokalni Odoo po zmene v modulu.
#
#   ./refresh.sh          jen styly (SCSS/JS) - rychle, ~15 s
#   ./refresh.sh page     i obsah stranky (pages.xml) - pomalejsi, ~40 s
#
# Proc dva rezimy: theme_* modul kopiruje theme.website.page -> website.page
# jen pri prvni aplikaci tematu. Upgrade zmeni zdroj, kopii ne. Po zmene
# pages.xml se proto kopie musi zahodit a nechat vyrobit znovu.

set -e
cd "$(dirname "$0")"

DB=hauzr
MODUL=theme_honzahauzr
PORT=8078

if [ "$1" = "page" ]; then
    echo "==> zahazuji zkopirovanou stranku"
    docker exec -i hauzr-odoo odoo shell -d "$DB" --no-http <<'PY' 2>&1 | grep -iE "smazano|error" || true
env['website.page'].search([('url', '=', '/')]).unlink()
env['ir.ui.view'].search([('key', 'like', 'theme_honzahauzr.hh_page_landing')]).unlink()
env.cr.commit()
print("smazano")
PY
fi

echo "==> mazu cache assetu"
docker exec hauzr-db psql -U odoo -d "$DB" -q -c \
    "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';"

if [ "$1" = "page" ]; then
    echo "==> upgrade modulu"
    docker exec hauzr-odoo odoo -d "$DB" -u "$MODUL" --stop-after-init 2>&1 \
        | grep -iE "error|parseerror|traceback" || true
fi

echo "==> restart"
docker compose restart odoo >/dev/null 2>&1

for i in $(seq 1 45); do
    C=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "http://localhost:$PORT/" 2>/dev/null || true)
    if [ "$C" = "200" ]; then
        echo "==> hotovo: http://localhost:$PORT/"
        exit 0
    fi
    sleep 1
done

echo "==> Odoo nenabehlo, mrkni na logy:  docker logs --tail 100 hauzr-odoo"
exit 1
