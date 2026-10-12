/* Stavebnice e-mailů v podobě "Krémový editorial".
 *
 * Druhý vzhled vedle nastroje/mail-bloky.js. Rozhraní je stejné -
 * bloky() a tabulky() berou tytéž značky textu (P, OTAZKA,
 * RAMECEK, UDAJE) - takže se u kterékoliv řady dá přepnout jedním
 * řádkem v generátoru.
 *
 * Podklad je od Honzy. Proti němu se mění jen obal, ne vzhled:
 * hodnoty, které byly u každé značky zvlášť, sedí v
 * <style id="design-element">, aby s nimi uměl hýbat editor.
 * Při odeslání si je Odoo rozepíše zpátky ke značkám samo.
 *
 * Třídy mají předponu hhe-, aby se nepraly s prvním vzhledem.
 *
 * Písma: v podkladu jsou Playfair Display a Inter z Google Fonts.
 * V e-mailu se nenačtou - schránky webová písma ignorují a Gmail
 * je zahazuje úplně - takže doopravdy se čte Georgia a Arial.
 * Serifový nadpis zůstane serifový, o to tu jde. Načíst je přes
 * @import nejde: editor si styly rozebírá po selektorech (splitCss
 * v mass_mailing) a na pravidle @import, které žádný selektor
 * nemá, spadne celá záložka Návrh.
 */

const { P, OTAZKA, RAMECEK, UDAJE } = require("./mail-bloky.js");

const KREM_STRANKA = "#efe7d8";
const KREM_KARTA = "#f4efe6";
const LINKA = "#e3d9c8";
const GRAFIT = "#23211d";
const INKOUST = "#5d554b";
const BRONZ = "#a06a37";
const BRONZ_SVETLY = "#c08a52";
const TAUPE = "#a89681";
const SEDA = "#857b6e";

const LOGO = "/theme_honzahauzr/static/src/img/vr/vr-logo-email.png";
const ZNAK = "/honzahauzr_crm/static/src/img/hh-znak-email.png";

const PODPIS = "Honza Hauzr";
const ROLE = "Mentor pro muže &#183; Vlastní režie";

/* ---------------------------------------------------------------- */
/* podoba pro editor: Odoo bloky                                    */
/* ---------------------------------------------------------------- */

const STYLY = `<style id="design-element">
.o_mail_wrapper_td { background-color: ${KREM_KARTA} !important; border: 1px solid ${LINKA}; }
.o_mail_wrapper { font-family: Inter, Arial, sans-serif; color: ${INKOUST}; }
.o_mail_wrapper p { font-size: 16px; line-height: 27px; margin: 0 0 18px 0; }
.o_mail_wrapper h1.hhe-nadpis { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 34px; line-height: 40px; font-weight: 700; letter-spacing: -0.3px; color: ${GRAFIT}; margin: 14px 0 0 0; }
.o_mail_wrapper .hhe-jmeno { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${TAUPE}; margin: 0; }
.o_mail_wrapper .hhe-eyebrow { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${BRONZ}; margin: 0; }
.o_mail_wrapper .hhe-prah { width: 48px; height: 2px; background-color: ${BRONZ}; margin-top: 22px; font-size: 0; line-height: 2px; }
.o_mail_wrapper .hhe-oslo { color: ${GRAFIT}; font-weight: 600; }
.o_mail_wrapper .hhe-tmave { color: ${GRAFIT}; }
.o_mail_wrapper .hhe-otazka { background-color: ${GRAFIT}; border-left: 3px solid ${BRONZ_SVETLY}; padding: 28px 30px; }
.o_mail_wrapper .hhe-otazka .hhe-eyebrow { color: ${BRONZ_SVETLY}; font-size: 10px; }
.o_mail_wrapper .hhe-otazka p { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 22px; line-height: 30px; font-weight: 700; color: ${KREM_KARTA}; margin: 10px 0 0 0; }
.o_mail_wrapper .hhe-ramecek { background-color: #ffffff; border: 1px solid ${LINKA}; padding: 24px 26px 6px 26px; }
.o_mail_wrapper .hhe-ramecek p { color: ${GRAFIT}; }
.o_mail_wrapper .hhe-pod { font-size: 12.5px; line-height: 19px; color: ${SEDA}; margin: 14px 0 0 0; }
.o_mail_wrapper .hhe-linka-nad { border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hhe-podpis { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: ${GRAFIT}; margin: 0; }
.o_mail_wrapper .hhe-role { font-size: 12px; letter-spacing: 1px; text-transform: uppercase; color: ${TAUPE}; margin: 2px 0 0 0; }
.o_mail_wrapper .hhe-paticka { background-color: ${GRAFIT}; }
.o_mail_wrapper .hhe-paticka p { font-size: 12px; line-height: 19px; color: #9c958a; margin: 0; }
.o_mail_wrapper .hhe-paticka .hhe-odesilatel { color: #d6cec1; }
.o_mail_wrapper .hhe-paticka a { color: ${BRONZ_SVETLY}; text-decoration: underline; }
.o_mail_wrapper a.btn.btn-primary { background-color: ${BRONZ}; border-color: ${BRONZ}; color: #ffffff; font-size: 12px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; padding: 17px 36px; border-radius: 3px; }
</style>`;

/* Odsazeni jako v podkladu: 48 px po stranach. Drzi se na bloku,
   ne ve stylech - editor s nim pak umi hybat. */
const BOKY = "padding-left:48px;padding-right:48px;";

const blok = (trida, vnitrek, styl) =>
    `        <div class="${trida} o_mail_snippet_general">
          <div class="container s_allow_columns" style="${styl || BOKY}">
${vnitrek}
          </div>
        </div>`;

/* Logo je obrazek, ne vysazeny text - jen tak ho jde v editoru
   vymenit dvojklikem za jiny. */
const HLAVICKA = `        <div class="s_header_logo o_mail_block_header_logo o_mail_snippet_general pt24 pb24" style="border-bottom:1px solid ${LINKA};">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-7">
                <img src="${LOGO}" alt="Vlastní režie" width="170" style="width:170px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-5" style="text-align:right;">
                <p class="hhe-jmeno">Honza Hauzr</p>
              </div>
            </div>
          </div>
        </div>`;

function blokyTelo(telo) {
    const kusy = [];
    let odstavce = [];

    /* Souvisle odstavce zustavaji v jednom textovem bloku. Kdyby
       mel kazdy vlastni, nasekal by se text na desitku bloku
       a v editoru by se v tom nedalo hnout. */
    const vysypat = (trida) => {
        if (!odstavce.length) return;
        kusy.push(blok(trida || "s_text_block pt24 pb0", odstavce.join("\n")));
        odstavce = [];
    };

    for (const kus of telo) {
        if (kus.typ === "p") {
            const trida = kus.barva && kus.barva !== "#5d554b"
                ? ' class="hhe-tmave"' : "";
            odstavce.push(`            <p${trida}>${kus.t}</p>`);
        } else if (kus.typ === "otazka") {
            vysypat();
            kusy.push(blok("s_mail_blockquote pt24 pb24",
`            <div class="hhe-otazka">
              <p class="hhe-eyebrow">Otázka na dnešek</p>
              <p>${kus.t}</p>
            </div>`));
        } else if (kus.typ === "ramecek" || kus.typ === "udaje") {
            vysypat();
            const radky = (kus.odstavce || kus.radky)
                .map((r) => `              <p>${r}</p>`).join("\n");
            kusy.push(blok("s_mail_alert pt8 pb24",
                           `            <div class="hhe-ramecek">\n${radky}\n            </div>`));
        }
    }
    vysypat("s_text_block pt0 pb0");
    return kusy.join("\n");
}

function blokTlacitko(text, odkaz, pod) {
    return `        <div class="s_call_to_action o_mail_snippet_general pt32 pb8">
          <div class="container" style="${BOKY}text-align:center;">
            <a href="${odkaz}" role="button" class="btn btn-primary">${text}</a>${pod ? `
            <p class="hhe-pod">${pod}</p>` : ""}
          </div>
        </div>`;
}

function blokPodpis(podpis) {
    return `        <div class="s_text_block o_mail_snippet_general hhe-linka-nad pt32 pb32">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-2">
                <img src="${ZNAK}" alt="Honza Hauzr" width="44" style="width:44px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-10">
                <p class="hhe-podpis">${podpis || PODPIS}</p>
                <p class="hhe-role">${ROLE}</p>
              </div>
            </div>
          </div>
        </div>`;
}

/* Patička s odhlášením. Do hotových zpráv ji doplňuje modul sám
   (hh.mail.sablona._hh_srovnat_sablony), ať je u všech stejná
   a nedá se z ní vypadnout. Tahle podoba je kvůli návrhu
   v galerii - nová zpráva ji musí mít hned. Zástupné texty jsou
   stejné, podle nich se pozná, že odhlášení ve zprávě je. */
function paticka() {
    return `        <div class="s_text_block o_mail_snippet_general hhe-paticka pt24 pb24">
          <div class="container" style="${BOKY}text-align:center;">
            <p class="hhe-odesilatel">{{ object.hh_paticka_odesilatel }}</p>
            <p style="margin-top:8px;">Tenhle e-mail ti přišel, protože ses přihlásil do bezplatné výzvy Z autopilota zpět do života.</p>
            <p style="margin-top:10px;"><a href="{{ object.hh_odkaz_odhlaseni }}">Nechceš ode mě další e-maily? Odhlas se.</a></p>
          </div>
        </div>`;
}

/* Obal, ktery kolem obsahu stavi sam editor, kdyz se vybere
   predloha. Drzime se jeho tvaru do pismene - jinak se zprava
   tvari jako prazdna a misto textu naskoci galerie predloh. */
function kostra(obsah) {
    return `<div class="o_layout oe_unremovable oe_unmovable bg-200 oe_styling_vr o_mass_mailing_no_theme" style="background-color:${KREM_STRANKA};" data-name="Mailing">
${STYLY}
  <div class="container o_mail_wrapper o_mail_regular oe_unremovable">
    <div class="row">
      <div class="col o_mail_no_options o_mail_wrapper_td bg-white oe_structure o_editable">
${obsah}
      </div>
    </div>
  </div>
</div>`;
}

function bloky({ eyebrow, nadpis, telo, tlacitko, odkaz, pod, podpis,
                 osloveni = true }) {
    const kusy = [HLAVICKA];

    kusy.push(blok("s_title pt40 pb0",
`            <p class="hhe-eyebrow">${eyebrow}</p>
            <h1 class="hhe-nadpis">${nadpis}</h1>
            <div class="hhe-prah">&#160;</div>`));

    if (osloveni) {
        kusy.push(blok("s_text_block pt24 pb0",
            '            <p class="hhe-oslo">{{ object.hh_osloveni }}</p>'));
    }

    kusy.push(blokyTelo(telo));
    if (tlacitko) kusy.push(blokTlacitko(tlacitko, odkaz, pod));
    kusy.push(blokPodpis(podpis));

    return kostra(kusy.join("\n"));
}

/* ---------------------------------------------------------------- */
/* podoba pro poštu: tabulky a styly u značek                       */
/* ---------------------------------------------------------------- */

const PISMO = "Inter,Arial,sans-serif";
const SERIF = "'Playfair Display',Georgia,'Times New Roman',serif";

const tP = (t, barva) =>
    `            <p style="margin:0 0 18px 0;font-family:${PISMO};font-size:16px;line-height:27px;color:${barva || INKOUST};">${t}</p>`;

function tabulkyTelo(telo) {
    return telo.map((kus) => {
        if (kus.typ === "p") {
            const tmave = kus.barva && kus.barva !== "#5d554b";
            return tP(kus.t, tmave ? GRAFIT : INKOUST);
        }
        if (kus.typ === "otazka") {
            return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:8px 0 26px 0;background-color:${GRAFIT};">
              <tr>
                <td style="padding:28px 30px;border-left:3px solid ${BRONZ_SVETLY};">
                  <p style="margin:0;font-family:${PISMO};font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${BRONZ_SVETLY};">Otázka na dnešek</p>
                  <p style="margin:10px 0 0 0;font-family:${SERIF};font-size:22px;line-height:30px;font-weight:700;color:${KREM_KARTA};">${kus.t}</p>
                </td>
              </tr>
            </table>`;
        }
        const radky = kus.odstavce || kus.radky;
        return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:8px 0 26px 0;background-color:#ffffff;">
              <tr>
                <td style="padding:24px 26px 6px 26px;border:1px solid ${LINKA};">
${radky.map((r) => tP(r, GRAFIT)).join("\n")}
                </td>
              </tr>
            </table>`;
    }).join("\n");
}

function tabulky({ eyebrow, nadpis, telo, tlacitko, odkaz, pod, podpis,
                   osloveni = true }) {
    return `<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:${KREM_STRANKA};margin:0;padding:0;">
  <tr>
    <td align="center" style="padding:32px 12px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:600px;background-color:${KREM_KARTA};border:1px solid ${LINKA};">

        <!-- hlavicka: logo a jmeno -->
        <tr>
          <td style="padding:28px 48px 24px 48px;border-bottom:1px solid ${LINKA};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="left" valign="middle">
                  <img src="${LOGO}" alt="Vlastní režie" width="170" height="32"
                       style="display:block;border:0;outline:none;text-decoration:none;width:170px;height:32px;"/>
                </td>
                <td align="right" valign="middle"
                    style="font-family:${PISMO};font-size:10.5px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${TAUPE};">
                  Honza Hauzr
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- nadpis -->
        <tr>
          <td style="padding:44px 48px 0 48px;">
            <p style="margin:0;font-family:${PISMO};font-size:10.5px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${BRONZ};">${eyebrow}</p>
            <h1 style="margin:14px 0 0 0;font-family:${SERIF};font-size:34px;line-height:40px;font-weight:700;letter-spacing:-0.3px;color:${GRAFIT};">${nadpis}</h1>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:22px;">
              <tr><td width="48" height="2" bgcolor="${BRONZ}" style="width:48px;height:2px;font-size:0;line-height:2px;">&#160;</td></tr>
            </table>
          </td>
        </tr>

        <!-- obsah -->
        <tr>
          <td style="padding:28px 48px 0 48px;">
${osloveni ? tP("{{ object.hh_osloveni }}", GRAFIT) : ""}
${tabulkyTelo(telo)}
          </td>
        </tr>
${tlacitko ? `
        <!-- jedina vyzva k akci -->
        <tr>
          <td align="center" style="padding:34px 48px 10px 48px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="${BRONZ}" style="background-color:${BRONZ};border-radius:3px;">
                  <a href="${odkaz}"
                     style="display:inline-block;padding:17px 36px;font-family:${PISMO};font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#ffffff;text-decoration:none;border-radius:3px;">${tlacitko}</a>
                </td>
              </tr>
            </table>${pod ? `
            <p style="margin:14px 0 0 0;font-family:${PISMO};font-size:12.5px;line-height:19px;color:${SEDA};">${pod}</p>` : ""}
          </td>
        </tr>` : ""}

        <!-- podpis -->
        <tr>
          <td style="padding:36px 48px 40px 48px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid ${LINKA};">
              <tr>
                <td width="58" valign="middle" style="padding-top:26px;">
                  <img src="${ZNAK}" alt="Honza Hauzr" width="44" height="44"
                       style="display:block;border:0;outline:none;text-decoration:none;width:44px;height:44px;"/>
                </td>
                <td valign="middle" style="padding-top:26px;">
                  <p style="margin:0;font-family:${SERIF};font-size:19px;font-weight:700;color:${GRAFIT};">${podpis || PODPIS}</p>
                  <p style="margin:2px 0 0 0;font-family:${PISMO};font-size:12px;letter-spacing:1px;text-transform:uppercase;color:${TAUPE};">${ROLE}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>`;
}

module.exports = {
    P, OTAZKA, RAMECEK, UDAJE,
    bloky, tabulky, kostra, paticka, STYLY,
    KREM_STRANKA, GRAFIT,
};
