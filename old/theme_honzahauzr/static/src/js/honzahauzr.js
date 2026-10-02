/**
 * Honza Hauzr Theme - Scroll Animation Engine
 * GSAP-like scroll animations, parallax, sticky CTA, counter animations
 * Pure JS, no dependencies
 */
(function () {
    "use strict";

    /* Sekce jsou v CSS videt; schovat je smime az ve chvili, kdy je umime
       zase odkryt. Proto se trida .hh-anim nasazuje odsud a jen kdyz:
        - existuje IntersectionObserver (jinak by animace nikdy nedobehla), a
        - nejsme v Odoo editoru ani v nahledu snippetu - tam se pozorovatel
          nespusti a sekce by zustaly prazdne bile. */
    var vEditoru = !!document.querySelector(
        ".o_editable, #oe_snippets, .o_we_website_top_actions"
    ) || document.body.classList.contains("editor_enable");

    /* Kdo si v systemu vypnul animace, dostane stranku rovnou celou.
       Drive se mu schovavala a nabihala stejne jako ostatnim. */
    var bezPohybu = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var animuje = "IntersectionObserver" in window && !vEditoru && !bezPohybu;

    if (animuje) {
        document.documentElement.classList.add("hh-anim");
    }

    /* Zachranna brzda: kdyz cokoliv v motoru spadne, obsah nesmi zustat
       schovany. Sundani tridy vrati stranku do stavu, ve kterem je bez
       JavaScriptu - tedy celou videt. */
    function vzdatSeAnimaci() {
        document.documentElement.classList.remove("hh-anim");
        document.querySelectorAll("[data-anim]").forEach(function (el) {
            el.classList.add("anim-visible");
            el.style.opacity = "";
            el.style.transform = "";
            el.style.clipPath = "";
        });
    }

    // ===== SCROLL ANIMATION ENGINE =====
    var animEls = document.querySelectorAll("[data-anim]");
    var parallaxEls = document.querySelectorAll("[data-parallax]");
    var counterEls = document.querySelectorAll('[data-anim="counter"]');
    var countersAnimated = new Set();

    // Easing functions
    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    function easeOutQuart(t) {
        return 1 - Math.pow(1 - t, 4);
    }

    // Animate element with JS for smoother GSAP-like feel
    function animateElement(el, hned) {
        if (el.classList.contains("anim-visible")) return;

        /* Prvek, ktery uz pri startu lezi v okne, se odkryje rovnou.
           Skript se totiz nacita az se zbytkem stranky - do te doby je
           obsah videt, pak by ho trida .hh-anim schovala a teprve pak
           by nabehl. Navstevnik tak videl, jak mu text zmizi a zase se
           objevi. */
        if (hned) {
            el.classList.add("anim-visible");
            return;
        }

        var type = el.getAttribute("data-anim");

        /* Zpozdeni v sablonach jsou pomerne velka (az 450 ms) a delala
           z kaskady cekani. Pomer mezi prvky zustava, jen se cela
           kaskada zkrati. */
        var delay = Math.min(
            180, Math.round(parseInt(el.getAttribute("data-delay") || "0", 10) / 3));
        var duration = 420;

        setTimeout(function () {
            var start = null;
            var fromProps = getFromProps(type);
            var toProps = { x: 0, y: 0, scale: 1, clipY: 0 };

            function step(timestamp) {
                if (!start) start = timestamp;
                var elapsed = timestamp - start;
                var progress = Math.min(elapsed / duration, 1);
                var eased = easeOutQuart(progress);

                var x = fromProps.x + (toProps.x - fromProps.x) * eased;
                var y = fromProps.y + (toProps.y - fromProps.y) * eased;
                var s = fromProps.scale + (toProps.scale - fromProps.scale) * eased;

                el.style.opacity = eased;
                el.style.transform = "translate3d(" + x + "px, " + y + "px, 0) scale(" + s + ")";

                if (type === "reveal-up") {
                    var clipVal = 100 - eased * 100;
                    el.style.clipPath = "inset(" + clipVal + "% 0 0 0)";
                }

                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    el.classList.add("anim-visible");
                    el.style.transform = "";
                    el.style.opacity = "";
                    el.style.clipPath = "";
                }
            }

            requestAnimationFrame(step);
        }, delay);
    }

    /* Kratsi drahy nez driv (bylo 60 a 80 px). Dlouhy posun znamena, ze
       prvek startuje hluboko pod svym mistem, takze se do okna dostane
       pozdeji a nabeh pusobi opozdene. */
    function getFromProps(type) {
        switch (type) {
            case "fade-up": return { x: 0, y: 24, scale: 1, clipY: 0 };
            case "fade-down": return { x: 0, y: -18, scale: 1, clipY: 0 };
            case "fade-left": return { x: 28, y: 0, scale: 1, clipY: 0 };
            case "fade-right": return { x: -28, y: 0, scale: 1, clipY: 0 };
            case "zoom-in": return { x: 0, y: 0, scale: 0.94, clipY: 0 };
            case "zoom-out": return { x: 0, y: 0, scale: 1.05, clipY: 0 };
            case "reveal-up": return { x: 0, y: 0, scale: 1, clipY: 100 };
            /* Ciste prolnuti, bez jakehokoliv posunu. Pro prvky, ktere
               uz maji vlastni transform (napriklad vycentrovani pres
               translate(-50%, -50%)) - jakykoliv posun by jim ho
               prepsal a prvek by behem nabehu odskocil stranou. */
            case "fade-in": return { x: 0, y: 0, scale: 1, clipY: 0 };
            default: return { x: 0, y: 18, scale: 1, clipY: 0 };
        }
    }

    // Counter animation
    function animateCounter(el) {
        var target = parseInt(el.getAttribute("data-count") || "0", 10);
        var suffix = "+";
        var duration = 1800;
        var start = null;

        function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = easeOutCubic(progress);
            var current = Math.round(target * eased);
            el.textContent = current + suffix;
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    // Navesi pozorovatele, kteri sekce odkryvaji, jakmile se doscrolluji.
    function spustitPozorovatele() {
        if ("IntersectionObserver" in window) {
            /* threshold 0 misto 0.08: u vysokych sekci znamenalo osm
               procent vysky pekny kus scrollovani navic, nez se vubec
               zacaly odkryvat. Staci, aby prvek zavadil do okna. */
            var animObserver = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            animateElement(entry.target);
                            animObserver.unobserve(entry.target);
                        }
                    });
                },
                { threshold: 0, rootMargin: "0px 0px -10px 0px" }
            );

            var vyskaOkna = window.innerHeight || 0;

            animEls.forEach(function (el) {
                if (el.getAttribute("data-anim") === "counter") {
                    return;
                }
                // Co uz je pri startu videt, se odkryje bez animace.
                if (el.getBoundingClientRect().top < vyskaOkna) {
                    animateElement(el, true);
                    return;
                }
                animObserver.observe(el);
            });

            // Counter observer
            var counterObserver = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting && !countersAnimated.has(entry.target)) {
                            countersAnimated.add(entry.target);
                            var parent = entry.target.closest("[data-anim]");
                            if (parent && !parent.classList.contains("anim-visible")) {
                                animateElement(parent);
                            }
                            setTimeout(function () {
                                entry.target.style.opacity = "1";
                                animateCounter(entry.target);
                            }, 500);
                            counterObserver.unobserve(entry.target);
                        }
                    });
                },
                { threshold: 0.5 }
            );

            counterEls.forEach(function (el) {
                el.style.opacity = "1";
                counterObserver.observe(el);
            });
        } else {
            // Fallback
            animEls.forEach(function (el) {
                el.classList.add("anim-visible");
            });
        }
    }

    if (!animuje) {
        // Bez animaci se nic neschovava ani nepozoruje - stranka je
        // rovnou cela videt.
        animEls.forEach(function (el) {
            el.classList.add("anim-visible");
        });
    } else {
        try {
            spustitPozorovatele();
        } catch (chyba) {
            vzdatSeAnimaci();
        }

        /* Hlidac. Kdyby se na nejaky prvek v okne pozorovatel nechytil
           (stava se, kdyz se rozvrzeni po nacteni obrazku posune),
           po chvili se odkryje sam. Lepsi zadna animace nez diry
           ve strance. */
        setTimeout(function () {
            var vyskaOkna = window.innerHeight || 0;
            animEls.forEach(function (el) {
                if (el.classList.contains("anim-visible")) {
                    return;
                }
                if (el.getBoundingClientRect().top < vyskaOkna) {
                    el.classList.add("anim-visible");
                }
            });
        }, 1200);
    }

    // ===== PARALLAX =====
    var ticking = false;

    function updateParallax() {
        var scrollY = window.pageYOffset || document.documentElement.scrollTop;
        var winH = window.innerHeight;

        parallaxEls.forEach(function (el) {
            var rect = el.getBoundingClientRect();
            var speed = parseFloat(el.getAttribute("data-parallax") || "0.1");

            if (rect.bottom > -200 && rect.top < winH + 200) {
                var center = rect.top + rect.height / 2 - winH / 2;
                var offset = center * speed * -1;
                el.style.transform = "translate3d(0, " + offset + "px, 0)";
            }
        });

        ticking = false;
    }

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    }

    // Only parallax on desktop
    if (window.matchMedia("(min-width: 769px) and (hover: hover)").matches) {
        window.addEventListener("scroll", onScroll, { passive: true });
        updateParallax();
    }

    // ===== STICKY CTA =====
    var sticky = document.getElementById("hhStickyCta");
    var heroEl = document.getElementById("hero");

    if (sticky && heroEl) {
        var stickyObserver = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        sticky.classList.add("hh-visible");
                    } else {
                        sticky.classList.remove("hh-visible");
                    }
                });
            },
            { threshold: 0 }
        );

        stickyObserver.observe(heroEl);
    }
})();

/**
 * PLYNULE ROLOVANI NA KOTVY
 *
 * Proc vlastni animace a ne scroll-behavior: smooth:
 *  - Odoo ma na a[href^="#"] vlastni JS scroll navesny na #wrapwrap.
 *    Pral se s CSS smooth a rolovani nedojelo k cili.
 *  - Potrebujeme odsadit o vysku fixni navigace, coz scroll-padding
 *    pri programovem scrollu neresi.
 *
 * Klik proto bereme uz v capture fazi (driv nez Odoo) a odrolujeme sami.
 * Cil se prepocitava v kazdem snimku, takze i kdyz se vyska stranky behem
 * rolovani zmeni, dojedeme presne.
 *
 * DULEZITE: uvnitr animace se scrolluje s behavior "auto". Kdyby se predal
 * jen window.scrollTo(0, y), pouzil by se scroll-behavior z CSS a animace
 * by se prala sama se sebou.
 */
(function () {
    "use strict";

    var landing = document.querySelector(".hh-landing");
    if (!landing) return;

    // Hlavicku vykresluje Odoo (website.layout), ne nase sablona. Kdyz je
    // prilepena nahore, musi se o jeji vysku odsadit cil rolovani - jinak
    // zacatek sekce skonci pod ni.
    function navOffset() {
        var hlavicka = document.querySelector("#wrapwrap > header, header#top, .o_header_standard");
        if (!hlavicka) return 16;
        var poz = window.getComputedStyle(hlavicka).position;
        if (poz !== "fixed" && poz !== "sticky") return 16;
        return hlavicka.getBoundingClientRect().height + 16;
    }

    function targetTop(el) {
        var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        var top = el.getBoundingClientRect().top + window.pageYOffset - navOffset();
        return Math.max(0, Math.min(Math.round(top), Math.round(maxScroll)));
    }

    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    var animId = null;

    function stopAnim() {
        if (animId !== null) {
            cancelAnimationFrame(animId);
            animId = null;
        }
    }

    // kdyz uzivatel sam zaroluje, animaci pustime
    ["wheel", "touchstart"].forEach(function (evt) {
        window.addEventListener(evt, stopAnim, { passive: true });
    });

    function slideTo(el) {
        stopAnim();

        var startY = window.pageYOffset;
        if (Math.abs(targetTop(el) - startY) < 2) return;

        // delsi cesta = delsi animace, ale drzime to v rozumnych mezich
        var duration = Math.min(1200, Math.max(500, Math.abs(targetTop(el) - startY) * 0.4));
        var startTime = null;

        function step(now) {
            if (startTime === null) startTime = now;
            var p = Math.min((now - startTime) / duration, 1);
            var goal = targetTop(el);
            var y = startY + (goal - startY) * easeInOutCubic(p);

            window.scrollTo({ top: Math.round(y), behavior: "auto" });

            if (p < 1) {
                animId = requestAnimationFrame(step);
            } else {
                animId = null;
                window.scrollTo({ top: targetTop(el), behavior: "auto" });
            }
        }

        animId = requestAnimationFrame(step);
    }

    document.addEventListener("click", function (ev) {
        if (!(ev.target instanceof Element)) return;

        var a = ev.target.closest('a[href^="#"]');
        if (!a || !landing.contains(a)) return;

        var href = a.getAttribute("href");
        if (!href || href === "#") return;

        var el = document.getElementById(href.slice(1));
        if (!el) return;

        // Odoo handler uz se k tomu nedostane
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation();

        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            window.scrollTo({ top: targetTop(el), behavior: "auto" });
        } else {
            slideTo(el);
        }

        if (window.history && history.replaceState) {
            history.replaceState(null, "", href);
        }
    }, true);
})();

/**
 * Zavirani rozbaleneho menu na mobilu.
 *
 * U odkazu na jinou stranku se menu zavre samo pri nacteni. U kotvy
 * na teze strance (treba /#jak-pracuji) ale zadne nacteni neprobehne -
 * prohlizec jen odscrolluje a rozbalene menu zustalo viset pres obsah,
 * na ktery clovek prave skocil.
 */
(function () {
    "use strict";

    document.addEventListener("click", function (udalost) {
        if (!(udalost.target instanceof Element)) {
            return;
        }

        var odkaz = udalost.target.closest(
            ".offcanvas a[href], .navbar-collapse a[href]"
        );
        if (!odkaz) {
            return;
        }

        var panel = odkaz.closest(".offcanvas, .navbar-collapse");
        if (!panel) {
            return;
        }

        // Bootstrap je na frontendu Odoo k dispozici. Kdyby nebyl,
        // sahne se na zaviraci tlacitko uvnitr panelu - dela totez.
        var bs = window.bootstrap;
        if (bs && bs.Offcanvas && panel.classList.contains("offcanvas")) {
            (bs.Offcanvas.getInstance(panel) || new bs.Offcanvas(panel)).hide();
            return;
        }
        if (bs && bs.Collapse && panel.classList.contains("navbar-collapse")) {
            (bs.Collapse.getInstance(panel) || new bs.Collapse(panel)).hide();
            return;
        }

        var zavrit = panel.querySelector("[data-bs-dismiss]");
        if (zavrit) {
            zavrit.click();
        }
    });
})();
