/** @odoo-module **/

/**
 * Stranka tridenni vyzvy - odpocet u zamcenych dnu.
 *
 * Video si ke kazdemu dni vklada Honza sam v editoru, jako kterykoliv
 * jiny video blok - odkazem na YouTube nebo Vimeo. Ve strance je proto
 * ulozene i u dnu, ktere jeste nejsou odemcene.
 *
 * Aby zamek nebyl jen na oko, vyrizne server zamcene dny z uz hotove
 * odpovedi, tesne nez odejde do prohlizece, a misto videa tam vlozi
 * zamek (models/ir_http.py). Do zdroje stranky se tak zamcene video
 * vubec nedostane. Kdo web upravuje, vidi vsechny tri dny - jinak by
 * si k nim video nemel jak vlozit.
 *
 * Tomuhle skriptu proto zbyvaji dve drobnosti: rozpohybovat odpocet
 * u zamcenych dnu a nabidnout policko na e-mail tomu, koho server
 * nepozna. Bez odpoctu by cislo po nacteni zamrzlo a kdo necha
 * stranku otevrenou, videl by po hodine porad totez.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

function escapuj(text) {
    const d = document.createElement("div");
    d.textContent = text == null ? "" : String(text);
    return d.innerHTML;
}

function dva(n) {
    return String(n).padStart(2, "0");
}

publicWidget.registry.hhVyzvaDny = publicWidget.Widget.extend({
    selector: ".s_hh_vyzva_dny",
    // V editoru se nespousti. Honza tam upravuje nadpisy dnu, ne
    // odpocty - a hlavne se tim do stranky neulozi nic vykresleneho.
    disabledInEditableMode: true,

    /**
     * @override
     */
    async start() {
        // _super se musi zavolat driv, nez se na cokoliv ceka. Stara
        // tridni nadstavba Odoo ho nastavuje jen na dobu synchronniho
        // behu metody - po prvnim awaitu uz this._super neexistuje.
        const rodic = this._super(...arguments);

        this.odpocty = [];
        try {
            // Klic z odkazu v e-mailu je v adrese stranky, ne v tomhle
            // pozadavku - musi se predat rucne, jinak by odkaz
            // z e-mailu prestal ucastnika rozpoznavat.
            const klic = new URLSearchParams(window.location.search).get("k");
            const stav = await rpc("/zpet-do-zivota/vyzva/stav", klic ? { k: klic } : {});
            this._vykresli(stav);
        } catch (chyba) {
            this._selhalo();
            throw chyba;
        }

        return rodic;
    },

    /**
     * @override
     */
    destroy() {
        this.odpocty.forEach((id) => clearInterval(id));
        this.odpocty = [];
        this._super(...arguments);
    },

    // ------------------------------------------------------------------
    // vykresleni
    // ------------------------------------------------------------------

    _vykresli(stav) {
        const obnova = this.el.querySelector("[data-hhd-obnova]");
        if (obnova) {
            obnova.innerHTML = stav.zname ? "" : this._obnovaHtml();
        }

        // Zamky uz na strance jsou - server je vyrizl misto videa
        // u dnu, na ktere navstevnik jeste nema narok (viz
        // models/ir_http.py). Skript je jen rozpohybuje, aby cislo
        // nezamrzlo tomu, kdo necha stranku otevrenou.
        for (const zamek of this.el.querySelectorAll(".hhd-zamek")) {
            this._spustOdpocet(zamek);
        }

    },


    _selhalo() {
        const obnova = this.el.querySelector("[data-hhd-obnova]");
        if (obnova) {
            obnova.innerHTML =
                '<p class="hhd-micro">Obsah se nepodařilo načíst. Zkus stránku načíst znovu.</p>';
        }
    },

    _obnovaHtml() {
        const chyba = new URLSearchParams(window.location.search).has("chyba")
            ? '<p class="hhd-chyba">Tuhle adresu mezi přihlášenými nevidím. ' +
              'Zkontroluj ji, nebo se <a href="/zpet-do-zivota">přihlas do výzvy</a>.</p>'
            : "";
        const token = document.querySelector('meta[name="csrf_token"]');
        return (
            '<div class="hhd-hlaska"><p><b>Nevím, kdo jsi.</b></p>' +
            '<p class="hhd-micro">Otevři odkaz z e-mailu, nebo mi tady napiš adresu, ' +
            "kterou jsi zadal při přihlášení – podle ní ti odemknu dny, " +
            "na které už máš nárok.</p>" +
            '<form class="hhd-obnova" action="/zpet-do-zivota/vyzva/obnovit" method="post">' +
            '<input type="hidden" name="csrf_token" value="' +
            escapuj(token ? token.content : odoo.csrf_token) + '"/>' +
            '<input type="email" name="email" required="required" autocomplete="email"' +
            ' placeholder="E-mail, kterým ses přihlásil"/>' +
            "<button type=\"submit\">Pokračovat</button></form>" + chyba + "</div>"
        );
    },

    // ------------------------------------------------------------------
    // odpocet
    // ------------------------------------------------------------------

    _spustOdpocet(zamek) {
        if (!zamek || !zamek.dataset.odemkneSe) {
            return;
        }
        const cil = new Date(zamek.dataset.odemkneSe).getTime();
        const text = zamek.querySelector(".hhd-zamek__text");
        if (!cil || !text) {
            return;
        }

        /* Obe promenne musi vzniknout drive, nez se prekresli() poprve
           zavola. Kdyz uz cas odemceni uplynul, skonci prvni volani
           hned v te vetvi dole - a sahlo by na id, ktere by jeste
           neexistovalo. Prohlizec na to odpovi vyjimkou
           "Cannot access 'id' before initialization" a cely skript
           stranky se zastavi. */
        let id = null;
        let hotovo = false;

        const prekresli = () => {
            const zbyva = cil - Date.now();
            if (zbyva <= 0) {
                hotovo = true;
                if (id !== null) {
                    clearInterval(id);
                    id = null;
                }
                text.textContent = "Odemykám…";
                // Jedno nacteni navic, ne opakovane - kdyby se server
                // s prohlizecem rozesel o par vterin, stranka by se
                // jinak tocila dokola.
                window.setTimeout(() => window.location.reload(), 1200);
                return;
            }
            const celkem = Math.floor(zbyva / 1000);
            const h = Math.floor(celkem / 3600);
            const m = Math.floor((celkem % 3600) / 60);
            const s = celkem % 60;
            text.textContent = `Odemkne se za ${dva(h)}:${dva(m)}:${dva(s)}`;
        };

        prekresli();

        /* Kdyz uz je po case, stranka se za chvili sama nacte znovu -
           tikat vterinu po vterine do te doby nema smysl. */
        if (!hotovo) {
            id = setInterval(prekresli, 1000);
            this.odpocty.push(id);
        }
    },
});
