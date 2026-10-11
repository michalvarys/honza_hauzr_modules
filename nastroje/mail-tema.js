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
 * Spuštění:  node nastroje/mail-tema.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/views/mail_tema.xml");

const { P, bloky, KREM } = require("./mail-bloky.js");

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

/* Celá kostra i s obalem; z galerie se bere jen vnitřek. Editor si
   obal (o_layout, container, .oe_structure) staví sám a dvakrát ho
   tam nechceme. */
const ZACATEK = UKAZKA.indexOf("<style");
const KONEC = UKAZKA.lastIndexOf("      </div>");
const VNITREK = UKAZKA.slice(ZACATEK, KONEC).replace(
    /\n      <div class="col o_mail_no_options[^\n]*\n/, "\n")
    .replace(/\n  <div class="container o_mail_wrapper[^\n]*\n/, "\n")
    .replace(/\n    <div class="row">\n/, "\n");

/* Zástupné texty jako entity. V XML se z nich po načtení stanou
   zase složené závorky, ale v souboru je takhle vidět, že to není
   omylem rozepsaný QWeb. */
const zastupne = (t) => t
    .replace(/\{\{/g, "&#123;&#123;")
    .replace(/\}\}/g, "&#125;&#125;");

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
    <xpath expr="//div[@data-name='default']" position="after">
        <div data-name="vr_vyzva"
             title="Vlastní režie"
             data-layout-styles="background-color:${KREM};"
             data-img="/honzahauzr_crm/static/src/img/tema_vr">
${zastupne(VNITREK.trimEnd())}
        </div>
    </xpath>
</template>

</odoo>
`;

fs.writeFileSync(CIL, xml);
console.log("zapsano: " + CIL);
console.log("bloku v navrhu: " +
    (VNITREK.split("o_mail_snippet_general").length - 1));
