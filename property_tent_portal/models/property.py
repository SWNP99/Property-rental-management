# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyProperty(models.Model):
    _name = "property.property"
    _description = "Property"

    name = fields.Char(required=True)
    code = fields.Char(default="New", copy=False, readonly=True)
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state")
    zip = fields.Char()
    country_id = fields.Many2one("res.country")

    unit_ids = fields.One2many("property.unit", "property_id", string="Units")

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
                    self.env["ir.sequence"].next_by_code("property.property") or "New"
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
