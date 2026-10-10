/** @odoo-module **/

/**
 * Prehled sekvenci e-mailu.
 *
 * Proc vlastni obrazovka a ne seznam od Odoo: seznam seskupeny podle
 * stitku sice totez ukaze, ale nese s sebou filtry, razeni, vyber
 * sloupcu a hromadne akce - vsechno veci, ktere tady nejsou k nicemu
 * a jen zdrzuji. Honza potrebuje videt jednu vec: ktery stitek posila
 * ktere zpravy a v jakem poradi.
 *
 * Usporadani zustava presne takove, jake uz je v datech - stitek
 * a pod nim jeho zpravy serazene podle odstupu ve dnech. Nic se tu
 * nepredelava, jen se to ukazuje bez balastu.
 *
 * Upravy zpravy se otviraji v beznem formulari, protoze v nem sedi
 * editor z Email Marketingu. Prepsat ho by znamenalo prijit o nej.
 */

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class MailyPrehled extends Component {
    static template = "honzahauzr_crm.MailyPrehled";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.stav = useState({ stitky: [], nacita: true });

        onWillStart(async () => {
            await this.nacti();
        });
    }

    async nacti() {
        this.stav.nacita = true;

        const stitky = await this.orm.searchRead(
            "hh.mail.stitek", [], ["name", "color"], { order: "name" }
        );
        const zpravy = await this.orm.searchRead(
            "hh.mail.sablona", [], ["name", "predmet", "po_dnech", "zapnuto", "stitek_id"],
            { order: "po_dnech, id" }
        );

        // Zpravy k svym stitkum. Poradi uz z databaze sedi, takze
        // staci je rozradit.
        const podleStitku = {};
        for (const z of zpravy) {
            const id = z.stitek_id ? z.stitek_id[0] : 0;
            (podleStitku[id] = podleStitku[id] || []).push(z);
        }

        this.stav.stitky = stitky.map((s) => ({
            ...s,
            zpravy: podleStitku[s.id] || [],
        }));

        // Zpravy bez stitku by jinak zmizely ze sveta - nikde jinde
        // uz se neukazuji.
        if (podleStitku[0]) {
            this.stav.stitky.push({
                id: 0,
                name: _t("Bez štítku"),
                zpravy: podleStitku[0],
            });
        }

        this.stav.nacita = false;
    }

    kdy(zprava) {
        if (!zprava.po_dnech) {
            return _t("hned");
        }
        return _t("%s. den", zprava.po_dnech);
    }

    async prepni(zprava) {
        // Zapis napred, at tlacitko nereaguje se zpozdenim.
        zprava.zapnuto = !zprava.zapnuto;
        await this.orm.write("hh.mail.sablona", [zprava.id], { zapnuto: zprava.zapnuto });
    }

    otevri(zprava) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.sablona",
            res_id: zprava.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    pridej(stitek) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hh.mail.sablona",
            views: [[false, "form"]],
            target: "current",
            context: stitek.id ? { default_stitek_id: stitek.id } : {},
        });
    }

    otevriStitky() {
        this.action.doAction("honzahauzr_crm.action_hh_mail_stitek");
    }
}

registry.category("actions").add("hh_maily_prehled", MailyPrehled);
