from odoo import fields, models
from odoo.exceptions import UserError


class MultiActivitySwitchEstablishment(models.TransientModel):
    _name = "multi.activity.switch.establishment"
    _description = "Switch current establishment"

    establishment_id = fields.Many2one(
        "multi.activity.establishment",
        required=True,
        default=lambda self: self.env.user.current_establishment_id,
    )

    def action_switch(self):
        self.ensure_one()
        allowed = self.env.user._ma_allowed_establishment_ids()
        if self.establishment_id not in allowed:
            raise UserError(self.env._("You are not authorized for this establishment."))
        self.env.user.sudo().write(
            {
                "current_establishment_id": self.establishment_id.id,
                "default_establishment_id": self.establishment_id.id,
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}
