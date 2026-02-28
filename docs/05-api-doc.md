
# POST access token

https://accounts.zoho.com/oauth/v2/token?refresh_token={refresh token}&client_id={}&client_secret={}&grant_type=refresh_token


# GET meta data of report


GET - https://www.zohoapis.com/creator/v2.1/meta/{ZOHO_ACCOUNT_OWNER}/{ZOHO_APP_LINK_NAME}/reports

Header - Authorization : Zoho-oauthtoken {ZOHO ACCESS TOKEN}

response :

{
    "reports": [
        {
            "display_name": "All Medical Records",
            "link_name": "medical_records_Report",
            "type": 1
        },
        {
            "display_name": "Severities",
            "link_name": "medical_records_by_severity",
            "type": 4
        },
        {
            "display_name": "All Appointments",
            "link_name": "appointments_Report",
            "type": 1
        },
        {
            "display_name": "Statuses",
            "link_name": "appointments_by_status",
            "type": 4
        },
        {
            "display_name": "All Bills",
            "link_name": "bills_Report",
            "type": 1
        },
        {
            "display_name": "Payment Modes",
            "link_name": "bills_by_payment_mode",
            "type": 4
        },
        {
            "display_name": "All Doctors",
            "link_name": "doctors_Report",
            "type": 1
        },
        {
            "display_name": "All Prescriptions",
            "link_name": "prescriptions_Report",
            "type": 1
        },
        {
            "display_name": "All Patients",
            "link_name": "patients_Report",
            "type": 1
        },
        {
            "display_name": "Blood Groups",
            "link_name": "patients_by_blood_group",
            "type": 4
        },
        {
            "display_name": "All Lab Orders",
            "link_name": "lab_orders_Report",
            "type": 1
        }
    ],
    "code": 3000
}




(ii) GET REports inside data

GET - https://www.zohoapis.com/creator/v2.1/data/{ZOHO_ACCOUNT_OWNER}/{ZOHO_APP_LINK_NAME}/report/{REPORT NAME}

Header - Authorization : Zoho-oauthtoken {ZOHO ACCESS TOKEN}

vary based on different app-
sample respose : 

{
    "code": 3000,
    "data": [
        {
            "severity": "Mild",
            "condition_type": "Chronic",
            "appointment": [
                {
                    "appointment_id": "1",
                    "ID": "4668599000002312027",
                    "zc_display_value": "1"
                },
                {
                    "appointment_id": "2",
                    "ID": "4668599000002312031",
                    "zc_display_value": "2"
                }
            ],
            "follow_up_required": "true",
            "procedure_done": "Stool test",
            "doctor": [
                {
                    "doctor_id": "1",
                    "ID": "4668599000002314011",
                    "zc_display_value": "1"
                },
                {
                    "doctor_id": "3",
                    "ID": "4668599000002314019",
                    "zc_display_value": "3"
                },
                {
                    "doctor_id": "4",
                    "ID": "4668599000002314023",
                    "zc_display_value": "4"
                }
            ],
            "symptoms": "Cramping, bloating",
            "duration": "4 days",
            "icd_code": "A09.9",
            "follow_up_date": "20-Mar-2026",
            "record_id": "5",
            "patient": [
                {
                    "patient_id": "1",
                    "ID": "4668599000002312007",
                    "zc_display_value": "1"
                },
                {
                    "patient_id": "2",
                    "ID": "4668599000002312011",
                    "zc_display_value": "2"
                },
                {
                    "patient_id": "3",
                    "ID": "4668599000002312015",
                    "zc_display_value": "3"
                },
                {
                    "patient_id": "4",
                    "ID": "4668599000002312019",
                    "zc_display_value": "4"
                },
                {
                    "patient_id": "5",
                    "ID": "4668599000002312023",
                    "zc_display_value": "5"
                }
            ],
            "chief_complaint": "Abdominal pain",
            "treatment_plan": "Hydration, rest",
            "provisional_diagnosis": "Gastroenteritis",
            "ID": "4668599000002311027",
            "final_diagnosis": "Viral gastroenteritis",
            "visit_date": "27-Feb-2026",
            "status": "Ongoing"
        },
        {
            "severity": "Moderate",
            "condition_type": "Acute",
            "appointment": [
                {
                    "appointment_id": "2",
                    "ID": "4668599000002312031",
                    "zc_display_value": "2"
                }
            ],
            "follow_up_required": "false",
            "procedure_done": "Neurological exam",
            "doctor": [
                {
                    "doctor_id": "1",
                    "ID": "4668599000002314011",
                    "zc_display_value": "1"
                },
                {
                    "doctor_id": "2",
                    "ID": "4668599000002314015",
                    "zc_display_value": "2"
                },
                {
                    "doctor_id": "3",
                    "ID": "4668599000002314019",
                    "zc_display_value": "3"
                },
                {
                    "doctor_id": "4",
                    "ID": "4668599000002314023",
                    "zc_display_value": "4"
                },
                {
                    "doctor_id": "5",
                    "ID": "4668599000002314027",
                    "zc_display_value": "5"
                }
            ],
            "symptoms": "Severe headache, nausea",
            "duration": "1 day",
            "icd_code": "G43.1",
            "follow_up_date": "01-Mar-2026",
            "record_id": "4",
            "patient": [
                {
                    "patient_id": "1",
                    "ID": "4668599000002312007",
                    "zc_display_value": "1"
                },
                {
                    "patient_id": "2",
                    "ID": "4668599000002312011",
                    "zc_display_value": "2"
                },
                {
                    "patient_id": "3",
                    "ID": "4668599000002312015",
                    "zc_display_value": "3"
                },
                {
                    "patient_id": "4",
                    "ID": "4668599000002312019",
                    "zc_display_value": "4"
                }
            ],
            "chief_complaint": "Headache and dizziness",
            "treatment_plan": "Avoid triggers, rest",
            "provisional_diagnosis": "Migraine",
            "ID": "4668599000002311023",
            "final_diagnosis": "Migraine with aura",
            "visit_date": "27-Feb-2026",
            "status": "Resolved"
        },
        {
            "severity": "Mild",
            "condition_type": "Chronic",
            "appointment": [
                {
                    "appointment_id": "1",
                    "ID": "4668599000002312027",
                    "zc_display_value": "1"
                },
                {
                    "appointment_id": "2",
                    "ID": "4668599000002312031",
                    "zc_display_value": "2"
                },
                {
                    "appointment_id": "3",
                    "ID": "4668599000002312035",
                    "zc_display_value": "3"
                },
                {
                    "appointment_id": "5",
                    "ID": "4668599000002312043",
                    "zc_display_value": "5"
                }
            ],
            "follow_up_required": "true",
            "procedure_done": "Joint aspiration",
            "doctor": [
                {
                    "doctor_id": "1",
                    "ID": "4668599000002314011",
                    "zc_display_value": "1"
                },
                {
                    "doctor_id": "2",
                    "ID": "4668599000002314015",
                    "zc_display_value": "2"
                },
                {
                    "doctor_id": "3",
                    "ID": "4668599000002314019",
                    "zc_display_value": "3"
                },
                {
                    "doctor_id": "4",
                    "ID": "4668599000002314023",
                    "zc_display_value": "4"
                }
            ],
            "symptoms": "Stiffness, redness in knees",
            "duration": "2 weeks",
            "icd_code": "M05.9",
            "follow_up_date": "14-Mar-2026",
            "record_id": "3",
            "patient": [
                {
                    "patient_id": "1",
                    "ID": "4668599000002312007",
                    "zc_display_value": "1"
                },
                {
                    "patient_id": "2",
                    "ID": "4668599000002312011",
                    "zc_display_value": "2"
                }
            ],
            "chief_complaint": "Joint swelling",
            "treatment_plan": "NSAIDs, physical therapy",
            "provisional_diagnosis": "Rheumatoid arthritis",
            "ID": "4668599000002311019",
            "final_diagnosis": "Seropositive RA",
            "visit_date": "27-Feb-2026",
            "status": "Ongoing"
        },
        {
            "severity": "Moderate",
            "condition_type": "Acute",
            "appointment": [
                {
                    "appointment_id": "1",
                    "ID": "4668599000002312027",
                    "zc_display_value": "1"
                }
            ],
            "follow_up_required": "false",
            "procedure_done": "Blood test",
            "doctor": [
                {
                    "doctor_id": "1",
                    "ID": "4668599000002314011",
                    "zc_display_value": "1"
                }
            ],
            "symptoms": "High temperature, weakness",
            "duration": "5 days",
            "icd_code": "A50.0",
            "follow_up_date": "05-Mar-2026",
            "record_id": "2",
            "patient": [
                {
                    "patient_id": "1",
                    "ID": "4668599000002312007",
                    "zc_display_value": "1"
                },
                {
                    "patient_id": "2",
                    "ID": "4668599000002312011",
                    "zc_display_value": "2"
                },
                {
                    "patient_id": "4",
                    "ID": "4668599000002312019",
                    "zc_display_value": "4"
                }
            ],
            "chief_complaint": "Fever and fatigue",
            "treatment_plan": "Antiviral therapy, rest",
            "provisional_diagnosis": "Infectious mononucleosis",
            "ID": "4668599000002311015",
            "final_diagnosis": "Epstein-Barr virus infection",
            "visit_date": "27-Feb-2026",
            "status": "Ongoing"
        },
        {
            "severity": "Moderate",
            "condition_type": "Acute",
            "appointment": [
                {
                    "appointment_id": "2",
                    "ID": "4668599000002312031",
                    "zc_display_value": "2"
                },
                {
                    "appointment_id": "3",
                    "ID": "4668599000002312035",
                    "zc_display_value": "3"
                },
                {
                    "appointment_id": "4",
                    "ID": "4668599000002312039",
                    "zc_display_value": "4"
                }
            ],
            "follow_up_required": "true",
            "procedure_done": "ECG, stress test",
            "doctor": [
                {
                    "doctor_id": "1",
                    "ID": "4668599000002314011",
                    "zc_display_value": "1"
                }
            ],
            "symptoms": "Chest discomfort, shortness of breath",
            "duration": "3 days",
            "icd_code": "I21.9",
            "follow_up_date": "27-Feb-2026",
            "record_id": "1",
            "patient": [
                {
                    "patient_id": "1",
                    "ID": "4668599000002312007",
                    "zc_display_value": "1"
                },
                {
                    "patient_id": "2",
                    "ID": "4668599000002312011",
                    "zc_display_value": "2"
                },
                {
                    "patient_id": "3",
                    "ID": "4668599000002312015",
                    "zc_display_value": "3"
                },
                {
                    "patient_id": "4",
                    "ID": "4668599000002312019",
                    "zc_display_value": "4"
                },
                {
                    "patient_id": "5",
                    "ID": "4668599000002312023",
                    "zc_display_value": "5"
                }
            ],
            "chief_complaint": "Persistent chest pain",
            "treatment_plan": "Rest, medication, monitor",
            "provisional_diagnosis": "Myocardial ischemia",
            "ID": "4668599000002311011",
            "final_diagnosis": "Acute coronary syndrome",
            "visit_date": "27-Feb-2026",
            "status": "Ongoing"
        }
    ]
}