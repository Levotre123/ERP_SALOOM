from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        user = self.env.user
        if user._is_public():
            result["ma_establishment"] = False
            return result
        establishment = user.current_establishment_id
        result["ma_establishment"] = (
            {
                "id": establishment.id,
                "name": establishment.display_name,
            }
            if establishment
            else False
        )
        return result
