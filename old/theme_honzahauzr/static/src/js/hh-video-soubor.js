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

        obal.classList.add("hhv-soubor--hraje");
        obal.appendChild(prehravac);
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
