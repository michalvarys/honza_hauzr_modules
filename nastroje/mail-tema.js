/* Náš návrh v galerii editoru.
 *
 * Když Honza založí novou zprávu, editor mu u prázdného textu
 * nabídne galerii návrhů. Mezi vestavěnými je i "Vlastní režie" —
 * tohle je její obsah.
 *
 * Dřív to byla jedna velká tabulka. Zpráva z ní složená šla jen
 * přepsat: blok se v ní nedal vybrat ani posunout, mezi části
 * nešlo nic pustit a tlačítku nešel změnit odkaz. Teď je z bloků,
 * stejně jako zbytek knihovny (nastroje/mail-bloky.js).
 *
 * Obsah je schválně obecný — je to začátek nové zprávy, ne kopie
 * některé z těch, co už chodí.
 *
 * Návrhy, které do galerie dává samo Odoo, se zároveň schovávají.
 * Honza je nepoužije a hledal by mezi nimi ty svoje.
 *
 * Spuštění:  node nastroje/mail-tema.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/views/mail_tema.xml");

const { P, bloky, paticka, KREM } = require("./mail-bloky.js");

const UKAZKA = bloky({
    eyebrow: "Vlastní režie",
    nadpis: "Nadpis zprávy",
    telo: [
        P("tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo."),
        P("Tlačítko níž má zatím prázdný odkaz. Klikni na něj a v liště nahoře mu adresu doplň."),
    ],
    tlacitko: "Text tlačítka",
    odkaz: "#",
});

/* Patička s odhlášením. Do hotových zpráv ji doplňuje modul, ale
   nová zpráva z galerie ji musí mít hned - jinak by si Honza
   napsal text, odeslal a odhlášení by v něm chybělo. */
/* Úplně na konec obsahu, pod podpis - tam, kam ji dává i modul
   (KONEC_OBSAHU v hh_mail_sablona.py). */
const KONEC_OBSAHU = "      </div>\n    </div>\n  </div>\n</div>";
const S_PATICKOU = UKAZKA.replace(
    KONEC_OBSAHU, paticka() + "\n" + KONEC_OBSAHU);

/* Celá kostra i s obalem; z galerie se bere jen vnitřek. Editor si
   obal (o_layout, container, .oe_structure) staví sám a dvakrát ho
   tam nechceme. */
const ZACATEK = S_PATICKOU.indexOf("<style");
const KONEC = S_PATICKOU.lastIndexOf("      </div>");
const VNITREK = S_PATICKOU.slice(ZACATEK, KONEC).replace(
    /\n      <div class="col o_mail_no_options[^\n]*\n/, "\n")
    .replace(/\n  <div class="container o_mail_wrapper[^\n]*\n/, "\n")
    .replace(/\n    <div class="row">\n/, "\n");

/* Zástupné texty jako entity. V XML se z nich po načtení stanou
   zase složené závorky, ale v souboru je takhle vidět, že to není
   omylem rozepsaný QWeb. */
const zastupne = (t) => t
    .replace(/\{\{/g, "&#123;&#123;")
    .replace(/\}\}/g, "&#125;&#125;");

/* Návrhy, které do galerie dává Odoo. Tři z mass_mailing, zbytek
   z mass_mailing_themes - proto je ten modul v závislostech:
   bez něj by se xpath na jeho návrhy nenašlo a upgrade by spadl. */
const ODOO_NAVRHY = [
    "basic", "empty", "default",
    "bignews", "blogging", "coffeebreak", "coupon", "event",
    "magazine", "newsletter", "promotion", "roadshow1", "roadshow2",
    "training",
];

const SCHOVAT = ODOO_NAVRHY.map((nazev) =>
    `        <xpath expr="//div[@data-name='${nazev}']" position="replace"/>`
).join("\n");

const xml = `<?xml version="1.0" encoding="utf-8"?>
<odoo>

<!-- ================================================================
     NÁŠ NÁVRH V GALERII EDITORU

     Galerie, kterou editor nabídne u prázdné zprávy, se skládá ze
     šablony mass_mailing.email_designer_themes. Každá dlaždice je
     jeden div s názvem, titulkem a cestou k náhledům; editor si
     z té cesty složí dva obrázky: _small.png do dlaždice
     a _large.png do velkého náhledu.

     Obsah jsou bloky Odoo (o_mail_snippet_general). Jen takový blok
     umí editor vybrat, posunout, smazat a dát mezi něj jiný —
     a tlačítko jako <a class="btn btn-primary"> má volby, mezi
     nimi odkaz. Dřív tu byla jedna velká tabulka a zpráva z ní
     složená se dala jen přepsat.

     Bez data-nowrap schválně: obal (o_layout, container,
     .oe_structure) ať postaví editor sám. V něm je jediné místo,
     kam jdou pouštět bloky.

     data-layout-styles dává stránce kolem karty krémové pozadí,
     stejné jako mají ostatní zprávy.

     Soubor vyrábí nastroje/mail-tema.js, needituje se ručně.
     ================================================================ -->

<template id="theme_vr_vyzva" inherit_id="mass_mailing.email_designer_themes"
          name="Vlastní režie — návrh do galerie">
    <xpath expr="." position="inside">
        <div data-name="vr_vyzva"
             title="Vlastní režie"
             data-layout-styles="background-color:${KREM};"
             data-img="/honzahauzr_crm/static/src/img/tema_vr">
${zastupne(VNITREK.trimEnd())}
        </div>
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
console.log("bloku v navrhu: " +
    (VNITREK.split("o_mail_snippet_general").length - 1));
