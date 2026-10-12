/* Návrh "Krémový editorial" do galerie editoru.
 *
 * Podklad je od Honzy (varianta A). Tenhle soubor z něj dělá
 * předlohu, se kterou jde v editoru pracovat: každá část je blok
 * Odoo (o_mail_snippet_general), takže se dá vybrat, posunout,
 * smazat a prokládat jinými bloky. Tlačítko je <a class="btn">,
 * takže mu jde přepsat odkaz přes řetízek v liště.
 *
 * Proti podkladu se mění jen obal, ne vzhled:
 *
 *   - hodnoty, které byly v podkladu u každé značky zvlášť, sedí
 *     v <style id="design-element">. Editor je tak umí přepisovat
 *     a při odeslání si je Odoo rozepíše ke značkám samo.
 *   - třídy mají předponu hhe- (editorial), aby se nepraly
 *     s prvním návrhem, který má hh-.
 *
 * Písma: v podkladu jsou Playfair Display a Inter z Google Fonts.
 * V e-mailu se stejně nenačtou - schránky webová písma ignorují
 * a Gmail je zahazuje úplně - takže doopravdy se čte Georgia
 * a Arial. Serifový nadpis zůstane serifový, o to tu jde.
 *
 * Načíst je přes @import nejde: editor si styly rozebírá po
 * selektorech (splitCss v mass_mailing) a na pravidle @import,
 * které žádný selektor nemá, spadne celá záložka Návrh.
 */

const KREM_STRANKA = "#efe7d8";
const KREM_KARTA = "#f4efe6";
const LINKA = "#e3d9c8";
const GRAFIT = "#23211d";
const INKOUST = "#5d554b";
const BRONZ = "#a06a37";
const BRONZ_SVETLY = "#c08a52";
const TAUPE = "#a89681";
const SEDA = "#857b6e";

const STYLY = `<style id="design-element">
.o_mail_wrapper_td { background-color: ${KREM_KARTA} !important; border: 1px solid ${LINKA}; }
.o_mail_wrapper { font-family: Inter, Arial, sans-serif; color: ${INKOUST}; }
.o_mail_wrapper p { font-size: 16px; line-height: 27px; margin: 0 0 18px 0; }
.o_mail_wrapper h1.hhe-nadpis { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 34px; line-height: 40px; font-weight: 700; letter-spacing: -0.3px; color: ${GRAFIT}; margin: 14px 0 0 0; }
.o_mail_wrapper .hhe-znacka { font-size: 12px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: ${GRAFIT}; margin: 0; }
.o_mail_wrapper .hhe-znacka span { color: ${BRONZ}; }
.o_mail_wrapper .hhe-jmeno { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${TAUPE}; margin: 0; }
.o_mail_wrapper .hhe-eyebrow { font-size: 10.5px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: ${BRONZ}; margin: 0; }
.o_mail_wrapper .hhe-prah { width: 48px; height: 2px; background-color: ${BRONZ}; margin-top: 22px; font-size: 0; line-height: 2px; }
.o_mail_wrapper .hhe-oslo { color: ${GRAFIT}; font-weight: 600; }
.o_mail_wrapper .hhe-tmave { color: ${GRAFIT}; }
.o_mail_wrapper .hhe-otazka { background-color: ${GRAFIT}; border-left: 3px solid ${BRONZ_SVETLY}; padding: 28px 30px; }
.o_mail_wrapper .hhe-otazka .hhe-eyebrow { color: ${BRONZ_SVETLY}; font-size: 10px; }
.o_mail_wrapper .hhe-otazka p { font-family: 'Playfair Display', Georgia, 'Times New Roman', serif; font-size: 22px; line-height: 30px; font-weight: 700; color: ${KREM_KARTA}; margin: 10px 0 0 0; }
.o_mail_wrapper .hhe-pod { font-size: 12.5px; line-height: 19px; color: ${SEDA}; margin: 14px 0 0 0; }
.o_mail_wrapper .hhe-linka-nad { border-top: 1px solid ${LINKA}; }
.o_mail_wrapper .hhe-znak { width: 44px; height: 44px; background-color: ${GRAFIT}; border-radius: 22px; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: ${BRONZ_SVETLY}; text-align: center; line-height: 44px; }
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

const HLAVICKA = `        <div class="s_header_logo o_mail_block_header_logo o_mail_snippet_general pt24 pb24" style="border-bottom:1px solid ${LINKA};">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-7">
                <p class="hhe-znacka">Vlastní <span>režie</span></p>
              </div>
              <div class="col-5" style="text-align:right;">
                <p class="hhe-jmeno">Honza Hauzr</p>
              </div>
            </div>
          </div>
        </div>`;

const NADPIS = blok("s_title pt40 pb0",
`            <p class="hhe-eyebrow">Tvůj tah &#183; po výzvě</p>
            <h1 class="hhe-nadpis">Nadpis zprávy</h1>
            <div class="hhe-prah">&#160;</div>`);

const TEXT_PRVNI = blok("s_text_block pt24 pb0",
`            <p class="hhe-oslo">{{ object.hh_osloveni }}</p>
            <p>tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo.</p>
            <p>Otázku pod tímhle textem můžeš smazat jako kterýkoliv jiný blok, nebo si ji přetáhnout jinam.</p>`);

const OTAZKA = blok("s_mail_blockquote pt24 pb24",
`            <div class="hhe-otazka">
              <p class="hhe-eyebrow">Otázka na dnešek</p>
              <p>Sem patří jedna věta, se kterou má člověk odejít.</p>
            </div>`);

const TEXT_DRUHY = blok("s_text_block pt0 pb0",
`            <p>Další odstavec. Tlačítko níž má zatím prázdný odkaz — klikni na něj a v liště nahoře mu adresu doplň.</p>`);

const TLACITKO = `        <div class="s_call_to_action o_mail_snippet_general pt32 pb8">
          <div class="container" style="${BOKY}text-align:center;">
            <a href="#" role="button" class="btn btn-primary">Text tlačítka</a>
            <p class="hhe-pod">Nezávazně. Zhruba 30 minut.</p>
          </div>
        </div>`;

const PODPIS = `        <div class="s_text_block o_mail_snippet_general hhe-linka-nad pt32 pb32">
          <div class="container" style="${BOKY}">
            <div class="row">
              <div class="col-2">
                <p class="hhe-znak">H</p>
              </div>
              <div class="col-10">
                <p class="hhe-podpis">Honza</p>
                <p class="hhe-role">Mentor pro muže &#183; Vlastní režie</p>
              </div>
            </div>
          </div>
        </div>`;

/* Patička s odhlášením. Do hotových zpráv ji doplňuje modul, ale
   nová zpráva z galerie ji musí mít hned - jinak by si Honza
   napsal text, odeslal a odhlášení by v něm chybělo. Zástupné
   texty jsou stejné jako v PATICKA_BLOK (crm_lead_maily.py),
   podle nich se pozná, že zpráva odhlášení už má. */
const PATICKA = `        <div class="s_text_block o_mail_snippet_general hhe-paticka pt24 pb24">
          <div class="container" style="${BOKY}text-align:center;">
            <p class="hhe-odesilatel">{{ object.hh_paticka_odesilatel }}</p>
            <p style="margin-top:8px;">Tenhle e-mail ti přišel, protože ses přihlásil do bezplatné výzvy Z autopilota zpět do života.</p>
            <p style="margin-top:10px;"><a href="{{ object.hh_odkaz_odhlaseni }}">Nechceš ode mě další e-maily? Odhlas se.</a></p>
          </div>
        </div>`;

module.exports = {
    klic: "vr_editorial",
    titul: "Vlastní režie — editorial",
    nahled: "tema_editorial",
    pozadi: KREM_STRANKA,
    barvy: {
        stranka: KREM_STRANKA, karta: KREM_KARTA, linka: LINKA,
        grafit: GRAFIT, bronz: BRONZ, taupe: TAUPE, serif: true,
    },
    obsah: () => [STYLY, HLAVICKA, NADPIS, TEXT_PRVNI, OTAZKA,
                  TEXT_DRUHY, TLACITKO, PODPIS, PATICKA].join("\n"),
};
