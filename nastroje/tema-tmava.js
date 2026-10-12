/* Návrh "Honza Hauzr — tmavá" do galerie editoru.
 *
 * Skládá ho stavebnice nastroje/mail-bloky-tmava.js - tatáž, ze
 * které je i uvítací zpráva řady Chci odebírat. Návrh v galerii
 * a hotová zpráva tak vypadají stejně.
 *
 * Obsah je schválně obecný: je to začátek nové zprávy, ne kopie
 * té, co už chodí.
 */

const { P, PANEL, bloky, paticka, CERNA } =
    require("./mail-bloky-tmava.js");

const UKAZKA = bloky({
    eyebrow: "Vítej ve Vlastní režii",
    nadpis: "Nadpis zprávy",
    telo: [
        P("tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo."),
        PANEL({
            eyebrow: "Zvýrazněný panel",
            nadpis: "Sem patří nabídka",
            cisla: [["3", "dny"], ["3", "krátká videa"], ["20", "minut denně"]],
            text: "Věta pod čísly. Celý panel jde smazat jako kterýkoliv jiný blok.",
        }),
        P("Tlačítko níž má zatím prázdný odkaz — klikni na něj a v liště nahoře mu adresu doplň."),
    ],
    tlacitko: "Text tlačítka",
    odkaz: "#",
    pod: "Drobná poznámka pod tlačítkem.",
});

/* Patička s odhlášením úplně na konec obsahu, pod podpis - tam,
   kam ji dává i modul (KONEC_OBSAHU v hh_mail_sablona.py). */
const KONEC_OBSAHU = "      </div>\n    </div>\n  </div>\n</div>";
const S_PATICKOU = UKAZKA.replace(
    KONEC_OBSAHU, paticka() + "\n" + KONEC_OBSAHU);

/* Z galerie se bere jen vnitřek: obal staví editor sám. */
const ZACATEK = S_PATICKOU.indexOf("<style");
const KONEC = S_PATICKOU.lastIndexOf("      </div>");
const VNITREK = S_PATICKOU.slice(ZACATEK, KONEC)
    .replace(/\n      <div class="col o_mail_no_options[^\n]*\n/, "\n")
    .replace(/\n  <div class="container o_mail_wrapper[^\n]*\n/, "\n")
    .replace(/\n    <div class="row">\n/, "\n")
    .trimEnd();

module.exports = {
    klic: "hh_tmava",
    titul: "Honza Hauzr — tmavá",
    nahled: "tema_tmava",
    pozadi: CERNA,
    obsah: () => VNITREK,
};
