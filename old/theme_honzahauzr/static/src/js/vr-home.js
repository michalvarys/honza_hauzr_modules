/**
 * Vlastni rezie - hamburger v hlavicce
 *
 * Hlavicka stranky ma na uzkem okne misto rady odkazu hamburger.
 * Odkazy sedi porad ve stejnem <nav>, jen se na mobilu vysouvaji
 * pod hlavicku - viz .navlinks v static/src/css/vr-home.scss.
 * Tenhle skript jen prepina tridu vr-open na hlavicce.
 *
 * Posluchac se vesi na dokument v CAPTURE fazi a hned pri nacteni
 * souboru, ne az na DOMContentLoaded. Oboji ma duvod:
 *
 * Plynule rolovani na kotvy v honzahauzr.js bere klik taky v capture
 * fazi a vola stopImmediatePropagation - tim umlci vsechny
 * posluchace, ktere se prihlasily po nem. Odkaz v menu by se k nam
 * tedy vubec nedostal a menu by po klepnuti zustalo viset pres
 * obsah, na ktery se ma odrolovat. Musime byt prvni, a proto se
 * posluchac vesi okamzite (hlavicku si najde az v okamziku kliku,
 * takze nepotrebuje hotovy DOM). Poradi souboru ve svazku hlida
 * sequence 10 v data/ir_asset.xml - honzahauzr.js ma vychozich 16.
 *
 * Zavira se po klepnuti na odkaz, po klepnuti vedle a po rozsireni
 * okna.
 */
(function () {
    "use strict";

    function hlavicka() {
        return document.querySelector("#vr-home header");
    }

    function zavri(h) {
        h.classList.remove("vr-open");
        var tlacitko = h.querySelector(".vr-burger");
        if (tlacitko) {
            tlacitko.setAttribute("aria-expanded", "false");
        }
    }

    document.addEventListener("click", function (ev) {
        var cil = ev.target;
        if (!cil || !cil.closest) {
            return;
        }
        var h = hlavicka();
        if (!h) {
            return;
        }

        var tlacitko = cil.closest(".vr-burger");
        if (tlacitko && h.contains(tlacitko)) {
            var otevreno = h.classList.toggle("vr-open");
            tlacitko.setAttribute("aria-expanded", otevreno ? "true" : "false");
            return;
        }

        /* Odkaz v hlavicce (vcetne loga) i klepnuti kamkoli mimo ni
           menu zaviraji. */
        if (!h.contains(cil) || cil.closest("a")) {
            zavri(h);
        }
    }, true);

    /* Nad 900 px je menu zase v rade a trida vr-open by jen zustala
       viset na hlavicce. */
    window.addEventListener("resize", function () {
        var h = hlavicka();
        if (h && window.innerWidth > 900) {
            zavri(h);
        }
    });
})();
