/** @odoo-module **/

/**
 * Kalendar terminu na uvodni hovor - jedine misto, kde se terminy
 * spravuji.
 *
 * Proc vlastni pohled a ne kalendar od Odoo: pri trinacti terminech
 * denne ukazuje mesicni kalendar Odoo jen "+dalsi: 9" a kliknuti na
 * cislo dne nikam nevede - navigacni odkazy ma vypnute. Prave tohle
 * ale Honza potrebuje delat kazdy tyden: otevrit den a odskrtat
 * hodiny, ktere se mu nehodi.
 *
 * Obrazovka ma tri casti:
 *   mesic  - prehled dnu, kliknuti na den prepne na hodiny,
 *   den    - mrizka hodin, krizky se davaji kliknutim nebo tazenim,
 *   rozvrh - nastaveni pod kalendarem (dny v tydnu, od-do, delka).
 *
 * Vzhled je zamerne stejny jako rezervacni stranka na webu - stejna
 * paleta i patkova cisla dnu - aby Honza videl v adminu to same,
 * co uvidi zakaznik.
 */

import { Component, onWillStart, useExternalListener, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

const { DateTime } = luxon;

const DNY_ZKRATKA = ["po", "út", "st", "čt", "pá", "so", "ne"];
const DNY_PLNE = ["pondělí", "úterý", "středa", "čtvrtek", "pátek", "sobota", "neděle"];
const MESICE = [
    "leden", "únor", "březen", "duben", "květen", "červen",
    "červenec", "srpen", "září", "říjen", "listopad", "prosinec",
];

/**
 * Okno pro rucni zapis, ze si termin nekdo domluvil.
 *
 * Nepouziva formular z Odoo zamerne: potrebuji jen ctyri policka
 * a chci zustat v kalendari, ne odskakovat na jinou obrazovku.
 */
export class RezervaceDialog extends Component {
    static template = "honzahauzr_crm.RezervaceDialog";
    static components = { Dialog };
    static props = {
        termin: Object,
        close: Function,
        potvrdit: Function,
        zrusit: Function,
    };

    setup() {
        const t = this.props.termin;
        this.udaje = useState({
            jmeno: t.jmeno || "",
            email: t.email || "",
            telefon: t.telefon || "",
            poznamka: t.poznamka || "",
            chyba: "",
            uklada: false,
        });
    }

    get jeUprava() {
        return this.props.termin.stav === "rezervovany";
    }

    get nadpis() {
        return this.jeUprava
            ? _t("Domluvený hovor %s", this.props.termin.cas)
            : _t("Zapsat rezervaci na %s", this.props.termin.cas);
    }

    async uloz() {
        if (!this.udaje.jmeno.trim()) {
            this.udaje.chyba = _t("Bez jména nevím, s kým ten hovor je.");
            return;
        }
        this.udaje.chyba = "";
        this.udaje.uklada = true;
        try {
            await this.props.potvrdit({
                jmeno: this.udaje.jmeno.trim(),
                email: this.udaje.email.trim(),
                telefon: this.udaje.telefon.trim(),
                poznamka: this.udaje.poznamka.trim(),
            });
            this.props.close();
        } catch (chyba) {
            this.udaje.uklada = false;
            throw chyba;
        }
    }

    async zrus() {
        this.udaje.uklada = true;
        try {
            await this.props.zrusit();
            this.props.close();
        } catch (chyba) {
            this.udaje.uklada = false;
            throw chyba;
        }
    }
}

export class TerminyKalendar extends Component {
    static template = "honzahauzr_crm.TerminyKalendar";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.stav = useState({
            rezim: "mesic",
            mesic: DateTime.local().startOf("month"),
            terminy: {},      // 'yyyy-MM-dd' -> pole terminu
            vybranyDen: null,
            nacita: true,
            rozvrhOtevren: false,
            uklada: false,
        });

        // Rozvrh je zvlast, at ho jde menit bez prekreslovani kalendare.
        this.rozvrh = useState({
            od: 8,
            do: 21,
            delka: 45,
            dopredu: 30,
            dny: [true, true, true, true, true, false, false],
        });

        // Pasmo, ve kterem se kresli. Prepise ho server pri nacteni
        // rozvrhu. Nesmi se spolehnout na pasmo prohlizece ani na
        // pasmo prihlaseneho uzivatele: terminy se vyrabeji podle
        // pasma firmy, takze jen v nem odpovidaji hodiny v mrizce
        // tomu, co je nastavene v rozvrhu.
        this.pasmo = "Europe/Prague";

        // Tazeni pres vic hodin. Zamerne mimo useState - behem tahu se
        // prekresluji jen stavy jednotlivych terminu, ne tahle pomucka.
        this.maluje = null;

        // Pusteni tlacitka muze prijit i mimo mrizku (treba az nad
        // listou), proto se posloucha na celem okne.
        useExternalListener(window, "pointerup", () => this.dokonciTah());

        onWillStart(async () => {
            // Rozvrh prvni - nese pasmo, ve kterem se terminy prevadeji.
            // Az podle nej se urci, ktery mesic je ten dnesni: kolem
            // pulnoci a na prelomu mesice muze byt v pasme firmy jiny
            // nez v pasme prohlizece.
            await this.nactiRozvrh();
            this.stav.mesic = this.dnesek.startOf("month");
            await this.nacti();
        });
    }

    // ------------------------------------------------------------------
    // data
    // ------------------------------------------------------------------

    async nacti() {
        this.stav.nacita = true;
        try {
            // Okraje mesice se berou s tydenni rezervou na obe strany,
            // protoze v mrizce jsou videt i dny ze sousednich mesicu.
            const od = this.stav.mesic.startOf("month").minus({ days: 7 });
            const doKdy = this.stav.mesic.endOf("month").plus({ days: 7 });

            const zaznamy = await this.orm.searchRead(
                "hh.termin",
                [
                    ["zacatek", ">=", od.toUTC().toFormat("yyyy-MM-dd HH:mm:ss")],
                    ["zacatek", "<=", doKdy.toUTC().toFormat("yyyy-MM-dd HH:mm:ss")],
                    ["stav", "!=", "zruseny"],
                ],
                ["zacatek", "delka", "stav", "jmeno", "email", "telefon", "poznamka"],
                { order: "zacatek asc" }
            );

            const podleDnu = {};
            for (const z of zaznamy) {
                // Do pasma, ve kterem se terminy vyrabeji - viz this.pasmo.
                const kdy = deserializeDateTime(z.zacatek).setZone(this.pasmo);
                const klic = kdy.toFormat("yyyy-MM-dd");
                if (!podleDnu[klic]) {
                    podleDnu[klic] = [];
                }
                podleDnu[klic].push({
                    id: z.id,
                    cas: kdy.toFormat("HH:mm"),
                    stav: z.stav,
                    jmeno: z.jmeno || "",
                    email: z.email || "",
                    telefon: z.telefon || "",
                    poznamka: z.poznamka || "",
                });
            }
            this.stav.terminy = podleDnu;
        } finally {
            this.stav.nacita = false;
        }
    }

    async nactiRozvrh() {
        const r = await this.orm.call("hh.termin", "hh_nacist_rozvrh", []);
        if (r.pasmo) {
            this.pasmo = r.pasmo;
            delete r.pasmo;
        }
        Object.assign(this.rozvrh, r);
    }

    /** Dnesek v pasmu, ve kterem se terminy vyrabeji. */
    get dnesek() {
        return DateTime.now().setZone(this.pasmo);
    }

    // ------------------------------------------------------------------
    // mesic
    // ------------------------------------------------------------------

    get nazevMesice() {
        return `${MESICE[this.stav.mesic.month - 1]} ${this.stav.mesic.year}`;
    }

    get zahlaviDnu() {
        return DNY_ZKRATKA;
    }

    get tydny() {
        // Mrizka zacina pondelim tydne, ve kterem je prvni den mesice,
        // a konci nedeli tydne, ve kterem je posledni.
        const zacatek = this.stav.mesic.startOf("month").startOf("week");
        const konec = this.stav.mesic.endOf("month").endOf("week");
        const dnes = this.dnesek.toFormat("yyyy-MM-dd");

        const tydny = [];
        let den = zacatek;
        while (den <= konec) {
            const radek = [];
            for (let i = 0; i < 7; i++) {
                const klic = den.toFormat("yyyy-MM-dd");
                const terminy = this.stav.terminy[klic] || [];
                radek.push({
                    klic,
                    cislo: den.day,
                    cizi: den.month !== this.stav.mesic.month,
                    dnes: klic === dnes,
                    // Den, ktery uz probehl. Terminy se do minulosti
                    // nevyrabeji, takze takovy den je prazdny vzdycky -
                    // bez odliseni to ale vypada stejne, jako by se
                    // rozvrh nepropsal.
                    minulost: klic < dnes,
                    // Den, ktery rozvrh nema zapnuty - ukazuje se jinak,
                    // at je na prvni pohled videt, proc je prazdny.
                    vypnuty: !this.rozvrh.dny[den.weekday - 1],
                    volnych: terminy.filter((t) => t.stav === "volny").length,
                    obsazenych: terminy.filter((t) => t.stav === "rezervovany").length,
                    preskrtnutych: terminy.filter((t) => t.stav === "zablokovany").length,
                    celkem: terminy.length,
                });
                den = den.plus({ days: 1 });
            }
            tydny.push(radek);
        }
        return tydny;
    }

    async posunMesic(o) {
        this.stav.mesic = this.stav.mesic.plus({ months: o });
        await this.nacti();
    }

    async dnes() {
        this.stav.mesic = this.dnesek.startOf("month");
        this.stav.rezim = "mesic";
        await this.nacti();
    }

    // ------------------------------------------------------------------
    // prepinani mesic <-> den
    // ------------------------------------------------------------------

    otevriDen(den) {
        // Prazdny den se neotevira - nebylo by v nem co delat.
        if (!den.celkem) {
            return;
        }
        this.stav.vybranyDen = den.klic;
        this.stav.rezim = "den";
    }

    zpetNaMesic() {
        this.stav.rezim = "mesic";
    }

    async posunDen(o) {
        const novy = DateTime.fromFormat(this.stav.vybranyDen, "yyyy-MM-dd")
            .plus({ days: o });
        this.stav.vybranyDen = novy.toFormat("yyyy-MM-dd");

        // Prechod pres hranici mesice si vyzada dotazeni dat.
        if (novy.month !== this.stav.mesic.month || novy.year !== this.stav.mesic.year) {
            this.stav.mesic = novy.startOf("month");
            await this.nacti();
        }
    }

    get denniTerminy() {
        if (!this.stav.vybranyDen) {
            return [];
        }
        return this.stav.terminy[this.stav.vybranyDen] || [];
    }

    get popisVybranehoDne() {
        if (!this.stav.vybranyDen) {
            return "";
        }
        const d = DateTime.fromFormat(this.stav.vybranyDen, "yyyy-MM-dd");
        return `${DNY_PLNE[d.weekday - 1]} ${d.day}. ${MESICE[d.month - 1]} ${d.year}`;
    }

    get souhrnDne() {
        const t = this.denniTerminy;
        return {
            volnych: t.filter((x) => x.stav === "volny").length,
            preskrtnutych: t.filter((x) => x.stav === "zablokovany").length,
            rezervovanych: t.filter((x) => x.stav === "rezervovany").length,
        };
    }

    // ------------------------------------------------------------------
    // krizkovani - kliknutim i tazenim
    // ------------------------------------------------------------------

    zacniTah(termin) {
        // Domluveny hovor se preskrtnout neda - otevre se misto toho
        // okno s udaji, at je videt, s kym je.
        if (termin.stav === "rezervovany") {
            this.otevriRezervaci(termin);
            return;
        }

        // Smer tahu urcuje prvni hodina: kdyz byla volna, tah krizkuje,
        // kdyz byla preskrtnuta, tah maze. Diky tomu jde jednim tahem
        // odskrtat cele odpoledne i ho zase vratit.
        this.maluje = {
            cil: termin.stav === "volny" ? "zablokovany" : "volny",
            ids: new Set(),
        };
        this.natri(termin);
    }

    pokracujTah(termin) {
        if (!this.maluje || termin.stav === "rezervovany") {
            return;
        }
        this.natri(termin);
    }

    natri(termin) {
        if (termin.stav === this.maluje.cil) {
            return;
        }
        // Prekresli se hned, at tah nedrhne. Kdyby zapis selhal,
        // vrati se puvodni stav v dokonciTah.
        termin.stav = this.maluje.cil;
        this.maluje.ids.add(termin.id);
    }

    async dokonciTah() {
        const tah = this.maluje;
        this.maluje = null;
        if (!tah || !tah.ids.size) {
            return;
        }

        const ids = [...tah.ids];
        const nabizet = tah.cil === "volny";
        try {
            // Jeden zapis za cely tah, ne jeden na kazdou hodinu.
            await this.orm.write("hh.termin", ids, { hh_nabizet: nabizet });
        } catch (chyba) {
            // Zpatky do puvodniho stavu, at obrazovka neukazuje neco,
            // co v databazi neni.
            const puvodni = nabizet ? "zablokovany" : "volny";
            for (const den of Object.values(this.stav.terminy)) {
                for (const t of den) {
                    if (tah.ids.has(t.id)) {
                        t.stav = puvodni;
                    }
                }
            }
            this.notification.add(_t("Změnu se nepodařilo uložit."), {
                type: "danger",
            });
            throw chyba;
        }
    }

    // ------------------------------------------------------------------
    // rucni rezervace
    // ------------------------------------------------------------------

    otevriRezervaci(termin) {
        this.dialog.add(RezervaceDialog, {
            termin,
            potvrdit: async (udaje) => {
                await this.orm.call("hh.termin", "hh_rezervovat_rucne",
                    [termin.id, udaje]);
                Object.assign(termin, udaje, { stav: "rezervovany" });
                this.notification.add(_t("Rezervace uložena."), { type: "success" });
            },
            zrusit: async () => {
                await this.orm.call("hh.termin", "hh_zrusit_rucne", [termin.id]);
                Object.assign(termin, {
                    stav: "volny", jmeno: "", email: "", telefon: "", poznamka: "",
                });
                this.notification.add(_t("Termín je zase volný."), { type: "success" });
            },
        });
    }

    // ------------------------------------------------------------------
    // hromadne akce na cely den
    // ------------------------------------------------------------------

    async preskrtnoutVse() {
        await this._hromadne("volny", "zablokovany", false);
    }

    async vratitVse() {
        await this._hromadne("zablokovany", "volny", true);
    }

    async _hromadne(zdroj, cil, nabizet) {
        const vybrane = this.denniTerminy.filter((t) => t.stav === zdroj);
        if (!vybrane.length) {
            return;
        }
        const ids = vybrane.map((t) => t.id);
        vybrane.forEach((t) => (t.stav = cil));
        try {
            await this.orm.write("hh.termin", ids, { hh_nabizet: nabizet });
        } catch (chyba) {
            vybrane.forEach((t) => (t.stav = zdroj));
            this.notification.add(_t("Změnu se nepodařilo uložit."), {
                type: "danger",
            });
            throw chyba;
        }
    }

    // ------------------------------------------------------------------
    // rozvrh pod kalendarem
    // ------------------------------------------------------------------

    prepniRozvrh() {
        this.stav.rozvrhOtevren = !this.stav.rozvrhOtevren;
    }

    prepniDen(index) {
        this.rozvrh.dny[index] = !this.rozvrh.dny[index];
    }

    get dnyNaVyber() {
        return DNY_PLNE.map((nazev, i) => ({
            index: i,
            nazev,
            zkratka: DNY_ZKRATKA[i],
            zapnuty: this.rozvrh.dny[i],
        }));
    }

    _cas(h) {
        const cele = Math.floor(h);
        const min = Math.round((h - cele) * 60);
        return `${String(cele).padStart(2, "0")}:${String(min).padStart(2, "0")}`;
    }

    get rozsahPopis() {
        const dny = DNY_ZKRATKA.filter((_, i) => this.rozvrh.dny[i]).join(", ");
        return `${dny || "žádný den"} · ${this._cas(this.rozvrh.od)}–${this._cas(this.rozvrh.do)} · po ${this.rozvrh.delka} min`;
    }

    async ulozRozvrh() {
        this.stav.uklada = true;
        try {
            const vysledek = await this.orm.call("hh.termin", "hh_ulozit_rozvrh", [{
                od: this.rozvrh.od,
                do: this.rozvrh.do,
                delka: this.rozvrh.delka,
                dopredu: this.rozvrh.dopredu,
                dny: [...this.rozvrh.dny],
            }]);

            await this.nacti();

            // Domluveny hovor, ktery vypadl z rozvrhu, se nesmaze -
            // ale Honza se o nem musi dozvedet, jinak by mu tise
            // zustal v kalendari mimo pracovni dobu.
            const mimo = vysledek.rezervovane_mimo || [];
            if (mimo.length) {
                this.notification.add(
                    _t("Mimo nový rozvrh zůstávají domluvené hovory: %s. Nechal jsem je být.",
                        mimo.map((m) => `${m.kdy}${m.jmeno ? ` (${m.jmeno})` : ""}`).join(", ")),
                    { type: "warning", sticky: true }
                );
            }
            this.notification.add(
                _t("Rozvrh uložen, doplněno %s termínů.", vysledek.vyrobeno),
                { type: "success" }
            );
        } finally {
            this.stav.uklada = false;
        }
    }
}

registry.category("actions").add("hh_terminy_kalendar", TerminyKalendar);
