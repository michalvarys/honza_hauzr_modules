/**
 * Logo v liste na landing page
 *
 * Na ostatnich strankach vede logo na hlavni stranku. Na landing page
 * ne: ta ma jedinou ulohu, dostat navstevnika do vyzvy, a kazdy odkaz
 * pryc je cesta ven. Logo proto jen vyjede zpatky nahoru na uvodni
 * obrazovku.
 *
 * Prepisuje se odkaz, ne odchytava kliknuti. Diky tomu cil odpovida
 * tomu, co se stane - stavovy radek prohlizece i otevreni v nove karte
 * ukazou tuhle stranku, ne hlavni.
 *
 * Soubor sedi ve svazku "minimal", ktery se nacita jako prvni. V bezne
 * frontend svazku by se dostal ke slovu az za par stovek milisekund po
 * zobrazeni stranky a po tu dobu by logo vedlo pryc. Musi byt az za
 * module_loader.js, protoze Odoo kazdy soubor ve svazku obali do
 * odoo.define.
 */
(function () {
    "use strict";

    function prepisZnacku() {
        /* Landing page se pozna podle obalu #wrap, ktery nese tridu
           hhv. Na ostatnich strankach skript neudela nic. */
        if (!document.querySelector("#wrap.hhv")) {
            return;
        }

        Array.prototype.forEach.call(
            document.querySelectorAll('header a.navbar-brand[href="/"]'),
            function (znacka) {
                znacka.setAttribute("href", "#uvod");
            }
        );
    }

    /* Hlavicka i obsah stranky uz musi byt prectene. Stav "interactive"
       prijde hned po docteni, jeste pred DOMContentLoaded. */
    if (document.readyState === "loading") {
        document.addEventListener("readystatechange", function () {
            if (document.readyState !== "loading") {
                prepisZnacku();
            }
        });
        document.addEventListener("DOMContentLoaded", prepisZnacku);
    } else {
        prepisZnacku();
    }
})();
