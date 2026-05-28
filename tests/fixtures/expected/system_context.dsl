workspace {
model {
    crm = softwareSystem "CRM" {
        description "Used by contact center agents, based on microfrontends"
    }
    supporting_business_services_system = softwareSystem "Supporting Business Services System" {
        description "Contains microservices, provides business logic"
    }
    contact_center_platform = softwareSystem "Contact Center Platform" {
        description "Provides call routing and handling logic"
    }
    contact_center_agent = Person "Contact Center Agent" {
        description "Handles calls"
    }
    crm -> supporting_business_services_system "Makes API calls to business services" "JSON/HTTPS"
    crm -> contact_center_platform "CTI Panel uses to receive call events and metadata, user actions on calls" "WSS"
    contact_center_agent -> crm "Handles calls" "unknown"
}
views {
    systemLandscape {
        include *
        autoLayout
    }
    themes default
    }
}
