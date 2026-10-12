/* Další dvě předlohy do knihovny e-mailů:
 *
 *   Chci odebírat  — uvítací zpráva s tlačítkem do třídenní výzvy
 *   Rezervace      — potvrzení domluveného hovoru s datem a časem,
 *                    do řady u stejnojmenného sloupce nástěnky
 *
 * Vzhled i obě podoby zprávy (bloky pro editor, tabulky pro poštu)
 * dodává nastroje/mail-bloky.js — stejně jako u řady po výzvě.
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

/* Kazda z tech dvou zprav ma svuj vzhled:
     Chci odebirat  tmava podoba v barvach webu Honza Hauzr
     Rezervace      puvodni svetla - potvrzeni hovoru je provozni
                    zprava, ne pozvanka, a tmave pozadi by se k ni
                    nehodilo
   Rozhrani obou stavebnic je stejne, takze se to da prehodit
   jednim radkem. */
const { P, UDAJE, bloky, tabulky } = require("./mail-bloky.js");
const tmava = require("./mail-bloky-tmava.js");

/* ---------------------------------------------------------------- */

const ODBER = {
    eyebrow: "Vítej ve Vlastní režii",
    nadpis: "Díky, že čteš.",
    telo: [
        tmava.P("budu ti sem posílat to, co sám považuju za užitečné. Žádné novinky ze světa a žádné rozesílky každý týden."),
        tmava.P("Než přijde první, mám pro tebe jednu věc, která ti dá víc než čtení:"),
        tmava.PANEL({
            eyebrow: "Bezplatná třídenní výzva",
            nadpis: "Z autopilota zpět do života",
            cisla: [["3", "dny"], ["3", "krátká videa"], ["20", "minut denně"]],
            text: "U každého videa jedna konkrétní věc, kterou si odneseš do běžného dne.",
        }),
        tmava.P("Stačí na to dvacet minut denně. Klidně dneska večer."),
    ],
    tlacitko: "Vstoupit do výzvy zdarma",
    // Adresa vyzvy je pro vsechny stejna, takze tu stoji primo.
    // Relativni zamerne: pri odeslani ji Odoo doplni na uplnou podle
    // domeny, ze ktere clovek prisel.
    odkaz: "/zpet-do-zivota",
    pod: "Je zdarma a nic tím nekupuješ.",
};

const REZERVACE = {
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
    ],
    tlacitko: "Zrušit termín",
    odkaz: "{{ object.hh_termin_zruseni }}",
    pod: "Tlačítko použij jen tehdy, když opravdu nemůžeš.",
};

/* ---------------------------------------------------------------- */

const PREDLOHY = [
    {
        klic: "odber",
        stitek: "Chci odebírat",
        nazev: "Uvítání a pozvánka do výzvy",
        predmet: "Díky za přihlášení — a jedna věc na začátek",
        preheader: "Tři dny, tři videa, tři konkrétní kroky. Zdarma.",
        zprava: ODBER,
        vzhled: tmava,
    },
    {
        klic: "rezervace",
        stitek: "Rezervace",
        nazev: "Potvrzení domluveného hovoru",
        predmet: "Úvodní hovor je domluvený",
        preheader: "Tady je termín, na kterém jsme se domluvili.",
        zprava: REZERVACE,
    },
];

const zaznamy = PREDLOHY.map((p) => `    <record id="hh_predloha_${p.klic}" model="hh.mail.sablona">
        <field name="name">${p.nazev}</field>
        <field name="stitek_id" search="[('name', '=ilike', '${p.stitek}')]"/>
        <field name="po_dnech">0</field>
        <field name="predmet">${p.predmet}</field>
        <field name="preheader">${p.preheader}</field>
        <!-- body_arch je podoba pro editor (bloky), body_html to,
             co odejde do pošty (tabulky). Viz nastroje/mail-bloky.js. -->
        <field name="body_arch"><![CDATA[${(p.vzhled || { bloky, tabulky }).bloky(p.zprava)}]]></field>
        <field name="body_html"><![CDATA[${(p.vzhled || { bloky, tabulky }).tabulky(p.zprava)}]]></field>
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

     Potvrzení patří do řady u sloupce Rezervace, stejně jako
     u každého jiného sloupce: Honza si ho může přepsat, vypnout
     nebo k němu přidat další zprávy. Odesílá se až po uložení
     termínu, takže datum i čas v něm sedí.

     Zabudované potvrzení v kódu zůstává jako pojistka pro případ,
     že v té řadě žádná zapnutá zpráva s odstupem nula nebude.

     Skládá je nastroje/predlohy-dalsi.js; tenhle soubor se needituje
     ručně, přegeneruje se.

     noupdate="1": při prvním nasazení se založí, dál si je Honza
     upravuje v editoru a upgrade mu to nepřepíše.
     ================================================================= -->

<data noupdate="1">


${zaznamy}

</data>
</odoo>
`;

fs.writeFileSync(CIL, xml);
console.log("zapsano: " + CIL);
for (const p of PREDLOHY) {
    console.log("  " + p.stitek.padEnd(16) + p.predmet);
}
