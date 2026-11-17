import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class HelpGuideAction extends Component {
    static template = "sale_consignment_app.HelpGuideAction";
    static props = ["*"];

    setup() {
        const params = this.props.action.params || {};
        this.url = params.url || "";
        this.title = this.props.action.name || "";
    }
}

registry.category("actions").add("sale_consignment_app.help_guide", HelpGuideAction);
