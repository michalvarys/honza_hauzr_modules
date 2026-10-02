/**
 * Video nahrane primo na web.
 *
 * Na strance stoji nahledovy obrazek s tlacitkem play a pod nim
 * prehravac, ktery se chysta dopredu - jakmile se k nemu navstevnik
 * priblizi rolovanim, nacte se hlavicka videa. Kliknuti pak jen
 * zmackne play a video nabehne hned, bez cekani.
 *
 * Proc ne hned pri nacteni stranky: video ma desitky az stovky MB.
 * Stahovat ho kazdemu, kdo stranku jen proscrolluje, by bylo drahe
 * jemu i serveru. Priprava az u bloku je kompromis - kdo se k videu
 * dostane, ma ho pripravene; kdo ne, nestahne nic.
 *
 * Nahledovy obrazek drzi celou plochu, dokud video opravdu nezacne
 * hrat. Plakat prehravace se do bloku nenatahuje, takze by se
 * u svisleho videa fotka pri kliknuti smrskla doprostred.
 */
(function () {
    "use strict";

    /* V editoru se nic nechysta ani neprehrava - Honza tam meni
       nahled a vybira soubor, ne aby mu pod rukama nabehlo video.

       Editor Odoo 18 vykresluje stranku v ramu, a panel se snippety
       i horni lista jsou v dokumentu NAD nim. Hledat je uvnitr ramu
       proto nestaci - pojistka tam nikdy nezabrala a editor se pak
       na pozadi dusil stahovanim videa.

       Rozhoduje tedy i to, jestli stranka bezi v ramu. Verejny web
       se do ramu nevklada, takze se tim nic neztrati. */
    function vEditoru() {
        try {
            if (window.top !== window.self) {
                return true;
            }
        } catch (potiz) {
            // Ram z jine domeny - na dotaz odpovi vyjimkou. I to je
            // ram, takze se chovame stejne.
            return true;
        }
        return (
            !!document.querySelector(
                ".o_editable, #oe_snippets, .o_we_website_top_actions"
            ) || document.body.classList.contains("editor_enable")
        );
    }

    /**
     * Nachysta prehravac, aby pozdejsi kliknuti jen zmacklo play.
     *
     * Vola se dvakrat: jednou pri priblizeni rolovanim, podruhe pro
     * jistotu pri kliknuti. Druhe volani uz nic nedela - video
     * v bloku je, takze se vraci rovnou.
     *
     * @returns {HTMLVideoElement|null}
     */
    function priprav(obal) {
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

        if (obal.querySelector("video")) {
            return obal.querySelector("video");
        }
        if (!adresa) {
            return null;
        }

        var prehravac = document.createElement("video");
        prehravac.className = "hhv-soubor__video";
        prehravac.setAttribute("src", adresa);
        prehravac.setAttribute("controls", "controls");
        prehravac.setAttribute("playsinline", "playsinline");
        /* Stahne se jen hlavicka videa, ne cely soubor. Diky tomu
           je prehravac pripraveny a kliknuti uz jen zmackne play. */
        prehravac.setAttribute("preload", "metadata");

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

        /* Nahled zustava pres celou plochu, dokud video opravdu
           nezacne hrat. Driv se schoval uz pri kliknuti a zustal
           po nem plakat prehravace, ktery se do bloku nenatahne -
           u svisleho videa se tim fotka smrskla doprostred mezi
           cerne pruhy. */
        obal.classList.add("hhv-soubor--nacita");
        obal.appendChild(prehravac);

        prehravac.addEventListener("playing", function odkryj() {
            prehravac.removeEventListener("playing", odkryj);
            obal.classList.remove("hhv-soubor--nacita");
            obal.classList.add("hhv-soubor--hraje");
        });

        nasadPrehravac(prehravac, !!titulky);
        return prehravac;
    }

    /**
     * Pusti video. Kdyz jeste neni nachystane, nachysta ho.
     */
    function spust(obal) {
        var video = priprav(obal);
        if (!video) {
            return;
        }
        var slib = video.play();
        /* Starsi prohlizece z play() nic nevraci; novejsi slib,
           ktery muze skoncit zamitnutim - treba kdyz uzivatel mezitim
           odroloval pryc. Neni to chyba, jen se nehraje. */
        if (slib && typeof slib.catch === "function") {
            slib.catch(function () {});
        }
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

        /* Kliknuti uvnitr prehravace si resi Plyr sam - pauza,
           prehravani, hlasitost, casova osa.

           Bez tohohle se video nedalo zastavit: Plyr ho na pauzu
           zastavil, jenze kliknuti bublalo dal sem a spust() ho
           okamzite rozjel znovu. */
        if (udalost.target.closest(".plyr")) {
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

    /* ===== PRIPRAVA DOPREDU =====

       Jakmile se blok priblizi k oknu, nachysta se prehravac a stahne
       se hlavicka videa. Kliknuti pak uz jen zmackne play a video jede
       hned, misto aby se teprve zacalo nacitat.

       Hranice je 600 px pred oknem - zhruba pulka obrazovky, takze
       priprava probehne, zatimco navstevnik jeste roluje. */
    function hlidej() {
        if (vEditoru() || !("IntersectionObserver" in window)) {
            return;
        }

        var hlidac = new IntersectionObserver(function (zaznamy) {
            zaznamy.forEach(function (z) {
                if (!z.isIntersecting) {
                    return;
                }
                hlidac.unobserve(z.target);
                priprav(z.target);
            });
        }, { rootMargin: "600px 0px" });

        function pridej(koren) {
            if (koren.matches && koren.matches(".hhv-soubor[data-hhv-soubor]")) {
                hlidac.observe(koren);
            }
            if (koren.querySelectorAll) {
                koren.querySelectorAll(".hhv-soubor[data-hhv-soubor]")
                    .forEach(function (obal) { hlidac.observe(obal); });
            }
        }

        pridej(document);

        /* Blok muze na strance pribyt i pozdeji - treba kdyz ho Honza
           pretahne v editoru nebo kdyz se cast stranky dokresli az
           dodatecne. Bez tohohle by se takovy blok nenachystal
           a cekalo by se az na kliknuti. */
        if ("MutationObserver" in window) {
            new MutationObserver(function (zmeny) {
                zmeny.forEach(function (zmena) {
                    zmena.addedNodes.forEach(function (uzel) {
                        if (uzel.nodeType === 1) {
                            pridej(uzel);
                        }
                    });
                });
            }).observe(document.body, { childList: true, subtree: true });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", hlidej);
    } else {
        hlidej();
    }
})();
