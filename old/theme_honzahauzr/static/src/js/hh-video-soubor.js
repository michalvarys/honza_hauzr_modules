/**
 * Video nahrane primo na web - nacte se az po kliknuti.
 *
 * Na strance stoji jen nahledovy obrazek s tlacitkem play. Video se
 * stahne teprve ve chvili, kdy na nej nekdo klikne. Soubor ma desitky
 * MB a nacitat ho rovnou by znamenalo, ze navstevnik chvili kouka na
 * prazdne misto a na mobilnich datech stahuje neco, co treba ani
 * nechce videt.
 *
 * Po kliknuti se obrazek nahradi prehravacem a rovnou se spusti.
 * Autoplay prohlizec pustit nechá, protoze mu predchazi kliknuti -
 * bez nej by ho zablokoval.
 */
(function () {
    "use strict";

    /* V editoru se nic neprehrava - Honza tam meni nahled a vybira
       soubor, ne aby mu pod rukama nabehlo video. */
    function vEditoru() {
        return (
            !!document.querySelector(
                ".o_editable, #oe_snippets, .o_we_website_top_actions"
            ) || document.body.classList.contains("editor_enable")
        );
    }

    function spust(obal) {
        // Na uzkem okne se pouzije svisle video, kdyz je vyplnene.
        // Hranice 991 px je ta sama jako u videi z YouTube.
        var naSirku = obal.getAttribute("data-hhv-soubor");
        var naVysku = obal.getAttribute("data-hhv-soubor-mobil");
        var adresa = (naVysku && window.innerWidth <= 991) ? naVysku : naSirku;

        // Kdyz je vyplnene jen jedno z poli, pustime ho vzdycky.
        // Jinak by blok na druhe sirce okna zustal mrtvy - clovek
        // klikne a nic se nestane, aniz by tusil proc.
        if (!adresa) {
            adresa = naSirku || naVysku;
        }

        if (!adresa || obal.querySelector("video")) {
            return;
        }

        var prehravac = document.createElement("video");
        prehravac.className = "hhv-soubor__video";
        prehravac.setAttribute("src", adresa);
        prehravac.setAttribute("controls", "controls");
        prehravac.setAttribute("autoplay", "autoplay");
        prehravac.setAttribute("playsinline", "playsinline");
        prehravac.setAttribute("preload", "auto");

        // Nahled zustava jako plakat, nez se nacte prvni snimek -
        // jinak by na okamzik probliklo cerne misto.
        var nahled = obal.querySelector(".hhv-soubor__nahled");
        if (nahled) {
            prehravac.setAttribute("poster", nahled.getAttribute("src") || "");
        }

        // Titulky. Prohlizec si je zapina sam, Plyr je navic nabidne
        // v nabidce pod ozubenym kolem.
        var titulky = obal.getAttribute("data-hhv-titulky");
        if (titulky) {
            var stopa = document.createElement("track");
            stopa.setAttribute("kind", "captions");
            stopa.setAttribute("label", "Čeština");
            stopa.setAttribute("srclang", "cs");
            stopa.setAttribute("src", titulky);
            stopa.setAttribute("default", "default");
            prehravac.appendChild(stopa);
        }

        obal.classList.add("hhv-soubor--hraje");
        obal.appendChild(prehravac);
        nasadPrehravac(prehravac, !!titulky);
    }

    /**
     * Prebali video do Plyru, kdyz je k dispozici.
     *
     * Plyr je hotovy prehravac - dava vsem prohlizecum stejne
     * ovladani, nabidku titulku a rychlosti prehravani. Barvy se mu
     * nastavuji promennymi v CSS (--plyr-color-main a spol.), takze
     * se nic nekompiluje.
     *
     * Kdyz se z nejakeho duvodu nenacte, zustane obycejne <video>
     * s ovladanim od prohlizece. Video se tedy prehraje tak jako tak.
     */
    function nasadPrehravac(video, maTitulky) {
        if (typeof window.Plyr !== "function") {
            return;
        }
        try {
            var ovladani = [
                "play-large", "play", "progress", "current-time",
                "mute", "volume",
            ];
            if (maTitulky) {
                ovladani.push("captions");
            }
            ovladani.push("settings", "fullscreen");

            new window.Plyr(video, {
                controls: ovladani,
                settings: ["captions", "speed"],
                // Ikony si Plyr jinak tahá z cdn.plyr.io. Tohle je
                // tatáž sada ulozena v tematu, takze web nezavisi na
                // cizim serveru.
                iconUrl: "/theme_honzahauzr/static/lib/plyr/plyr.svg",
                captions: { active: maTitulky, update: true },
                tooltips: { controls: false, seek: true },
                i18n: {
                    play: "Přehrát",
                    pause: "Pozastavit",
                    mute: "Ztlumit",
                    unmute: "Zapnout zvuk",
                    enterFullscreen: "Na celou obrazovku",
                    exitFullscreen: "Zpět",
                    captions: "Titulky",
                    settings: "Nastavení",
                    speed: "Rychlost",
                    normal: "Normální",
                    enabled: "Zapnuté",
                    disabled: "Vypnuté",
                },
            });
        } catch (potiz) {
            // Radeji obycejne video nez zadne.
            if (window.console && console.warn) {
                console.warn("Plyr se nepodarilo nasadit:", potiz);
            }
        }
    }

    function pripoj(udalost) {
        if (vEditoru() || !(udalost.target instanceof Element)) {
            return;
        }
        var obal = udalost.target.closest(".hhv-soubor[data-hhv-soubor]");
        if (obal) {
            spust(obal);
        }
    }

    /* Kliknuti se odchytava na cele strance, ne na jednotlivych blocich.
       Blok muze na strance pribyt i pozdeji - treba kdyz ho Honza prave
       pretahl v editoru nebo po ulozeni stranky - a takhle to funguje
       bez ohledu na to, kdy vznikl. */
    document.addEventListener("click", pripoj);
})();
