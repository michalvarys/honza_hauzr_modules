/** @odoo-module **/

/**
 * Kam lidi na webu klikaji.
 *
 * Honza se pta, co na strance funguje: ktere tlacitko lidi mackaji
 * a ktereho si nikdo nevsimne. Z CRM to nevycte - tam se objevi az
 * ten, kdo formular opravdu odeslal.
 *
 * Posloucha se jedno kliknuti na celem dokumentu, ne poslucac na
 * kazdem odkazu: odkazu je na strance pres sto a cast z nich doplni
 * skripty az pozdeji, takze by se na ne nedostalo.
 *
 * Hlasi se jen odkazy a tlacitka, ne kazde kliknuti do stranky -
 * jinak by v prehledu prevazily kliky do prazdna. Posila se adresa
 * stranky, popisek prvku a kam vede; nic o navstevnikovi.
 *
 * Mereni nesmi nikdy stat v ceste tomu, kvuli cemu clovek na stranku
 * prisel. Posila se bez cekani a chyby se mlcky polykaji.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/* Delka popisku. Tlacitko ma par slov, ale kliknout jde i na
   odstavec s odkazem - z toho by byl v prehledu roman. */
const POPIS_MAX = 120;

/* Stejny prvek rozklikany dokola behem par vterin je jeden umysl,
   ne pet. Bez tohohle by netrpeliva dvojkliknuti nafoukla cisla. */
const UTLUM_MS = 1500;

function popisek(prvek) {
    const text = (prvek.innerText || prvek.textContent || "").trim();
    if (text) {
        return text.replace(/\s+/g, " ").slice(0, POPIS_MAX);
    }
    // Obrazkove odkazy a ikony text nemaji - vezme se popis obrazku
    // nebo nazev pro odecitace obrazovky.
    const obrazek = prvek.querySelector("img[alt]");
    return (
        prvek.getAttribute("aria-label") ||
        prvek.getAttribute("title") ||
        (obrazek && obrazek.getAttribute("alt")) ||
        ""
    ).trim().slice(0, POPIS_MAX);
}

publicWidget.registry.hhWebKlik = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    // V editoru ne: Honza tam klika na bloky, ktere upravuje, a do
    // statistiky by to spadlo jako zajem navstevniku.
    disabledInEditableMode: true,

    /**
     * @override
     */
    start() {
        this.posledni = new Map();
        this._naKlik = (udalost) => this._zapis(udalost);
        this.el.addEventListener("click", this._naKlik, true);
        return this._super(...arguments);
    },

    /**
     * @override
     */
    destroy() {
        if (this._naKlik) {
            this.el.removeEventListener("click", this._naKlik, true);
        }
        this._super(...arguments);
    },

    _zapis(udalost) {
        const prvek =
            udalost.target && udalost.target.closest
                ? udalost.target.closest("a, button, [role='button']")
                : null;
        if (!prvek) {
            return;
        }

        const popis = popisek(prvek);
        if (!popis) {
            return;
        }

        const odkaz = prvek.getAttribute("href") || "";
        // Kotvy a javascript: nikam nevedou, ale kliknuti na ne je
        // porad informace - ukladaji se s prazdnym cilem.
        const cil = /^(https?:|\/)/.test(odkaz) ? odkaz : "";

        const klic = popis + "|" + cil;
        const ted = Date.now();
        if (ted - (this.posledni.get(klic) || 0) < UTLUM_MS) {
            return;
        }
        this.posledni.set(klic, ted);

        // Bez await a bez hlaseni chyb: odkaz uz odchazi a cekat na
        // odpoved by jen zdrzovalo.
        rpc("/hh/klik", {
            stranka: window.location.pathname,
            popis: popis,
            cil: cil,
        }).catch(() => {});
    },
});
