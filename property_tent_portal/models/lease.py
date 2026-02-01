# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyLease(models.Model):
    _name = "property.lease"
    _description = "Lease Contract"
    _inherit = ["portal.mixin"]
    _order = "start_date desc, id desc"

    name = fields.Char(default="New", copy=False, readonly=True)
    unit_id = fields.Many2one("property.unit", required=True, ondelete="cascade")
    property_id = fields.Many2one(related="unit_id.property_id", store=True, readonly=True)
    tenant_id = fields.Many2one("res.partner", required=True)

    start_date = fields.Date(required=True)
    end_date = fields.Date()
    rent_amount = fields.Monetary(required=True)
    billing_cycle = fields.Selection(
        [("monthly", "Monthly")], default="monthly", required=True
    )

    rent_product_id = fields.Many2one(
        "product.product",
        required=True,
        domain=[("sale_ok", "=", True)],
    )

    next_invoice_date = fields.Date()
    last_invoice_date = fields.Date()

    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("ended", "Ended")],
        default="draft",
        required=True,
    )

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )

    @api.onchange("unit_id")
    def _onchange_unit_id(self):
        for rec in self:
            if rec.unit_id:
                rec.rent_amount = rec.unit_id.rent_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("property.lease") or "New"
                )
            if not vals.get("next_invoice_date") and vals.get("start_date"):
                vals["next_invoice_date"] = vals["start_date"]
        return super().create(vals_list)

    def action_activate(self):
        self.write({"state": "active"})

    def action_end(self):
        self.write({"state": "ended"})

    def _prepare_invoice_values(self, invoice_date):
        self.ensure_one()
        if not self.rent_product_id:
            raise UserError("Please set a rent product on the lease contract.")
        line_name = "Rent for %s (%s)" % (self.unit_id.name, invoice_date.strftime("%B %Y"))
        return {
            "move_type": "out_invoice",
            "partner_id": self.tenant_id.id,
            "invoice_date": invoice_date,
            "invoice_date_due": invoice_date,
            "invoice_origin": self.name,
            "property_lease_id": self.id,
            "property_unit_id": self.unit_id.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.rent_product_id.id,
                        "name": line_name,
                        "quantity": 1.0,
                        "price_unit": self.rent_amount,
                    },
                )
            ],
        }

    def action_generate_invoice(self, invoice_date=False):
        for lease in self:
            if lease.state != "active":
                continue
            date_to_use = invoice_date or lease.next_invoice_date
            if not date_to_use:
                continue
            move_vals = lease._prepare_invoice_values(date_to_use)
            move = self.env["account.move"].create(move_vals)
            if move.state == "draft":
                move.action_post()
            lease.last_invoice_date = date_to_use
            lease.next_invoice_date = date_to_use + relativedelta(months=1)

    @api.model
    def cron_generate_rent_invoices(self):
        today = fields.Date.context_today(self)
        leases = self.search(
            [
                ("state", "=", "active"),
                ("next_invoice_date", "!=", False),
                ("next_invoice_date", "<=", today),
            ]
        )
        for lease in leases:
            lease.action_generate_invoice(lease.next_invoice_date)
