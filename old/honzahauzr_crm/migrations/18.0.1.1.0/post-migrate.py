# -*- coding: utf-8 -*-
"""Dopise zdroj a stitek prilezitostem, ktere vznikly driv nez stitkovani.

Na nastence se u nich neukazoval zadny barevny stitek, takze nebylo
poznat, odkud clovek prisel. Zdroj se odvodi z nazvu prilezitosti -
stejnym zalozim postupem, jaky uz pouziva _hh_oznacit_zdroj.

Bezi jen jednou, pri upgradu na tuhle verzi. Prilezitosti, ktere uz
nejaky stitek maji, se nechavaji byt.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})

    leady = env['crm.lead'].with_context(active_test=False).search([
        ('hh_zdroj', '=', False),
    ])
    doplneno = 0
    for lead in leady:
        pred = lead.tag_ids
        lead._hh_oznacit_zdroj()
        if lead.hh_zdroj or lead.tag_ids != pred:
            doplneno += 1

    _logger.info(
        'Honza Hauzr CRM: zdroj doplnen u %s z %s prilezitosti bez zdroje.',
        doplneno, len(leady))
