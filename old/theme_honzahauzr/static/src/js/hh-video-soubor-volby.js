/** @odoo-module **/

/**
 * Tlacitka "Nahrát video" v pravem panelu editoru.
 *
 * Odoo ma hotove vybiratko na obrazky (we-imagepicker) i na videa
 * z YouTube (we-videopicker), ale na nahrany soubor zadne. Tohle ho
 * doplnuje: otevre bezny dialog "Vyberte média" na zalozce Dokumenty,
 * kde se soubor nahraje, a adresu vybraneho souboru zapise na blok.
 * Odtud si ji bere hh-video-soubor.js.
 *
 * Adresy jsou dve, stejne jako u videi z YouTube: jedna pro sirokou
 * verzi na pocitac, druha pro svislou na mobil. Stranka podle sirky
 * vybere, kterou pustit.
 *
 * Nahled videa se meni jako kterykoliv jiny obrazek - dvojklikem
 * primo na nej, k tomu neni potreba nic navic.
 */

import options from "@web_editor/js/editor/snippets.options";
import { MediaDialog } from "@web_editor/components/media_dialog/media_dialog";

/**
 * Dialog vraci u dokumentu adresu s "download=true". Takovy odkaz
 * posle prohlizeci hlavicku "ulozit jako" a video by se misto
 * prehrani nabidlo ke stazeni. Pro <video src> ho potrebujeme bez ni.
 *
 * @param {string} adresa
 * @returns {string}
 */
function ocisti(adresa) {
    const delic = adresa.indexOf("?");
    if (delic === -1) {
        return adresa;
    }
    const zbyle = adresa
        .slice(delic + 1)
        .split("&")
        .filter((dvojice) => dvojice !== "download=true");
    return zbyle.length
        ? adresa.slice(0, delic) + "?" + zbyle.join("&")
        : adresa.slice(0, delic);
}

options.registry.hhVideoSoubor = options.Class.extend({
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
     * Otevre dialog s dokumenty a adresu vybraneho souboru ulozi na
     * blok pod zadanou znacku.
     *
     * @private
     * @param {boolean} previewMode
     * @param {string} znacka nazev data atributu v camelCase
     */
    async _hhVybrat(previewMode, znacka) {
        // Odoo vola metody i pri najeti mysi kvuli nahledu. Dialog se
        // ma otevrit az po skutecnem kliknuti.
        if (previewMode) {
            return;
        }

        const blok = this.$target[0];
        await new Promise((hotovo) => {
            this.call(
                "dialog",
                "add",
                MediaDialog,
                {
                    noImages: true,
                    noVideos: true,
                    noIcons: true,
                    noDocuments: false,
                    save: (prvek) => {
                        const adresa =
                            prvek.getAttribute("href") ||
                            prvek.getAttribute("src") ||
                            "";
                        if (adresa) {
                            blok.dataset[znacka] = ocisti(adresa);
                        }
                    },
                },
                { onClose: () => hotovo() }
            );
        });
    },
});

export default options.registry.hhVideoSoubor;
