# Define applications, entities, and examples
APPLICATIONS = {
    "REPORTS_AND_INSIGHTS": "Search, filter, and favorite aggregated reports for merchandisers.",
    "OHIO_LIQUOR_DASHBOARD": "View and filter Ohio liquor-related data through a React UI.",
    "GLOBAL_MESSAGE_SERVICE": "Schedule messages for applications registered within MX space.",
    "WIC_MANAGEMENT": "Monitor and address items eligible for WIC benefits in stores.",
    "ITEM_MANAGEMENT_EXPERIENCE": "Manage product and item information for the enterprise.",
    "DIGITAL_ADS_EVENT_PRIORITY": "Set event priority for digital advertisements across all divisions.",
    "ITEM_WATCHTOWER": "Look up the status of a product at a specific Kroger location.",
    "FAMILY_TREE_MANAGEMENT": "View and browse item family tree data.",
    "PRODUCT_VARIANTS": "Create, edit, and manage product variant groups.",
    "MX_COMPLIANCE": "Repository for Kroger’s restrictions, fees, and bans.",
    "SWITCHBOARD": "Manage online availability through web overrides and unsellable family trees."
}

ENTITIES = [
    "STORE_ID",
    "ITEM_ID",
    "AD_ID",
    "CATEGORY",
    "PROMOTION_ID",
]

EXAMPLES = [
    {
        "Query": "I want to check item status in Store 123",
        "Output": {
            "Application": "ITEM_WATCHTOWER",
            "Entities": ["Store 123"],
            "Follow-up": ["Item ID"]
        }
    },
    {
        "Query": "What are the current digital ad priorities?",
        "Output": {
            "Application": "DIGITAL_ADS_EVENT_PRIORITY",
            "Entities": [],
            "Follow-up": []
        }
    },
    {
        "Query": "Check compliance rules for product 456",
        "Output": {
            "Application": "MX_COMPLIANCE",
            "Entities": ["Product 456"],
            "Follow-up": []
        }
    }
]