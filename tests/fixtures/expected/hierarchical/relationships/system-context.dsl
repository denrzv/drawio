    crm -> supporting_business_services_system "Makes API calls to business services" "JSON/HTTPS"
    crm -> contact_center_platform "CTI Panel uses to receive call events and metadata, user actions on calls" "WSS"
    contact_center_agent -> crm "Handles calls" "unknown"
