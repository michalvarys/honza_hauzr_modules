# -*- coding: utf-8 -*-
"""Presun prehravaci hlavicky mp4 na zacatek souboru.

Soubor mp4 je slozeny z bloku. Dva jsou podstatne: "mdat" nese
samotny obraz a zvuk, "moov" je rejstrik - kde ktery snimek lezi,
jak je video dlouhe, jake ma rozmery. Bez nej prehravac nevi, co
s daty, takze cekat musi prave na nej.

Vetsina strihovych programu zapisuje moov az na konec, protoze
dopredu nevi, jak bude vysledek velky. Na disku to nevadi, na webu
ano: prohlizec musi stahnout cely soubor, nez vubec zacne hrat.
U videa na 292 MB to znamena, ze se netocilo nic a jen beželo
kolecko.

Tenhle modul presune moov dopredu, hned za hlavicku souboru. Je to
tataz operace, kterou dela "ffmpeg -movflags +faststart", jen bez
ffmpegu - ten na serveru neni a kvuli jedne veci ho tam
neinstalujeme.

Pozor na jednu vec: moov obsahuje tabulky s pozicemi snimku
(stco, u delsich videi co64) pocitane od zacatku souboru. Kdyz se
moov presune dopredu, vsechno za nim se posune o jeho velikost -
a kazda pozice v tech tabulkach se o tutez hodnotu musi zvysit,
jinak by prehravac hledal snimky na spatnych mistech.
"""
import logging
import struct

_logger = logging.getLogger(__name__)

# Bloky, ktere smeji stat pred mdat, aniz by se neco presouvalo.
PRED_DATY = (b'ftyp', b'free', b'skip', b'wide', b'pnot')


def _cti_hlavicku(soubor, pozice):
    """Precte hlavicku bloku na dane pozici.

    Vraci (typ, velikost celeho bloku, delka hlavicky), nebo None
    na konci souboru.
    """
    soubor.seek(pozice)
    hlavicka = soubor.read(8)
    if len(hlavicka) < 8:
        return None

    velikost, typ = struct.unpack('>I4s', hlavicka)
    delka_hlavicky = 8

    if velikost == 1:
        # Rozsirena velikost - skutecne cislo je v dalsich osmi bajtech.
        rozsireni = soubor.read(8)
        if len(rozsireni) < 8:
            return None
        velikost = struct.unpack('>Q', rozsireni)[0]
        delka_hlavicky = 16
    elif velikost == 0:
        # Blok sahá do konce souboru.
        soubor.seek(0, 2)
        velikost = soubor.tell() - pozice

    if velikost < delka_hlavicky:
        return None
    return typ, velikost, delka_hlavicky


def _projdi_bloky(soubor):
    """Vrati seznam (typ, zacatek, velikost) vsech bloku nejvyssi urovne."""
    soubor.seek(0, 2)
    konec = soubor.tell()

    bloky = []
    pozice = 0
    while pozice < konec:
        hlava = _cti_hlavicku(soubor, pozice)
        if not hlava:
            break
        typ, velikost, _ = hlava
        bloky.append((typ, pozice, velikost))
        pozice += velikost
    return bloky


def _posun_tabulky(moov, posun):
    """Zvysi vsechny pozice v tabulkach stco a co64 o dany posun.

    Prochazi se cely moov po bajtech a hleda se znacka tabulky.
    Je to hrube, ale spolehlive: tabulky mohou byt zanorene ruzne
    hluboko podle toho, kolik ma video stop.

    @param moov: bytearray s celym blokem moov
    @param posun: o kolik bajtu se vsechno za moov posune
    """
    upraveno = 0
    i = 0
    delka = len(moov)

    while i < delka - 8:
        znacka = bytes(moov[i:i + 4])

        if znacka in (b'stco', b'co64'):
            # Pred znackou stoji ctyri bajty s velikosti bloku,
            # za ni verze s priznaky (4 bajty) a pocet zaznamu (4).
            zacatek_dat = i + 8
            if zacatek_dat + 4 > delka:
                break
            pocet = struct.unpack('>I', bytes(moov[zacatek_dat:zacatek_dat + 4]))[0]
            sirka = 4 if znacka == b'stco' else 8
            tabulka = zacatek_dat + 4

            if tabulka + pocet * sirka > delka:
                # Neco nesedi - radeji nesahat a nechat soubor byt.
                _logger.warning('mp4: tabulka %s presahuje moov, preskakuji',
                                znacka.decode())
                i += 4
                continue

            for n in range(pocet):
                p = tabulka + n * sirka
                if sirka == 4:
                    hodnota = struct.unpack('>I', bytes(moov[p:p + 4]))[0] + posun
                    # Kdyz by se 32bitova tabulka pretekla, soubor by se
                    # rozbil. Takove video nechame, jak je.
                    if hodnota > 0xFFFFFFFF:
                        raise ValueError('posun by pretekl 32bitovou tabulku')
                    moov[p:p + 4] = struct.pack('>I', hodnota)
                else:
                    hodnota = struct.unpack('>Q', bytes(moov[p:p + 8]))[0] + posun
                    moov[p:p + 8] = struct.pack('>Q', hodnota)

            upraveno += 1
            i = tabulka + pocet * sirka
            continue

        i += 1

    return upraveno


def prekopiruj_s_hlavickou_vepredu(zdroj, cil, blok=4 * 1024 * 1024):
    """Prepise mp4 tak, aby moov stal pred mdat.

    @param zdroj: cesta ke vstupnimu souboru
    @param cil: cesta, kam se zapise vysledek
    @return: True kdyz se neco zmenilo, False kdyz uz bylo v poradku
             nebo kdyz soubor nelze bezpecne upravit
    """
    with open(zdroj, 'rb') as vstup:
        bloky = _projdi_bloky(vstup)
        if not bloky:
            return False

        poradi = [typ for typ, _, _ in bloky]
        if b'moov' not in poradi or b'mdat' not in poradi:
            return False
        if poradi.index(b'moov') < poradi.index(b'mdat'):
            # Uz je to tak, jak ma byt.
            return False

        # Nic jineho nez znamé bloky pred mdat byt nesmi - jinak
        # bychom mohli rozbit neco, co neznáme.
        for typ in poradi[:poradi.index(b'mdat')]:
            if typ not in PRED_DATY:
                _logger.info('mp4: pred daty je neznamy blok %r, nechavam byt',
                             typ)
                return False

        _, zacatek_moov, velikost_moov = next(
            b for b in bloky if b[0] == b'moov')

        vstup.seek(zacatek_moov)
        moov = bytearray(vstup.read(velikost_moov))
        if len(moov) != velikost_moov:
            return False

        try:
            upraveno = _posun_tabulky(moov, velikost_moov)
        except ValueError as potiz:
            _logger.info('mp4: %s, nechavam soubor byt', potiz)
            return False

        if not upraveno:
            _logger.info('mp4: v moov nejsou tabulky pozic, nechavam byt')
            return False

        # Porovnava se poradi v souboru, ne typ - stejny typ se muze
        # v souboru opakovat a hledani podle nej by naslo vzdy ten
        # prvni.
        kde_mdat = poradi.index(b'mdat')

        def prepis(zacatek, velikost, vystup):
            vstup.seek(zacatek)
            zbyva = velikost
            while zbyva:
                kus = vstup.read(min(blok, zbyva))
                if not kus:
                    break
                vystup.write(kus)
                zbyva -= len(kus)

        with open(cil, 'wb') as vystup:
            # 1. bloky, ktere stoji pred daty (ftyp a spol.)
            for poradove, (typ, zacatek, velikost) in enumerate(bloky):
                if poradove >= kde_mdat or typ == b'moov':
                    continue
                prepis(zacatek, velikost, vystup)

            # 2. prehravaci hlavicka s opravenymi pozicemi
            vystup.write(moov)

            # 3. zbytek souboru od dat dal, uz bez puvodniho moov
            for poradove, (typ, zacatek, velikost) in enumerate(bloky):
                if poradove < kde_mdat or typ == b'moov':
                    continue
                prepis(zacatek, velikost, vystup)

    return True
