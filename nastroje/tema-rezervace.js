/* Návrh "Vlastní režie — rezervace" do galerie editoru.
 *
 * Skládá ho stavebnice nastroje/mail-bloky-rezervace.js - tatáž,
 * ze které je i potvrzení domluveného hovoru. Návrh v galerii
 * a hotová zpráva tak vypadají stejně.
 *
 * Obsah je schválně obecný: je to začátek nové zprávy, ne kopie
 * té, co už chodí.
 */

const { P, TERMIN, KROKY, ZRUSENI, bloky, paticka, PISEK } =
    require("./mail-bloky-rezervace.js");

const UKAZKA = bloky({
    eyebrow: "Potvrzeno",
    nadpis: "Nadpis zprávy",
    podnadpis: "Podnadpis pod ním",
    telo: [
        P("tenhle odstavec přepiš. Pod ním můžeš další bloky přidávat, posouvat i mazat — přetáhni si je z panelu vpravo."),
        TERMIN({
            kdy: "čtvrtek 15. 10. ve 12:00",
            udaje: [["Jak dlouho", "30 minut"], ["Forma", "Telefonát, volám já"]],
        }),
        P("Odstavec mezi kartou a kroky."),
        KROKY([
            ["Klidné místo.", "Najdi si chvíli, kdy tě nikdo neruší."],
            ["Papír po ruce.", "Hodí se, co sis zapsal během výzvy."],
            ["Telefon u sebe.", "Zavolám ti přesně v domluvený čas."],
        ]),
        ZRUSENI({
            text: "Věta, proč a kdy má člověk tlačítko použít.",
            tlacitko: "Text tlačítka",
            odkaz: "#",
            pod: "Drobná poznámka pod tlačítkem.",
        }),
    ],
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
    klic: "vr_rezervace",
    titul: "Vlastní režie — rezervace",
    nahled: "tema_rezervace",
    pozadi: PISEK,
    obsah: () => VNITREK,
};
