/* Stavebnice e-mailů Honzy Hauzra.
 *
 * Každá zpráva se vyrábí dvakrát, protože editor a pošta chtějí
 * každý něco jiného:
 *
 *   bloky()   -> pole body_arch. Odoo bloky, jaké zná editor
 *                z Email Marketingu: <div class="... o_mail_snippet_general">
 *                uvnitř .oe_structure. Jen takové bloky umí editor
 *                vybrat, posunout, smazat a dát mezi ně jiné.
 *                Tlačítko je <a class="btn btn-primary">, takže se
 *                mu dá přepsat odkaz přes řetízek v liště.
 *
 *   tabulky() -> pole body_html. To, co opravdu odejde. Outlook
 *                kreslí HTML jádrem Wordu: nezná flexbox, mřížku
 *                ani styly v hlavičce. Proto vnořené tabulky
 *                a styly přímo u značek.
 *
 * Když Honza zprávu otevře v editoru a uloží, vyrobí si Odoo
 * body_html z body_arch samo (widget mass_mailing_html, volba
 * inline-field). Tahle stavebnice řeší jen výchozí podobu.
 *
 * Text zprávy se popisuje značkami P / OTAZKA / RAMECEK / UDAJE.
 * Nevrací HTML, ale popis - teprve emitor z něj udělá bloky nebo
 * tabulku. Díky tomu je text v generátorech na jednom místě.
 */

const KREM = "#f4efe6";
const GRAFIT = "#23211d";
const INKOUST = "#5d554b";
const LINKA = "#e2dacb";
const SVETLA = "#a89681";
const SEDA = "#8c8276";
const LOGO = "/theme_honzahauzr/static/src/img/vr/vr-logo-email.png";

/* ---------------------------------------------------------------- */
/* značky textu                                                     */
/* ---------------------------------------------------------------- */

const P = (t, barva) => ({ typ: "p", t, barva: barva || INKOUST });

/* Otázka k zamyšlení. Svislá linka vlevo, jako má web u claimu. */
const OTAZKA = (t) => ({ typ: "otazka", t });

/* Rámeček na delší pasáž, kterou je potřeba odlišit od výkladu -
   třeba podmínky garance. */
const RAMECEK = (odstavce) => ({ typ: "ramecek", odstavce });

/* Rámeček na údaje k zapamatování - datum a čas hovoru. */
const UDAJE = (radky) => ({ typ: "udaje", radky });

/* Zvýrazněný panel: eyebrow, nadpis, pár čísel vedle sebe a věta
   pod nimi. Nese nabídku uvnitř zprávy - třídenní výzvu
   v uvítacím e-mailu. Čísla se píšou jako [["3", "dny"], ...].

   Vzhled, který s čísly umí, je zatím jen tmavý
   (nastroje/mail-bloky-tmava.js). Ostatní ho vykreslí jako
   obyčejný rámeček - nic se tím nerozbije, jen to nebude tak
   výrazné. */
const PANEL = ({ eyebrow, nadpis, cisla, text }) =>
    ({ typ: "panel", eyebrow, nadpis, cisla: cisla || [], text });

/* ---------------------------------------------------------------- */
/* podoba pro editor: Odoo bloky                                    */
/* ---------------------------------------------------------------- */

/* Styly zprávy. V editoru je vidět hned, při odeslání si je Odoo
   přepíše k jednotlivým značkám samo.

   Selektory jsou schválně přes .o_mail_wrapper a s názvem značky
   (a.btn, ne .btn): styly editoru mají u tlačítka vlastní barvu
   a bez té váhy navíc by přebily tu naši. */
const STYLY = `<style id="design-element">
.o_mail_wrapper { font-family: Helvetica, Arial, sans-serif; color: ${INKOUST}; }
/* Barva musi byt primo na p, jinak ji prebije Bootstrap. */
.o_mail_wrapper p { font-size: 16px; line-height: 1.65; margin: 0 0 18px 0; color: ${INKOUST}; }
.o_mail_wrapper h1 { font-size: 28px; line-height: 1.25; font-weight: bold; color: ${GRAFIT}; margin: 0 0 24px 0; }
.o_mail_wrapper .hh-eyebrow { font-size: 12px; letter-spacing: 1.6px; text-transform: uppercase; color: ${SVETLA}; margin: 0 0 14px 0; }
.o_mail_wrapper .hh-tmave { color: ${GRAFIT}; }
.o_mail_wrapper .hh-drobne { font-size: 12px; line-height: 1.6; color: ${SEDA}; margin: 0; }
.o_mail_wrapper .hh-otazka { border-left: 3px solid ${GRAFIT}; padding: 2px 0 2px 18px; font-size: 18px; line-height: 1.5; font-weight: bold; color: ${GRAFIT}; margin: 0; }
.o_mail_wrapper .hh-ramecek { background-color: ${KREM}; border: 1px solid ${LINKA}; padding: 20px 22px 4px 22px; }
.o_mail_wrapper .hh-ramecek p { color: ${GRAFIT}; }
.o_mail_wrapper .hh-linka-nad { border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hh-linka-pod { border-bottom: 1px solid ${LINKA}; }
.o_mail_wrapper a.btn.btn-primary { background-color: ${GRAFIT}; border-color: ${GRAFIT}; color: #ffffff; font-size: 14px; letter-spacing: 1.2px; text-transform: uppercase; font-weight: bold; padding: 16px 34px; border-radius: 0; }
</style>`;

/* Obal, který kolem obsahu staví sám editor, když se vybere
   předloha. Držíme se jeho tvaru do písmene - jinak se zpráva
   tváří jako prázdná a místo textu naskočí galerie předloh.

   .oe_structure je jediné místo, kam jde pustit blok, a volby
   bloku dostane jen <div> přímo pod ní. Proto je obsah složený
   z divů, ne z jedné velké tabulky jako dřív. */
function kostra(obsah) {
    return `<div class="o_layout oe_unremovable oe_unmovable bg-200 oe_styling_vr o_mass_mailing_no_theme" style="background-color:${KREM};" data-name="Mailing">
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

const blok = (trida, vnitrek, styl) =>
    `        <div class="${trida} o_mail_snippet_general pt16 pb16"${styl ? ` style="${styl}"` : ""}>
          <div class="container s_allow_columns">
${vnitrek}
          </div>
        </div>`;

function blokHlavicka() {
    return `        <div class="s_header_logo o_mail_block_header_logo o_mail_snippet_general hh-linka-pod pt24 pb16">
          <div class="container">
            <div class="row">
              <div class="col-8">
                <img src="${LOGO}" alt="Vlastní režie" width="190" style="width:190px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-4" style="text-align:right;">
                <p class="hh-eyebrow" style="margin:10px 0 0 0;">Honza Hauzr</p>
              </div>
            </div>
          </div>
        </div>`;
}

/* Panel bez vlastniho vykresleni: cisla se slozi do vety, at se
   obsah neztrati. */
function panelRadky(kus) {
    const radky = [];
    if (kus.nadpis) radky.push("<strong>" + kus.nadpis + "</strong>");
    if (kus.cisla && kus.cisla.length) {
        radky.push(kus.cisla.map(([c, popis]) => c + " " + popis).join(" &#183; "));
    }
    if (kus.text) radky.push(kus.text);
    return radky;
}

function blokyTelo(telo, uvod) {
    const kusy = [];
    let odstavce = uvod ? uvod.slice() : [];

    /* Souvislé odstavce zůstávají v jednom textovém bloku. Kdyby
       měl každý vlastní, nasekal by se text na desítku bloků
       a v editoru by se v tom nedalo hnout. */
    const vysypat = () => {
        if (!odstavce.length) return;
        kusy.push(blok("s_text_block", odstavce.join("\n"),
                       "padding-left:15px;padding-right:15px;"));
        odstavce = [];
    };

    for (const kus of telo) {
        if (kus.typ === "p") {
            const trida = kus.barva === GRAFIT ? ' class="hh-tmave"' : "";
            odstavce.push(`            <p${trida}>${kus.t}</p>`);
        } else if (kus.typ === "otazka") {
            vysypat();
            kusy.push(blok("s_mail_blockquote",
                           `            <p class="hh-otazka">${kus.t}</p>`,
                           "padding-left:15px;padding-right:15px;"));
        } else if (kus.typ === "ramecek" || kus.typ === "udaje") {
            vysypat();
            const radky = (kus.odstavce || kus.radky)
                .map((r) => `              <p>${r}</p>`).join("\n");
            kusy.push(blok("s_mail_alert",
                           `            <div class="hh-ramecek">\n${radky}\n            </div>`,
                           "padding-left:15px;padding-right:15px;"));
        }
    }
    vysypat();
    return kusy.join("\n");
}

function blokTlacitko(text, odkaz) {
    return `        <div class="s_call_to_action o_mail_snippet_general pt8 pb24" style="text-align:center;">
          <div class="container">
            <a href="${odkaz}" role="button" class="btn btn-primary">${text}</a>
          </div>
        </div>`;
}

const PODPIS = "<strong>Honza</strong>";

/* Znacka HH vedle podpisu. Obrazek, ne vysazene pismeno - jen tak
   ji jde v editoru vymenit dvojklikem za jiny obrazek. */
const ZNAK = "/honzahauzr_crm/static/src/img/hh-znak-email.png";

function blokPodpis(podpis) {
    return `        <div class="s_text_block o_mail_snippet_general hh-linka-nad pt24 pb24" style="padding-left:15px;padding-right:15px;">
          <div class="container">
            <div class="row">
              <div class="col-2">
                <img src="${ZNAK}" alt="Honza Hauzr" width="40" style="width:40px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-10">
                <p class="hh-tmave">${podpis || PODPIS}</p>
              </div>
            </div>
          </div>
        </div>`;
}

function blokDrobne(text) {
    return blok("s_text_block", `            <p class="hh-drobne">${text}</p>`,
                "padding-left:15px;padding-right:15px;text-align:center;");
}

/* Patička s odhlášením.

   Do hotových zpráv ji doplňuje modul sám
   (hh.mail.sablona._hh_srovnat_sablony podle PATICKA_BLOK
   v crm_lead_maily.py), ať je u všech stejná a nedá se z ní
   vypadnout. Tady stojí podruhé kvůli návrhu v galerii: nová
   zpráva ji musí mít hned, ne až po nějakém srovnání.

   Obě podoby musí zůstat stejné - kdyby se rozešly, srovnání by
   u nové zprávy našlo odhlášení a druhou patičku už nepřidalo. */
function paticka() {
    return `        <div class="s_text_block o_mail_snippet_general hh-linka-nad pt16 pb16" style="padding-left:15px;padding-right:15px;text-align:center;">
          <div class="container s_allow_columns">
            <p class="hh-drobne">{{ object.hh_paticka_odesilatel }}<br/>Tenhle e-mail ti přišel, protože ses přihlásil do bezplatné výzvy Z autopilota zpět do života.<br/><a href="{{ object.hh_odkaz_odhlaseni }}" style="text-decoration:underline;">Nechceš ode mě další e-maily? Odhlas se.</a></p>
          </div>
        </div>`;
}

/* Hlavička, obsah, jedna výzva k akci, podpis. */
function bloky({ eyebrow, nadpis, telo, tlacitko, odkaz, pod, podpis,
                 osloveni = true }) {
    const kusy = [blokHlavicka()];

    /* Eyebrow, nadpis a oslovení jdou do stejného bloku jako první
       odstavce. Samostatný blok by mezi oslovení a text vrazil
       mezeru, která v původní zprávě nebyla. */
    const uvod = [`            <p class="hh-eyebrow">${eyebrow}</p>`,
                  `            <h1>${nadpis}</h1>`];
    if (osloveni) {
        uvod.push('            <p class="hh-tmave">{{ object.hh_osloveni }}</p>');
    }

    kusy.push(blokyTelo(telo, uvod));
    if (tlacitko) kusy.push(blokTlacitko(tlacitko, odkaz));
    if (pod) kusy.push(blokDrobne(pod));
    kusy.push(blokPodpis(podpis));

    return kostra(kusy.join("\n"));
}

/* ---------------------------------------------------------------- */
/* podoba pro poštu: tabulky a styly u značek                       */
/* ---------------------------------------------------------------- */

const tP = (t, barva) =>
    `            <p style="margin:0 0 18px 0;font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.65;color:${barva || INKOUST};">${t}</p>`;

function tabulkyTelo(telo) {
    return telo.map((kus) => {
        if (kus.typ === "p") return tP(kus.t, kus.barva);
        if (kus.typ === "otazka") {
            return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 22px 0;">
              <tr>
                <td style="padding:2px 0 2px 18px;border-left:3px solid ${GRAFIT};font-family:Helvetica,Arial,sans-serif;font-size:18px;line-height:1.5;color:${GRAFIT};font-weight:bold;">${kus.t}</td>
              </tr>
            </table>`;
        }
        const radky = kus.odstavce || kus.radky || panelRadky(kus);
        return `            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 22px 0;background-color:${KREM};">
              <tr>
                <td style="padding:20px 22px 4px 22px;border:1px solid ${LINKA};">
${radky.map((r) => tP(r, GRAFIT)).join("\n")}
                </td>
              </tr>
            </table>`;
    }).join("\n");
}

function tabulky({ eyebrow, nadpis, telo, tlacitko, odkaz, pod, podpis,
                   osloveni = true }) {
    return `<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:${KREM};margin:0;padding:0;">
  <tr>
    <td align="center" style="padding:24px 10px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid ${LINKA};">

        <!-- hlavicka: logo a jmeno -->
        <tr>
          <td style="padding:24px 22px 20px 22px;border-bottom:1px solid ${LINKA};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="left" valign="middle">
                  <img src="${LOGO}" alt="Vlastní režie" width="190" height="35"
                       style="display:block;border:0;outline:none;text-decoration:none;width:190px;height:35px;"/>
                </td>
                <td align="right" valign="middle"
                    style="font-family:Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:1.2px;text-transform:uppercase;color:${INKOUST};">
                  Honza Hauzr
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- obsah -->
        <tr>
          <td style="padding:30px 22px 8px 22px;">
            <p style="margin:0 0 14px 0;font-family:Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:1.6px;text-transform:uppercase;color:${SVETLA};">${eyebrow}</p>
            <h1 style="margin:0 0 24px 0;font-family:Helvetica,Arial,sans-serif;font-size:28px;line-height:1.25;font-weight:bold;color:${GRAFIT};">${nadpis}</h1>
${osloveni ? tP("{{ object.hh_osloveni }}", GRAFIT) : ""}
${tabulkyTelo(telo)}
          </td>
        </tr>
${tlacitko ? `
        <!-- jedina vyzva k akci -->
        <tr>
          <td align="center" style="padding:14px 22px 10px 22px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="${GRAFIT}" style="background-color:${GRAFIT};">
                  <a href="${odkaz}"
                     style="display:inline-block;padding:16px 34px;font-family:Helvetica,Arial,sans-serif;font-size:14px;letter-spacing:1.2px;text-transform:uppercase;font-weight:bold;color:#ffffff;text-decoration:none;">${tlacitko}</a>
                </td>
              </tr>
            </table>
          </td>
        </tr>` : ""}
${pod ? `
        <tr>
          <td align="center" style="padding:6px 22px 24px 22px;">
            <p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;color:${SEDA};">${pod}</p>
          </td>
        </tr>` : `
        <tr><td style="padding:0 22px 16px 22px;"></td></tr>`}

        <!-- podpis -->
        <tr>
          <td style="padding:0 22px 30px 22px;border-top:1px solid ${LINKA};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:26px;">
              <tr>
                <td valign="top" width="54" style="padding-right:14px;">
                  <img src="${ZNAK}" alt="Honza Hauzr" width="40" height="40"
                       style="display:block;border:0;outline:none;text-decoration:none;width:40px;height:40px;"/>
                </td>
                <td valign="middle" style="font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:${GRAFIT};">
                  ${podpis || PODPIS}
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
    KREM, GRAFIT, INKOUST, LINKA, SVETLA, SEDA, LOGO,
    P, OTAZKA, RAMECEK, UDAJE, PANEL,
    bloky, tabulky, kostra, paticka, STYLY,
};
