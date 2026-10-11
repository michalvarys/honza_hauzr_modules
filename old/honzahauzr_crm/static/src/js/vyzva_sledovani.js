/** @odoo-module **/

/**
 * Kolik z videa vyzvy clovek opravdu videl.
 *
 * Honza potrebuje vedet vic nez "poslal jsem mu e-mail": jestli
 * video vubec pustil, kam se dostal a jestli dosel i na druhy
 * a treti den.
 *
 * Videa jsou vlozena jako bezny video blok z editoru, tedy YouTube
 * v ramu. Ram sam o sobe nic nerekne - prohlizec dovnitr cizi
 * stranky nevidi. YouTube na to ma vlastni rozhrani, ale pusti ho
 * jen tehdy, kdyz ma adresa ramu enablejsapi=1. Honza ten parametr
 * v editoru zadavat nebude a nemel by proc, takze se dopisuje tady
 * pri nacteni stranky; v ulozene strance nic nepribyva.
 *
 * Hlasi se nejdal dosazena vterina, ne soucet prehraneho casu -
 * jinak by z pretaceni sem a tam vyslo vic, nez ma video minut.
 *
 * Statistika nesmi nikdy rusit prehravani. Kdyz se cokoliv nepovede,
 * skript mlci a video bezi dal.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const CIL = "/zpet-do-zivota/vyzva/sledovani";

// Jak casto se hlasi postup u beziciho videa. Deset vterin je
// kompromis: pri kratsim intervalu by se server ptal zbytecne casto,
// pri delsim by se u cloveka, ktery odejde uprostred, ztratilo moc.
const INTERVAL_MS = 10000;

let apiSlibena = null;

/**
 * Nacte rozhrani YouTube. Jen jednou za stranku, i kdyz jsou videa tri.
 */
function nactiApi() {
    if (apiSlibena) {
        return apiSlibena;
    }
    apiSlibena = new Promise((hotovo, selhalo) => {
        if (window.YT && window.YT.Player) {
            hotovo(window.YT);
            return;
        }
        // YouTube si po nacteni samo zavola tuhle funkci. Puvodni
        // se zachova - kdyby ji na strance uz nekdo mel, prepsanim
        // by se rozbila.
        const puvodni = window.onYouTubeIframeAPIReady;
        window.onYouTubeIframeAPIReady = () => {
            if (puvodni) {
                puvodni();
            }
            hotovo(window.YT);
        };
        const znacka = document.createElement("script");
        znacka.src = "https://www.youtube.com/iframe_api";
        znacka.async = true;
        znacka.onerror = () => selhalo(new Error("YouTube API se nenacetlo"));
        document.head.appendChild(znacka);
    });
    return apiSlibena;
}

/**
 * Dopise do adresy ramu enablejsapi=1. Vraci true, kdyz se adresa
 * zmenila a ram se musi nacist znovu.
 */
function povolRozhrani(ram) {
    const puvodni = ram.getAttribute("src") || "";
    if (!puvodni || !/youtube(-nocookie)?\.com/.test(puvodni)) {
        return false;
    }
    if (/[?&]enablejsapi=1/.test(puvodni)) {
        return false;
    }
    // Adresa z editoru zacina //www.youtube.com/... bez protokolu,
    // proto se doplnuje vuci aktualni strance. Na localhostu by z toho
    // vyslo http a YouTube by nas poslal pres presmerovani - natvrdo
    // tedy https.
    const adresa = new URL(puvodni, window.location.href);
    adresa.protocol = "https:";
    adresa.searchParams.set("enablejsapi", "1");
    adresa.searchParams.set("origin", window.location.origin);
    ram.setAttribute("src", adresa.toString());
    return true;
}

publicWidget.registry.hhVyzvaSledovani = publicWidget.Widget.extend({
    selector: ".s_hh_vyzva_dny",
    // V editoru ne: Honza tam videa vyminuje a jeho vlastni
    // prehravani by se pocitalo lidem do statistiky.
    disabledInEditableMode: true,

    /**
     * @override
     */
    async start() {
        const rodic = this._super(...arguments);

        this.prehravace = [];
        this.intervaly = [];
        this.nejdale = {};

        try {
            await this._nasad();
        } catch (chyba) {
            // Statistika je vedlejsi vec. Kdyz nevyjde, video bezi dal.
            console.debug("Sledování videí výzvy se nenasadilo:", chyba);
        }

        return rodic;
    },

    /**
     * @override
     */
    destroy() {
        this.intervaly.forEach((id) => clearInterval(id));
        this.intervaly = [];
        this.prehravace.forEach((p) => {
            try {
                p.destroy();
            } catch (chyba) {
                // Prehravac uz muze byt pryc i s ramem.
            }
        });
        this.prehravace = [];
        this._super(...arguments);
    },

    // ------------------------------------------------------------------

    async _nasad() {
        const bloky = [...this.el.querySelectorAll("[data-hhd-video]")];
        const ramy = [];
        for (const blok of bloky) {
            const den = blok.dataset.hhdVideo;
            const ram = blok.querySelector("iframe");
            // Zamceny den ram nema - server ho ze stranky vyrizl.
            if (!den || !ram) {
                continue;
            }
            povolRozhrani(ram);
            ramy.push({ den, ram });
        }
        if (!ramy.length) {
            return;
        }

        const YT = await nactiApi();
        for (const { den, ram } of ramy) {
            this.prehravace.push(
                new YT.Player(ram, {
                    events: {
                        onStateChange: (udalost) =>
                            this._stav(den, udalost),
                    },
                })
            );
        }
    },

    _stav(den, udalost) {
        const prehravac = udalost.target;
        const YT = window.YT;

        if (udalost.data === YT.PlayerState.PLAYING) {
            this._posli(den, prehravac, true);
            // Behem prehravani se hlasi prubezne - kdyz clovek
            // zavre zalozku uprostred, zustane aspon posledni znamy
            // bod a ne jen "spustil".
            const id = setInterval(
                () => this._posli(den, prehravac, false), INTERVAL_MS);
            this.intervaly.push(id);
            prehravac.hhInterval = id;
            return;
        }

        if (prehravac.hhInterval) {
            clearInterval(prehravac.hhInterval);
            prehravac.hhInterval = null;
        }
        if (udalost.data === YT.PlayerState.PAUSED
                || udalost.data === YT.PlayerState.ENDED) {
            // U konce se posila delka jako dosazeny cas: prehravac
            // hlasi o zlomek min a video by zustalo na 99 %.
            const konec = udalost.data === YT.PlayerState.ENDED;
            this._posli(den, prehravac, false, konec);
        }
    },

    _posli(den, prehravac, spustil, konec) {
        let sekund = 0;
        let delka = 0;
        try {
            sekund = Math.floor(prehravac.getCurrentTime() || 0);
            delka = Math.floor(prehravac.getDuration() || 0);
        } catch (chyba) {
            return;
        }
        if (konec && delka) {
            sekund = delka;
        }

        // Nejdal dosazeny bod si drzi i server, ale posilat porad
        // dokola totez cislo pri pretaceni dozadu nema smysl.
        if (!spustil && sekund <= (this.nejdale[den] || 0)) {
            return;
        }
        this.nejdale[den] = Math.max(this.nejdale[den] || 0, sekund);

        const klic = new URLSearchParams(window.location.search).get("k");
        const data = { den, sekund, delka, spustil: !!spustil };
        if (klic) {
            data.k = klic;
        }
        // Zamerne bez await a bez hlaseni chyb: statistika nesmi
        // zdrzet ani prerusit prehravani.
        rpc(CIL, data).catch(() => {});
    },
});
