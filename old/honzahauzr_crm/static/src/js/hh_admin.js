/** @odoo-module **/

/**
 * Administrace Honzy Hauzra.
 *
 * Jedna obrazovka se zalozkami misto nekolika ruznych pohledu Odoo.
 * Duvod je praktický: Honza potrebuje videt lidi, vyzvu, hovory
 * a sekvence, ne filtry, razeni, vyber sloupcu a chatter. Co tu
 * neni, je zamerne pryc.
 *
 * Logika zustava stejna jako doted - nic se neprepocitava a nic
 * nove nevznika. Meni se jen to, jak je to videt.
 *
 * Nastenka prilezitosti (kanban) se zamerne nenahrazuje, jen se na
 * ni odsud da skocit. Honza ji pouziva a je na ni zvykly.
 *
 * Data chodi po obrazovkach z modelu hh.admin, vzdycky jednim
 * dotazem - jinak by cisla naskakovala postupne.
 */

import { Component, onWillStart, useExternalListener, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const ZALOZKY = [
    { klic: "nastenka", popis: "Nástěnka" },
    { klic: "lide", popis: "Lidé" },
    { klic: "vyzva", popis: "Výzva" },
    { klic: "hovory", popis: "Hovory" },
    { klic: "statistiky", popis: "Statistiky" },
];

class HhAdmin extends Component {
    static template = "honzahauzr_crm.HhAdmin";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.zalozky = ZALOZKY;

        // Na kterou obrazovku se ma otevrit, rekne akce. Diky tomu
        // muze nabidka v CRM mirit rovnou na sekvence nebo stitky
        // a nemusi pro ne existovat vlastni obrazovka.
        const kontext = (this.props.action && this.props.action.context) || {};

        this.stav = useState({
            obrazovka: kontext.hh_obrazovka || "nastenka",
            tazena: null,
            cil: null,
            novaSekce: null,
            prejmenovavana: null,
            hlaska: null,
            nacita: true,
            cisla: null,
            data: null,
            hledani: "",
            stupen: null,
            nabidka: false,
        });

        // Kliknuti mimo nabidku ji zavre. Bez toho by zustala
        // viset, dokud na ni clovek neklikne znovu.
        useExternalListener(window, "click", () => {
            this.stav.nabidka = false;
        });

        onWillStart(async () => {
            this.stav.cisla = await this.orm.call("hh.admin", "hh_cisla", []);
            await this.nacti();
        });
    }

    async nacti() {
        this.stav.nacita = true;
        const o = this.stav.obrazovka;
        try {
            if (o === "nastenka") {
                this.stav.data = await this.orm.call("hh.admin", "hh_nastenka", []);
            } else if (o === "lide") {
                this.stav.data = await this.orm.call("hh.admin", "hh_lide",
                    [this.stav.hledani, this.stav.stupen]);
            } else if (o === "vyzva") {
                this.stav.data = await this.orm.call("hh.admin", "hh_vyzva", []);
            } else if (o === "hovory") {
                this.stav.data = await this.orm.call("hh.admin", "hh_hovory", []);
            } else if (o === "sekvence") {
                this.stav.data = await this.orm.call("hh.admin", "hh_sekvence", []);
            } else if (o === "stitky") {
                this.stav.data = await this.orm.call("hh.admin", "hh_stitky", []);
            } else {
                this.stav.data = await this.orm.call("hh.admin", "hh_statistiky", []);
            }
        } finally {
            this.stav.nacita = false;
        }
    }

    async prepni(klic) {
        this.stav.nabidka = false;
        if (this.stav.obrazovka === klic) {
            return;
        }
        this.stav.obrazovka = klic;
        this.stav.data = null;
        await this.nacti();
    }

    prepniNabidku(udalost) {
        // Bez zastaveni by ji hned zavrel posluchac na okne.
        udalost.stopPropagation();
        this.stav.nabidka = !this.stav.nabidka;
    }

    async hledej(udalost) {
        this.stav.hledani = udalost.target.value;
        await this.nacti();
    }

    async filtrujStupen(udalost) {
        const v = udalost.target.value;
        this.stav.stupen = v ? parseInt(v, 10) : null;
        await this.nacti();
    }

    /* Nejvyssi sloupec urcuje merítko, aby se dal graf precist
       i kdyz jsou cisla mala. */
    vyska(pocet, data) {
        const max = Math.max(...data.map((d) => d.pocet), 1);
        return Math.round((pocet / max) * 100) + "%";
    }

    zacniTahnout(karta, sloupec, udalost) {
        this.stav.tazena = { id: karta.id, zeSloupce: sloupec.id };
        // Bez dataTransfer nekterе prohlizece tazeni vubec nezahaji.
        if (udalost.dataTransfer) {
            udalost.dataTransfer.effectAllowed = "move";
            udalost.dataTransfer.setData("text/plain", String(karta.id));
        }
    }

    prestanTahnout() {
        this.stav.tazena = null;
        this.stav.cil = null;
    }

    nadSloupcem(sloupec, udalost) {
        // Bez tohohle prohlizec pusteni vubec nedovoli.
        udalost.preventDefault();
        if (udalost.dataTransfer) {
            udalost.dataTransfer.dropEffect = "move";
        }
        if (this.stav.tazena && this.stav.cil !== sloupec.id) {
            this.stav.cil = sloupec.id;
        }
    }

    opustilSloupec(sloupec) {
        if (this.stav.cil === sloupec.id) {
            this.stav.cil = null;
        }
    }

    async pustNaSloupec(sloupec) {
        const t = this.stav.tazena;
        this.stav.tazena = null;
        this.stav.cil = null;
        if (!t || t.zeSloupce === sloupec.id) {
            return;
        }

        // Karta se prehodi rovnou tady, jeste pred zapisem. Drive se
        // cekalo na server a deska se pak nacetla cela znovu - pri
        // kazdem presunu to bliklo a karta na okamzik zmizela.
        const zdroj = this.stav.data.find((s) => s.id === t.zeSloupce);
        const cil = this.stav.data.find((s) => s.id === sloupec.id);
        if (!zdroj || !cil) {
            return;
        }
        const kde = zdroj.karty.findIndex((k) => k.id === t.id);
        if (kde < 0) {
            return;
        }
        const karta = zdroj.karty[kde];
        zdroj.karty.splice(kde, 1);
        zdroj.celkem -= 1;
        cil.karty.unshift(karta);
        cil.celkem += 1;

        // Bezny zapis, at plati stejna pravidla jako doted: presun
        // do sloupce spusti e-maily navazane na jeho stitky.
        await this.orm.write("crm.lead", [t.id], { stage_id: sloupec.id });
        // Jen cisla nahore. Celou desku uz nacitat netreba, na
        // obrazovce sedi spravne.
        this.stav.cisla = await this.orm.call("hh.admin", "hh_cisla", []);
    }

    // ------------------------------------------------------------------
    // nova sekce
    //
    // Jde toutez cestou jako sekce zalozena formularem z webu, takze
    // vznikne sloupec i oba stitky a jsou spolu svazane.
    // ------------------------------------------------------------------

    zacniSekci() {
        this.stav.novaSekce = "";
    }

    zrusSekci() {
        this.stav.novaSekce = null;
    }

    pisSekci(udalost) {
        this.stav.novaSekce = udalost.target.value;
    }

    async klavesaSekce(udalost) {
        if (udalost.key === "Enter") {
            await this.ulozSekci();
        } else if (udalost.key === "Escape") {
            this.zrusSekci();
        }
    }

    async ulozSekci() {
        const nazev = (this.stav.novaSekce || "").trim();
        if (!nazev) {
            this.stav.novaSekce = null;
            return;
        }
        await this.orm.call("hh.admin", "hh_pridat_sekci", [nazev]);
        this.stav.novaSekce = null;
        await this.nacti();
    }

    // --- karta do sloupce ---
    //
    // Otevre bezny formular s predvyplnenym sloupcem. Vlastni rychle
    // zalozeni by znamenalo obejit kontroly, ktere formular dela.
    pridejKartu(sloupec) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            views: [[false, "form"]],
            target: "current",
            context: { default_stage_id: sloupec.id },
        });
    }

    // --- prejmenovani sloupce ---

    zacniPrejmenovat(sloupec, udalost) {
        udalost.stopPropagation();
        this.stav.prejmenovavana = { id: sloupec.id, nazev: sloupec.nazev };
    }

    pisNazev(udalost) {
        this.stav.prejmenovavana.nazev = udalost.target.value;
    }

    async klavesaNazev(udalost) {
        if (udalost.key === "Enter") {
            await this.ulozNazev();
        } else if (udalost.key === "Escape") {
            this.stav.prejmenovavana = null;
        }
    }

    async ulozNazev() {
        const p = this.stav.prejmenovavana;
        this.stav.prejmenovavana = null;
        if (!p || !p.nazev.trim()) {
            return;
        }
        await this.orm.call("hh.admin", "hh_prejmenovat_sekci", [p.id, p.nazev]);
        await this.nacti();
    }

    // --- smazani sloupce ---

    async smazSekci(sloupec, udalost) {
        udalost.stopPropagation();
        const odpoved = await this.orm.call("hh.admin", "hh_smazat_sekci", [sloupec.id]);
        if (!odpoved.ok) {
            // Hlaska rovnou u sloupce, ne v rohu obrazovky - clovek
            // se diva sem.
            this.stav.hlaska = odpoved.duvod;
            return;
        }
        this.stav.hlaska = null;
        this.stav.cisla = await this.orm.call("hh.admin", "hh_cisla", []);
        await this.nacti();
    }

    kdy(zprava) {
        return zprava.po_dnech ? `${zprava.po_dnech}. den` : "hned";
    }

    async prepniOdesilani(zprava) {
        // Zapis napred, at prepinac nereaguje se zpozdenim.
        zprava.zapnuto = !zprava.zapnuto;
        await this.orm.write("hh.mail.sablona", [zprava.id], { zapnuto: zprava.zapnuto });
    }

    // ------------------------------------------------------------------
    // odskoky do bezneho formulare
    //
    // Upravy se zamerne otviraji tam: sedi v nem veci, ktere by
    // prepsani stalo - editor e-mailu i historie u prilezitosti.
    // ------------------------------------------------------------------

    otevriLead(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    otevriZpravu(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.sablona",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    pridejZpravu(stitek) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.sablona",
            views: [[false, "form"]],
            target: "current",
            context: stitek.id ? { default_stitek_id: stitek.id } : {},
        });
    }

    otevriStitek(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.stitek",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    pridejStitek() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.stitek",
            views: [[false, "form"]],
            target: "current",
        });
    }

    otevriKalendar() {
        this.stav.nabidka = false;
        this.action.doAction("honzahauzr_crm.hh_terminy_kalendar_action");
    }

    otevriNastenku() {
        this.stav.nabidka = false;
        this.action.doAction("crm.crm_lead_action_pipeline");
    }
}

registry.category("actions").add("hh_admin", HhAdmin);
