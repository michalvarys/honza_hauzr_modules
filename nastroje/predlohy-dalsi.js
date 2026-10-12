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
     Rezervace      vlastni vzhled s kartou terminu
   Rozhrani obou stavebnic je stejne, takze se to da prehodit
   jednim radkem. */
const { P, UDAJE, bloky, tabulky } = require("./mail-bloky.js");
const tmava = require("./mail-bloky-tmava.js");
const rezervace = require("./mail-bloky-rezervace.js");

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
    eyebrow: "Rezervace potvrzena",
    nadpis: "Termín máme domluvený.",
    podnadpis: "Úvodní hovor k programu Tvůj tah",
    telo: [
        rezervace.P("rezervace proběhla v pořádku. Tady je, na čem jsme:"),
        rezervace.TERMIN({
            kdy: "{{ object.hh_termin_kdy }}",
            udaje: [
                ["Jak dlouho", "{{ object.hh_termin_delka }}"],
                ["Forma", "Videohovor přes Google Meet"],
            ],
        }),
        rezervace.P("Potkáme se přes Google Meet. Odkaz na hovor ti pošlu samostatným e-mailem před termínem, připojíš se jedním kliknutím. Nemusíš se nijak připravovat. Stačí, že si na to vyhradíš klid."),
        rezervace.KROKY([
            ["Klidné místo.", "Najdi si chvíli, kdy tě nikdo neruší."],
            ["Papír po ruce.", "Hodí se, co sis zapsal během výzvy."],
            ["Odkaz z e-mailu.", "Přijde ti před hovorem, tak ho měj po ruce."],
        ]),
        rezervace.ZRUSENI({
            text: "Kdyby ti to nakonec nevyšlo, dej mi prosím vědět předem. Termín zrušíš sám a uvolníš ho někomu dalšímu.",
            tlacitko: "Zrušit termín",
            // Osobni odkaz: kazdy termin ma vlastni klic, aby nesel
            // zrusit cizi.
            odkaz: "{{ object.hh_termin_zruseni }}",
            pod: "Tlačítko použij jen tehdy, když opravdu nemůžeš.",
        }),
    ],
};

/* ---------------------------------------------------------------- */

/* Odkaz na hovor. Posílá ji Honza tlačítkem z karty, ne řada:
   schůzka v Google Meetu vzniká až těsně před hovorem a žádný
   odstup ve dnech by ji netrefil. Do tlačítka se odkaz doplní
   z karty, viz models/crm_lead_meet.py. */
const MEET = {
    eyebrow: "Odkaz na hovor",
    // Fajfka patri k potvrzeni rezervace, tady by hlasila neco,
    // co se zrovna nestalo.
    fajfka: false,
    nadpis: "Tady je odkaz na náš hovor.",
    podnadpis: "Stačí na něj v domluvený čas kliknout",
    telo: [
        rezervace.P("blíží se náš termín, tak posílám odkaz, kterým se připojíš:"),
        rezervace.TERMIN({
            kdy: "{{ object.hh_termin_kdy or 'podle domluvy' }}",
            udaje: [
                ["Jak dlouho", "{{ object.hh_termin_delka or '45 minut' }}"],
                ["Kde", "Google Meet"],
            ],
        }),
        rezervace.TLACITKO({
            text: "Připojit se k hovoru",
            odkaz: "{{ object.hh_meet_odkaz }}",
            pod: "Odkaz funguje v prohlížeči, nic se nemusí instalovat.",
        }),
        rezervace.P("Kdyby tlačítko nešlo otevřít, zkus stránku načíst znovu nebo mi napiš. Připojit se jde z počítače i z telefonu."),
    ],
};

/* Zrušení hovoru Honzou. Posílá ji tlačítko Zrušit rezervaci
   v kalendáři, ne řada - zákazník se to jinak nedozví a bude
   v domluvený čas čekat. Když hovor ruší sám přes odkaz v potvrzení,
   tahle zpráva mu nechodí; to by mu oznamovalo, co právě udělal. */
const ZRUSENI = {
    eyebrow: "Hovor se ruší",
    fajfka: false,
    nadpis: "Náš hovor musím zrušit.",
    podnadpis: "Omlouvám se za komplikace",
    telo: [
        rezervace.P("bohužel ti musím zrušit termín, na kterém jsme se domluvili:"),
        rezervace.TERMIN({
            kdy: "{{ object.hh_termin_kdy or 'původní termín' }}",
            udaje: [],
        }),
        rezervace.P("Nic se neděje, jen si prosím vyber jiný čas. V kalendáři vidíš všechny, které mám volné."),
        rezervace.TLACITKO({
            text: "Vybrat nový termín",
            odkaz: "{{ object.hh_odkaz_rezervace }}",
            pod: "Trvá to minutu a potvrzení ti přijde hned.",
        }),
        rezervace.P("Kdyby ti žádný z nabízených časů nevyhovoval, napiš mi a domluvíme se napřímo."),
    ],
};

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
        vzhled: rezervace,
    },
    {
        klic: "meet",
        stitek: "Rezervace",
        nazev: "Odkaz na hovor (posílám ručně)",
        predmet: "Odkaz na náš hovor",
        preheader: "Připojíš se jedním kliknutím.",
        zprava: MEET,
        vzhled: rezervace,
        // Rada ji preskoci, odchazi tlacitkem z karty.
        rucni: true,
    },
    {
        klic: "zruseni",
        stitek: "Rezervace",
        nazev: "Zrušení hovoru (posílám já)",
        predmet: "Musím zrušit náš hovor",
        preheader: "Vyber si prosím jiný termín.",
        zprava: ZRUSENI,
        vzhled: rezervace,
        // Posila ji tlacitko Zrusit rezervaci v kalendari.
        rucni: true,
    },
];

const zaznamy = PREDLOHY.map((p) => `    <record id="hh_predloha_${p.klic}" model="hh.mail.sablona">
        <field name="name">${p.nazev}</field>
        <field name="stitek_id" search="[('name', '=ilike', '${p.stitek}')]"/>
        <field name="po_dnech">0</field>${p.rucni ? `
        <field name="rucni" eval="True"/>` : ""}
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
