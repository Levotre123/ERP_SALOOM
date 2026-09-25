from odoo import fields, models


class MultiActivityProvisioningLog(models.Model):
    _name = "multi.activity.provisioning.log"
    _description = "Tenant Provisioning Log"
    _order = "id desc"

    tenant_id = fields.Many2one("multi.activity.tenant", required=True, ondelete="cascade", index=True)
    state = fields.Selection(
        [("running", "Running"), ("done", "Done"), ("failed", "Failed")],
        required=True,
        default="running",
    )
    message = fields.Text()
    create_date = fields.Datetime(readonly=True)
