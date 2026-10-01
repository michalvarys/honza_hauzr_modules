/** @odoo-module **/

/**
 * Tlacitka "Nahrát video" v pravem panelu editoru.
 *
 * Odoo ma hotove vybiratko na obrazky i na videa z YouTube, ale na
 * nahrany soubor zadne - a hlavne nahrava cely soubor jednim
 * pozadavkem. Na ostrem webu to neprojde: pred Odoo stoji WAF, ktery
 * vetsi pozadavek utne a vrati HTML chybovou stranku. Odoo misto
 * odpovedi dostane necekany text, upload tise skonci a v editoru to
 * vypada, ze tlacitko nereaguje.
 *
 * Proto tohle video kraji a posila po kouscich - viz protejsek
 * v controllers/nahravani.py. Zadny jednotlivy pozadavek neni velky,
 * takze na strop WAF ani Cloudflare nenarazi.
 *
 * Adresy jsou dve, stejne jako u videi z YouTube: jedna pro sirokou
 * verzi na pocitac, druha pro svislou na mobil. Stranka podle sirky
 * vybere, kterou pustit. Nahled videa se meni jako kterykoliv jiny
 * obrazek - dvojklikem primo na nej.
 */

import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/* Musi sedet s KOUSEK v controllers/nahravani.py. Merenim: 300 kB
   projde, 600 kB uz WAF utne; 200 kB necha rezervu i potom, co
   base64 objem zvedne o tretinu. */
const KOUSEK = 200 * 1024;

const POVOLENE = ["mp4", "webm", "mov", "m4v", "ogv"];

/**
 * Prevede kus souboru na base64.
 *
 * Pres FileReader, protoze btoa() by na binarnich datech spadlo
 * a String.fromCharCode na celem kousku taky neni zadarmo.
 *
 * @param {Blob} kus
 * @returns {Promise<string>} base64 bez hlavicky "data:...;base64,"
 */
function naBase64(kus) {
    return new Promise((hotovo, chyba) => {
        const cteni = new FileReader();
        cteni.onload = () => hotovo(String(cteni.result).split(",")[1] || "");
        cteni.onerror = () => chyba(cteni.error);
        cteni.readAsDataURL(kus);
    });
}

options.registry.hhVideoSoubor = options.Class.extend({
    /**
     * @override
     */
    start() {
        this._hhBezi = false;
        return this._super(...arguments);
    },

    /**
     * Video na sirku, pro pocitac.
     */
    async vybratSoubor(previewMode) {
        await this._hhVybrat(previewMode, "hhvSoubor");
    },

    /**
     * Video na vysku, pro mobil.
     */
    async vybratSouborMobil(previewMode) {
        await this._hhVybrat(previewMode, "hhvSouborMobil");
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Otevre vyber souboru a vybrane video nahraje na web.
     *
     * @private
     * @param {boolean} previewMode
     * @param {string} znacka nazev data atributu v camelCase
     */
    async _hhVybrat(previewMode, znacka) {
        // Odoo vola metody i pri najeti mysi kvuli nahledu. Vyber
        // souboru se ma otevrit az po skutecnem kliknuti.
        if (previewMode || this._hhBezi) {
            return;
        }

        const soubor = await this._hhVyberSoubor();
        if (!soubor) {
            return;
        }

        const pripona = (soubor.name.split(".").pop() || "").toLowerCase();
        if (!POVOLENE.includes(pripona)) {
            this._hhHlaska(
                _t("Tenhle typ souboru nejde nahrát. Povolené jsou: %s.",
                   POVOLENE.join(", ")),
                "danger"
            );
            return;
        }

        this._hhBezi = true;
        try {
            const adresa = await this._hhNahraj(soubor);
            if (adresa) {
                this.$target[0].dataset[znacka] = adresa;
                this._hhHlaska(_t("Video je nahrané."), "success");
            }
        } finally {
            this._hhBezi = false;
            this._hhPrubeh(null);
        }
    },

    /**
     * Otevre systemovy vyber souboru a pocka na vybrane video.
     *
     * @private
     * @returns {Promise<File|null>}
     */
    _hhVyberSoubor() {
        return new Promise((hotovo) => {
            const vstup = document.createElement("input");
            vstup.type = "file";
            vstup.accept = "video/*";
            vstup.style.display = "none";
            document.body.appendChild(vstup);
            vstup.addEventListener("change", () => {
                const soubor = vstup.files && vstup.files[0];
                vstup.remove();
                hotovo(soubor || null);
            });
            // Kdyz vyber nekdo zavre bez vybrani, zadna udalost
            // neprijde. Uklid po navratu do okna to dorovna.
            window.addEventListener("focus", function uklid() {
                window.removeEventListener("focus", uklid);
                setTimeout(() => {
                    if (vstup.isConnected && !(vstup.files || []).length) {
                        vstup.remove();
                        hotovo(null);
                    }
                }, 500);
            });
            vstup.click();
        });
    },

    /**
     * Posle video po kouscich a vrati jeho adresu na webu.
     *
     * @private
     * @param {File} soubor
     * @returns {Promise<string|null>}
     */
    async _hhNahraj(soubor) {
        const pocet = Math.max(1, Math.ceil(soubor.size / KOUSEK));

        for (let i = 0; i < pocet; i++) {
            const kus = soubor.slice(i * KOUSEK, (i + 1) * KOUSEK);
            let odpoved;
            try {
                odpoved = await rpc("/hh/nahravani/kousek", {
                    nazev: soubor.name,
                    poradi: i,
                    celkem: pocet,
                    data: await naBase64(kus),
                });
            } catch {
                // Sem to spadne, kdyz pozadavek nedorazi cely nebo se
                // misto odpovedi vrati neco jineho nez JSON.
                await this._hhZrus(soubor.name);
                this._hhHlaska(
                    _t("Nahrávání se přerušilo. Zkus to prosím znovu."),
                    "danger"
                );
                return null;
            }
            if (odpoved && odpoved.chyba) {
                await this._hhZrus(soubor.name);
                this._hhHlaska(odpoved.chyba, "danger");
                return null;
            }
            this._hhPrubeh(Math.round(((i + 1) / pocet) * 100));
        }

        const konec = await rpc("/hh/nahravani/dokonci", {
            nazev: soubor.name,
        });
        if (!konec || konec.chyba) {
            this._hhHlaska(
                (konec && konec.chyba) || _t("Video se nepodařilo uložit."),
                "danger"
            );
            return null;
        }
        return konec.adresa;
    },

    /**
     * @private
     * @param {string} nazev
     */
    async _hhZrus(nazev) {
        try {
            await rpc("/hh/nahravani/zrus", { nazev });
        } catch {
            // Uklid je jen laskavost, rozdelany soubor nikomu nevadi.
        }
    },

    /**
     * Ukaze, jak daleko nahravani je.
     *
     * Bez tohohle by clovek u delsiho videa koukal na nehybny panel
     * a myslel si, ze se nic nedeje - presne to byla puvodni potiz.
     *
     * @private
     * @param {number|null} procenta null schova ukazatel
     */
    _hhPrubeh(procenta) {
        const skupina = this.$el && this.$el[0];
        if (!skupina) {
            return;
        }
        let pruh = skupina.querySelector(".hhv-prubeh");
        if (procenta === null) {
            if (pruh) {
                pruh.remove();
            }
            return;
        }
        if (!pruh) {
            pruh = document.createElement("div");
            pruh.className = "hhv-prubeh";
            pruh.style.cssText =
                "color:#b4b8bf;font-size:11px;padding:4px 0;text-align:center;";
            skupina.appendChild(pruh);
        }
        pruh.textContent = _t("Nahrávám video… %s %%", procenta);
    },

    /**
     * @private
     * @param {string} zprava
     * @param {string} druh
     */
    _hhHlaska(zprava, druh) {
        this.call("notification", "add", zprava, {
            type: druh,
            sticky: druh === "danger",
        });
    },
});

export default options.registry.hhVideoSoubor;
