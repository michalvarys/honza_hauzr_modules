/* Návrh "Vlastní režie" do galerie editoru.
 *
 * Ten původní: bílá karta na krémové stránce, logo v hlavičce,
 * grafitové tlačítko. Skládá ho stavebnice nastroje/mail-bloky.js,
 * stejná, ze které jsou i zprávy v knihovně - návrh a hotové
 * zprávy tak vypadají stejně.
 *
 * Obsah je schválně obecný: je to začátek nové zprávy, ne kopie
 * některé z těch, co už chodí.
 */

const { P, bloky, paticka, KREM } = require("./mail-bloky.js");

const UKAZKA = bloky({
    eyebrow: "Vlastní režie",
    nadpis: "Nadpis zprávy",
    telo: [
        P("tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo."),
        P("Tlačítko níž má zatím prázdný odkaz. Klikni na něj a v liště nahoře mu adresu doplň."),
    ],
    tlacitko: "Text tlačítka",
    odkaz: "#",
});

/* Patička s odhlášením úplně na konec obsahu, pod podpis - tam,
   kam ji dává i modul (KONEC_OBSAHU v hh_mail_sablona.py). Nová
   zpráva ji musí mít hned: jinak by si Honza napsal text, odeslal
   a odhlášení by v něm chybělo. */
const KONEC_OBSAHU = "      </div>\n    </div>\n  </div>\n</div>";
const S_PATICKOU = UKAZKA.replace(
    KONEC_OBSAHU, paticka() + "\n" + KONEC_OBSAHU);

/* Z galerie se bere jen vnitřek: obal (o_layout, container,
   .oe_structure) staví editor sám a dvakrát ho tam nechceme. */
const ZACATEK = S_PATICKOU.indexOf("<style");
const KONEC = S_PATICKOU.lastIndexOf("      </div>");
const VNITREK = S_PATICKOU.slice(ZACATEK, KONEC)
    .replace(/\n      <div class="col o_mail_no_options[^\n]*\n/, "\n")
    .replace(/\n  <div class="container o_mail_wrapper[^\n]*\n/, "\n")
    .replace(/\n    <div class="row">\n/, "\n")
    .trimEnd();

module.exports = {
    klic: "vr_vyzva",
    titul: "Vlastní režie",
    nahled: "tema_vr",
    pozadi: KREM,
    obsah: () => VNITREK,
};
