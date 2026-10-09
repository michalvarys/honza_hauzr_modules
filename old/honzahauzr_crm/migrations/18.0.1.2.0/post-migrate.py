# -*- coding: utf-8 -*-
"""Prevod e-mailu sloupcu do knihovny.

Do verze 1.1.0 se texty psaly primo na sloupec, a to ve trech pevnych
trojicich poli (prepinac, odstup, predmet, telo). Od 1.2.0 jsou
zpravy v knihovne (hh.mail.sablona), sdruzene stitkem, a sloupec na
ne jen ukazuje.

Prevod musi udelat tri veci:

 1. Z kazde vyplnene trojice udelat zpravu v knihovne.
 2. Kazdemu sloupci zalozit vlastni stitek a prihodit mu ho.
 3. Prenest, co uz komu odeslo. Bez toho by vsichni, kdo prave ted
    ve sloupci sedi, dostali celou radu znovu - jejich karta uz je
    v hh_odeslane_stupne_ids, takze rada se znovu nezahaji, ale
    hodinovy ukol by poslal zpravy, o kterych nevi, ze uz sly.

Stare sloupce v databazi (hh_mail_enabled, hh_stupen_maily, ...)
se nemazou. Odoo je po odebrani poli necha byt a jsou pak jedinou
zachranou, kdyby se prevod nepovedl.
"""
import logging

_logger = logging.getLogger(__name__)

# cislo zpravy -> (prepinac, odstup, predmet, telo, vychozi odstup)
TROJICE = [
    (1, 'hh_mail_enabled', None, 'hh_mail_subject', 'hh_mail_body', 0),
    (2, 'hh_mail2_enabled', 'hh_mail2_po', 'hh_mail2_subject',
     'hh_mail2_body', 1),
    (3, 'hh_mail3_enabled', 'hh_mail3_po', 'hh_mail3_subject',
     'hh_mail3_body', 2),
]


def _sloupec_existuje(cr, tabulka, sloupec):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (tabulka, sloupec))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    # Kdyz uz stara pole nejsou, prevod probehl driv - neni co delat.
    if not _sloupec_existuje(cr, 'crm_stage', 'hh_mail_subject'):
        _logger.info('Honza Hauzr CRM: e-maily sloupcu uz jsou v knihovne.')
        return

    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    Stitek = env['hh.mail.stitek']
    Sablona = env['hh.mail.sablona']

    pole = [p for trojice in TROJICE for p in trojice[1:5] if p]
    cr.execute("""
        SELECT id, %s FROM crm_stage ORDER BY sequence, id
    """ % ', '.join(pole))
    radky = cr.dictfetchall()

    # cislo zpravy + id sloupce -> id zpravy v knihovne. Potrebuje to
    # treti krok, az bude prepisovat, co uz komu odeslo.
    prevedeno = {}
    zalozeno = 0

    for radek in radky:
        stupen = env['crm.stage'].browse(radek['id'])
        if not stupen.exists():
            continue

        # Predmet a telo jsou prekladatelne, takze je v databazi jsonb.
        # Bere se cesky text, a kdyz neni, prvni jaky je.
        def text(klic):
            hodnota = radek.get(klic)
            if isinstance(hodnota, dict):
                return (hodnota.get('cs_CZ') or hodnota.get('en_US')
                        or next(iter(hodnota.values()), '') or '')
            return hodnota or ''

        zpravy = []
        for cislo, p_zap, p_po, p_predmet, p_telo, vychozi in TROJICE:
            if not radek.get(p_zap):
                continue
            predmet = text(p_predmet)
            if not predmet:
                continue
            zpravy.append({
                'cislo': cislo,
                'po_dnech': (radek.get(p_po) if p_po else vychozi) or vychozi,
                'predmet': predmet,
                'telo': text(p_telo),
            })

        if not zpravy:
            continue

        stitek = Stitek.search([('name', '=', stupen.name)], limit=1)
        if not stitek:
            stitek = Stitek.create({'name': stupen.name})

        for zprava in zpravy:
            sablona = Sablona.create({
                'name': '%s – %s' % (
                    stupen.name,
                    'hned' if not zprava['po_dnech']
                    else '%s. den' % zprava['po_dnech']),
                'stitek_id': stitek.id,
                'po_dnech': zprava['po_dnech'],
                'predmet': zprava['predmet'],
                'body_arch': zprava['telo'],
                'body_html': zprava['telo'],
                'zapnuto': True,
            })
            prevedeno[(stupen.id, zprava['cislo'])] = sablona.id
            zalozeno += 1

        stupen.hh_stitek_ids = [(4, stitek.id)]

    # --- co uz komu odeslo -------------------------------------------
    preneseno = 0
    if _sloupec_existuje(cr, 'crm_lead', 'hh_stupen_maily'):
        cr.execute("""
            SELECT id, stage_id, hh_stupen_maily
            FROM crm_lead
            WHERE hh_stupen_maily IS NOT NULL AND hh_stupen_maily <> ''
        """)
        for lead_id, stage_id, odeslane in cr.fetchall():
            idcka = []
            for kus in (odeslane or '').split(','):
                kus = kus.strip()
                if not kus.isdigit():
                    continue
                sablona_id = prevedeno.get((stage_id, int(kus)))
                if sablona_id:
                    idcka.append(sablona_id)
            if not idcka:
                continue
            cr.execute("""
                INSERT INTO hh_lead_odeslany_mail_rel (lead_id, mail_id)
                SELECT %s, unnest(%s::int[])
                ON CONFLICT DO NOTHING
            """, (lead_id, idcka))
            preneseno += len(idcka)

    _logger.info(
        'Honza Hauzr CRM: do knihovny prevedeno %s e-mailu, '
        'u prilezitosti preneseno %s uz odeslanych zprav.',
        zalozeno, preneseno)
