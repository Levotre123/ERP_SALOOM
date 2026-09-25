def _volume_category(env):
    category = env.ref("uom.product_uom_categ_vol", raise_if_not_found=False)
    if category:
        return category
    category = env.ref("uom.uom_categ_volume", raise_if_not_found=False)
    if category:
        return category
    return env["uom.category"].search([("name", "ilike", "vol")], limit=1)


def _litre(env, category):
    litre = env.ref("uom.product_uom_litre", raise_if_not_found=False)
    if litre:
        return litre
    return env["uom.uom"].search([("category_id", "=", category.id), ("name", "in", ["L", "Liter", "Litre"])], limit=1)


def _create_uom(env, xmlid, name, category, litre, factor):
    existing = env.ref(xmlid, raise_if_not_found=False)
    if existing:
        return existing
    vals = {
        "name": name,
        "category_id": category.id,
    }
    fields_map = env["uom.uom"]._fields
    if "uom_type" in fields_map:
        vals["uom_type"] = "smaller"
        vals["factor"] = factor
    elif "relative_uom_id" in fields_map:
        vals["relative_uom_id"] = litre.id
        vals["relative_factor"] = factor
    if "rounding" in fields_map:
        vals["rounding"] = 0.001
    uom = env["uom.uom"].create(vals)
    module, name = xmlid.split(".", 1)
    if not env["ir.model.data"].search([("module", "=", module), ("name", "=", name)], limit=1):
        env["ir.model.data"].create(
            {
                "name": name,
                "module": module,
                "model": "uom.uom",
                "res_id": uom.id,
                "noupdate": True,
            }
        )
    return uom


def post_init_hook(env):
    category = _volume_category(env)
    if not category:
        return
    litre = _litre(env, category)
    if not litre:
        return
    _create_uom(env, "multi_activity_bar.uom_ml", "ml", category, litre, 1000.0)
    _create_uom(env, "multi_activity_bar.uom_dose", "Dose (50ml)", category, litre, 20.0)
    _create_uom(env, "multi_activity_bar.uom_glass", "Glass (200ml)", category, litre, 5.0)
    _create_uom(env, "multi_activity_bar.uom_bottle_750", "Bottle (750ml)", category, litre, 1000.0 / 750.0)
