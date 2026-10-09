# -*- coding: utf-8 -*-
"""Prevod textu e-mailu do editoru.

Do verze 1.2.0 mely zpravy jedno pole s textem. Od 1.3.0 se piši
v editoru z Email Marketingu, ktery potrebuje pole dve: v jednom se
zprava sklada, do druheho si sam ulozi verzi se styly prepsanymi
primo do znacek - tu, ktera se opravdu posila. Posta totiz externi
styly zahazuje a bez toho by zprava dorazila rozsypana.

Pole se jmenuji body_arch a body_html, anglicky. Widget editoru si
body_html hleda podle jmena primo v kodu, takze pod ceskym nazvem
formular spadne.
"""
import logging

_logger = logging.getLogger(__name__)


def _sloupec(cr, nazev):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'hh_mail_sablona' AND column_name = %s
    """, (nazev,))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return
    if not _sloupec(cr, 'body_html'):
        # Tabulka jeste nema nova pole - modul se teprve instaluje.
        return

    prejmenovano = 0
    for stary, novy in (('telo_arch', 'body_arch'), ('telo', 'body_html')):
        if not _sloupec(cr, stary):
            continue
        cr.execute("""
            UPDATE hh_mail_sablona SET %s = %s
            WHERE %s IS NOT NULL AND %s IS NULL
        """ % (novy, stary, stary, novy))
        prejmenovano += cr.rowcount

    # Kdyz se zprava psala jeste pred editorem, verze pro odeslani
    # chybi - vezme se text tak, jak je.
    cr.execute("""
        UPDATE hh_mail_sablona SET body_html = body_arch
        WHERE body_html IS NULL AND body_arch IS NOT NULL
    """)

    _logger.info(
        'Honza Hauzr CRM: do editoru prevedeno %s textu.', prejmenovano)
