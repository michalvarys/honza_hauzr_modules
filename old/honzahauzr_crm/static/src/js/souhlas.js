/** @odoo-module **/

/**
 * Hlídá souhlas se zpracováním údajů ve formulářích na webu.
 *
 * Políčko má v šabloně required, jenže na to se spolehnout nedá:
 * tlačítko „Odeslat nezávaznou přihlášku" na starší stránce je
 * odkaz, ne odesílací tlačítko, takže prohlížeč formulář nevaliduje
 * vůbec. Odesílalo se i bez zaškrtnutí.
 *
 * Tohle je rychlá odpověď pro člověka u obrazovky. Skutečnou
 * pojistkou je kontrola na serveru (models/crm_lead_souhlas.py) -
 * ta platí i pro toho, kdo si políčko odškrtne v nástrojích
 * prohlížeče.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.hhSouhlas = publicWidget.Widget.extend({
    selector: "form:has(.hh-souhlas input)",
    events: {
        "click button[type='submit'], click .s_website_form_send": "_overit",
        "submit": "_overit",
        "change .hh-souhlas input": "_schovatHlasku",
    },

    /**
     * Pustí odeslání jen se zaškrtnutým souhlasem.
     *
     * Odoo odesílá formulář kliknutím na tlačítko, takže se hlídá
     * i klik - samotné "submit" by u odkazu nikdy nenastalo.
     */
    _overit(ev) {
        const policko = this.el.querySelector(".hh-souhlas input");
        if (!policko || policko.checked) {
            return true;
        }
        ev.preventDefault();
        ev.stopImmediatePropagation();
        const label = policko.closest(".hh-souhlas");
        if (label) {
            label.classList.add("hh-souhlas--chyba");
            label.scrollIntoView({ block: "center", behavior: "smooth" });
        }
        policko.focus();
        return false;
    },

    _schovatHlasku() {
        const label = this.el.querySelector(".hh-souhlas");
        if (label) {
            label.classList.remove("hh-souhlas--chyba");
        }
    },
});

export default publicWidget.registry.hhSouhlas;
