from agent.zoho_client import ZohoCreatorClient


def test_extract_reports_from_result_reports() -> None:
    payload = {
        "result": {
            "reports": [
                {
                    "name": "All Leads",
                    "report_link_name": "All_Leads",
                    "description": "Lead report",
                }
            ]
        }
    }
    out = ZohoCreatorClient._extract_reports_from_payload(payload)
    assert len(out) == 1
    assert out[0]["report_link_name"] == "All_Leads"
    assert out[0]["table_name"] == "all_leads"


def test_extract_reports_from_data_reports_with_fallback_fields() -> None:
    payload = {
        "data": {
            "reports": [
                {
                    "display_name": "Tickets",
                    "link_name": "Support_Tickets",
                }
            ]
        }
    }
    out = ZohoCreatorClient._extract_reports_from_payload(payload)
    assert len(out) == 1
    assert out[0]["name"] == "Tickets"
    assert out[0]["table_name"] == "support_tickets"
