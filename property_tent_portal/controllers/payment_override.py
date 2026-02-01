# -*- coding: utf-8 -*-
from odoo import _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request, route

from odoo.addons.account_payment.controllers.payment import PaymentPortal as AccountPaymentPortal


class PaymentPortalOverride(AccountPaymentPortal):
    @route('/invoice/transaction/<int:invoice_id>', type='json', auth='public')
    def invoice_transaction(self, invoice_id, access_token=None, **kwargs):
        """Allow portal users to pay invoices even if access_token is not sent."""
        if not access_token:
            # If user is logged in and has access, generate a portal token.
            if not request.env.user._is_public():
                invoice = request.env['account.move'].browse(invoice_id).exists()
                if not invoice:
                    raise MissingError(_("This document does not exist."))
                try:
                    invoice.check_access('read')
                except AccessError:
                    raise ValidationError(_("The access token is invalid."))
                access_token = invoice._portal_ensure_token()
            else:
                raise ValidationError(_("The access token is invalid."))
        return super().invoice_transaction(invoice_id, access_token, **kwargs)
