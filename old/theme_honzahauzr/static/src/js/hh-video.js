/**
 * Videa - stahuje se jen ta verze, ktera je videt
 *
 * Na hlavni strance i na landing page lezi videa ve dvojici:
 * sirokouhla 16:9 na desktop a svisla 9:16 na mobil. Jedna z nich je
 * vzdycky schovana pres display: none. To ale nestaci - prohlizec
 * schovany <iframe> stahne stejne. loading="lazy" nepomuze: schovane
 * ramecky Chrome zamerne neodklada, protoze se casto pouzivaji na
 * mereni.
 *
 * V markupu je jen prazdny <div class="media_iframe_video"> s adresou
 * v data-oe-expression. Ramecek do nej dosadi az Odoo pri nacteni
 * stranky, a to dvema cestami: generate_video_iframe.js na
 * DOMContentLoaded a widget mediaVideo ze snippets.animation.js.
 * Obe berou vsechny bloky na strance vcetne schovanych - odtud dve
 * stazeni misto jednoho.
 *
 * Obe ale spolecne preskakuji blok, ktery uz nejaky <iframe> ma. Staci
 * je tedy predbehnout a ramecky dosadit sam: viditelne variante i s
 * adresou, schovane prazdny. Odoo pak nema co delat.
 *
 * Proto je tenhle soubor obycejny skript, ne odoo modul. Obycejne
 * skripty ve svazku bezi driv nez moduly, takze se jeho posluchac na
 * DOMContentLoaded prihlasi jako prvni a jako prvni se i spusti.
 * Poradi ve svazku hlida directive="before" v data/ir_asset.xml.
 *
 * Adresu skript nikde neurcuje, bere ji z data-oe-expression. Kazdy
 * blok si tak drzi svou vlastni a meni se v editoru jako kterykoli
 * jiny video blok.
 *
 * Sedi zvlast, protoze se tyka obou stranek.
 */
(function () {
    "use strict";

    /* Prevod bezneho odkazu na vkladaci podobu.
    
       Do policka "Video pro mobil" clovek prirozene vlozi to, co ma
       v prohlizeci - tedy youtube.com/watch?v=..., youtu.be/... nebo
       u svislych videi youtube.com/shorts/.... Takovy odkaz ale
       v <iframe> nehraje, YouTube ho odmitne. Dialog Odoo si to
       prevede sam, tohle policko je obycejny text, takze prevod musi
       udelat skript.
    
       Co uz vkladaci podobu ma, projde beze zmeny. */
    function naVkladaci(adresa) {
        var a = (adresa || "").trim();
        if (!a || a.indexOf("/embed/") !== -1 || a.indexOf("player.vimeo.com") !== -1) {
            return a;
        }

        var m = a.match(
            /(?:youtube\.com\/watch\?[^#]*\bv=|youtu\.be\/|youtube\.com\/shorts\/|youtube\.com\/live\/)([\w-]{6,})/
        );
        if (m) {
            return "//www.youtube.com/embed/" + m[1] + "?rel=0&autoplay=0&controls=1";
        }

        m = a.match(/vimeo\.com\/(?:video\/)?(\d+)/);
        if (m) {
            return "//player.vimeo.com/video/" + m[1];
        }

        return a;
    }


    /* Seznam funkci, ktere prohlizec vlozenemu ramecku z ciziho webu
       povoli. Nastavuje se kazdemu ramecku, nejen tomu, ktery skript
       sam vyrobi - ve strankach ulozenych z editoru uz ramecek je
       a Odoo mu tenhle seznam nedava. */
    var POVOLENI =
        "accelerometer; autoplay; clipboard-write; encrypted-media;"
        + " gyroscope; fullscreen";

    /* Ramecek se stavi stejne, jak by ho postavilo Odoo - vcetne dvou
       pomocnych divu, na ktere se vaze jeho vlastni CSS. Adresu zatim
       nedostava, tu resi volajici. */
    function pripravRamecek(prehravac, popis) {
        var ramecek = prehravac.querySelector("iframe");
        if (ramecek) {
            return ramecek;
        }

        if (!prehravac.querySelector(".media_iframe_video_size")) {
            var proEditor = document.createElement("div");
            proEditor.className = "css_editable_mode_display";
            var proVelikost = document.createElement("div");
            proVelikost.className = "media_iframe_video_size";
            prehravac.appendChild(proEditor);
            prehravac.appendChild(proVelikost);
        }

        ramecek = document.createElement("iframe");
        ramecek.setAttribute("frameborder", "0");
        ramecek.setAttribute("allowfullscreen", "allowfullscreen");
        ramecek.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
        /* Bez tohohle prohlizec prehravaci cast funkci zakaze -
           u vlozeneho ramecku z ciziho webu se ridi timhle seznamem,
           ne jen atributem allowfullscreen. */
        ramecek.setAttribute("allow", POVOLENI);
        ramecek.setAttribute("aria-label", popis || "Video");
        prehravac.appendChild(ramecek);
        return ramecek;
    }

    /* Projde vsechny bloky a srovna je s tim, co je zrovna videt.
       Bezi pri nacteni stranky a po zmene sirky okna. */
    function srovnejVidea() {
        var obaly = document.querySelectorAll(".hhn-video");

        Array.prototype.forEach.call(obaly, function (obal) {
            var prehravac = obal.querySelector(".media_iframe_video");
            if (!prehravac) {
                return;
            }

            /* Adresu drzi Odoo v data-oe-expression. Kdyz ma blok
               vyplnenou i adresu pro mobil, pouzije se na uzkem okne
               ona - jeden blok, dve adresy. Hranice 991 px je ta
               sama, na ktere se prepina pomer v hh-novy.scss. */
            /* Prevod i u hlavni adresy, nejen u te mobilni. Dialog Odoo
               si bezny odkaz obvykle prevede sam, ale ne vzdycky -
               u youtube.com/shorts/... ulozil 2. 10. 2026 do stranky
               adresu tak, jak byla. YouTube ji v ramecku odmitne
               zobrazit, prohlizec to zkousi dokola a cela stranka
               blika. naVkladaci necha vkladaci podobu beze zmeny,
               takze tohle nic nerozbije. */
            var adresa = naVkladaci(prehravac.getAttribute("data-oe-expression"));
            var proMobil = obal.getAttribute("data-hhn-video-mobil");
            if (proMobil && window.innerWidth <= 991) {
                adresa = naVkladaci(proMobil);
            }
            var ramecek = pripravRamecek(
                prehravac,
                obal.getAttribute("data-hhv-popis")
            );
            if (ramecek.getAttribute("allow") !== POVOLENI) {
                ramecek.setAttribute("allow", POVOLENI);
            }

            /* offsetParent je null u vseho, co ma display: none -
               vcetne rodicu. Presne to tu potrebujeme zjistit. */
            if (obal.offsetParent !== null) {
                if (adresa && ramecek.getAttribute("src") !== adresa) {
                    ramecek.setAttribute("src", adresa);
                }
                return;
            }

            /* Schovana varianta zustava prazdna. Adresu dostane az se
               okno zuzi a bude na ni videt. */
            if (ramecek.getAttribute("src")) {
                ramecek.removeAttribute("src");
            }
        });
    }

    /* Odoo si ramecky dosazuje na DOMContentLoaded. Tenhle skript se
       proto chyta o krok driv, na prechod do stavu "interactive" -
       ten prijde hned po docteni stranky a jeste pred
       DOMContentLoaded. Diky tomu nezalezi na tom, ktery skript se
       prihlasil driv. DOMContentLoaded je tu jen jako pojistka pro
       pripad, ze by stav "interactive" utekl. */
    if (document.readyState === "loading") {
        document.addEventListener("readystatechange", function () {
            if (document.readyState !== "loading") {
                srovnejVidea();
            }
        });
        document.addEventListener("DOMContentLoaded", srovnejVidea);
    } else {
        srovnejVidea();
    }

    /* Po zmene sirky se varianty prohodi - ta nova potrebuje svou
       adresu doplnit. Hlida se sirka stranky, ne okna: v editoru Odoo
       sedi stranka v ramecku a prepinac na mobilni nahled zuzi jen
       ten, takze okno o nicem nevi. */
    var prepinani;
    function poZmene() {
        clearTimeout(prepinani);
        prepinani = setTimeout(srovnejVidea, 200);
    }

    if ("ResizeObserver" in window) {
        new ResizeObserver(poZmene).observe(document.documentElement);
    } else {
        window.addEventListener("resize", poZmene);
    }
})();
