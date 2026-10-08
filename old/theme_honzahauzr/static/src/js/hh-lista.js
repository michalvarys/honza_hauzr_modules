/**
 * Horni lista: pri rolovani dolu zmizi, pri rolovani nahoru se vrati
 *
 * Plati na vsech strankach webu. Lista musi byt pristupna kdykoliv -
 * uzivatel nema proc rolovat zpatky na uplny zacatek, jen aby se
 * dostal k menu - ale zaroven nema prekazet pri cteni.
 *
 * Stranky maji listu dvoji. Vetsina pouziva hlavicku Odoo
 * (#wrapwrap > header#top), hlavni stranka Vlastni rezie a prodejni
 * stranka Tvuj tah si nesou vlastni (<header> resp. <nav> uvnitr
 * sveho obalu). Skript bere prvni, kterou najde, a chova se k nim
 * stejne.
 *
 * Posun se dela pres tridu a transform v CSS, ne zapisem do stylu
 * prvku. Diky tomu jde chovani vypnout nebo doladit ze samotneho
 * CSS a skript o vzhledu nic nevi.
 *
 * Nad hornim okrajem stranky se lista nikdy neschovava: dokud je
 * videt zacatek, nema se kam uhnout. Pri otevrenem mobilnim menu
 * taky ne - zmizela by i s menu pod sebou.
 */
(function () {
    "use strict";

    /* O kolik se musi stranka posunout, nez se lista hne. Bez toho
       by polockala pri kazdem drobnem posunu, treba pri doskoku
       prstem na dotykovem displeji. */
    var PRAH = 8;

    /* Dokud je videt prvnich par set pixelu, lista zustava. */
    var KLID = 90;

    /* Poradi selektoru tu neni jen tak. Stranky s vlastni listou maji
       hlavicku Odoo porad v kodu, jen schovanou pres d-none - a je
       v dokumentu driv. Jediny querySelector se seznamem selektoru
       vraci prvni prvek v poradi DOKUMENTU, ne v poradi selektoru,
       takze by sahl po te schovane a trida by pristala na necem,
       co neni videt. Proto se zkousi jeden po druhem a schovane
       listy se preskakuji. */
    var LISTY = ["#vr-home header", "#vr-tah nav", "#wrapwrap > header#top"];

    function najdiListu() {
        for (var i = 0; i < LISTY.length; i++) {
            var prvek = document.querySelector(LISTY[i]);
            if (prvek && prvek.getClientRects().length) {
                return prvek;
            }
        }
        return null;
    }

    function spust() {
        var lista = najdiListu();
        if (!lista) {
            return;
        }

        lista.classList.add("hh-lista");

        var posledni = window.scrollY;
        var ceka = false;

        function prekresli() {
            ceka = false;
            var ted = window.scrollY;
            var rozdil = ted - posledni;

            if (Math.abs(rozdil) < PRAH) {
                return;
            }
            posledni = ted;

            /* Otevrene mobilni menu visi pod listou - kdyby se
               schovala, zmizelo by s ni. */
            if (lista.classList.contains("vr-open")) {
                lista.classList.remove("hh-lista--pryc");
                return;
            }

            if (ted <= KLID) {
                lista.classList.remove("hh-lista--pryc");
            } else if (rozdil > 0) {
                lista.classList.add("hh-lista--pryc");
            } else {
                lista.classList.remove("hh-lista--pryc");
            }
        }

        window.addEventListener("scroll", function () {
            if (!ceka) {
                ceka = true;
                window.requestAnimationFrame(prekresli);
            }
        }, { passive: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", spust);
    } else {
        spust();
    }
})();
