/** @odoo-module **/

/**
 * Snippet s rezervaci uvodniho hovoru.
 *
 * Blok se da pretahnout na libovolnou stranku. Obsah si dotahuje sam
 * pres /rezervace/data, takze v ulozene strance zadny seznam terminu
 * neni - kdyby tam byl, zamrzl by v podobe, v jake byl pri ukladani.
 *
 * Pri odchodu (a tedy i pred ulozenim stranky v editoru) se blok
 * uklidi zpatky na hlasku "Nacitam", aby se do stranky nezapsalo nic
 * z toho, co skript vykreslil.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const HLASKY = {
    obsazeno: "Tenhle termín mezitím někdo zabral. Vyber si prosím jiný.",
    neuplne: "Potřebuju jméno i e-mail, jinak ti nemám kam napsat.",
    souhlas: "Bez souhlasu se zpracováním osobních údajů to odeslat nejde.",
    chyba: "Něco se pokazilo. Zkus to prosím znovu.",
};

publicWidget.registry.hhRezervaceSnippet = publicWidget.Widget.extend({
    selector: ".s_hh_rezervace",
    // V editoru se nespousti. Honza tam upravuje nadpis a text, ne
    // seznam terminu - a hlavne se tim nic nevykreslene neulozi.
    disabledInEditableMode: true,

    /**
     * @override
     */
    async start() {
        // _super se musi zavolat driv, nez se na cokoliv ceka. Stara
        // tridni nadstavba Odoo ho nastavuje jen na dobu synchronniho
        // behu metody - po prvnim awaitu uz this._super neexistuje
        // a spadne to na "this._super is not a function".
        const rodic = this._super(...arguments);

        this.blok = this.el.querySelector("[data-hhr-blok]");
        if (this.blok) {
            this.vybranyDen = null;
            this.vybranyCas = null;
            await this.nacti();
        }

        return rodic;
    },

    /**
     * @override
     */
    destroy() {
        // Uklid pred ulozenim stranky - viz komentar nahore.
        if (this.blok) {
            this.blok.innerHTML =
                '<div class="hhr-dny hhr-dny--kostra">' +
                '<div class="hhr-kostra"></div>'.repeat(10) +
                '</div>';
        }
        this._super(...arguments);
    },

    // ------------------------------------------------------------------
    // data
    // ------------------------------------------------------------------

    async nacti() {
        try {
            // Blok na strance vyzvy si vyzada den, se kterym se ma
            // odemknout. Kalendar je videt porad, jen do te doby
            // nejde kliknout. Rozhoduje o tom server, ne tahle
            // znacka - ta jen rekne, na ktery den se ma zeptat.
            const odemkneDen = this.el.getAttribute("data-hhr-odemkne-den");
            const odpoved = await rpc(
                "/rezervace/data",
                odemkneDen ? { odemkne_den: odemkneDen } : {}
            );
            this.dny = odpoved.dny || [];
            this.zamceno = !!odpoved.zamceno;
        } catch {
            this.blok.innerHTML =
                '<p class="hhr-micro">Termíny se teď nepodařilo načíst. Zkus stránku obnovit.</p>';
            return;
        }
        this.vykresliDny();
    },

    // ------------------------------------------------------------------
    // 1. krok - dny
    // ------------------------------------------------------------------

    vykresliDny(hlaska) {
        const kusy = [];
        if (hlaska) {
            kusy.push(`<div class="hhr-hlaska">${hlaska}</div>`);
        }

        // Mrizka dnu se vykresli i kdyz nic volneho neni - clovek ma
        // videt, ve ktere dny se hovory beru. Hlaska se k ni jen
        // pripoji nad ni.
        if (!this.dny.some((d) => d.stav === "volno")) {
            kusy.push(
                '<div class="hhr-prazdno">' +
                    "<p>Zrovna teď nemám vypsaný žádný volný termín.</p>" +
                    '<p class="hhr-micro">Napiš mi na ' +
                    '<a href="mailto:honzahauzr@gmail.com">honzahauzr@gmail.com</a>' +
                    " a domluvíme se napřímo.</p></div>"
            );
        }
        kusy.push('<div class="hhr-dny">');
        for (const den of this.dny) {
            const dnes = den.dnes ? " hhr-denkarta--dnes" : "";
            const vnitrek =
                `<span class="hhr-denkarta__den">${den.den}</span>` +
                `<span class="hhr-denkarta__cislo">${den.cislo}</span>` +
                `<span class="hhr-denkarta__mesic">${den.mesic}</span>`;

            if (den.stav === "volno") {
                kusy.push(
                    `<button type="button" class="hhr-denkarta${dnes}" data-datum="${den.datum}">` +
                        vnitrek +
                        `<span class="hhr-denkarta__pocet">${this.pocetSlovy(den.volnych)}</span>` +
                        "</button>"
                );
            } else {
                // Den bez volneho casu se vypisuje taky, ale neni to
                // tlacitko - nema kam vest. Bez nej by mezi datumy
                // zustavaly diry a nebylo by poznat, ve ktere dny se
                // hovory vubec neberou.
                const popis = den.stav === "nepracovni" ? "nepracovní" : "nic volného";
                kusy.push(
                    `<div class="hhr-denkarta hhr-denkarta--pryc${dnes}">` +
                        vnitrek +
                        `<span class="hhr-denkarta__pocet">${popis}</span>` +
                        "</div>"
                );
            }
        }
        kusy.push("</div>");
        if (this.zamceno) {
            // Zamceny kalendar je videt cely, vcetne skutecnych
            // terminu - jen po nem nejde kliknout. Ma byt znat, ze
            // volno existuje; to je duvod, proc se vubec ukazuje.
            kusy.push(
                '<p class="hhr-micro hhr-pod-dny">' +
                    "Výběr času se otevře spolu s třetím dnem výzvy." +
                    "</p>"
            );
        } else {
            kusy.push(
                '<p class="hhr-micro hhr-pod-dny">Klikni na den, ve kterém mám volno, a vyber si hodinu.</p>'
            );
        }

        this.blok.classList.toggle("hhr-blok--zamceno", !!this.zamceno);
        this.blok.innerHTML = kusy.join("");
        if (this.zamceno) {
            return;
        }
        this.blok.querySelectorAll("button.hhr-denkarta").forEach((tlacitko) => {
            tlacitko.addEventListener("click", () =>
                this.vykresliCasy(tlacitko.dataset.datum)
            );
        });
    },

    pocetSlovy(kolik) {
        if (kolik === 1) {
            return "1 volný čas";
        }
        if (kolik < 5) {
            return `${kolik} volné časy`;
        }
        return `${kolik} volných časů`;
    },

    // ------------------------------------------------------------------
    // 2. krok - hodiny vybraneho dne
    // ------------------------------------------------------------------

    vykresliCasy(datum, hlaska) {
        const den = this.dny.find((d) => d.datum === datum);
        if (!den) {
            return this.vykresliDny();
        }
        this.vybranyDen = den;
        this.vybranyCas = null;

        const kusy = [];
        kusy.push(
            '<button type="button" class="hhr-zpet" data-zpet="1">' +
                "&#8249; Zpátky na výběr dne</button>"
        );
        kusy.push(`<h3 class="hhr-denNadpis">${den.popis}</h3>`);
        if (hlaska) {
            kusy.push(`<div class="hhr-hlaska">${hlaska}</div>`);
        }

        kusy.push('<div class="hhr-casy">');
        for (const cas of den.casy) {
            const trida = cas.volny ? "hhr-cas" : "hhr-cas hhr-cas--pryc";
            const vypnuto = cas.volny ? "" : " disabled=\"disabled\"";
            const popis = cas.volny ? `${cas.minut} min` : "obsazeno";
            kusy.push(
                `<button type="button" class="${trida}" data-termin="${cas.id}"${vypnuto}>` +
                    `<span class="hhr-cas__hodina">${cas.cas}</span>` +
                    `<span class="hhr-cas__delka">${popis}</span>` +
                    "</button>"
            );
        }
        kusy.push("</div>");

        kusy.push(this.sablonaFormulare());

        this.blok.innerHTML = kusy.join("");
        this.navazPosluchace();
    },

    sablonaFormulare() {
        return (
            '<div class="hhr-udaje" hidden="hidden">' +
            '<h4 class="hhr-udaje__nadpis">Vybraný čas: ' +
            '<span class="hhr-vybrano">zatím žádný</span></h4>' +
            '<div class="hhr-pole"><input type="text" class="hhr-jmeno" placeholder="Jméno" autocomplete="given-name"/></div>' +
            '<div class="hhr-pole"><input type="email" class="hhr-email" placeholder="E-mail" autocomplete="email"/></div>' +
            '<div class="hhr-pole"><input type="tel" class="hhr-telefon" placeholder="Telefon (nepovinné)" autocomplete="tel"/></div>' +
            '<div class="hhr-pole hhr-pole--siroke"><textarea class="hhr-poznamka" rows="3" placeholder="Chceš mi něco napsat dopředu? (nepovinné)"></textarea></div>' +
            // Souhlas se zpracovanim udaju. Formular stavi skript,
            // takze se sem sablona hh_souhlas_udaje nedostane -
            // text i odkaz proto musi sedet s ni.
            '<label class="hh-souhlas hhr-pole--siroke" for="hhr_souhlas">' +
            '<input type="checkbox" id="hhr_souhlas" class="hhr-souhlas" required="required"/>' +
            "<span>Souhlasím se zpracováním " +
            '<a href="/ochrana-osobnich-udaju" target="_blank" rel="noopener">osobních údajů</a>' +
            " za účelem domluvení hovoru." +
            '<span class="hh-souhlas__chyba">Bez souhlasu to bohužel nejde odeslat.</span>' +
            "</span></label>" +
            '<button type="button" class="hhr-cta hhr-odeslat" disabled="disabled">Rezervovat termín</button>' +
            '<p class="hhr-micro">Potvrzení ti přijde do e-mailu. Termín můžeš kdykoli zrušit odkazem, který v něm najdeš.</p>' +
            "</div>"
        );
    },

    navazPosluchace() {
        const zpet = this.blok.querySelector("[data-zpet]");
        if (zpet) {
            zpet.addEventListener("click", () => this.vykresliDny());
        }

        const udaje = this.blok.querySelector(".hhr-udaje");
        const odeslat = this.blok.querySelector(".hhr-odeslat");
        const popisek = this.blok.querySelector(".hhr-vybrano");

        this.blok.querySelectorAll(".hhr-cas:not(.hhr-cas--pryc)").forEach((tlacitko) => {
            tlacitko.addEventListener("click", () => {
                this.blok
                    .querySelectorAll(".hhr-cas")
                    .forEach((jine) => jine.classList.remove("hhr-cas--vybrany"));
                tlacitko.classList.add("hhr-cas--vybrany");

                this.vybranyCas = tlacitko.dataset.termin;
                const hodina = tlacitko.querySelector(".hhr-cas__hodina").textContent;
                popisek.textContent = `${this.vybranyDen.popis} v ${hodina}`;

                udaje.hidden = false;
                odeslat.disabled = false;
                udaje.scrollIntoView({ behavior: "smooth", block: "nearest" });
            });
        });

        odeslat.addEventListener("click", () => this.odesli());
    },

    // ------------------------------------------------------------------
    // 3. krok - odeslani
    // ------------------------------------------------------------------

    async odesli() {
        const jmeno = this.blok.querySelector(".hhr-jmeno").value.trim();
        const email = this.blok.querySelector(".hhr-email").value.trim();
        const telefon = this.blok.querySelector(".hhr-telefon").value.trim();
        const poznamka = this.blok.querySelector(".hhr-poznamka").value.trim();
        const odeslat = this.blok.querySelector(".hhr-odeslat");

        if (!jmeno || !email) {
            this.vykresliCasy(this.vybranyDen.datum, HLASKY.neuplne);
            return;
        }

        // Bez souhlasu se neodesila. Formular neni <form>, takze
        // required prohlizec sam nevyhodnoti - hlida se to tady
        // a hlaska se ukaze primo u zaskrtavatka, ne nahore.
        const souhlas = this.blok.querySelector(".hhr-souhlas");
        if (souhlas && !souhlas.checked) {
            souhlas.closest(".hh-souhlas")
                .classList.add("hh-souhlas--chyba");
            souhlas.focus();
            return;
        }

        odeslat.disabled = true;
        odeslat.textContent = "Odesílám…";

        let odpoved;
        try {
            odpoved = await rpc("/rezervace/data/rezervovat", {
                termin_id: this.vybranyCas,
                jmeno,
                email,
                telefon,
                poznamka,
                souhlas: !!(souhlas && souhlas.checked),
            });
        } catch {
            odpoved = { ok: false, chyba: "chyba" };
        }

        if (!odpoved.ok) {
            // Nekdo byl rychlejsi - nacteme terminy znovu, at uz
            // zabrany cas nesviti jako volny.
            await this.nacti();
            this.vykresliCasy(
                this.vybranyDen.datum,
                HLASKY[odpoved.chyba] || HLASKY.chyba
            );
            return;
        }

        this.blok.innerHTML =
            '<div class="hhr-hotovo">' +
            '<div class="hhr-hotovo__ikona">' +
            '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>' +
            "</div>" +
            '<h3 class="hhr-h1">Termín je domluvený</h3>' +
            `<p class="hhr-lead">${odpoved.kdy}</p>` +
            '<p class="hhr-micro">Potvrzení ti právě posílám do e-mailu. ' +
            "Najdeš v něm i odkaz, kterým termín zrušíš, kdyby ti to nevyšlo.</p>" +
            "</div>";
    },
});

export default publicWidget.registry.hhRezervaceSnippet;
