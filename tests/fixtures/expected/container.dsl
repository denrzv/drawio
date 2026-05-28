workspace {
model {
    contact_center_platform = softwareSystem "Contact Center Platform" {
        description "Provides call routing and handling logic"
    }
    crm = softwareSystem "CRM" {
        agent_ui = container "agent-ui" {
            description "Provides main operator functions"
            technology "ReactJS"
        }
        cti_panel = container "cti-panel" {
            description "Provides backend for contact center integration for CTI"
            technology "SpringBoot"
        }
    }
    supporting_business_services_system = softwareSystem "Supporting Business Services System" {
        online_kpi = container "Online KPI" {
            description "Microservice that provides online kpi for agents"
            technology "SpringBoot"
        }
    }
    contact_center_agent = Person "Contact Center Agent" {
        description "Handles calls"
    }
    agent_ui -> online_kpi "Makes API calls to business services" "JSON/HTTPS"
    cti_panel -> contact_center_platform "CTI Panel uses to receive call events and metadata, user actions on calls" "WSS"
    agent_ui -> cti_panel "Makes API calls for calls handling" "JSON/HTTPS, WSS"
    contact_center_agent -> agent_ui "Handles calls" "unknown"
}
views {
    systemLandscape {
        include *
        autoLayout
    }
    container crm {
        include *
        autoLayout
    }
    container supporting_business_services_system {
        include *
        autoLayout
    }
    themes default
    }
}
