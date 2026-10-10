#!/bin/sh
# Zamek na stranky.
#
# Zmeri stav webu a vypise ho jako radky, ktere jdou porovnat.
# Pouziva se tak, ze se pred zasahem ulozi otisk a po zasahu se
# porovna:
#
#     sh nastroje/kontrola-stranek.sh > /tmp/pred.txt
#     ... prace ...
#     sh nastroje/kontrola-stranek.sh > /tmp/po.txt
#     diff /tmp/pred.txt /tmp/po.txt && echo "nic se nehnulo"
#
# Adresu lze predat parametrem, jinak se bere lokalni instance.
#
# Co se meri a proc prave to:
#   navratovy kod   - stranka vubec odpovida
#   sekci           - obsah se nevytratil
#   oe_structure    - plocha, do ktere jdou pouzet bloky, tam je
#   chyby v CSS     - prelozil se balik stylu; kdyz ne, Odoo posle
#                     stary a web vypada rozsypane, ale vraci 200
#   skript odkazu   - adresy z parametru se maji cim doplnit

ZAKLAD="${1:-http://localhost:8078}"

echo "# otisk webu: $ZAKLAD"

for CESTA in / /zpet-do-zivota /stary /wip /blue /rezervace /vr-test /tah-test /zpet-do-zivota/vyzva; do
    TELO=$(curl -s --max-time 30 "$ZAKLAD$CESTA" 2>/dev/null)
    KOD=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$ZAKLAD$CESTA" 2>/dev/null)
    if [ "$KOD" != "200" ]; then
        printf '%-24s kod=%s\n' "$CESTA" "$KOD"
        continue
    fi
    SEKCI=$(printf '%s' "$TELO" | grep -o '<section' | wc -l | tr -d ' ')
    STRUKTUR=$(printf '%s' "$TELO" | grep -o 'oe_structure' | wc -l | tr -d ' ')
    printf '%-24s kod=%s sekci=%s struktur=%s\n' "$CESTA" "$KOD" "$SEKCI" "$STRUKTUR"
done

# Styly a skripty se berou z uvodni stranky, jsou pro cely web spolecne.
UVOD=$(curl -s --max-time 30 "$ZAKLAD/" 2>/dev/null)
CSS=$(printf '%s' "$UVOD" | grep -o '/web/assets/[^"]*\.css' | head -1)
JS=$(printf '%s' "$UVOD" | grep -o '/web/assets/[^"]*minimal[^"]*\.js' | head -1)

if [ -n "$CSS" ]; then
    OBSAH=$(curl -s --max-time 40 "$ZAKLAD$CSS" 2>/dev/null)
    printf 'styly                    chyb=%s dvojcat=%s\n' \
        "$(printf '%s' "$OBSAH" | grep -ci 'css error occured')" \
        "$(printf '%s' "$OBSAH" | grep -o '\.vr-tah' | wc -l | tr -d ' ')"
else
    echo "styly                    NENALEZENY"
fi

if [ -n "$JS" ]; then
    printf 'skript odkazu            vyskytu=%s\n' \
        "$(curl -s --max-time 40 "$ZAKLAD$JS" 2>/dev/null | grep -c 'hh-odkaz-')"
else
    echo "skript odkazu            NENALEZEN"
fi
