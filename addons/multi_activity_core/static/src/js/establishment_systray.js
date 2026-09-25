/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

function switchEstablishmentItem(env) {
    return {
        type: "item",
        id: "ma_switch_establishment",
        description: _t("Switch Establishment"),
        callback: async () => {
            await env.services.action.doAction("multi_activity_core.action_switch_establishment");
        },
        sequence: 15,
    };
}

export class EstablishmentSystray extends Component {
    static template = "multi_activity_core.EstablishmentSystray";
    static props = {};

    setup() {
        this.action = useService("action");
    }

    get label() {
        return session.ma_establishment?.name || _t("Establishment");
    }

    async onClick() {
        await this.action.doAction("multi_activity_core.action_switch_establishment");
    }
}

registry.category("user_menuitems").add("ma_switch_establishment", switchEstablishmentItem);
registry.category("systray").add(
    "multi_activity_core.establishment",
    { Component: EstablishmentSystray },
    { sequence: 20 }
);
