/**
 * Landing page bezplatne tridenni vyzvy (/vyzva)
 *
 * Ctyri drobne veci, nic vic:
 *  1. jemny nabeh bloku pri scrollu (a nic, kdyz si navstevnik
 *     v systemu vypnul animace),
 *  2. lepkave tlacitko na mobilu az po prvnim odrolovani,
 *  3. posun na formular po kliknuti na tlacitko,
 *  4. mereni - klik na tlacitko, zobrazeni formulare, odeslani.
 *
 * Skript zamerne nepouziva animacni motor z honzahauzr.js. Ten se
 * spousti driv a neptal by se na prefers-reduced-motion, ktere si
 * zadani teto stranky vyslovne vymiňuje.
 */
(function () {
    "use strict";

    var stranka = document.querySelector(".hhv");
    if (!stranka) {
        return;
    }

    /* V editoru Odoo se nic neschovava ani nelepi - jinak by Honza
       upravoval sekce, ktere nejsou videt. */
    var vEditoru =
        !!document.querySelector(
            ".o_editable, #oe_snippets, .o_we_website_top_actions"
        ) || document.body.classList.contains("editor_enable");

    var bezPohybu =
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var umiPozorovat = "IntersectionObserver" in window;

    // ------------------------------------------------------------------
    // mereni
    // ------------------------------------------------------------------

    /* Udalosti se odkladaji do dataLayer. Az na strance pribude GTM
       nebo Google Analytics, zacnou se cist bez dalsiho zasahu; dokud
       tam neni, jen se hromadi v pameti a nic se nedeje. */
    function zmer(nazev, podrobnosti) {
        window.dataLayer = window.dataLayer || [];
        var udalost = { event: nazev };
        if (podrobnosti) {
            Object.keys(podrobnosti).forEach(function (klic) {
                udalost[klic] = podrobnosti[klic];
            });
        }
        window.dataLayer.push(udalost);
    }

    // ------------------------------------------------------------------
    // 1. nabeh bloku pri scrollu
    // ------------------------------------------------------------------

    var nabehy = stranka.querySelectorAll("[data-hhv-anim]");

    function odkryjVse() {
        stranka.classList.remove("hhv-anim-on");
        nabehy.forEach(function (prvek) {
            prvek.classList.add("hhv-in");
        });
    }

    if (umiPozorovat && !vEditoru && !bezPohybu) {
        // Trida se nasazuje az tady - dokud ji nikdo nenasadi, je
        // stranka normalne videt i bez JavaScriptu.
        stranka.classList.add("hhv-anim-on");

        try {
            /* threshold 0 misto 0.12: u vysokych bloku znamenalo dvanact
               procent vysky zbytecne cekani, nez se vubec zacaly
               odkryvat. Staci, aby prvek zavadil do okna. */
            var hlidacNabehu = new IntersectionObserver(
                function (zaznamy) {
                    zaznamy.forEach(function (zaznam) {
                        if (!zaznam.isIntersecting) {
                            return;
                        }
                        var prvek = zaznam.target;
                        // Zpozdeni v sablone jsou az 340 ms a delala
                        // z kaskady cekani. Pomer mezi prvky zustava.
                        var zpozdeni = Math.min(150, Math.round(parseInt(
                            prvek.getAttribute("data-hhv-delay") || "0", 10) / 2.5));
                        setTimeout(function () {
                            prvek.classList.add("hhv-in");
                        }, zpozdeni);
                        hlidacNabehu.unobserve(prvek);
                    });
                },
                { threshold: 0, rootMargin: "0px 0px -10px 0px" }
            );

            var vyskaOkna = window.innerHeight || 0;

            nabehy.forEach(function (prvek) {
                // Co uz je pri startu videt, se odkryje rovnou, bez
                // cekani na pozorovatele.
                if (prvek.getBoundingClientRect().top < vyskaOkna) {
                    prvek.classList.add("hhv-in");
                    return;
                }
                hlidacNabehu.observe(prvek);
            });
        } catch (chyba) {
            // Radeji zadna animace nez schovana stranka.
            odkryjVse();
        }

        /* Hlidac na prvky, na ktere se pozorovatel nechytil - treba
           kdyz se rozvrzeni po nacteni fotek posune. */
        setTimeout(function () {
            var vyska = window.innerHeight || 0;
            nabehy.forEach(function (prvek) {
                if (!prvek.classList.contains("hhv-in") &&
                        prvek.getBoundingClientRect().top < vyska) {
                    prvek.classList.add("hhv-in");
                }
            });
        }, 1200);
    }

    var registrace = document.getElementById("registrace");

    // ------------------------------------------------------------------
    // 2. posun na formular
    // ------------------------------------------------------------------

    document
        .querySelectorAll('.hhv a[href="#registrace"]')
        .forEach(function (odkaz) {
            odkaz.addEventListener("click", function (udalost) {
                zmer("hhv_cta_klik", {
                    hhv_cta: (odkaz.textContent || "").trim(),
                    hhv_misto: odkaz.getAttribute("data-hhv-misto") || "",
                });

                if (!registrace) {
                    return;
                }
                udalost.preventDefault();
                registrace.scrollIntoView({
                    behavior: bezPohybu ? "auto" : "smooth",
                    block: "start",
                });
                // Adresa se ma zmenit, at funguje zpet i sdileni odkazu.
                if (window.history && window.history.replaceState) {
                    window.history.replaceState(null, "", "#registrace");
                }
            });
        });

    // ------------------------------------------------------------------
    // 3. formular
    // ------------------------------------------------------------------

    var formular = document.querySelector(".hhv-form");
    if (formular) {
        var souhlas = formular.querySelector(".hhv-consent input");

        /* Souhlas zamerne nema atribut name - Odoo posila jen pojmenovana
           pole a neznamy nazev by zapis leadu shodil.

           Hlidat ho pres udalost submit ale nestaci: Odoo formular
           neodesila prohlizecem, obslouzi si kliknuti na tlacitko samo
           a zadny submit pritom nevznikne. Nezaskrtnuty souhlas by tak
           prosel. Proto se poslouchá primo kliknuti, a to na documentu
           v zachytne fazi - tam jsme na rade drive nez Odoo. */
        document.addEventListener(
            "click",
            function (udalost) {
                var tlacitko =
                    udalost.target &&
                    udalost.target.closest &&
                    udalost.target.closest(".hhv-form .s_website_form_send");
                if (!tlacitko) {
                    return;
                }

                if (souhlas && !souhlas.checked) {
                    udalost.preventDefault();
                    udalost.stopPropagation();
                    udalost.stopImmediatePropagation();
                    formular.classList.add("hhv-form--chyba");
                    souhlas.focus();
                    return;
                }

                formular.classList.remove("hhv-form--chyba");
                zmer("hhv_formular_odeslan");
            },
            true
        );

        // Zobrazeni formulare je zvlast merena udalost - rika, kolik
        // lidi se vubec doscrollovalo k registraci.
        if (umiPozorovat && registrace) {
            var hlidacZobrazeni = new IntersectionObserver(
                function (zaznamy) {
                    if (!zaznamy[0].isIntersecting) {
                        return;
                    }
                    zmer("hhv_formular_zobrazen");
                    hlidacZobrazeni.disconnect();
                },
                { threshold: 0.3 }
            );
            hlidacZobrazeni.observe(registrace);
        }

        /* Hlavni konverze je az potvrzeni od serveru, ne kliknuti na
           odeslat. Odoo po uspesnem zapisu sundá z dekovaci hlasky
           tridu d-none - na to se tu ceka. */
        var hlaska = document.querySelector(".hhv-done");
        if (hlaska && "MutationObserver" in window) {
            var hlidacHlasky = new MutationObserver(function () {
                if (hlaska.classList.contains("d-none")) {
                    return;
                }
                zmer("hhv_registrace");
                hlidacHlasky.disconnect();
            });
            hlidacHlasky.observe(hlaska, {
                attributes: true,
                attributeFilter: ["class"],
            });
        }
    }
})();
