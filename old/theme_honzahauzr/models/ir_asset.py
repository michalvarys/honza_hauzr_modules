import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrAsset(models.Model):
    """Brání vzniku dvojníků, které po sobě nechává kopírování tématu.

    Z theme.ir.asset vzniká při každé aktualizaci tématu nový
    ir.asset, aniž by Odoo poznalo, že stejný záznam už tam je.
    U šablon to jen mate, u assetů to web **shodí**: záznam
    s direktivou "remove" odebere soubor ze svazku, druhý stejný už
    nemá co odebrat a každá stránka vrátí 500

        ValueError: File(s) [...] not found in bundle
        web.assets_frontend_lazy

    Dělo se to po každém upgradu tématu a muselo se to uklízet ručně.
    Úklid v _post_copy nestačil: ten běží jen při aplikaci tématu na
    web, ne při aktualizaci modulu.

    Řeší se to proto u zdroje - duplicitní záznam vůbec nevznikne.
    Dva naprosto stejné asset záznamy nemají co dělat: druhý nic
    nepřidá a u direktivy "remove" přímo škodí.
    """

    _inherit = "ir.asset"

    @api.model_create_multi
    def create(self, vals_list):
        zbyva = []
        preskoceno = 0

        for vals in vals_list:
            cesta = vals.get("path") or ""
            # Hlida se jen nase tema. Do cizich modulu nam nic neni
            # a jejich duplicity mohou mit duvod, o kterem nevime.
            if not cesta.startswith("theme_honzahauzr"):
                zbyva.append(vals)
                continue

            if self.sudo().with_context(active_test=False).search_count([
                ("name", "=", vals.get("name")),
                ("bundle", "=", vals.get("bundle")),
                ("path", "=", cesta),
                ("directive", "=", vals.get("directive", "append")),
                ("target", "=", vals.get("target") or False),
            ]):
                preskoceno += 1
                continue

            zbyva.append(vals)

        if preskoceno:
            _logger.info(
                "Honza Hauzr: preskoceno %s duplicitnich zaznamu v "
                "ir.asset (uz v databazi jsou).", preskoceno)

        return super().create(zbyva)
