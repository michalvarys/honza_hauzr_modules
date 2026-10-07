/** @odoo-module **/

/**
 * Chyby, ktere do stranky zanese sam prohlizec
 *
 * Odoo hlida nezachycene chyby v JavaScriptu a kazdou ukaze
 * navstevnikovi jako okno "Oops! Something went wrong". To je
 * spravne u chyb z naseho kodu. Jenze do stranky vklada svuj kod
 * i prohlizec a jeho doplnky, a kdyz spadne ten, okno vyskoci uplne
 * stejne - akorat s nim nikdo nic nenadela a stranka pritom funguje.
 *
 * Konkretne Firefox na iPhonu vklada do kazde stranky obsluhu ctecky
 * clanku. Ta sahne na window._firefox_.reader driv, nez ho prohlizec
 * stihne vytvorit, spadne na TypeError a Odoo na to vytahne okno
 * s chybou. Na strance vyzvy se to opakuje pri kazdem odrolovani,
 * protoze ctecka znovu a znovu zkousi, jestli uz jde text precist.
 * Nahlasil to Honza 7. 10. 2026.
 *
 * Pozna se to podle toho, odkud chyba prisla. Vsechen kod webu -
 * nas i Odoo - se nacita ze svazku /web/assets/..., takze jeho chyby
 * maji tuhle cestu ve stope. Kod vlozeny prohlizecem nebo doplnkem
 * zadny vlastni soubor nema: ukaze se bud u adresy same stranky,
 * nebo bez nazvu souboru. Overeno na devu - chyba z naseho kodu
 * nesla z web.assets_frontend_lazy.min.js, chyba ctecky z niceho.
 *
 * Nefiltruje se podle textu hlasky zamerne. Kazdy prohlizec ji pise
 * jinak: Safari a Firefox na iOS vypisou cely vyraz
 * ("window._firefox_.reader.checkReadability"), Chrome jen nazev
 * vlastnosti ("reading 'reader'"). Filtr podle textu by tak zabral
 * jen nekde.
 *
 * Takove chyby se zahazuji - jen vypisem do konzole, at se na ne da
 * pri hledani problemu prijit. Nase vlastni chyby prochazeji dal
 * a okno se u nich ukaze jako predtim.
 */

import { registry } from "@web/core/registry";

/* Svazky, ze kterych se nacita kod webu. */
const KOD_WEBU = /\/web\/assets\//;

/* Kde chyba vznikla.

   Zamerne se nesaha na chyba.stack. Obalku UncaughtClientError vyrabi
   Odoo az ve svem error_service, takze jeji vlastni stack vede vzdycky
   do svazku /web/assets/ - a kazda chyba by podle nej vypadala jako
   nase. Puvod nese az traceback, nazev souboru v udalosti a stack
   puvodni chyby. */
function stopa(chyba, puvodni) {
    const kousky = [];
    if (chyba) {
        kousky.push(chyba.traceback);
        if (chyba.event) {
            kousky.push(chyba.event.filename);
        }
    }
    if (puvodni) {
        kousky.push(puvodni.stack);
    }
    return kousky.filter(Boolean).join(" ");
}

function cizíChybaProhlizece(env, chyba, puvodni) {
    const kde = stopa(chyba, puvodni);
    /* Bez jakekoliv stopy se nic nezahazuje - radeji okno navic nez
       spolknuta chyba, o ktere nevime nic. */
    if (!kde || KOD_WEBU.test(kde)) {
        /* Chyba z naseho kodu - at se ukaze jako kdykoliv predtim. */
        return false;
    }
    console.warn(
        "Chyba mimo kod webu, nejspis z prohlizece nebo jeho doplnku:",
        (puvodni && puvodni.message) || (chyba && chyba.message)
    );
    return true;
}

/* Sekvence 1: musime se dostat ke slovu driv nez obsluha, ktera
   chybu ukaze v okne. */
registry
    .category("error_handlers")
    .add("hh_cizi_chyby_prohlizece", cizíChybaProhlizece, { sequence: 1 });
