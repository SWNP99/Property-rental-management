# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request


class TenantPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "lease_count" in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            lease_count = request.env["property.lease"].search_count(
                [("tenant_id", "child_of", partner.id)]
            )
            values["lease_count"] = lease_count
        if "maintenance_count" in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            maintenance_count = request.env["property.maintenance.request"].search_count(
                [("tenant_id", "child_of", partner.id)]
            )
            values["maintenance_count"] = maintenance_count
        return values

    @http.route(["/my/leases"], type="http", auth="user", website=True)
    def portal_my_leases(self, page=1, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        Lease = request.env["property.lease"]
        domain = [("tenant_id", "child_of", partner.id)]
        total = Lease.search_count(domain)
        pager = portal_pager(
            url="/my/leases",
            total=total,
            page=page,
            step=20,
        )
        leases = Lease.search(
            domain, order="start_date desc, id desc", limit=20, offset=pager["offset"]
        )
        values = {
            "leases": leases,
            "page_name": "leases",
            "pager": pager,
        }
        return request.render("property_tent_portal.portal_my_leases", values)

    @http.route(["/my/leases/<int:lease_id>"], type="http", auth="user", website=True)
    def portal_lease_detail(self, lease_id, **kw):
        lease = self._document_check_access("property.lease", lease_id)
        invoices = request.env["account.move"].search(
            [("property_lease_id", "=", lease.id)], order="invoice_date desc, id desc"
        )
        values = {
            "lease": lease,
            "invoices": invoices,
            "page_name": "leases",
        }
        return request.render("property_tent_portal.portal_lease_detail", values)

    @http.route(["/my/maintenance"], type="http", auth="user", website=True)
    def portal_my_maintenance(self, page=1, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        Request = request.env["property.maintenance.request"]
        domain = [("tenant_id", "child_of", partner.id)]
        total = Request.search_count(domain)
        pager = portal_pager(
            url="/my/maintenance",
            total=total,
            page=page,
            step=20,
        )
        requests = Request.search(
            domain, order="request_date desc, id desc", limit=20, offset=pager["offset"]
        )
        values = {
            "requests": requests,
            "page_name": "maintenance",
            "pager": pager,
        }
        return request.render("property_tent_portal.portal_my_maintenance", values)

    @http.route(["/my/maintenance/new"], type="http", auth="user", website=True)
    def portal_new_maintenance(self, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        units = request.env["property.unit"].search(
            [("lease_ids.tenant_id", "child_of", partner.id)]
        )
        values = {
            "units": units,
            "page_name": "maintenance",
        }
        return request.render("property_tent_portal.portal_maintenance_new", values)

    @http.route(["/my/maintenance/<int:request_id>"], type="http", auth="user", website=True)
    def portal_maintenance_detail(self, request_id, **kw):
        request_rec = self._document_check_access(
            "property.maintenance.request", request_id
        )
        values = {
            "request_rec": request_rec,
            "page_name": "maintenance",
        }
        return request.render("property_tent_portal.portal_maintenance_detail", values)

    @http.route(["/my/maintenance/create"], type="http", auth="user", website=True, methods=["POST"])
    def portal_create_maintenance(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        unit_id = int(post.get("unit_id") or 0)
        description = (post.get("description") or "").strip()
        issue_type = post.get("issue_type") or "other"
        if not unit_id or not description:
            return request.redirect("/my/maintenance/new?error=1")
        allowed_units = request.env["property.unit"].search(
            [("lease_ids.tenant_id", "child_of", partner.id)]
        )
        if unit_id not in allowed_units.ids:
            return request.redirect("/my/maintenance/new?error=1")
        req_vals = {
            "tenant_id": partner.id,
            "unit_id": unit_id,
            "issue_type": issue_type,
            "description": description,
        }
        upload = request.httprequest.files.get("photo")
        if upload and upload.filename:
            import base64
            req_vals["photo"] = base64.b64encode(upload.read())
            req_vals["photo_filename"] = upload.filename
        request.env["property.maintenance.request"].create(req_vals)
        return request.redirect("/my/maintenance")
