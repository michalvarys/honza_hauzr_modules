/* Návrh "Krémový editorial" do galerie editoru.
 *
 * Skládá ho stavebnice nastroje/mail-bloky-editorial.js - tatáž,
 * ze které jsou i zprávy třídenní výzvy a řady Tvůj tah. Návrh
 * v galerii a hotové zprávy tak vypadají stejně.
 *
 * Obsah je schválně obecný: je to začátek nové zprávy, ne kopie
 * některé z těch, co už chodí.
 */

const { P, OTAZKA, bloky, paticka, KREM_STRANKA } =
    require("./mail-bloky-editorial.js");

const UKAZKA = bloky({
    eyebrow: "Tvůj tah &#183; po výzvě",
    nadpis: "Nadpis zprávy",
    telo: [
        P("tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo."),
        P("Otázku pod tímhle textem můžeš smazat jako kterýkoliv jiný blok, nebo si ji přetáhnout jinam."),
        OTAZKA("Sem patří jedna věta, se kterou má člověk odejít."),
        P("Další odstavec. Tlačítko níž má zatím prázdný odkaz — klikni na něj a v liště nahoře mu adresu doplň."),
    ],
    tlacitko: "Text tlačítka",
    odkaz: "#",
    pod: "Nezávazně. Zhruba 30 minut.",
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
    klic: "vr_editorial",
    titul: "Vlastní režie — editorial",
    nahled: "tema_editorial",
    pozadi: KREM_STRANKA,
    obsah: () => VNITREK,
};
