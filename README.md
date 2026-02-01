# Property Tenant Portal

A full property rental workflow with tenant portal access for leases, invoices, payments, and maintenance requests (odoo 18 Enterprise).



## Highlights
- Property + Unit master data
- Lease management with recurring rent invoices
- Tenant Portal pages for:
  - Leases
  - Invoices (with Pay Now)
  - Maintenance requests (create, view, photo)
- Maintenance workflow with assignment and status tracking
- SMS notifications (Odoo SMS)
- Reports: Lease and Maintenance analysis

## Requirements
- Odoo 18 Enterprise
- Apps: Accounting, Website, Portal, SMS, Payment

## Installation
1. Add this module path to `addons_path`:
   - `E:\odoo\odoo_18e\server\property_rent`
2. Update apps list.
3. Install **Property Tenant Portal**.

## Configuration (Quick)
1. Create Property
2. Create Units
3. Create Tenant (Contact) and grant Portal access
4. Create Lease (Unit + Tenant + Rent)
5. Generate or auto-schedule invoices
6. Portal user can view invoices and submit maintenance requests

## Stripe Setup (Odoo Payment)
1. Install **Payment** and **Stripe** apps (included in module dependencies).
2. Go to **Accounting → Configuration → Payment Providers**.
3. Open **Stripe** and set:
   - Publishable Key
   - Secret Key
4. Enable the provider and select payment methods.
5. Ensure the provider is enabled for your website.

Test from portal:
- Open an unpaid invoice in `/my/invoices`.
- Click **Pay Now** and complete payment.

## SMS Flow
Configured by cron in `data/sms_cron.xml` to send:
- rent due reminders
- overdue alerts
- payment confirmations

## Portal URLs
- `/my/leases`
- `/my/maintenance`
- `/my/invoices`

## Notes
- This module uses Odoo core SMS.
- Payments use Odoo's core payment framework with Stripe enabled.
- Maintenance can only move to **In Progress** when assigned.

## License
This module is provided for internal use and demonstration purposes.
