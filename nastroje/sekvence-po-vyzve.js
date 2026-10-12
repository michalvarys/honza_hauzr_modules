/* Sedm e-mailů prodejní řady po dokončení třídenní výzvy.
 *
 * Texty, předměty i náhledové řádky jsou doslova ze zadání od Honzy
 * (Tvůj tah, verze 1.1, 11. 10. 2026). Tenhle skript z nich skládá
 * HTML v naší šabloně a vyrábí datový soubor modulu.
 *
 * Vzhled i obě podoby zprávy (bloky pro editor, tabulky pro poštu)
 * dodává nastroje/mail-bloky.js.
 *
 * Co se do textu nepíše:
 *   - "[ODKAZ NA REZERVACI]" - z toho je tlačítko
 *   - "Patičku ... doplní e-mailový systém" - pokyn, ne text zprávy;
 *     patičku i náhledový řádek doplní odesílač sám
 *
 * Spuštění:  node nastroje/sekvence-po-vyzve.js
 */

const fs = require("fs");
const path = require("path");

const KOREN = path.join(__dirname, "..");
const CIL = path.join(KOREN, "old/honzahauzr_crm/data/sekvence_po_vyzve.xml");

/* ---------------------------------------------------------------- */
/* stavebnice                                                       */
/* ---------------------------------------------------------------- */

const { P, OTAZKA, RAMECEK, GRAFIT, bloky, tabulky } =
    require("./mail-bloky-editorial.js");

/* Adresa stranky s kalendarem. Je pro vsechny stejna, takze tu
   stoji primo - zadny zastupny text. Relativni zamerne: pri
   odeslani ji Odoo doplni na uplnou podle domeny, ze ktere
   clovek prisel, takze jeden text funguje na obou webech. */
const ODKAZ = "/uvodni-hovor";
const KAMPAN = "utm_source=email&amp;utm_medium=email" +
    "&amp;utm_campaign=tvuj_tah_po_vyzve_v1&amp;utm_content=";

function cil(cislo) {
    const poradi = String(cislo).padStart(2, "0");
    return ODKAZ + "?" + KAMPAN + "email_" + poradi;
}

/* ---------------------------------------------------------------- */
/* texty ze zadání                                                  */
/* ---------------------------------------------------------------- */

const EYEBROW = "Tvůj tah &#183; po výzvě";

const MAILY = [
    {
        cislo: 1,
        den: 1,
        nazev: "1 · Co uděláš s tím, co sis uvědomil",
        predmet: "Co z výzvy zůstane, až zavřeš notebook?",
        preheader: "Vrať se k jedné věci, kterou už nechceš přehlížet.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "Co z výzvy zůstane, až zavřeš notebook?",
        telo: [
            P("ve výzvě jsme prošli tři kroky: podívat se pravdivě na svůj život, vytvořit jeden malý důkaz a všimnout si rozhodnutí, které za tebe zatím dělá autopilot."),
            P("Teď přijde obyčejný den. Práce, zprávy, povinnosti. A to, co ti při sledování dávalo smysl, může zase ustoupit do pozadí."),
            P("Zkus se dnes vrátit k jedné věci:"),
            OTAZKA("Co už nechceš dál přehlížet &#8212; a co s tím uděláš během příštích 24&#160;hodin?"),
            P("Třeba si vyhradíš čas, který pořád dáváš ostatním. Otevřeš odkládaný rozhovor. Nebo dodržíš svoje minimum, přestože dnešek není ideální."),
            P("Pokud chceš na výzvu navázat s vedením, připravil jsem <strong>Tvůj tah</strong>. Během 40 dní půjdeme od pojmenování současné situace přes vlastní hranice a pravidla až ke konkrétnímu směru na dalších 90 dní."),
            P("Prvním krokem je společný hovor. Probereme, co teď řešíš a jestli ti s tím program může pomoct."),
        ],
    },
    {
        cislo: 2,
        den: 3,
        nazev: "2 · Nemám žádný velký problém",
        predmet: "„Já ale nemám žádný velký problém.“",
        preheader: "Nemusí se ti nic rozpadnout, abys měl důvod něco změnit.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "„Já ale nemám žádný velký problém.“",
        telo: [
            P("práce nějak funguje. Máš kde bydlet. Možná máš vztah, rodinu a zvenku docela normální život."),
            P("A tak si říkáš, jestli vůbec máš důvod něco řešit."),
            P("Jenže vedle toho třeba už měsíce nemáš čas na sebe. V důležitých věcech automaticky ustupuješ. Nebo pokračuješ směrem, který sis vlastně nikdy sám nevybral."),
            P("<strong>Nemusí se ti nic rozpadnout, abys měl důvod něco změnit.</strong>", GRAFIT),
            P("Vybav si jednu situaci z posledního týdne, kdy jsi řekl „to je v pohodě“, ale uvnitř ti to úplně v pohodě nebylo."),
            OTAZKA("Co bys v té situaci potřeboval říct nebo udělat jinak?"),
            P("I takové věci mají v Tvém tahu místo. Učíš se přesněji poznat, co potřebuješ, dát tomu slova a postupně podle toho jednat."),
            P("Nemusíš čekat, až za tebe rozhodne krize."),
            P("Jestli chceš zjistit, zda je program vhodný právě pro tebe, můžeme to probrat."),
        ],
    },
    {
        cislo: 3,
        den: 5,
        nazev: "3 · Strach z nedokončení",
        predmet: "Co když zase začnu a nedokončím?",
        preheader: "Jak v programu funguje podpora, když se zasekneš.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "Co když zase začnu a nedokončím?",
        telo: [
            P("možná se nebojíš začít. Bojíš se, že za týden zase přestaneš."),
            P("Pár dní se držíš. Pak přijde náročnější den, vynecháš a v hlavě naskočí: „Tak zase nic.“"),
            P("U kouření jsem tenhle návrat ke starému návyku zažil opakovaně. Musel jsem se učit vracet, aniž bych každé uklouznutí bral jako důkaz, že všechno předtím bylo k ničemu."),
            P("Proto má Tvůj tah vedle lekcí také <strong>průběžnou podporu</strong>."),
            P("Víš, co máš dělat dál. Když se zasekneš, můžeš položit otázku. Během programu máme tři společná živá setkání. A když uvidím dva až tři dny bez pohybu, soukromě se ti ozvu."),
            P("Nemusíš před ostatními vysvětlovat svoje osobní věci. Potřebujeme zjistit, co ti brání pokračovat a jaký další krok je reálný."),
            P("Dokončení za tebe nikdo nezařídí. Ale na hledání cesty zpátky nemusíš být sám."),
            P("Jestli tě právě strach z dalšího nedokončeného pokusu brzdí, pojďme ho na hovoru probrat konkrétně."),
        ],
    },
    {
        cislo: 4,
        den: 7,
        nazev: "4 · Nemusíš předem znát celý směr",
        predmet: "Nemusíš vědět, co chceš dělat dalších dvacet let",
        preheader: "Na úvodní hovor můžeš přijít i bez hotového cíle.",
        tlacitko: "Probrat svůj další krok na hovoru",
        nadpis: "Nemusíš vědět, co chceš dělat dalších dvacet let",
        telo: [
            P("dlouho jsem věděl, že nechci pokračovat stejným způsobem v práci. Jenže pokaždé, když jsem připustil změnu, naskočila mi celá lavina otázek."),
            OTAZKA("Co budu dělat? Co mi půjde? Jak se tím uživím? A co když si vyberu špatně?"),
            P("Chtěl jsem mít jasno v celém dalším životě. Výsledkem bylo, že jsem často neudělal vůbec nic."),
            P("Pomohlo mi začít tím, co už jsem věděl: co dál nechci a co potřebuju začít dělat jinak."),
            P("To je důležité i pro vstup do Tvého tahu. Nemusíš na hovor přicházet s hotovým cílem. Klidně můžeš říct: „Vím, že takhle nechci pokračovat, ale nevím, co místo toho.“"),
            P("V programu budeme postupně hledat, co je pro tebe důležité, kde se přizpůsobuješ proti sobě a čemu chceš dát prostor. Z toho vznikne jedna konkrétní priorita na dalších 90 dní a první kroky."),
            P("<strong>Celou cestu dnes vidět nemusíš.</strong>", GRAFIT),
        ],
    },
    {
        cislo: 5,
        den: 9,
        nazev: "5 · Reálná časová náročnost",
        predmet: "Vejde se Tvůj tah do normálního života?",
        preheader: "Poctivě o čase, který budeš potřebovat.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "Vejde se Tvůj tah do normálního života?",
        telo: [
            P("pokud máš práci, vztah a další povinnosti, otázka času je úplně na místě."),
            P("Chci ti proto říct konkrétně, s čím počítat."),
            P("Tvůj tah trvá 40 dní. Některé hlubší pracovní dny můžou zabrat 45&#8211;60 minut, někdy i víc. Vedle nich jsou kratší reflexní dny a čtyři skutečné volné dny."),
            P("V závěru šest dní používáš svůj plán v běžném životě. Samotné zaznamenání zkušenosti zabere přibližně 5&#8211;10 minut denně; čas na zvolenou akci záleží na tom, co sis vybral."),
            P("K tomu patří tři společná živá setkání."),
            P("Prostor si tedy vyhradit potřebuješ. Nemusíš ale čtyřicet dní po sobě zvládat stejně náročnou lekci."),
            P("Zkus se podívat na svůj příští týden."),
            OTAZKA("Kam by se ti vešel klidný blok pro sebe? A co bys kvůli němu musel přesunout nebo odmítnout?"),
            P("Pokud si nejsi jistý, jestli je to ve tvé současné situaci reálné, probereme to předem. Hovor tě k nákupu nezavazuje."),
        ],
    },
    {
        cislo: 6,
        den: 12,
        nazev: "6 · Cena, vedení a garance",
        predmet: "Za co v Tvém tahu platíš 19 990 Kč",
        preheader: "Co dostaneš a za jakých podmínek ti vrátím peníze.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "Za co v Tvém tahu platíš 19&#160;990&#160;Kč",
        telo: [
            P("19&#160;990&#160;Kč je částka, u které dává smysl vědět, co přesně kupuješ a proč zrovna ode mě."),
            P("Tvůj tah vychází i z mojí zkušenosti s životem, který navenek fungoval, ale ve kterém jsem postupně přestával vidět vlastní směr. Prošel jsem dvěma koučovacími výcviky a dál se vzdělávám. Při práci s tebou propojuju otázky, strukturu a konkrétní kroky."),
            P("V ceně máš 40denní postup, 11 hlavních videí, fyzický workbook, tři společná živá setkání a průběžnou podporu. Víš, kde začít, máš kam zachytit vlastní odpovědi a koho se zeptat, když se zasekneš."),
            P("Postupně si připravíš svoje pravidla, hranice a konkrétní 90denní prioritu. Na konci svůj plán šest dní zkoušíš v běžném životě a vyhodnotíš, co potřebuje upravit."),
            P("A za svou částí stojím i garancí."),
            RAMECEK([
                "Když projdeš celý 40denní program, uděláš všechny povinné úkoly včetně práce ve workbooku a závěrečné praxe a zúčastníš se finálního vyhodnocení na společném hovoru nebo v domluveném náhradním termínu, platí jednoduchý příslib:",
                "Pokud ti ani potom program nepřinese žádné nové uvědomění, jasnější orientaci ve vlastní situaci ani konkrétní posun, <strong>vrátím ti celou zaplacenou cenu</strong>. Osobní odpovědi nemusíš sdílet před skupinou.",
            ]),
            P("Na úvodním hovoru probereme, jestli je právě tohle vhodná cesta pro to, co řešíš. Když mi program pro tvoji situaci nebude dávat smysl, řeknu ti to."),
        ],
    },
    {
        cislo: 7,
        den: 15,
        nazev: "7 · Závěrečné pozvání k hovoru",
        predmet: "Chceš na výzvu navázat?",
        preheader: "Poslední e-mail téhle série a prostor pro tvoje rozhodnutí.",
        tlacitko: "Domluvit si úvodní hovor",
        nadpis: "Chceš na výzvu navázat?",
        telo: [
            P("v posledních e-mailech jsem ti ukázal, jak můžeš na výzvu navázat v Tvém tahu. Tímhle tuhle sérii uzavírám."),
            P("Možná teď pokračuješ sám a první kroky ti fungují. Možná na program nemáš prostor. Nebo tě zajímá, ale zůstává jedna otázka, kvůli které ses zatím neozval."),
            P("Pokud chceš pokračovat se mnou, dalším krokem je úvodní hovor."),
            P("Probereme, co teď řešíš, co chceš mít jinak a jestli je pro tebe 40denní program vhodný. Když to bude dávat smysl oběma, domluvíme další postup."),
            P("Ať se rozhodneš jakkoliv, vrať se ještě k jedné věci z výzvy:"),
            OTAZKA("Co už nechceš dál přehlížet &#8212; a jak se to projeví v tvém příštím rozhodnutí?"),
            P("Odpověď může být malá. Důležité je, aby se dostala i do běžného dne."),
        ],
    },
];

/* ---------------------------------------------------------------- */
/* kostra pro editor                                                */
/* ---------------------------------------------------------------- */

/* ---------------------------------------------------------------- */
/* zápis datového souboru                                           */
/* ---------------------------------------------------------------- */

const zaznamy = MAILY.map((m) => {
    const spolecne = {
        eyebrow: EYEBROW,
        nadpis: m.nadpis,
        telo: m.telo,
        tlacitko: m.tlacitko,
        odkaz: cil(m.cislo),
    };
    return `    <record id="hh_mail_po_vyzve_${m.cislo}" model="hh.mail.sablona">
        <field name="name">${m.nazev}</field>
        <field name="stitek_id" ref="hh_stitek_po_vyzve"/>
        <field name="po_dnech">${m.den}</field>
        <field name="predmet">${m.predmet}</field>
        <field name="preheader">${m.preheader}</field>
        <!-- Bez type="html": ta podoba chce ve schématu skutečné XML
             potomky, zatímco my text vkládáme jako CDATA. Pole je Html,
             takže se řetězec uloží tak, jak je.

             body_arch je podoba pro editor (bloky), body_html to,
             co odejde do pošty (tabulky). Viz nastroje/mail-bloky.js. -->
        <field name="body_arch"><![CDATA[${bloky(spolecne)}]]></field>
        <field name="body_html"><![CDATA[${tabulky(spolecne)}]]></field>
    </record>`;
}).join("\n\n");

const xml = `<?xml version="1.0" encoding="utf-8"?>
<odoo>

<!-- =================================================================
     PRODEJNÍ ŘADA PO DOKONČENÍ TŘÍDENNÍ VÝZVY

     Sedm navazujících e-mailů pro lidi, kteří výzvu dokončili, ale
     nemají domluvený hovor ani koupený program. Cílem je rezervace
     úvodního hovoru - přes ten se teď do Tvého tahu vstupuje.

     Texty jsou doslova ze zadání od Honzy (verze 1.1, 11. 10. 2026).
     Skládá je nastroje/sekvence-po-vyzve.js; tenhle soubor se
     needituje ručně, přegeneruje se.

     noupdate="1" schválně: při prvním nasazení se řada založí, dál
     si ji Honza upravuje v editoru a upgrade mu to nepřepíše.

     Den 0 je potvrzené dokončení výzvy, ne registrace. Odpočet běží
     od chvíle, kdy karta vstoupí do tohohle sloupce, a tam ji
     posune až účastníkovo potvrzení na stránce výzvy.
     ================================================================= -->

<data noupdate="1">

    <record id="hh_stitek_po_vyzve" model="hh.mail.stitek">
        <field name="name">Po výzvě · Tvůj tah</field>
        <field name="prodejni" eval="True"/>
        <field name="color">3</field>
    </record>

    <record id="hh_stupen_po_vyzve" model="crm.stage">
        <field name="name">Po výzvě · Tvůj tah</field>
        <field name="sequence">3</field>
        <field name="hh_stitek_ids" eval="[(4, ref('hh_stitek_po_vyzve'))]"/>
    </record>

    <record id="hh_stitek_karty_po_vyzve" model="crm.tag">
        <field name="name">Po výzvě · Tvůj tah</field>
    </record>

${zaznamy}

</data>

<!-- Srovnání pořadí schválně mimo blok s noupdate: tam se funkce
     při upgradu přeskakují a sloupec by zůstal viset na stejném
     čísle jako Rezervace. Tady se pustí pokaždé - je spočítaná tak,
     aby podruhé už nic nezměnila. -->
<data>
    <function model="crm.stage" name="_hh_srovnat_poradi"/>
</data>

</odoo>
`;

fs.writeFileSync(CIL, xml);
console.log("zapsano: " + CIL);
console.log("zprav: " + MAILY.length + ", znaku: " + xml.length);
for (const m of MAILY) {
    console.log("  " + String(m.den).padStart(2) + ". den  " + m.predmet);
}
