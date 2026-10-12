/* Stavebnice e-mailů pro potvrzení rezervace.
 *
 * Čtvrtý vzhled vedle světlého, editorialu a tmavého. Rozhraní mají
 * všechny stejné - bloky() a tabulky() berou tytéž značky textu -
 * takže se u kterékoliv řady dá přepnout jedním řádkem
 * v generátoru.
 *
 * Podklad je od Honzy. Proti němu se mění jen obal, ne vzhled:
 * hodnoty, které byly u každé značky zvlášť, sedí v
 * <style id="design-element">, aby s nimi uměl hýbat editor.
 *
 * Třídy mají předponu hhr- (rezervace), aby se nepraly s ostatními.
 *
 * Co je tu navíc proti ostatním vzhledům:
 *   TERMIN    bílá karta s bronzovým pruhem: kdy, jak dlouho, forma
 *   KROKY     číslovaný seznam toho, co si má člověk připravit
 *   ZRUSENI   rámeček s obtaženým tlačítkem na zrušení termínu
 *
 * Tři úpravy proti podkladu, všechny podle pravidel projektu:
 *   - tlačítko zrušení míří na {{ object.hh_termin_zruseni }}
 *   - v patičce je odkaz na odhlášení; podklad ho neměl, a modul by
 *     pak přilepil druhou patičku
 *   - ilustrace telefonu v tmavém pásu tu není: podklad ji vezl
 *     jako base64 přímo v HTML, což by nafouklo každou odeslanou
 *     zprávu. Až bude obrázek jako soubor, vloží se do modulu
 *     a doplní sem.
 */

const { P, OTAZKA, RAMECEK, UDAJE, PANEL } = require("./mail-bloky.js");

const PISEK = "#efe7d8";
const KREM = "#f4efe6";
const BILA = "#ffffff";
const LINKA = "#e3d9c8";
const GRAFIT = "#23211d";
const INKOUST = "#5d554b";
const BRONZ = "#a06a37";
const BRONZ_SVETLY = "#c08a52";
const TAUPE = "#a89681";
const SEDA = "#857b6e";
const ZELENA = "#35694a";
const KREM_TLUMENY = "#b8b0a3";

// Logo je obrazek s zapecenym pozadim, ne pruhledny - tmavy rezim
// posty by pod pruhlednost podlozil svou barvu a znak by zmizel.
// Proto ma kazdy vzhled svou kopii v barve sveho pruhu; tahle sedi
// na grafitovou #23211d.
const LOGO = "/honzahauzr_crm/static/src/img/vr-logo-rezervace.png";
const ZNAK = "/honzahauzr_crm/static/src/img/hh-znak-email.png";

const PODPIS = "Těším se, Honza";
const ROLE = "Mentor pro muže &#183; Vlastní režie";

/* ---------------------------------------------------------------- */
/* značky navíc                                                     */
/* ---------------------------------------------------------------- */

/* Karta termínu: velké datum a pod ním dva údaje vedle sebe. */
const TERMIN = ({ kdy, udaje }) => ({ typ: "termin", kdy, udaje: udaje || [] });

/* Co si má člověk nachystat. Číslo, tučný začátek, zbytek věty. */
const KROKY = (kroky) => ({ typ: "kroky", kroky });

/* Rámeček se zrušením: věta, obtažené tlačítko, drobná poznámka. */
const ZRUSENI = ({ text, tlacitko, odkaz, pod }) =>
    ({ typ: "zruseni", text, tlacitko, odkaz, pod });

/* ---------------------------------------------------------------- */
/* podoba pro editor: Odoo bloky                                    */
/* ---------------------------------------------------------------- */

const STYLY = `<style id="design-element">
.o_mail_wrapper_td { background-color: ${KREM} !important; border: 1px solid ${LINKA}; }
.o_mail_wrapper { font-family: Inter, Arial, sans-serif; color: ${INKOUST}; }
.o_mail_wrapper p { font-size: 16px; line-height: 27px; margin: 0 0 18px 0; color: ${INKOUST}; }
.o_mail_wrapper h1.hhr-nadpis { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 36px; line-height: 42px; font-weight: 700; letter-spacing: -0.3px; color: ${KREM}; margin: 18px 0 0 0; }
.o_mail_wrapper .hhr-hlava { background-color: ${GRAFIT}; }
.o_mail_wrapper .hhr-jmeno { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${TAUPE}; margin: 0; }
.o_mail_wrapper .hhr-odznak { display: inline-block; background-color: ${ZELENA}; border-radius: 999px; padding: 7px 14px; font-size: 10.5px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #ffffff; margin: 0; }
.o_mail_wrapper .hhr-podnadpis { font-size: 15px; line-height: 24px; color: ${KREM_TLUMENY}; margin: 12px 0 0 0; }
.o_mail_wrapper .hhr-prah { height: 4px; background-color: ${BRONZ}; font-size: 0; line-height: 4px; }
.o_mail_wrapper .hhr-oslo { color: ${GRAFIT}; font-weight: 600; }
.o_mail_wrapper .hhr-tmave { color: ${GRAFIT}; }
.o_mail_wrapper .hhr-karta { background-color: ${BILA}; border: 1px solid ${LINKA}; border-left: 6px solid ${BRONZ}; padding: 24px 26px; }
.o_mail_wrapper .hhr-stitek { font-size: 10px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${BRONZ}; margin: 0; }
.o_mail_wrapper .hhr-kdy { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 24px; line-height: 31px; font-weight: 700; color: ${GRAFIT}; margin: 6px 0 0 0; }
.o_mail_wrapper .hhr-nadlinka { border-top: 1px solid ${PISEK}; padding-top: 16px; margin-top: 18px; }
.o_mail_wrapper .hhr-popisek { font-size: 10px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${TAUPE}; margin: 0; }
.o_mail_wrapper .hhr-hodnota { font-size: 15px; line-height: 23px; font-weight: 600; color: ${GRAFIT}; margin: 5px 0 0 0; }
.o_mail_wrapper .hhr-cislo { font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: ${BRONZ}; margin: 0; }
.o_mail_wrapper .hhr-krok { font-size: 15px; line-height: 24px; color: ${INKOUST}; margin: 0 0 14px 0; }
.o_mail_wrapper .hhr-zruseni { background-color: ${PISEK}; padding: 24px 26px 26px 26px; text-align: center; }
.o_mail_wrapper .hhr-zruseni p { font-size: 15px; line-height: 24px; margin: 0; }
.o_mail_wrapper .hhr-pod { font-size: 12px; line-height: 18px; color: ${SEDA}; margin: 10px 0 0 0; }
.o_mail_wrapper .hhr-linka-nad { border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hhr-podpis { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: ${GRAFIT}; margin: 0; }
.o_mail_wrapper .hhr-role { font-size: 12px; letter-spacing: 1px; line-height: 19px; text-transform: uppercase; color: ${TAUPE}; margin: 2px 0 0 0; }
.o_mail_wrapper .hhr-paticka { background-color: ${GRAFIT}; }
.o_mail_wrapper .hhr-paticka p { font-size: 12px; line-height: 19px; color: #9c958a; margin: 0; }
.o_mail_wrapper .hhr-paticka .hhr-odesilatel { color: #d6cec1; }
.o_mail_wrapper .hhr-paticka a { color: ${BRONZ_SVETLY}; text-decoration: underline; }
.o_mail_wrapper a.btn.btn-primary { background-color: transparent; border: 1px solid ${BRONZ}; color: ${BRONZ}; font-size: 11.5px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; padding: 13px 28px; border-radius: 3px; }
</style>`;

const BOKY = "padding-left:48px;padding-right:48px;";

const blok = (trida, vnitrek, styl) =>
    `        <div class="${trida} o_mail_snippet_general">
          <div class="container s_allow_columns" style="${styl || BOKY}">
${vnitrek}
          </div>
        </div>`;

/* Hlavicka je tmavy pas: logo, jmeno, odznak a nadpis v nem.
   Logo je obrazek, ne vysazeny text - jen tak ho jde v editoru
   vymenit dvojklikem za jiny. */
function blokHlavicka(eyebrow, nadpis, podnadpis) {
    return `        <div class="s_header_logo o_mail_block_header_logo o_mail_snippet_general hhr-hlava pt24 pb8">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-7">
                <img src="${LOGO}" alt="Vlastní režie" width="150" style="width:150px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-5" style="text-align:right;">
                <p class="hhr-jmeno">Honza Hauzr</p>
              </div>
            </div>
          </div>
        </div>
        <div class="s_title o_mail_snippet_general hhr-hlava pt8 pb40">
          <div class="container s_allow_columns" style="${BOKY}text-align:center;">
            <p><span class="hhr-odznak">&#10003;&#160; ${eyebrow}</span></p>
            <h1 class="hhr-nadpis">${nadpis}</h1>${podnadpis ? `
            <p class="hhr-podnadpis">${podnadpis}</p>` : ""}
          </div>
        </div>
        <div class="s_hr o_mail_snippet_general">
          <div class="container">
            <div class="hhr-prah">&#160;</div>
          </div>
        </div>`;
}

function blokTermin(kus) {
    const sirka = kus.udaje.length ? Math.floor(12 / kus.udaje.length) : 12;
    const udaje = kus.udaje.map(([popis, hodnota]) =>
`                <div class="col-${sirka}">
                  <p class="hhr-popisek">${popis}</p>
                  <p class="hhr-hodnota">${hodnota}</p>
                </div>`).join("\n");
    return `        <div class="s_mail_alert o_mail_snippet_general pt24 pb0">
          <div class="container" style="${BOKY}">
            <div class="hhr-karta">
              <p class="hhr-stitek">Kdy</p>
              <p class="hhr-kdy">${kus.kdy}</p>${udaje ? `
              <div class="row hhr-nadlinka">
${udaje}
              </div>` : ""}
            </div>
          </div>
        </div>`;
}

function blokKroky(kus) {
    const radky = kus.kroky.map(([tucne, zbytek], i) =>
`              <div class="row">
                <div class="col-1">
                  <p class="hhr-cislo">${i + 1}</p>
                </div>
                <div class="col-11">
                  <p class="hhr-krok"><strong class="hhr-tmave">${tucne}</strong> ${zbytek}</p>
                </div>
              </div>`).join("\n");
    return `        <div class="s_text_block o_mail_snippet_general pt24 pb0">
          <div class="container" style="${BOKY}">
${radky}
          </div>
        </div>`;
}

function blokZruseni(kus) {
    return `        <div class="s_call_to_action o_mail_snippet_general pt24 pb8">
          <div class="container" style="${BOKY}">
            <div class="hhr-zruseni">
              <p>${kus.text}</p>
              <p style="margin-top:18px;"><a href="${kus.odkaz}" role="button" class="btn btn-primary">${kus.tlacitko}</a></p>${kus.pod ? `
              <p class="hhr-pod">${kus.pod}</p>` : ""}
            </div>
          </div>
        </div>`;
}

function blokyTelo(telo) {
    const kusy = [];
    let odstavce = [];

    const vysypat = () => {
        if (!odstavce.length) return;
        kusy.push(blok("s_text_block pt24 pb0", odstavce.join("\n")));
        odstavce = [];
    };

    for (const kus of telo) {
        if (kus.typ === "p") {
            const trida = kus.barva && kus.barva !== "#5d554b"
                ? ' class="hhr-tmave"' : "";
            odstavce.push(`            <p${trida}>${kus.t}</p>`);
            continue;
        }
        vysypat();
        if (kus.typ === "termin") {
            kusy.push(blokTermin(kus));
        } else if (kus.typ === "kroky") {
            kusy.push(blokKroky(kus));
        } else if (kus.typ === "zruseni") {
            kusy.push(blokZruseni(kus));
        } else {
            const radky = (kus.odstavce || kus.radky || [kus.t])
                .map((r) => `              <p class="hhr-tmave">${r}</p>`).join("\n");
            kusy.push(blok("s_mail_alert pt24 pb0",
                `            <div class="hhr-karta">\n${radky}\n            </div>`));
        }
    }
    vysypat();
    return kusy.join("\n");
}

function blokPodpis(podpis) {
    return `        <div class="s_text_block o_mail_snippet_general pt24 pb32">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-2">
                <img src="${ZNAK}" alt="Honza Hauzr" width="44" style="width:44px;height:auto;" class="img-fluid"/>
              </div>
              <div class="col-10">
                <p class="hhr-podpis">${podpis || PODPIS}</p>
                <p class="hhr-role">${ROLE}</p>
              </div>
            </div>
          </div>
        </div>`;
}

/* Patička s odhlášením. Podklad ji měl bez odkazu na odhlášení;
   ten tu být musí, jinak by ji modul doplnil podruhé a zpráva by
   měla patičky dvě. */
function paticka() {
    return `        <div class="s_text_block o_mail_snippet_general hhr-paticka pt24 pb24">
          <div class="container" style="${BOKY}text-align:center;">
            <p class="hhr-odesilatel">{{ object.hh_paticka_odesilatel }}</p>
            <p style="margin-top:8px;">Tenhle e-mail ti přišel, protože sis rezervoval úvodní hovor k programu Tvůj tah.</p>
            <p style="margin-top:10px;"><a href="{{ object.hh_odkaz_odhlaseni }}">Nechceš ode mě další e-maily? Odhlas se.</a></p>
          </div>
        </div>`;
}

function kostra(obsah) {
    return `<div class="o_layout oe_unremovable oe_unmovable bg-200 oe_styling_vr hh-vzhled-rezervace o_mass_mailing_no_theme" style="background-color:${PISEK};" data-name="Mailing">
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

function bloky({ eyebrow, nadpis, podnadpis, telo, podpis, osloveni = true }) {
    const kusy = [blokHlavicka(eyebrow, nadpis, podnadpis)];

    if (osloveni) {
        kusy.push(blok("s_text_block pt32 pb0",
            '            <p class="hhr-oslo">{{ object.hh_osloveni }}</p>'));
    }

    kusy.push(blokyTelo(telo));
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

function tabulkyTermin(kus) {
    const sirka = kus.udaje.length ? Math.floor(100 / kus.udaje.length) : 100;
    const udaje = kus.udaje.map(([popis, hodnota]) =>
`                      <td width="${sirka}%" valign="top" style="padding:16px 12px 0 0;font-family:${PISMO};">
                        <div style="font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${TAUPE};">${popis}</div>
                        <div style="margin-top:5px;font-size:15px;line-height:23px;font-weight:600;color:${GRAFIT};">${hodnota}</div>
                      </td>`).join("\n");
    return `            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${BILA}" style="margin:4px 0 22px 0;background-color:${BILA};border:1px solid ${LINKA};">
              <tr>
                <td width="6" bgcolor="${BRONZ}" style="width:6px;background-color:${BRONZ};font-size:0;line-height:0;">&#160;</td>
                <td style="padding:24px 26px;">
                  <div style="font-family:${PISMO};font-size:10px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${BRONZ};">Kdy</div>
                  <div style="margin-top:6px;font-family:${SERIF};font-size:24px;line-height:31px;font-weight:700;color:${GRAFIT};">${kus.kdy}</div>${udaje ? `
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px;border-top:1px solid ${PISEK};">
                    <tr>
${udaje}
                    </tr>
                  </table>` : ""}
                </td>
              </tr>
            </table>`;
}

function tabulkyKroky(kus) {
    const radky = kus.kroky.map(([tucne, zbytek], i) =>
`                <tr>
                  <td width="34" valign="top" style="padding:2px 0 14px 0;font-family:${SERIF};font-size:18px;font-weight:700;color:${BRONZ};">${i + 1}</td>
                  <td valign="top" style="padding:0 0 14px 0;font-family:${PISMO};font-size:15px;line-height:24px;color:${INKOUST};"><strong style="color:${GRAFIT};">${tucne}</strong> ${zbytek}</td>
                </tr>`).join("\n");
    return `            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 8px 0;">
${radky}
            </table>`;
}

function tabulkyZruseni(kus) {
    return `            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${PISEK}" style="margin:14px 0 8px 0;background-color:${PISEK};">
              <tr>
                <td align="center" style="padding:24px 26px 26px 26px;font-family:${PISMO};">
                  <p style="margin:0;font-size:15px;line-height:24px;color:${INKOUST};">${kus.text}</p>
                  <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px;">
                    <tr>
                      <td align="center" style="border:1px solid ${BRONZ};border-radius:3px;">
                        <a href="${kus.odkaz}" style="display:inline-block;padding:13px 28px;font-family:${PISMO};font-size:11.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:${BRONZ};text-decoration:none;border-radius:3px;">${kus.tlacitko}</a>
                      </td>
                    </tr>
                  </table>${kus.pod ? `
                  <div style="margin-top:10px;font-size:12px;line-height:18px;color:${SEDA};">${kus.pod}</div>` : ""}
                </td>
              </tr>
            </table>`;
}

function tabulkyTelo(telo) {
    return telo.map((kus) => {
        if (kus.typ === "p") {
            const tmave = kus.barva && kus.barva !== "#5d554b";
            return tP(kus.t, tmave ? GRAFIT : INKOUST);
        }
        if (kus.typ === "termin") return tabulkyTermin(kus);
        if (kus.typ === "kroky") return tabulkyKroky(kus);
        if (kus.typ === "zruseni") return tabulkyZruseni(kus);
        const radky = kus.odstavce || kus.radky || [kus.t];
        return `            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${BILA}" style="margin:4px 0 22px 0;background-color:${BILA};border:1px solid ${LINKA};border-left:6px solid ${BRONZ};">
              <tr><td style="padding:24px 26px 6px 26px;">
${radky.map((r) => tP(r, GRAFIT)).join("\n")}
              </td></tr>
            </table>`;
    }).join("\n");
}

function tabulky({ eyebrow, nadpis, podnadpis, telo, podpis,
                   osloveni = true }) {
    return `<!-- hh-vzhled:rezervace -->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${PISEK}" style="background-color:${PISEK};margin:0;padding:0;">
  <tr>
    <td align="center" style="padding:32px 12px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" bgcolor="${KREM}" style="width:100%;max-width:600px;background-color:${KREM};border:1px solid ${LINKA};">

        <!-- hlavicka: tmavy pas s logem -->
        <tr>
          <td bgcolor="${GRAFIT}" style="padding:24px 48px 0 48px;background-color:${GRAFIT};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td align="left" valign="middle">
                  <img src="${LOGO}" alt="Vlastní režie" width="150" height="28"
                       style="display:block;border:0;outline:none;text-decoration:none;width:150px;height:28px;"/>
                </td>
                <td align="right" valign="middle"
                    style="font-family:${PISMO};font-size:10.5px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;color:${TAUPE};">
                  Honza Hauzr
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- nadpis v tmavem pasu -->
        <tr>
          <td align="center" bgcolor="${GRAFIT}" style="padding:24px 48px 42px 48px;background-color:${GRAFIT};">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td bgcolor="${ZELENA}" style="padding:7px 14px;border-radius:999px;font-family:${PISMO};font-size:10.5px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#ffffff;">&#10003;&#160; ${eyebrow}</td>
              </tr>
            </table>
            <h1 style="margin:18px 0 0 0;font-family:${SERIF};font-size:36px;line-height:42px;font-weight:700;letter-spacing:-0.3px;color:${KREM};">${nadpis}</h1>${podnadpis ? `
            <p style="margin:12px 0 0 0;font-family:${PISMO};font-size:15px;line-height:24px;color:${KREM_TLUMENY};">${podnadpis}</p>` : ""}
          </td>
        </tr>
        <tr><td style="height:4px;background-color:${BRONZ};line-height:4px;font-size:0;">&#160;</td></tr>

        <!-- obsah -->
        <tr>
          <td style="padding:38px 48px 0 48px;">
${osloveni ? tP("{{ object.hh_osloveni }}", GRAFIT) : ""}
${tabulkyTelo(telo)}
          </td>
        </tr>

        <!-- podpis -->
        <tr>
          <td style="padding:16px 48px 40px 48px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td width="58" valign="middle">
                  <img src="${ZNAK}" alt="Honza Hauzr" width="44" height="44"
                       style="display:block;border:0;outline:none;text-decoration:none;width:44px;height:44px;"/>
                </td>
                <td valign="middle">
                  <p style="margin:0;font-family:${SERIF};font-size:19px;font-weight:700;color:${GRAFIT};">${podpis || PODPIS}</p>
                  <p style="margin:2px 0 0 0;font-family:${PISMO};font-size:12px;letter-spacing:1px;line-height:19px;text-transform:uppercase;color:${TAUPE};">${ROLE}</p>
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
    P, OTAZKA, RAMECEK, UDAJE, PANEL, TERMIN, KROKY, ZRUSENI,
    bloky, tabulky, kostra, paticka, STYLY,
    PISEK, GRAFIT,
};
