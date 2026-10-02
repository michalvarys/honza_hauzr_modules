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

/* Musi sedet s KOUSEK v controllers/nahravani.py. Merenim na
   ostrem webu: 360 kB jeste projde, 420 kB uz WAF utne. */
const KOUSEK = 300 * 1024;

/* Kolik kousku letí soucasne.

   Rezie jednoho pozadavku je zhruba 0,7 s, zatimco server ho
   odbavi za 0,07 s - cekani na sit tedy naprosto prevazuje.
   Posilat kousky jeden po druhem znamenalo u videa na 260 MB
   sedmnact minut a nahravani se cestou utrhlo. Sest soucasne
   to srazi pod tri minuty. Vic uz nema smysl, zacala by se
   ucpavat linka pri odesilani. */
const SOUCASNE = 6;

/* Kolikrat zkusit kousek znovu, nez to vzdame. Pri stovkach
   pozadavku je skoro jiste, ze nektery obcas selze; bez
   opakovani by kvuli jedinemu propadlo cele nahravani. */
const POKUSU = 3;

const POVOLENE = ["mp4", "webm", "mov", "m4v", "ogv"];

/* Titulky. WebVTT je jediny format, kteremu prohlizece rozumi -
   soubory .srt je potreba prevest. */
const POVOLENE_TITULKY = ["vtt"];

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

    /**
     * Titulky k videu.
     */
    async vybratTitulky(previewMode) {
        await this._hhVybrat(previewMode, "hhvTitulky", POVOLENE_TITULKY, ".vtt");
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
    async _hhVybrat(previewMode, znacka, povolene, prijima) {
        povolene = povolene || POVOLENE;
        // Odoo vola metody i pri najeti mysi kvuli nahledu. Vyber
        // souboru se ma otevrit az po skutecnem kliknuti.
        if (previewMode || this._hhBezi) {
            return;
        }

        const soubor = await this._hhVyberSoubor(prijima);
        if (!soubor) {
            return;
        }

        const pripona = (soubor.name.split(".").pop() || "").toLowerCase();
        if (!povolene.includes(pripona)) {
            this._hhHlaska(
                _t("Tenhle typ souboru nejde nahrát. Povolené jsou: %s.",
                   povolene.join(", ")),
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
    _hhVyberSoubor(prijima) {
        return new Promise((hotovo) => {
            const vstup = document.createElement("input");
            vstup.type = "file";
            vstup.accept = prijima || "video/*";
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
    /**
     * Posle jeden kousek a pri selhani ho zkusi znovu.
     *
     * @private
     * @returns {Promise<string|null>} text chyby, nebo null pri uspechu
     */
    async _hhPosliKousek(soubor, davka, poradi, pocet) {
        const kus = soubor.slice(poradi * KOUSEK, (poradi + 1) * KOUSEK);
        const data = await naBase64(kus);

        for (let pokus = 1; pokus <= POKUSU; pokus++) {
            try {
                const odpoved = await rpc("/hh/nahravani/kousek", {
                    nazev: soubor.name,
                    davka,
                    poradi,
                    celkem: pocet,
                    data,
                });
                // Chybu, kterou posila server, opakovat nema smysl -
                // priste dopadne stejne.
                if (odpoved && odpoved.chyba) {
                    return odpoved.chyba;
                }
                // Server hlasi, co opravdu zapsal. Kdyz to nesedi,
                // kousek se ztratil a stoji za to ho poslat znovu -
                // driv se to poznalo az na konci a propadlo cele
                // nahravani.
                if (!odpoved || odpoved.poradi !== poradi
                    || odpoved.bajtu !== kus.size) {
                    if (pokus === POKUSU) {
                        return _t("Část videa se nepodařilo uložit.");
                    }
                    continue;
                }
                return null;
            } catch {
                // Sem to spadne, kdyz pozadavek nedorazi cely nebo
                // se misto odpovedi vrati neco jineho nez JSON.
                // To uz za zkouseni stoji.
                if (pokus === POKUSU) {
                    return _t("Spojení se serverem se přerušilo.");
                }
                await new Promise((d) => setTimeout(d, 400 * pokus));
            }
        }
        return _t("Spojení se serverem se přerušilo.");
    },

    /**
     * Posle video po kouscich a vrati jeho adresu na webu.
     *
     * Kousky jedou po nekolika soucasne - viz SOUCASNE. Kazdy nese
     * svoje poradi, takze na tom, v jakem sledu dojdou, nezalezi;
     * server je slozi az na konci.
     *
     * @private
     * @param {File} soubor
     * @returns {Promise<string|null>}
     */
    async _hhNahraj(soubor) {
        const pocet = Math.max(1, Math.ceil(soubor.size / KOUSEK));
        /* Oznaceni davky si vymysli prohlizec a drzi ho po celou
           dobu nahravani. Server podle nej pozna, kam kousky patri -
           drive to delal podle prihlaseni, ktere se ale behem
           dlouheho nahravani obnovi a kousky se rozsypaly. */
        const davka = (crypto.randomUUID && crypto.randomUUID())
            || String(Date.now()) + "-" + Math.random().toString(36).slice(2);
        let dalsi = 0;
        let hotovo = 0;
        let chyba = null;

        const delnik = async () => {
            while (chyba === null) {
                const poradi = dalsi++;
                if (poradi >= pocet) {
                    return;
                }
                const potiz = await this._hhPosliKousek(soubor, davka, poradi, pocet);
                if (potiz) {
                    chyba = potiz;
                    return;
                }
                hotovo++;
                this._hhPrubeh(Math.round((hotovo / pocet) * 100));
            }
        };

        await Promise.all(
            Array.from({ length: Math.min(SOUCASNE, pocet) }, delnik)
        );

        if (chyba) {
            await this._hhZrus(soubor.name, davka);
            this._hhHlaska(chyba, "danger");
            return null;
        }

        let konec;
        try {
            konec = await rpc("/hh/nahravani/dokonci", {
                nazev: soubor.name,
                davka,
                celkem: pocet,
            });
        } catch {
            this._hhHlaska(
                _t("Video se nahrálo, ale nepodařilo se ho uložit. "
                   + "Zkus to prosím znovu."),
                "danger"
            );
            return null;
        }

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
    async _hhZrus(nazev, davka) {
        try {
            await rpc("/hh/nahravani/zrus", { nazev, davka });
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
