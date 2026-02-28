# Zoho Creator API

## 1. Generate Access Token

**Endpoint**

```
POST https://accounts.zoho.com/oauth/v2/token
```

**Query Parameters**

- refresh_token={REFRESH_TOKEN}
- client_id={CLIENT_ID}
- client_secret={CLIENT_SECRET}
- grant_type=refresh_token

---

## 2. Get Report Metadata

Returns all available reports in the app.

**Endpoint**

```
GET https://www.zohoapis.com/creator/v2.1/meta/{ZOHO_ACCOUNT_OWNER}/{ZOHO_APP_LINK_NAME}/reports
```

**Headers**

```
Authorization: Zoho-oauthtoken {ACCESS_TOKEN}
```

**Sample Response**

```json
{
  "code": 3000,
  "reports": [
    {
      "display_name": "All Medical Records",
      "link_name": "medical_records_Report",
      "type": 1
    }
  ]
}
```

> Use `link_name` as `{REPORT_NAME}` in the next API call.

---

## 3. Get Report Data

Fetch records from a specific report.

**Endpoint**

```
GET https://www.zohoapis.com/creator/v2.1/data/{ZOHO_ACCOUNT_OWNER}/{ZOHO_APP_LINK_NAME}/report/{REPORT_NAME}
```

**Headers**

```
Authorization: Zoho-oauthtoken {ACCESS_TOKEN}
```

**Sample Response**

```json
{
  "code": 3000,
  "data": [
    {
      "severity": "Mild",
      "condition_type": "Chronic",
      "chief_complaint": "Abdominal pain",
      "status": "Ongoing",
      "visit_date": "27-Feb-2026",
      "ID": "4668599000002311027"
    }
  ]
}
```

