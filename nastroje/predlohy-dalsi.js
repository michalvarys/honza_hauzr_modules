/* Další dvě předlohy do knihovny e-mailů:
 *
 *   Chci odebírat  — uvítací zpráva s tlačítkem do třídenní výzvy
 *   Rezervace      — potvrzení domluveného hovoru s datem a časem
 *
 * Vzhled je stejný jako u řady po výzvě (nastroje/sekvence-po-vyzve.js):
 * tabulky, styly přímo u značek, šířka 100 % se stropem 600 px.
 * Outlook nezná flexbox ani styly v hlavičce a pevných 600 px
 * přeteče telefon.
 *
 * Obě mají odstup nula, tedy odejdou ve chvíli, kdy karta do
 * sloupce vstoupí.
 *
 * Spuštění:  node nastroje/predlohy-dalsi.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/data/predlohy_dalsi.xml");

const KREM = "#f4efe6";
const GRAFIT = "#23211d";
const INKOUST = "#5d554b";
const LINKA = "#e2dacb";
const SVETLA = "#a89681";

const P = (t, barva) =>
    `            <p style="margin:0 0 18px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.65;color:${barva || INKOUST};">${t}</p>`;

/* Rámeček na údaje, které si má člověk zapamatovat - datum a čas
   hovoru. V běžném odstavci by zapadly. */
const UDAJE = (radky) =>
    `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 22px 0;background-color:${KREM};">
              <tr>
                <td style="padding:20px 22px;border:1px solid ${LINKA};">
${radky.map((r) => `                  <p style="margin:0 0 8px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.5;color:${GRAFIT};">${r}</p>`).join("\n")}
                </td>
              </tr>
            </table>`;

function zprava({ eyebrow, nadpis, telo, tlacitko, odkaz, pod }) {
    return `<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:${KREM};margin:0;padding:0;">
  <tr>
    <td align="center" style="padding:24px 10px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid ${LINKA};">

        <!-- hlavicka: logo a jmeno -->
        <tr>
          <td style="padding:24px 22px 20px 22px;border-bottom:1px solid ${LINKA};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="left" valign="middle">
                  <img src="/theme_honzahauzr/static/src/img/vr/vr-logo-email.png"
                       alt="Vlastní režie" width="190" height="35"
                       style="display:block;border:0;outline:none;text-decoration:none;width:190px;height:35px;"/>
                </td>
                <td align="right" valign="middle"
                    style="font-family:Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:1.2px;text-transform:uppercase;color:${INKOUST};">
                  Honza Hauzr
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- obsah -->
        <tr>
          <td style="padding:30px 22px 8px 22px;">
            <p style="margin:0 0 14px 0;font-family:Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:${SVETLA};">${eyebrow}</p>
            <h1 style="margin:0 0 24px 0;font-family:Helvetica,Arial,sans-serif;font-size:28px;line-height:1.25;font-weight:bold;color:${GRAFIT};">${nadpis}</h1>
            <p style="margin:0 0 18px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.65;color:${GRAFIT};">{{ object.hh_osloveni }}</p>
${telo}
          </td>
        </tr>

        <!-- jedina vyzva k akci -->
        <tr>
          <td align="center" style="padding:14px 22px 10px 22px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="${GRAFIT}" style="background-color:${GRAFIT};">
                  <a href="${odkaz}"
                     style="display:inline-block;padding:16px 34px;font-family:Helvetica,Arial,sans-serif;font-size:14px;letter-spacing:1.2px;text-transform:uppercase;font-weight:bold;color:#ffffff;text-decoration:none;">${tlacitko}</a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
${pod ? `
        <tr>
          <td align="center" style="padding:6px 22px 24px 22px;">
            <p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;color:#8c8276;">${pod}</p>
          </td>
        </tr>
` : `
        <tr><td style="padding:0 22px 16px 22px;"></td></tr>
`}
        <!-- podpis -->
        <tr>
          <td style="padding:0 22px 30px 22px;border-top:1px solid ${LINKA};">
            <p style="margin:26px 0 0 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:${GRAFIT};">
              <strong>Honza</strong>
            </p>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>`;
}

/* ---------------------------------------------------------------- */

const ODBER = zprava({
    eyebrow: "Vlastní režie",
    nadpis: "Díky, že čteš.",
    telo: [
        P("budu ti sem posílat to, co sám považuju za užitečné &#8212; žádné novinky ze světa a žádné rozesílky každý týden."),
        P("Než přijde první, mám pro tebe jednu věc, která ti dá víc než čtení: <strong>bezplatnou třídenní výzvu</strong>. Tři dny, tři krátká videa a u každého jedna konkrétní věc, kterou si odneseš do běžného dne."),
        P("Stačí na to dvacet minut denně. Klidně dneska večer."),
    ].join("\n"),
    tlacitko: "Vstoupit do výzvy zdarma",
    // Adresa vyzvy je pro vsechny stejna, takze tu stoji primo.
    // Relativni zamerne: pri odeslani ji Odoo doplni na uplnou podle
    // domeny, ze ktere clovek prisel.
    odkaz: "/zpet-do-zivota",
    pod: "Je zdarma a nic tím nekupuješ.",
});

const REZERVACE = zprava({
    eyebrow: "Úvodní hovor",
    nadpis: "Termín máme domluvený.",
    telo: [
        P("rezervace proběhla v pořádku. Tady je, na čem jsme:"),
        UDAJE([
            "<strong>Kdy:</strong> {{ object.hh_termin_kdy }}",
            "<strong>Jak dlouho:</strong> {{ object.hh_termin_delka }}",
        ]),
        P("Ozvu se ti na spojení, které jsi zadal. Nemusíš se nijak připravovat &#8212; stačí, že si na to vyhradíš klid."),
        P("Kdyby ti to nakonec nevyšlo, dej mi prosím vědět předem. Tlačítkem níž si termín zrušíš sám a uvolníš ho někomu dalšímu."),
    ].join("\n"),
    tlacitko: "Zrušit termín",
    odkaz: "{{ object.hh_termin_zruseni }}",
    pod: "Tlačítko použij jen tehdy, když opravdu nemůžeš.",
});

/* ---------------------------------------------------------------- */

/* Editor z Email Marketingu hleda kostru o_layout + oe_structure.
   Bez ni bere zpravu jako prazdnou a nabidne galerii predloh. */
function proEditor(telo) {
    return `<div class="o_layout oe_styling_vr">
  <div class="container o_mail_wrapper o_mail_wrapper_td">
    <div class="col o_mail_no_options o_mail_wrapper_td oe_structure o_editable">
${telo}
    </div>
  </div>
</div>`;
}

const PREDLOHY = [
    {
        klic: "odber",
        stitek: "Chci odebírat",
        nazev: "Uvítání a pozvánka do výzvy",
        predmet: "Díky za přihlášení — a jedna věc na začátek",
        preheader: "Tři dny, tři videa, tři konkrétní kroky. Zdarma.",
        telo: ODBER,
    },
    {
        klic: "rezervace",
        stitek: "Potvrzení rezervace",
        nazev: "Potvrzení domluveného hovoru",
        predmet: "Úvodní hovor je domluvený",
        preheader: "Tady je termín, na kterém jsme se domluvili.",
        telo: REZERVACE,
    },
];

/* Stitek Potvrzeni rezervace zamerne nepatri zadnemu sloupci:
   zprava se neposila pri presunu karty, ale az kdyz je termin
   ulozeny - jinak by v ni chybelo datum a cas. Odesila ji
   _hh_potvrdit v hh_termin.py. V knihovne je videt a da se
   upravit jako kterakoliv jina. */
const STITEK_POTVRZENI = `    <record id="hh_stitek_potvrzeni_rezervace" model="hh.mail.stitek">
        <field name="name">Potvrzení rezervace</field>
        <field name="color">4</field>
    </record>`;

const zaznamy = PREDLOHY.map((p) => `    <record id="hh_predloha_${p.klic}" model="hh.mail.sablona">
        <field name="name">${p.nazev}</field>
        <field name="stitek_id" search="[('name', '=ilike', '${p.stitek}')]"/>
        <field name="po_dnech">0</field>
        <field name="predmet">${p.predmet}</field>
        <field name="preheader">${p.preheader}</field>
        <field name="body_arch"><![CDATA[${proEditor(p.telo)}]]></field>
        <field name="body_html"><![CDATA[${p.telo}]]></field>
    </record>`).join("\n\n");

const xml = `<?xml version="1.0" encoding="utf-8"?>
<odoo>

<!-- =================================================================
     DALŠÍ PŘEDLOHY DO KNIHOVNY

     Chci odebírat — uvítací zpráva s tlačítkem do třídenní výzvy.
     Rezervace     — potvrzení hovoru s datem a časem, které si
                     předloha bere z karty ({{ object.hh_termin_kdy }}).

     Obě mají odstup nula, takže odejdou ve chvíli, kdy karta do
     sloupce vstoupí.

     Potvrzení rezervace zabudované v kódu se v takovém případě
     přeskočí, aby zpráva nepřišla dvakrát — zůstává ale jako
     pojistka, kdyby předlohu někdo smazal nebo vypnul.

     Skládá je nastroje/predlohy-dalsi.js; tenhle soubor se needituje
     ručně, přegeneruje se.

     noupdate="1": při prvním nasazení se založí, dál si je Honza
     upravuje v editoru a upgrade mu to nepřepíše.
     ================================================================= -->

<data noupdate="1">

${STITEK_POTVRZENI}

${zaznamy}

</data>
</odoo>
`;

fs.writeFileSync(CIL, xml);
console.log("zapsano: " + CIL);
for (const p of PREDLOHY) {
    console.log("  " + p.stitek.padEnd(16) + p.predmet);
}
