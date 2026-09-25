from odoo import api, models


class ResLang(models.Model):
    _inherit = "res.lang"

    @api.model
    def _ma_recommended_language_codes(self):
        raw = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("multi_activity.languages", "fr_FR")
        )
        return [code.strip() for code in raw.split(",") if code.strip()]

    @api.model
    def _ma_ensure_recommended_languages(self):
        """Activate extra UI languages without replacing English."""
        codes = self._ma_recommended_language_codes()
        if not codes:
            return self.browse()
        langs = self.sudo().with_context(active_test=False).search([("code", "in", codes)])
        to_install = langs.filtered(lambda lang: not lang.active)
        if not to_install:
            return langs.filtered("active")
        if "base.language.install" in self.env:
            wizard = self.env["base.language.install"].sudo()
            if "lang_ids" in wizard._fields:
                installer = wizard.create(
                    {"lang_ids": [(6, 0, to_install.ids)], "overwrite": False}
                )
                installer.lang_install()
            elif "lang" in wizard._fields:
                for lang in to_install:
                    wizard.create({"lang": lang.code, "overwrite": False}).lang_install()
            else:
                to_install.sudo().write({"active": True})
        else:
            to_install.sudo().write({"active": True})
        return self.sudo().search([("code", "in", codes), ("active", "=", True)])
