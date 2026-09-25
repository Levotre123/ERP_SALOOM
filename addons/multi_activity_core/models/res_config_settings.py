from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ma_languages = fields.Char(
        string="Extra languages",
        config_parameter="multi_activity.languages",
        help="Comma-separated Odoo language codes to activate (example: fr_FR,es_ES).",
    )

    def action_ma_activate_languages(self):
        self.env["res.lang"]._ma_ensure_recommended_languages()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Languages"),
                "message": self.env._("Recommended languages have been activated."),
                "type": "success",
                "sticky": False,
            },
        }
