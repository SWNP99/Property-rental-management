# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyMaintenanceRequest(models.Model):
    _name = "property.maintenance.request"
    _description = "Maintenance Request"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True)
    tenant_id = fields.Many2one("res.partner", required=True)
    unit_id = fields.Many2one("property.unit", required=True, ondelete="cascade")
    lease_id = fields.Many2one(
        "property.lease", compute="_compute_lease", store=True, readonly=True
    )
    property_id = fields.Many2one(related="unit_id.property_id", store=True, readonly=True)

    request_date = fields.Date(default=fields.Date.context_today, required=True)
    issue_type = fields.Selection(
        [
            ("plumbing", "Plumbing"),
            ("electrical", "Electrical"),
            ("hvac", "HVAC"),
            ("appliance", "Appliance"),
            ("structural", "Structural"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
        tracking=True,
    )
    description = fields.Text(required=True)
    photo = fields.Binary()
    photo_filename = fields.Char()

    state = fields.Selection(
        [("new", "New"), ("in_progress", "In Progress"), ("done", "Done")],
        default="new",
        tracking=True,
    )
    assigned_to_id = fields.Many2one("res.users", tracking=True)

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.depends("tenant_id", "unit_id")
    def _compute_lease(self):
        for rec in self:
            lease = False
            if rec.tenant_id and rec.unit_id:
                lease = self.env["property.lease"].search(
                    [
                        ("unit_id", "=", rec.unit_id.id),
                        ("tenant_id", "=", rec.tenant_id.id),
                        ("state", "=", "active"),
                    ],
                    limit=1,
                )
            rec.lease_id = lease

    @api.constrains("tenant_id", "unit_id")
    def _check_tenant_unit_link(self):
        for rec in self:
            if rec.tenant_id and rec.unit_id and not rec.lease_id:
                if not self.env.user.has_group("base.group_user"):
                    raise ValidationError("Selected unit is not assigned to this tenant.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].sudo().next_by_code("property.maintenance")
                    or "New"
                )
        return super().create(vals_list)

    def action_in_progress(self):
        for rec in self:
            if not rec.assigned_to_id:
                raise ValidationError("Please assign a responsible user before starting.")
        self.write({"state": "in_progress"})

    def action_done(self):
        self.write({"state": "done"})
