from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMultilingual(TransactionCase):
    def test_recommended_languages_include_french(self):
        codes = self.env["res.lang"]._ma_recommended_language_codes()
        self.assertIn("fr_FR", codes)

    def test_user_can_have_french_when_active(self):
        self.env["res.lang"]._ma_ensure_recommended_languages()
        french = self.env["res.lang"].search([("code", "=", "fr_FR"), ("active", "=", True)], limit=1)
        self.assertTrue(french, "French should be available as an interface language")
        self.env.user.lang = "fr_FR"
        self.assertEqual(self.env.user.lang, "fr_FR")
