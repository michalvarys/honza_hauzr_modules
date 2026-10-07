/**
 * Logo v liste na strankach vyzvy
 *
 * Na ostatnich strankach vede logo na hlavni stranku. Na landing page
 * a na strance s obsahem vyzvy ne: obe maji jedinou ulohu - dostat
 * navstevnika do vyzvy, respektive ji projit - a kazdy odkaz pryc je
 * cesta ven. Logo proto jen vyjede zpatky nahoru na uvodni obrazovku.
 *
 * Prepisuje se odkaz, ne odchytava kliknuti. Diky tomu cil odpovida
 * tomu, co se stane - stavovy radek prohlizece i otevreni v nove karte
 * ukazou tuhle stranku, ne hlavni.
 *
 * Landing page uz kotvu #uvod v obsahu ma. Stranka vyzvy ne a jeji
 * obsah je ulozeny v databazi, takze pridat ji do sablony by se na uz
 * existujicich strankach neprojevilo. Skript ji proto v pripade
 * potreby dosadi prvni sekci sam.
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
        /* Stranky vyzvy se poznaji podle obalu #wrap - landing page
           nese tridu hhv, stranka s obsahem vyzvy hhd. Jinde skript
           neudela nic. */
        var obal = document.querySelector("#wrap.hhv, #wrap.hhd");
        if (!obal) {
            return;
        }

        if (!document.getElementById("uvod")) {
            var prvni = obal.firstElementChild;
            if (!prvni) {
                return;
            }
            prvni.id = "uvod";
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
