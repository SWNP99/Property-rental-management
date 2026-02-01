# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyUnit(models.Model):
    _name = "property.unit"
    _description = "Property Unit"

    name = fields.Char(required=True)
    code = fields.Char(default="New", copy=False, readonly=True)
    unit_number = fields.Char()
    property_id = fields.Many2one("property.property", required=True, ondelete="cascade")
    rent_amount = fields.Monetary(required=True)

    status = fields.Selection(
        [("vacant", "Vacant"), ("occupied", "Occupied")],
        default="vacant",
        required=True,
    )

    lease_ids = fields.One2many("property.lease", "unit_id", string="Leases")
    current_lease_id = fields.Many2one(
        "property.lease", compute="_compute_current_lease", store=True
    )
    current_tenant_id = fields.Many2one(
        "res.partner", compute="_compute_current_lease", store=True
    )

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "New") == "New":
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("property.unit") or "New"
                )
        return super().create(vals_list)

    def name_get(self):
        result = []
        for rec in self:
            if rec.code:
                name = f"{rec.code} - {rec.name}" if rec.name else rec.code
            else:
                name = rec.name
            result.append((rec.id, name))
        return result

    @api.depends("lease_ids.state", "lease_ids.start_date", "lease_ids.end_date")
    def _compute_current_lease(self):
        today = fields.Date.context_today(self)
        for unit in self:
            lease = self.env["property.lease"].search(
                [
                    ("unit_id", "=", unit.id),
                    ("state", "=", "active"),
                    ("start_date", "<=", today),
                    "|",
                    ("end_date", "=", False),
                    ("end_date", ">=", today),
                ],
                order="start_date desc, id desc",
                limit=1,
            )
            unit.current_lease_id = lease
            unit.current_tenant_id = lease.tenant_id if lease else False
