/* Tři e-maily třídenní výzvy "Z autopilota zpět do života".
 *
 * Texty jsou doslova ty, které už chodí — přenesené z původních
 * ručně psaných tabulek (nastroje/mail-den1.html, mail-den2.html,
 * old/honzahauzr_crm/data/mail_vyzva_den3.html). Mění se jen
 * podoba, ne obsah.
 *
 * Výstupem je JSON, ne XML. Dny 1 a 2 vznikly kdysi ručně a
 * v databázi existují bez vazby na modul; kdyby je modul zakládal
 * znovu jako záznamy, měl by Honza od každého dva. Soubor proto
 * jen nese obsah a modul (hh.mail.sablona._hh_dny_vyzvy) podle něj
 * stávající zprávy srovná, nebo chybějící doplní.
 *
 * Spuštění:  node nastroje/vyzva-dny.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/data/vyzva_dny.json");

const { P, bloky, tabulky } = require("./mail-bloky-editorial.js");

/* Osobní odkaz do výzvy. Tenhle zástupný text zůstává: každý má
   vlastní klíč a otevřou se mu jen dny, které už má odemčené. */
const ODKAZ = "{{ object.hh_vyzva_odkaz }}";

const DNY = [
    {
        /* po_dnech: odstup od vstupu do sloupce. Den 1 odchází hned. */
        po_dnech: 0,
        nazev: "3denní výzva – hned",
        predmet: "Jsi uvnitř. Den 1 na tebe čeká",
        preheader: "Tři dny, tři krátká videa, tři konkrétní kroky.",
        eyebrow: "Den 1 &#183; Z autopilota zpět do života",
        nadpis: "Vítej ve výzvě. Den&#160;1 na tebe čeká.",
        telo: [
            P("jsi uvnitř. Tři dny, tři krátká videa a u každého jedna konkrétní věc, kterou si odneseš do svého běžného dne."),
            P("<strong>Den 1 &#8211; Zrcadlo a pravda.</strong> Podíváš se bez obalu na to, kde dnes jsi, a vybereš jednu oblast, kterou už nechceš dál ignorovat."),
            P("Stačí na to dvacet minut v klidu. Klidně dneska večer."),
        ],
        tlacitko: "Otevřít Den 1",
        pod: "Den 2 ti odemknu za 24 hodin a dám ti vědět e-mailem.",
    },
    {
        po_dnech: 1,
        nazev: "vyzva den 2",
        predmet: "Den 2 je odemčený",
        preheader: "Od pojmenování k činu: malý důkaz, který vydrží.",
        eyebrow: "Den 2 &#183; Z autopilota zpět do života",
        nadpis: "Den&#160;2 je odemčený.",
        telo: [
            P("první den máš za sebou. Dneska půjdeme od pojmenování k činu."),
            P("<strong>Den 2 &#8211; Důkaz.</strong> Nadefinuješ malý konkrétní závazek, kterým začneš obnovovat respekt sám k sobě. Malý schválně &#8211; musí vydržet i ve špatném týdnu."),
            P("Video i úkol najdeš na stejné stránce jako včera."),
        ],
        tlacitko: "Otevřít Den 2",
        pod: "Den 3 ti odemknu zase za 24 hodin.",
    },
    {
        po_dnech: 2,
        nazev: "vyzva den 3",
        predmet: "Den 3 je odemčený",
        preheader: "Poslední díl výzvy a tvůj další krok.",
        eyebrow: "Den 3 &#183; Z autopilota zpět do života",
        nadpis: "Poslední díl: tvůj tah.",
        telo: [
            P("tohle je poslední den výzvy a zároveň ten, kvůli kterému to celé je."),
            P("<strong>Den 3 &#8211; Tvůj tah.</strong> Pojmenuješ autopilota, který tě drží na místě, a uvidíš svůj další krok &#8211; ten, který můžeš udělat bez čekání na vhodnější období."),
            P("Na konci na tebe čeká možnost domluvit si nezávazný hovor o tom, co ti z výzvy vyšlo."),
        ],
        tlacitko: "Otevřít Den 3",
        pod: "Díky, že sis na to udělal čas.",
    },
];

const data = DNY.map((d) => {
    const zprava = {
        eyebrow: d.eyebrow,
        nadpis: d.nadpis,
        telo: d.telo,
        tlacitko: d.tlacitko,
        odkaz: ODKAZ,
        pod: d.pod,
    };
    return {
        po_dnech: d.po_dnech,
        nazev: d.nazev,
        predmet: d.predmet,
        preheader: d.preheader,
        body_arch: bloky(zprava),
        body_html: tabulky(zprava),
    };
});

fs.writeFileSync(CIL, JSON.stringify(data, null, 2) + "\n");
console.log("zapsano: " + CIL);
for (const d of data) {
    console.log("  po " + d.po_dnech + " dnech  " + d.predmet);
}
