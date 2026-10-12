/** @odoo-module **/

/**
 * Jak lidé koukají na videa - na kterékoliv stránce webu.
 *
 * Vedle tohohle běží na stránce výzvy jeste vyzva_sledovani.js. Ten
 * hlídá tři dny a hlásí postup ke konkrétnímu člověku i se zámkem
 * dne; tenhle se o ně nestará (přeskakuje bloky [data-hhd-video])
 * a bere všechna ostatní videa.
 *
 * Umí dvě podoby videa:
 *
 *   YouTube v rámu  přes jejich rozhraní. Pustí se jen tehdy, když
 *                   má adresa rámu enablejsapi=1 - dopisuje se tady
 *                   při načtení, v uložené stránce nic nepřibývá.
 *   <video>         video nahrané přímo na web, přes běžné události
 *                   přehrávače.
 *
 * Hlásí se dvakrát za přehrání: na začátku "spustil" a na konci
 * "došel sem". Konec je pauza, dohrání nebo odchod ze stránky.
 * Průběžně se nehlásí nic - u souhrnu za video by se průměr
 * rozmělnil hlášeními z poloviny přehrávání.
 *
 * Měření nesmí nikdy rušit přehrávání. Když se cokoliv nepovede,
 * skript mlčí a video běží dál.
 */

import publicWidget from "@web/legacy/js/public/public_widget";

const CIL = "/hh/video";

let apiSlibena = null;

/** Načte rozhraní YouTube. Jen jednou za stránku. */
function nactiApi() {
    if (apiSlibena) {
        return apiSlibena;
    }
    apiSlibena = new Promise((hotovo, selhalo) => {
        if (window.YT && window.YT.Player) {
            hotovo(window.YT);
            return;
        }
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
        znacka.onerror = () => selhalo(new Error("YouTube API se nenačetlo"));
        document.head.appendChild(znacka);
    });
    return apiSlibena;
}

/** Dopíše do adresy rámu enablejsapi=1. */
function povolRozhrani(ram) {
    const puvodni = ram.getAttribute("src") || "";
    if (!puvodni || !/youtube(-nocookie)?\.com/.test(puvodni)) {
        return false;
    }
    if (/[?&]enablejsapi=1/.test(puvodni)) {
        return false;
    }
    const adresa = new URL(puvodni, window.location.href);
    adresa.protocol = "https:";
    adresa.searchParams.set("enablejsapi", "1");
    adresa.searchParams.set("origin", window.location.origin);
    ram.setAttribute("src", adresa.toString());
    return true;
}

/** Kód videa z adresy YouTube. Podle něj se pozná totéž video. */
function kodYoutube(adresa) {
    const shoda = (adresa || "").match(
        /(?:embed\/|v=|youtu\.be\/)([A-Za-z0-9_-]{6,})/);
    return shoda ? shoda[1] : "";
}

/**
 * Pošle hlášení. keepalive kvůli odchodu ze stránky: běžný
 * požadavek by prohlížeč při zavírání zahodil.
 */
function posli(data) {
    try {
        fetch(CIL, {
            method: "POST",
            keepalive: true,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: Object.assign({ stranka: window.location.pathname }, data),
            }),
        }).catch(() => {});
    } catch (chyba) {
        // Měření je vedlejší věc.
    }
}

publicWidget.registry.hhVideo = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    // V editoru ne: Honza si tam videa přehrává při úpravách
    // stránky a počítalo by se to lidem do statistiky.
    disabledInEditableMode: true,

    /**
     * @override
     */
    async start() {
        const rodic = this._super(...arguments);

        this.prehravace = [];
        this.stav = new Map();
        this._odchod = () => this._vsemKonec();
        window.addEventListener("pagehide", this._odchod);
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === "hidden") {
                this._vsemKonec();
            }
        });

        try {
            this._nasadSoubory();
            await this._nasadYoutube();
        } catch (chyba) {
            console.debug("Měření videí se nenasadilo:", chyba);
        }

        return rodic;
    },

    /**
     * @override
     */
    destroy() {
        this._vsemKonec();
        window.removeEventListener("pagehide", this._odchod);
        this.prehravace.forEach((p) => {
            try {
                p.destroy();
            } catch (chyba) {
                // Přehrávač už může být pryč i s rámem.
            }
        });
        this.prehravace = [];
        this._super(...arguments);
    },

    // ------------------------------------------------------------------

    /** Videa nahraná přímo na web. */
    _nasadSoubory() {
        for (const prvek of this.el.querySelectorAll("video")) {
            if (prvek.closest("[data-hhd-video]")) {
                continue;   // tři dny výzvy řeší vyzva_sledovani.js
            }
            const adresa = prvek.currentSrc || prvek.getAttribute("src")
                || (prvek.querySelector("source") || {}).src || "";
            if (!adresa) {
                continue;
            }
            const kod = adresa.split("/").pop().split("?")[0];
            const nazev = prvek.getAttribute("title") || kod;

            prvek.addEventListener("play", () =>
                this._zacatek(kod, nazev, Math.floor(prvek.duration || 0)));
            const konec = () => this._konec(
                kod, nazev, Math.floor(prvek.duration || 0),
                Math.floor(prvek.currentTime || 0));
            prvek.addEventListener("pause", konec);
            prvek.addEventListener("ended", () => this._konec(
                kod, nazev, Math.floor(prvek.duration || 0),
                Math.floor(prvek.duration || 0)));
            prvek.addEventListener("timeupdate", () => {
                const s = this.stav.get(kod);
                if (s) {
                    s.nejdale = Math.max(
                        s.nejdale, Math.floor(prvek.currentTime || 0));
                }
            });
        }
    },

    /** Videa z YouTube. */
    async _nasadYoutube() {
        const ramy = [...this.el.querySelectorAll("iframe")].filter((ram) => {
            if (ram.closest("[data-hhd-video]")) {
                return false;   // tři dny výzvy
            }
            return /youtube(-nocookie)?\.com/.test(ram.getAttribute("src") || "");
        });
        if (!ramy.length) {
            return;
        }
        ramy.forEach(povolRozhrani);

        const YT = await nactiApi();
        for (const ram of ramy) {
            const kod = kodYoutube(ram.getAttribute("src"));
            if (!kod) {
                continue;
            }
            this.prehravace.push(
                new YT.Player(ram, {
                    events: {
                        onStateChange: (udalost) => this._stavYoutube(kod, udalost),
                    },
                })
            );
        }
    },

    _stavYoutube(kod, udalost) {
        const prehravac = udalost.target;
        const YT = window.YT;
        let nazev = kod;
        let delka = 0;
        try {
            nazev = (prehravac.getVideoData() || {}).title || kod;
            delka = Math.floor(prehravac.getDuration() || 0);
        } catch (chyba) {
            // Přehrávač ještě nemusí mít data.
        }

        if (udalost.data === YT.PlayerState.PLAYING) {
            this._zacatek(kod, nazev, delka);
            const s = this.stav.get(kod);
            if (s) {
                s.cti = () => {
                    try {
                        return Math.floor(prehravac.getCurrentTime() || 0);
                    } catch (chyba) {
                        return s.nejdale;
                    }
                };
            }
            return;
        }
        if (udalost.data === YT.PlayerState.PAUSED) {
            let kde = 0;
            try {
                kde = Math.floor(prehravac.getCurrentTime() || 0);
            } catch (chyba) {
                kde = 0;
            }
            this._konec(kod, nazev, delka, kde);
        }
        if (udalost.data === YT.PlayerState.ENDED) {
            this._konec(kod, nazev, delka, delka);
        }
    },

    // ------------------------------------------------------------------

    _zacatek(kod, nazev, delka) {
        const s = this.stav.get(kod);
        if (s && s.bezi) {
            return;   // pokračování po přetočení není nové spuštění
        }
        this.stav.set(kod, {
            bezi: true,
            nazev,
            delka,
            nejdale: (s && s.nejdale) || 0,
            cti: s && s.cti,
        });
        posli({ video: kod, nazev, delka, spustil: true });
    },

    _konec(kod, nazev, delka, kde) {
        const s = this.stav.get(kod);
        if (!s || !s.bezi) {
            return;
        }
        s.bezi = false;
        s.nejdale = Math.max(s.nejdale || 0, kde || 0);
        s.delka = delka || s.delka;

        const procento = s.delka
            ? Math.min(100, Math.round((100 * s.nejdale) / s.delka))
            : 0;
        posli({
            video: kod,
            nazev: nazev || s.nazev,
            delka: s.delka,
            sekund: s.nejdale,
            procento,
            spustil: false,
        });
    },

    /** Odchod ze stránky uprostřed přehrávání. */
    _vsemKonec() {
        for (const [kod, s] of this.stav.entries()) {
            if (!s.bezi) {
                continue;
            }
            const kde = s.cti ? s.cti() : s.nejdale;
            this._konec(kod, s.nazev, s.delka, kde);
        }
    },
});
