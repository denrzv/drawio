workspace {
model {
    crm = softwareSystem "CRM" {
        description "Used by contact center agents, based on microfrontends"
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
        description "Contains microservices, provides business logic"
        online_kpi = container "Online KPI" {
            description "Microservice that provides online kpi for agents"
            technology "SpringBoot"
        }
    }
    contact_center_platform = softwareSystem "Contact Center Platform" {
        description "Provides call routing and handling logic"
    }
    contact_center_agent = Person "Contact Center Agent" {
        description "Handles calls"
    }
    !include relationships/system-context.dsl
    !include relationships/container-crm.dsl
}
views {
    !include views/system-landscape.dsl
    !include views/container-crm.dsl
    !include views/container-supporting_business_services_system.dsl
    themes default
    }
}
