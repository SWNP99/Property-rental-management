# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    property_lease_id = fields.Many2one("property.lease", string="Lease")
    property_unit_id = fields.Many2one("property.unit", string="Unit")

    rent_sms_due_sent = fields.Boolean(default=False)
    rent_sms_overdue_sent = fields.Boolean(default=False)
    rent_sms_paid_sent = fields.Boolean(default=False)

    def _send_rent_sms(self, body):
        for move in self:
            partner = move.partner_id
            if not partner:
                continue
            move._message_sms(body, partner_ids=[partner.id])

    def _get_rent_sms_context(self):
        self.ensure_one()
        unit_name = self.property_unit_id.name or "your unit"
        due_date = self.invoice_date_due or self.invoice_date
        return {
            "tenant": self.partner_id.name or "Tenant",
            "unit": unit_name,
            "due_date": due_date,
            "amount": self.amount_total,
            "invoice": self.name or "invoice",
        }

    def _build_due_sms(self):
        ctx = self._get_rent_sms_context()
        return (
            f"Rent reminder: {ctx['unit']} is due on {ctx['due_date']}. "
            f"Amount: {ctx['amount']:.2f}. Ref {ctx['invoice']}."
        )

    def _build_overdue_sms(self):
        ctx = self._get_rent_sms_context()
        return (
            f"Overdue rent: {ctx['unit']} was due on {ctx['due_date']}. "
            f"Amount: {ctx['amount']:.2f}. Ref {ctx['invoice']}."
        )

    def _build_paid_sms(self):
        ctx = self._get_rent_sms_context()
        return (
            f"Payment received. Thank you! {ctx['invoice']} for {ctx['unit']} "
            f"amount {ctx['amount']:.2f} is paid."
        )

    @api.model
    def _rent_due_reminder_days(self):
        return 3

    @api.model
    def cron_send_rent_sms_reminders(self):
        today = fields.Date.context_today(self)
        due_days = self._rent_due_reminder_days()
        due_date = today + timedelta(days=due_days)
        domain_base = [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "!=", "paid"),
            ("property_lease_id", "!=", False),
            ("invoice_date_due", "!=", False),
        ]
        due_moves = self.search(domain_base + [("invoice_date_due", "=", due_date), ("rent_sms_due_sent", "=", False)])
        for move in due_moves:
            move._send_rent_sms(move._build_due_sms())
            move.rent_sms_due_sent = True

        overdue_moves = self.search(domain_base + [("invoice_date_due", "<", today), ("rent_sms_overdue_sent", "=", False)])
        for move in overdue_moves:
            move._send_rent_sms(move._build_overdue_sms())
            move.rent_sms_overdue_sent = True

    def write(self, vals):
        res = super().write(vals)
        if "payment_state" in vals:
            paid_moves = self.filtered(
                lambda m: m.payment_state == "paid"
                and m.property_lease_id
                and not m.rent_sms_paid_sent
            )
            for move in paid_moves:
                move._send_rent_sms(move._build_paid_sms())
                move.rent_sms_paid_sent = True
        return res

    def get_portal_url(self, suffix=None, report_type=None, download=False, **kwargs):
        url = super().get_portal_url(
            suffix=suffix, report_type=report_type, download=download, **kwargs
        )
        if "access_token=" not in url:
            token = self._portal_ensure_token()
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}access_token={token}"
        return url
