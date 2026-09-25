# Tenant user guide

## Owner

After login, open **Dashboard**. Filter by establishment or all sites.
You should see revenue, cash collected, expenses, estimated profit,
low stock, and cash differences.

Switch site: **Settings → My Profile → Current establishment** (or the
switch wizard). New POS sessions and expenses use that site.

## Cashier

Open **Point of Sale** for your establishment, open the session (float),
sell, close with a physical count. A gap beyond tolerance is audited.

## Hairdresser

**Activity → Appointments**: create, confirm, start, complete.
Commission is stored when the appointment is completed.

## Storekeeper

Use standard **Inventory** receipts, counts, and purchases. Do not edit
quantities in SQL.

## Language

The platform is multilingual. English stays available. French is activated
by default. Platform administrators can add any other Odoo language from
**SaaS Admin → Languages** or **Business → Settings → Languages**.

- Each user chooses a language in **Preferences** (or **Users → Establishments**).
- Each tenant has a default **Language**. Provisioning applies it to the
  owner and the company partner.
- The login page shows a language selector once more than one language is
  active.

To activate extra languages, set the system parameter
`multi_activity.languages` to a comma-separated list of codes
(example: `fr_FR,es_ES,pt_PT`) then open **Languages**.

## Correction policy

Cancel, refund, or adjust. Never delete a sale, payment, or stock move.
