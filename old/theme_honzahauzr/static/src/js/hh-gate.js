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
    var FOTKA = "/theme_honzahauzr/static/src/img/gate-hands.webp";

    function vEditoru() {
        return !!document.querySelector(".o_editable, #oe_snippets, .o_we_website_top_actions") ||
               document.body.classList.contains("editor_enable") ||
               window.frameElement !== null;   // nahled webu v backendu bezi v iframe
    }

    function spustit() {
        // jen na landing strance - na /wip ani v administraci nema co delat
        if (!document.querySelector(".hh-landing")) return;
        if (vEditoru()) return;

        try {
            if (sessionStorage.getItem(KLIC) === "1") return;
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

        brana.innerHTML =
            '<div class="hh-gate__door hh-gate__door--left"></div>' +
            '<div class="hh-gate__door hh-gate__door--right"></div>' +
            '<div class="hh-gate__stage">' +
                '<h2 class="hh-gate__title">Vyber si.</h2>' +
                '<p class="hh-gate__sub">Většina lidí nevybírá. Jen jede dál.</p>' +
                '<div class="hh-gate__hands">' +
                    '<button type="button" class="hh-gate__pill hh-gate__pill--red" aria-label="Červená pilulka - vstoupit"></button>' +
                    '<button type="button" class="hh-gate__pill hh-gate__pill--blue" aria-label="Modrá pilulka - vstoupit"></button>' +
                '</div>' +
                '<p class="hh-gate__hint">Klikni na jednu z pilulek</p>' +
            '</div>' +
            '<button type="button" class="hh-gate__skip">Přeskočit</button>';

        document.body.appendChild(brana);
        document.documentElement.classList.add("hh-gate-active");

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

        brana.querySelectorAll(".hh-gate__pill").forEach(function (p) {
            p.addEventListener("click", function () { otevrit(p); });
        });
        brana.querySelector(".hh-gate__skip").addEventListener("click", function () { otevrit(null); });

        // Esc funguje jako preskoceni - nikoho tu nedrzime nasilim
        document.addEventListener("keydown", function (ev) {
            if (ev.key === "Escape") { otevrit(null); }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", spustit);
    } else {
        spustit();
    }
})();
