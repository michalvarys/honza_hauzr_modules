/* Stavebnice e-mailů v tmavé podobě, v barvách webu Honza Hauzr.
 *
 * Třetí vzhled vedle nastroje/mail-bloky.js (světlý, bílá karta)
 * a mail-bloky-editorial.js (krémový). Rozhraní mají všechny tři
 * stejné - bloky() a tabulky() berou tytéž značky textu - takže se
 * u kterékoliv řady dá přepnout jedním řádkem v generátoru.
 *
 * Podklad je od Honzy. Proti němu se mění jen obal, ne vzhled:
 * hodnoty, které byly u každé značky zvlášť, sedí v
 * <style id="design-element">, aby s nimi uměl hýbat editor.
 *
 * Třídy mají předponu hht- (tmavá), aby se nepraly s ostatními.
 *
 * Proti podkladu dvě úpravy, obě podle pravidel projektu:
 *   - tlačítko míří na /zpet-do-zivota, ne na úplnou adresu devu
 *   - odhlášení je {{ object.hh_odkaz_odhlaseni }}, ne
 *     /unsubscribe_from_list; podle téhle značky modul pozná, že
 *     zpráva odhlášení má, a nepřidává druhé
 *
 * Písma: v podkladu jsou Playfair Display a Inter z Google Fonts.
 * V e-mailu se nenačtou, čte se Georgia a Arial. Načíst je přes
 * @import nejde: editor si styly rozebírá po selektorech (splitCss
 * v mass_mailing) a na pravidle @import, které žádný selektor
 * nemá, spadne celá záložka Návrh.
 */

const { P, OTAZKA, RAMECEK, UDAJE, PANEL } = require("./mail-bloky.js");

const CERNA = "#0a0a0f";
const KARTA = "#111a26";
const PANEL_POZADI = "#0d141e";
const LINKA = "#1e2c40";
const LINKA_PANEL = "#243650";
const BILA = "#ffffff";
const TEXT = "#ffffff";
const SEDA = "#c9d1da";
const SEDA_SVETLA = "#a9b0b9";
const MODRA = "#2aa6ee";
const MODRA_SVETLA = "#6bb5ff";

/* Logo Honzy Hauzra, ne Vlastni rezie: tahle podoba patri ke
   strankam honzahauzr.cz, odkud chodi prihlaseni k odberu.
   Modre na pruhlednem pozadi, takze sedne na kazdou tmavou kartu. */
const LOGO = "/honzahauzr_crm/static/src/img/hh-logo-tmava.png";
const ZNAK = "/honzahauzr_crm/static/src/img/hh-znak-email.png";

const PODPIS = "Honza Hauzr";
const ROLE = "Mentor pro muže &#183; Vlastní režie";

/* ---------------------------------------------------------------- */
/* podoba pro editor: Odoo bloky                                    */
/* ---------------------------------------------------------------- */

const STYLY = `<style id="design-element">
.o_mail_wrapper_td { background-color: ${KARTA} !important; border: 1px solid ${LINKA}; border-radius: 6px; }
.o_mail_wrapper { font-family: Inter, Arial, sans-serif; color: ${TEXT}; }
/* Barva musi byt primo na p. Bez toho ji prebije Bootstrap
   (#212529) a text je na tmave karte skoro cerny. */
.o_mail_wrapper p { font-size: 16px; line-height: 27px; margin: 0 0 18px 0; color: ${BILA}; }
.o_mail_wrapper h1.hht-nadpis { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 38px; line-height: 44px; font-weight: 700; letter-spacing: -0.4px; color: ${BILA}; margin: 14px 0 0 0; }
.o_mail_wrapper .hht-znacka { font-size: 12px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; color: ${BILA}; margin: 0; }
.o_mail_wrapper .hht-jmeno { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${SEDA}; margin: 0; }
.o_mail_wrapper .hht-eyebrow { font-size: 11px; font-weight: 600; letter-spacing: 2.6px; text-transform: uppercase; color: ${MODRA_SVETLA}; margin: 0; }
.o_mail_wrapper .hht-prah { width: 48px; height: 2px; background-color: ${MODRA}; margin-top: 22px; font-size: 0; line-height: 2px; }
.o_mail_wrapper .hht-oslo { color: ${BILA}; font-weight: 600; }
.o_mail_wrapper .hht-tmave { color: ${BILA}; }
.o_mail_wrapper .hht-panel { background-color: ${PANEL_POZADI}; border: 1px solid ${LINKA_PANEL}; border-radius: 6px; padding: 28px 30px; }
.o_mail_wrapper .hht-panel .hht-eyebrow { font-size: 10px; letter-spacing: 2.5px; }
.o_mail_wrapper .hht-panel-nadpis { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 24px; line-height: 31px; font-weight: 700; color: ${BILA}; margin: 10px 0 0 0; }
.o_mail_wrapper .hht-cislo { font-size: 26px; line-height: 30px; font-weight: 800; color: ${MODRA_SVETLA}; margin: 0; }
.o_mail_wrapper .hht-popis { font-size: 12px; letter-spacing: 1px; text-transform: uppercase; color: ${SEDA}; margin: 2px 0 0 0; }
.o_mail_wrapper .hht-panel-text { font-size: 15px; line-height: 25px; color: ${BILA}; margin: 18px 0 0 0; }
.o_mail_wrapper .hht-otazka { background-color: ${PANEL_POZADI}; border-left: 3px solid ${MODRA}; border-radius: 6px; padding: 28px 30px; }
.o_mail_wrapper .hht-otazka p { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 22px; line-height: 30px; font-weight: 700; color: ${BILA}; margin: 10px 0 0 0; }
.o_mail_wrapper .hht-pod { font-size: 12.5px; line-height: 19px; color: ${SEDA}; margin: 14px 0 0 0; }
.o_mail_wrapper .hht-linka-nad { border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hht-podpis { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: ${BILA}; margin: 0; }
.o_mail_wrapper .hht-role { font-size: 12px; letter-spacing: 1px; line-height: 19px; text-transform: uppercase; color: ${SEDA}; margin: 2px 0 0 0; }
.o_mail_wrapper .hht-paticka { background-color: ${CERNA}; border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hht-paticka p { font-size: 12px; line-height: 19px; color: ${SEDA}; margin: 0; }
.o_mail_wrapper .hht-paticka .hht-odesilatel { color: ${SEDA_SVETLA}; }
.o_mail_wrapper .hht-paticka a { color: ${MODRA_SVETLA}; text-decoration: underline; }
.o_mail_wrapper a.btn.btn-primary { background-color: ${MODRA}; border-color: ${MODRA}; color: #ffffff; font-size: 12px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; padding: 17px 36px; border-radius: 999px; }
</style>`;

const BOKY = "padding-left:48px;padding-right:48px;";

const blok = (trida, vnitrek, styl) =>
    `        <div class="${trida} o_mail_snippet_general">
          <div class="container s_allow_columns" style="${styl || BOKY}">
${vnitrek}
          </div>
        </div>`;

/* Logo je obrazek, ne vysazeny text - jen tak ho jde v editoru
   vymenit dvojklikem za jiny.

   Jmeno vedle loga uz tu neni: nese ho samo logo a stalo by tam
   podruhe. */
const HLAVICKA = `        <div class="s_header_logo o_mail_block_header_logo o_mail_snippet_general pt24 pb24" style="border-bottom:1px solid ${LINKA};">
          <div class="container" style="${BOKY}">
            <img src="${LOGO}" alt="Honza Hauzr" width="150" style="width:150px;height:auto;" class="img-fluid"/>
          </div>
        </div>`;

function blokPanel(kus) {
    const sirka = kus.cisla.length ? Math.floor(12 / kus.cisla.length) : 12;
    const cisla = kus.cisla.map(([cislo, popis]) =>
`              <div class="col-${sirka}">
                <p class="hht-cislo">${cislo}</p>
                <p class="hht-popis">${popis}</p>
              </div>`).join("\n");
    return `        <div class="s_mail_alert o_mail_snippet_general pt24 pb0">
          <div class="container" style="${BOKY}">
            <div class="hht-panel">
${kus.eyebrow ? `              <p class="hht-eyebrow">${kus.eyebrow}</p>` : ""}
${kus.nadpis ? `              <p class="hht-panel-nadpis">${kus.nadpis}</p>` : ""}
${cisla ? `              <div class="row" style="margin-top:18px;">\n${cisla}\n              </div>` : ""}
${kus.text ? `              <p class="hht-panel-text">${kus.text}</p>` : ""}
            </div>
          </div>
        </div>`;
}

function blokyTelo(telo) {
    const kusy = [];
    let odstavce = [];

    const vysypat = (trida) => {
        if (!odstavce.length) return;
        kusy.push(blok(trida || "s_text_block pt24 pb0", odstavce.join("\n")));
        odstavce = [];
    };

    for (const kus of telo) {
        if (kus.typ === "p") {
            const trida = kus.barva && kus.barva !== "#5d554b"
                ? ' class="hht-tmave"' : "";
            odstavce.push(`            <p${trida}>${kus.t}</p>`);
        } else if (kus.typ === "otazka") {
            vysypat();
            kusy.push(blok("s_mail_blockquote pt24 pb0",
`            <div class="hht-otazka">
              <p class="hht-eyebrow">Otázka na dnešek</p>
              <p>${kus.t}</p>
            </div>`));
        } else if (kus.typ === "panel") {
            vysypat();
            kusy.push(blokPanel(kus));
        } else {
            vysypat();
            const radky = (kus.odstavce || kus.radky)
                .map((r) => `              <p class="hht-tmave">${r}</p>`).join("\n");
            kusy.push(blok("s_mail_alert pt24 pb0",
                `            <div class="hht-panel">\n${radky}\n            </div>`));
        }
    }
    vysypat("s_text_block pt24 pb0");
    return kusy.join("\n");
}

function blokTlacitko(text, odkaz, pod) {
    return `        <div class="s_call_to_action o_mail_snippet_general pt32 pb8">
          <div class="container" style="${BOKY}text-align:center;">
            <a href="${odkaz}" role="button" class="btn btn-primary">${text}</a>${pod ? `
            <p class="hht-pod">${pod}</p>` : ""}
          </div>
        </div>`;
}

function blokPodpis(podpis) {
    return `        <div class="s_text_block o_mail_snippet_general hht-linka-nad pt32 pb32">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-2">
                <img src="${ZNAK}" alt="Honza Hauzr" width="44" style="width:44px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-10">
                <p class="hht-podpis">${podpis || PODPIS}</p>
                <p class="hht-role">${ROLE}</p>
              </div>
            </div>
          </div>
        </div>`;
}

/* Patička s odhlášením. Do hotových zpráv ji doplňuje modul sám,
   tahle podoba je kvůli návrhu v galerii - nová zpráva ji musí mít
   hned. Zástupné texty jsou stejné, podle nich se pozná, že
   odhlášení ve zprávě je. */
function paticka() {
    return `        <div class="s_text_block o_mail_snippet_general hht-paticka pt24 pb24">
          <div class="container" style="${BOKY}text-align:center;">
            <p class="hht-odesilatel">{{ object.hh_paticka_odesilatel }}</p>
            <p style="margin-top:8px;">Tenhle e-mail ti přišel, protože ses přihlásil k odběru e-mailů od Honzy Hauzra.</p>
            <p style="margin-top:10px;"><a href="{{ object.hh_odkaz_odhlaseni }}">Nechceš ode mě další e-maily? Odhlas se.</a></p>
          </div>
        </div>`;
}

function kostra(obsah) {
    return `<div class="o_layout oe_unremovable oe_unmovable bg-200 oe_styling_vr hh-vzhled-tmava o_mass_mailing_no_theme" style="background-color:${CERNA};" data-name="Mailing">
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
`            <p class="hht-eyebrow">${eyebrow}</p>
            <h1 class="hht-nadpis">${nadpis}</h1>
            <div class="hht-prah">&#160;</div>`));

    if (osloveni) {
        kusy.push(blok("s_text_block pt24 pb0",
            '            <p class="hht-oslo">{{ object.hh_osloveni }}</p>'));
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
    `            <p style="margin:0 0 18px 0;font-family:${PISMO};font-size:16px;line-height:27px;color:${barva || TEXT};">${t}</p>`;

function tabulkyPanel(kus) {
    const sirka = kus.cisla.length ? Math.floor(100 / kus.cisla.length) : 100;
    const cisla = kus.cisla.map(([cislo, popis]) =>
`                      <td width="${sirka}%" valign="top" style="padding-right:8px;font-family:${PISMO};">
                        <div style="font-size:26px;line-height:30px;font-weight:800;color:${MODRA_SVETLA};">${cislo}</div>
                        <div style="margin-top:2px;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:${SEDA};">${popis}</div>
                      </td>`).join("\n");
    return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${PANEL_POZADI}" style="margin:8px 0 26px 0;background-color:${PANEL_POZADI};border:1px solid ${LINKA_PANEL};border-radius:6px;">
              <tr>
                <td style="padding:28px 30px;">
${kus.eyebrow ? `                  <div style="font-family:${PISMO};font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${MODRA_SVETLA};">${kus.eyebrow}</div>` : ""}
${kus.nadpis ? `                  <div style="margin-top:10px;font-family:${SERIF};font-size:24px;line-height:31px;font-weight:700;color:${BILA};">${kus.nadpis}</div>` : ""}
${cisla ? `                  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:18px;">
                    <tr>
${cisla}
                    </tr>
                  </table>` : ""}
${kus.text ? `                  <p style="margin:18px 0 0 0;font-family:${PISMO};font-size:15px;line-height:25px;color:${TEXT};">${kus.text}</p>` : ""}
                </td>
              </tr>
            </table>`;
}

function tabulkyTelo(telo) {
    return telo.map((kus) => {
        if (kus.typ === "p") {
            const tmave = kus.barva && kus.barva !== "#5d554b";
            return tP(kus.t, tmave ? BILA : TEXT);
        }
        if (kus.typ === "panel") {
            return tabulkyPanel(kus);
        }
        if (kus.typ === "otazka") {
            return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${PANEL_POZADI}" style="margin:8px 0 26px 0;background-color:${PANEL_POZADI};border-radius:6px;">
              <tr>
                <td style="padding:28px 30px;border-left:3px solid ${MODRA};">
                  <div style="font-family:${PISMO};font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${MODRA_SVETLA};">Otázka na dnešek</div>
                  <div style="margin-top:10px;font-family:${SERIF};font-size:22px;line-height:30px;font-weight:700;color:${BILA};">${kus.t}</div>
                </td>
              </tr>
            </table>`;
        }
        const radky = kus.odstavce || kus.radky;
        return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${PANEL_POZADI}" style="margin:8px 0 26px 0;background-color:${PANEL_POZADI};border:1px solid ${LINKA_PANEL};border-radius:6px;">
              <tr>
                <td style="padding:24px 26px 6px 26px;">
${radky.map((r) => tP(r, BILA)).join("\n")}
                </td>
              </tr>
            </table>`;
    }).join("\n");
}

function tabulky({ eyebrow, nadpis, telo, tlacitko, odkaz, pod, podpis,
                   osloveni = true }) {
    return `<!-- hh-vzhled:tmava -->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${CERNA}" style="background-color:${CERNA};margin:0;padding:0;">
  <tr>
    <td align="center" style="padding:32px 12px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${KARTA}" style="width:100%;max-width:600px;background-color:${KARTA};border:1px solid ${LINKA};border-radius:6px;">

        <!-- hlavicka: logo Honzy Hauzra -->
        <tr>
          <td style="padding:26px 48px 22px 48px;border-bottom:1px solid ${LINKA};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="left" valign="middle">
                  <img src="${LOGO}" alt="Honza Hauzr" width="150" height="90"
                       style="display:block;border:0;outline:none;text-decoration:none;width:150px;height:90px;"/>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- nadpis -->
        <tr>
          <td style="padding:44px 48px 0 48px;">
            <p style="margin:0;font-family:${PISMO};font-size:11px;font-weight:600;letter-spacing:2.6px;text-transform:uppercase;color:${MODRA_SVETLA};">${eyebrow}</p>
            <h1 style="margin:14px 0 0 0;font-family:${SERIF};font-size:38px;line-height:44px;font-weight:700;letter-spacing:-0.4px;color:${BILA};">${nadpis}</h1>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:22px;">
              <tr><td width="48" height="2" bgcolor="${MODRA}" style="width:48px;height:2px;font-size:0;line-height:2px;">&#160;</td></tr>
            </table>
          </td>
        </tr>

        <!-- obsah -->
        <tr>
          <td style="padding:28px 48px 0 48px;">
${osloveni ? tP("{{ object.hh_osloveni }}", BILA) : ""}
${tabulkyTelo(telo)}
          </td>
        </tr>
${tlacitko ? `
        <!-- jedina vyzva k akci -->
        <tr>
          <td align="center" style="padding:34px 48px 10px 48px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="${MODRA}" style="background-color:${MODRA};border-radius:999px;">
                  <a href="${odkaz}"
                     style="display:inline-block;padding:17px 36px;font-family:${PISMO};font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#ffffff;text-decoration:none;border-radius:999px;">${tlacitko}</a>
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
                  <p style="margin:0;font-family:${SERIF};font-size:19px;font-weight:700;color:${BILA};">${podpis || PODPIS}</p>
                  <p style="margin:2px 0 0 0;font-family:${PISMO};font-size:12px;letter-spacing:1px;line-height:19px;text-transform:uppercase;color:${SEDA};">${ROLE}</p>
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
    P, OTAZKA, RAMECEK, UDAJE, PANEL,
    bloky, tabulky, kostra, paticka, STYLY,
    CERNA, BILA,
};
