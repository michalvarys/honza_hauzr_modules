/** @odoo-module **/

/**
 * Administrace Honzy Hauzra.
 *
 * Jedna obrazovka se ctyrmi zalozkami misto peti ruznych pohledu
 * Odoo. Duvod je praktický: Honza potrebuje videt lidi, vyzvu
 * a hovory, ne filtry, razeni, vyber sloupcu a chatter. Co tu neni,
 * je zamerne pryc.
 *
 * Data chodi po zalozkach z modelu hh.admin, vzdycky jednim dotazem.
 * Pri prepnuti zalozky by se jinak poslalo nekolik dotazu za sebou
 * a cisla by naskakovala postupne.
 *
 * Nic se tu nepocita znovu a nic se tu nezapisuje - obrazovka data
 * jen ukazuje. Upravy se otviraji v beznem formulari, protoze v nem
 * sedi vec, kterou by prepsani stalo: editor e-mailu, kalendar,
 * chatter u prilezitosti.
 */

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const ZALOZKY = [
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

        this.stav = useState({
            zalozka: "lide",
            nacita: true,
            cisla: null,
            data: null,
            hledani: "",
            stupen: null,
        });

        onWillStart(async () => {
            this.stav.cisla = await this.orm.call("hh.admin", "hh_cisla", []);
            await this.nacti();
        });
    }

    async nacti() {
        this.stav.nacita = true;
        const z = this.stav.zalozka;
        try {
            if (z === "lide") {
                this.stav.data = await this.orm.call("hh.admin", "hh_lide",
                    [this.stav.hledani, this.stav.stupen]);
            } else if (z === "vyzva") {
                this.stav.data = await this.orm.call("hh.admin", "hh_vyzva", []);
            } else if (z === "hovory") {
                this.stav.data = await this.orm.call("hh.admin", "hh_hovory", []);
            } else {
                this.stav.data = await this.orm.call("hh.admin", "hh_statistiky", []);
            }
        } finally {
            this.stav.nacita = false;
        }
    }

    async prepni(klic) {
        if (this.stav.zalozka === klic) {
            return;
        }
        this.stav.zalozka = klic;
        this.stav.data = null;
        await this.nacti();
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

    otevriLead(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    otevriKalendar() {
        this.action.doAction("honzahauzr_crm.hh_terminy_kalendar_action");
    }

    otevriSekvence() {
        this.action.doAction("honzahauzr_crm.action_hh_maily_prehled");
    }
}

registry.category("actions").add("hh_admin", HhAdmin);
