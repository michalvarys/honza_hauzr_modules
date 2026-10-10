/**
 * Honza Hauzr - doplnění adres ze systémových parametrů
 *
 * Odkazy v obsahu mají statické href jako záchranu a navíc atribut
 * data-hh-odkaz s klíčem. Skutečnou adresu nese <meta name="hh-odkaz-KLÍČ">
 * v hlavičce stránky.
 *
 * Proč ne rovnou v šabloně: QWeb direktiva uvnitř obsahu sebere obalovému
 * divu editační značky a celý panel se snippety pak zešedne. Podrobně
 * ve views/odkazy.xml.
 */
(function () {
    "use strict";

    function doplnit() {
        var odkazy = document.querySelectorAll("[data-hh-odkaz]");
        for (var i = 0; i < odkazy.length; i++) {
            var klic = odkazy[i].getAttribute("data-hh-odkaz");
            var meta = document.querySelector('meta[name="hh-odkaz-' + klic + '"]');
            var adresa = meta && meta.getAttribute("content");
            if (adresa) {
                odkazy[i].setAttribute("href", adresa);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", doplnit);
    } else {
        doplnit();
    }
})();
