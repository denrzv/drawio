    agent_ui -> online_kpi "Makes API calls to business services" "JSON/HTTPS"
    cti_panel -> contact_center_platform "CTI Panel uses to receive call events and metadata, user actions on calls" "WSS"
    agent_ui -> cti_panel "Makes API calls for calls handling" "JSON/HTTPS, WSS"
    contact_center_agent -> agent_ui "Handles calls" "unknown"
