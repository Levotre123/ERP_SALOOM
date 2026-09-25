from odoo import api, fields, models


class MultiActivityEstablishmentMixin(models.AbstractModel):
    _name = "multi.activity.establishment.mixin"
    _description = "Establishment scoping mixin"

    establishment_id = fields.Many2one(
        "multi.activity.establishment",
        required=True,
        index=True,
        default=lambda self: self.env.user.current_establishment_id,
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        "res.company",
        related="establishment_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        establishment = self.env.user.current_establishment_id
        if establishment and "establishment_id" in fields_list and not values.get("establishment_id"):
            values["establishment_id"] = establishment.id
        return values
