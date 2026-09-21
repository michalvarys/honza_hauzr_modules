/**
 * VSTUPNI BRANA - "vyber si pilulku"
 *
 * Pred vstupem na web se polozi tmava vrstva: fotka prazdnych dlani,
 * nad nimi se vynori cervena a modra pilulka a lehce se vznaseji.
 * Kliknutim na kteroukoliv z nich vse zmizi a brana se rozevre.
 *
 * Cela vrstva se sklada tady v JS, ne v QWeb sablone. Ma to dva duvody:
 *  - kdyz JS z jakehokoliv duvodu nebezi, neni co by prekryvalo obsah,
 *    takze se web normalne zobrazi misto cerne obrazovky,
 *  - v Odoo editoru se brana vubec nevytvori a nezavazi pri praci se
 *    snippety (stejna uvaha jako u tridy .hh-anim v honzahauzr.js).
 */
(function () {
    "use strict";

    var KLIC = "hhGateVidano";      // v ramci jedne navstevy staci jednou
    var FOTKA = "/theme_honzahauzr/static/src/img/gate-morpheus.webp";

    var UVOD = "Tohle je tvoje poslední šance. Potom už není cesty zpět. " +
        "Vezmeš modrou pilulku – příběh končí, probudíš se ve své posteli a uvěříš " +
        "čemukoli, čemu chceš věřit. Vezmeš červenou pilulku – zůstaneš v říši divů " +
        "a já ti ukážu, jak hluboká je králičí nora.";

    var VAROVANI = "Jsi si tím opravdu jistý? Vážně nechceš poznat pravdu? " +
        "Pokud se rozhodneš pro modrou pilulku, všechno skončí – a už nikdy nebudeš mít šanci zjistit";

    function vEditoru() {
        return !!document.querySelector(".o_editable, #oe_snippets, .o_we_website_top_actions") ||
               document.body.classList.contains("editor_enable") ||
               window.frameElement !== null;   // nahled webu v backendu bezi v iframe
    }

    // Zatemneni z <head> musi jit pryc vzdy, kdyz branu nestavime -
    // jinak by stranka zustala schovana az do vyprseni pojistky.
    function odemknout() {
        document.documentElement.classList.remove("hh-gate-armed");
    }

    function spustit() {
        // jen na landing strance - na /wip ani v administraci nema co delat
        if (!document.querySelector(".hh-landing")) { odemknout(); return; }
        if (vEditoru()) { odemknout(); return; }

        try {
            if (sessionStorage.getItem(KLIC) === "1") { odemknout(); return; }
        } catch (e) {
            /* privatni okno muze pristup zakazat - branu proste ukazeme */
        }

        postavit();
    }

    function postavit() {
        var brana = document.createElement("div");
        brana.className = "hh-gate";
        brana.setAttribute("role", "dialog");
        brana.setAttribute("aria-label", "Vyber si pilulku a vstup na web");

        /* Zadny jiny text nez hlaska v bubline - zadny nadpis ani napoveda.
           Poradi pilulek kopiruje ilustraci: modra ruka je vlevo,
           cervena vpravo. */
        brana.innerHTML =
            '<div class="hh-gate__door hh-gate__door--left"></div>' +
            '<div class="hh-gate__door hh-gate__door--right"></div>' +
            '<div class="hh-gate__stage">' +
                '<div class="hh-gate__scene">' +
                    '<p class="hh-gate__bubble" aria-live="polite"></p>' +
                    /* Stin lezi na dlani a zustava na miste - proto je to
                       samostatny prvek, ne pseudoprvek pilulky. Kdyby byl
                       soucasti tlacitka, poskakoval by s nim a dojem
                       polozeni na dlan by se ztratil. */
                    '<span class="hh-gate__shadow hh-gate__shadow--blue"></span>' +
                    '<span class="hh-gate__shadow hh-gate__shadow--red"></span>' +
                    '<button type="button" class="hh-gate__pill hh-gate__pill--blue" aria-label="Modrá pilulka - vstoupit"></button>' +
                    '<button type="button" class="hh-gate__pill hh-gate__pill--red" aria-label="Červená pilulka - vstoupit"></button>' +
                '</div>' +
            '</div>';

        brana.querySelector(".hh-gate__bubble").textContent = UVOD;

        document.body.appendChild(brana);
        document.documentElement.classList.add("hh-gate-active");
        // Brana uz sama prekryva celou plochu, takze zatemneni z <head>
        // muze pryc. Kdyby zustalo, dvere by se pri otevirani rozjely
        // a odhalily prazdno misto webu.
        odemknout();

        // Kdyz fotka dlani chybi, nedelame z toho chybu - jen zustanou
        // pilulky ve tme. Vrstva tak funguje i bez doplneneho souboru.
        var test = new Image();
        test.onerror = function () { brana.classList.add("hh-gate--nofoto"); };
        test.src = FOTKA;

        var hotovo = false;

        function otevrit(pilulka) {
            if (hotovo) return;
            hotovo = true;

            try { sessionStorage.setItem(KLIC, "1"); } catch (e) { /* nevadi */ }

            if (pilulka) { pilulka.classList.add("is-chosen"); }
            brana.classList.add("is-choosing");

            // nejdriv zhasne scena, pak se teprve rozjedou dvere;
            // obe faze resi prechody v CSS pod temihle tridami
            var dobaSceny = 420;
            var dobaDveri = 900;
            setTimeout(function () { brana.classList.add("is-opening"); }, dobaSceny);

            // uklid az po dojeti dveri, s malou rezervou
            setTimeout(function () {
                document.documentElement.classList.remove("hh-gate-active");
                if (brana.parentNode) { brana.parentNode.removeChild(brana); }
            }, dobaSceny + dobaDveri + 120);
        }

        /* Na web pusti jen cervena pilulka. Modra misto toho prepise
           bublinu na varovani - Morpheus se jeste jednou zeptá. Dalsi
           kliknuti na modrou uz nic nemeni, text zustava. */
        var bublina = brana.querySelector(".hh-gate__bubble");
        var varovano = false;

        brana.querySelector(".hh-gate__pill--blue").addEventListener("click", function () {
            if (varovano) { return; }
            varovano = true;
            bublina.textContent = VAROVANI;
            // restart animace bubliny, aby zmena textu neprosla bez povsimnuti
            bublina.classList.remove("is-swap");
            void bublina.offsetWidth;
            bublina.classList.add("is-swap");
        });

        brana.querySelector(".hh-gate__pill--red").addEventListener("click", function () {
            otevrit(brana.querySelector(".hh-gate__pill--red"));
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", spustit);
    } else {
        spustit();
    }
})();
