/* Naše návrhy v galerii editoru.
 *
 * Když Honza založí novou zprávu, editor mu u prázdného textu
 * nabídne galerii návrhů. Tenhle skript ji vyrábí.
 *
 * Každý návrh je z bloků Odoo (o_mail_snippet_general). Dřív to
 * byla jedna velká tabulka a zpráva z ní složená šla jen přepsat:
 * blok se v ní nedal vybrat ani posunout, mezi části nešlo nic
 * pustit a tlačítku nešel změnit odkaz.
 *
 * Obsah návrhů je schválně obecný — je to začátek nové zprávy, ne
 * kopie některé z těch, co už chodí.
 *
 * Návrhy, které do galerie dává samo Odoo, se zároveň schovávají.
 * Honza je nepoužije a hledal by mezi nimi ty svoje.
 *
 * Přidat další návrh: nový soubor tema-*.js se stejným rozhraním
 * jako ty stávající, přihodit ho do seznamu NAVRHY a spustit
 * tenhle skript. Náhledy do galerie vyrábí nastroje/nahled-tema.py.
 *
 * Spuštění:  node nastroje/mail-tema.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/views/mail_tema.xml");

const NAVRHY = [
    require("./tema-editorial.js"),
    require("./tema-tmava.js"),
    require("./tema-rezervace.js"),
];

/* Návrhy, které do galerie dává Odoo. Tři z mass_mailing, zbytek
   z mass_mailing_themes - proto je ten modul v závislostech:
   bez něj by se xpath na jeho návrhy nenašlo a upgrade by spadl. */
const ODOO_NAVRHY = [
    "basic", "empty", "default",
    "bignews", "blogging", "coffeebreak", "coupon", "event",
    "magazine", "newsletter", "promotion", "roadshow1", "roadshow2",
    "training",
];

/* Zástupné texty jako entity. V XML se z nich po načtení stanou
   zase složené závorky, ale v souboru je takhle vidět, že to není
   omylem rozepsaný QWeb. */
const zastupne = (t) => t
    .replace(/\{\{/g, "&#123;&#123;")
    .replace(/\}\}/g, "&#125;&#125;");

const dlazdice = (navrh) => `        <div data-name="${navrh.klic}"
             title="${navrh.titul}"
             data-layout-styles="background-color:${navrh.pozadi};"
             data-img="/honzahauzr_crm/static/src/img/${navrh.nahled}">
${zastupne(navrh.obsah())}
        </div>`;

const SCHOVAT = ODOO_NAVRHY.map((nazev) =>
    `        <xpath expr="//div[@data-name='${nazev}']" position="replace"/>`
).join("\n");

const xml = `<?xml version="1.0" encoding="utf-8"?>
<odoo>

<!-- ================================================================
     NAŠE NÁVRHY V GALERII EDITORU

     Galerie, kterou editor nabídne u prázdné zprávy, se skládá ze
     šablony mass_mailing.email_designer_themes. Každá dlaždice je
     jeden div s názvem, titulkem a cestou k náhledům; editor si
     z té cesty složí dva obrázky: _small.png do dlaždice
     a _large.png do velkého náhledu.

     Obsah jsou bloky Odoo (o_mail_snippet_general). Jen takový blok
     umí editor vybrat, posunout, smazat a dát mezi něj jiný —
     a tlačítko jako <a class="btn btn-primary"> má volby, mezi
     nimi odkaz.

     Bez data-nowrap schválně: obal (o_layout, container,
     .oe_structure) ať postaví editor sám. V něm je jediné místo,
     kam jdou pouštět bloky.

     data-layout-styles dává stránce kolem karty barvu pozadí.

     Soubor vyrábí nastroje/mail-tema.js, needituje se ručně.
     ================================================================ -->

<template id="theme_vr_vyzva" inherit_id="mass_mailing.email_designer_themes"
          name="Vlastní režie — návrhy do galerie">
    <xpath expr="." position="inside">
${NAVRHY.map(dlazdice).join("\n\n")}
    </xpath>
</template>

<!-- ================================================================
     NÁVRHY ODOO Z GALERIE PRYČ

     Odoo jich tam dává čtrnáct — newsletter, kupón, konference…
     Honza žádný z nich nepoužije a mezi nimi by hledal ty svoje.
     Zůstávají jen naše.

     Vrátit se dá kterýkoliv: stačí vyškrtnout jeho jméno ze
     seznamu ODOO_NAVRHY v nastroje/mail-tema.js a soubor znovu
     vyrobit.
     ================================================================ -->

<template id="galerie_bez_navrhu_odoo"
          inherit_id="mass_mailing.email_designer_themes"
          name="Galerie bez návrhů Odoo">
${SCHOVAT}
</template>

</odoo>
`;

fs.writeFileSync(CIL, xml);
console.log("zapsano: " + CIL);
for (const n of NAVRHY) {
    console.log("  " + n.titul.padEnd(32) +
        (n.obsah().split("o_mail_snippet_general").length - 1) + " bloku");
}
