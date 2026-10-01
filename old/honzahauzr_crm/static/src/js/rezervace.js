/**
 * Vyber casu na strance /rezervace.
 *
 * Kliknuti na cas ho oznaci, zapise jeho cislo do skryteho pole
 * a teprve pak odkryje udaje. Bez vybraneho casu se neda odeslat -
 * server by stejne nevedel, co rezervovat.
 *
 * Kdyz JavaScript nebezi, zustanou udaje videt a formular funguje
 * jen s tim rozdilem, ze si clovek musi cas vybrat driv, nez ho
 * vyplni - hodnotu pak posle prohlizec sam.
 */
(function () {
    "use strict";

    function spustit() {
        var stranka = document.querySelector(".hhr");
        if (!stranka) {
            return;
        }

        var udaje = document.getElementById("hhr_udaje");
        var poleId = document.getElementById("hhr_termin_id");
        var popisek = document.getElementById("hhr_vybrano");
        var odeslat = document.getElementById("hhr_odeslat");
        var casy = stranka.querySelectorAll(".hhr-cas:not(.hhr-cas--pryc)");

        if (!udaje || !poleId || !casy.length) {
            return;
        }

        // Schovat a zablokovat smime az tady - dokud tenhle skript
        // nebezi, ma byt formular videt a odeslatelny, aby slo
        // rezervovat i bez JavaScriptu.
        if (!poleId.value) {
            udaje.hidden = true;
            if (odeslat) {
                odeslat.disabled = true;
            }
        }

        casy.forEach(function (tlacitko) {
            tlacitko.addEventListener("click", function () {
                casy.forEach(function (jine) {
                    jine.classList.remove("hhr-cas--vybrany");
                });
                tlacitko.classList.add("hhr-cas--vybrany");

                poleId.value = tlacitko.getAttribute("data-termin") || "";

                if (popisek) {
                    // Den je na teto strance jen jeden - stoji v podnadpisu
                    // hlavy ("ctvrtek 8. rijna").
                    var hlava = stranka.querySelector(".hhr-hlava .hhr-lead");
                    var nazevDne = hlava ? (hlava.textContent || "").trim() : "";
                    var hodina = (
                        tlacitko.querySelector(".hhr-cas__hodina").textContent || ""
                    ).trim();
                    popisek.textContent = (nazevDne + " v " + hodina).trim();
                }

                udaje.hidden = false;
                if (odeslat) {
                    odeslat.disabled = false;
                }

                // Po vybrani casu je dalsi krok dole - posuneme se k nemu,
                // at ho clovek na mobilu nemusi hledat.
                var plynule = !(
                    window.matchMedia &&
                    window.matchMedia("(prefers-reduced-motion: reduce)").matches
                );
                udaje.scrollIntoView({
                    behavior: plynule ? "smooth" : "auto",
                    block: "nearest",
                });
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", spustit);
    } else {
        spustit();
    }
})();
