"""The two source documents in `references/`, transcribed.

Templates start blank so a new job is filled in from scratch. These are the
originals, seeded into the document list at startup so the real thing is
always on hand to read, copy from, or diff a render against.
"""

from .models import DocumentData
from .templates import COMPANY

REFERENCE_INVOICE = DocumentData(
    fields={
        **COMPANY,
        "doc_title": "ROOFING JOB INVOICE",
        "compliance": (
            "This form complies with professional standards in effect "
            "January 1-December 31, 2023"
        ),
        "invoice_number": "0213-245272",
        "invoice_date": "February, 2024",
        "job_id": "silvercreck",
        "job_location": "San Jose",
        "client_name": "Jeff Westererine",
        "project_address": "5272 Arezzo way",
        "project_city": "San Jose",
        "project_state_zip": "CA",
        "project_phone": "",
        "alt_address": "",
        "alt_city": "",
        "alt_state_zip": "Ca 91303",
        "alt_phone": "",
        "terms": "",
        "warranty_prefix": "this project is covered with",
        "warranty": "1yrs workmanship warranty",
        "summary_heading": "SUMMARY",
        "subtotal": "$8,094.00",
        "scheduled_payment": "7,244.00",
        "less_credits": "$850.00",
        "grand_total": "$7,244.00",
        "closing": "Thank You!",
    },
    checks={
        "down_payment": False,
        "progress_payment": False,
        "final_payment": True,
    },
    lists={
        "scope": [
            {"text": "hereby propose to furnish the following Roofing work:"},
            {"text": "#1 power wash entire roof $2,950.00"},
            {
                "text": "#2remove existing tiles from valleys walls and pipes and "
                "clean any loose debris so water can flow properly $1,950.00"
            },
            {"text": "Replace up to 10 broken tiles and re install falling tiles $450.00"},
            {
                "text": "Install rubber seal on all the plumbing pipes total of 12. "
                "Pipes$12.00each"
            },
            {
                "text": "Remove an area of 4x4\u2019on back side to replace damage plywood "
                "and install new plywood matching existing install new double "
                "underlyment and new batter system and inspect and install tile "
                "back $1,750.00"
            },
            {
                "text": "paint all flashing heating vents and plumbing vents and chimney "
                "at closes color of tile as closes possible"
            },
            {
                "text": "If at time we found any damage flashing ar any that we dont have "
                "and are estimate we will bring to yo attention so you can aproof "
                "any replacement or repairs as extra"
            },
            {"text": "Extra work we perform clean all gutters and seal"},
            {
                "text": "We found extra area were we use one plywood and one roll of felt "
                "and new batter system"
            },
        ],
        "summary": [
            {"label": "Replace broken tile and re install", "amount": "$450.00", "align": "right"},
            {"label": "install rubber seal an oil pipes", "amount": "$144.00", "align": "right"},
            {"label": "repair the area on the back", "amount": "$1,750.00", "align": "left"},
            {"label": "Power wash", "amount": "$2,950.00", "align": "left"},
            {"label": "Clean valleys and flashing", "amount": "$1,950.00", "align": "left"},
            {"label": "Extra work material and labor", "amount": "$850.00", "align": "left"},
            {"label": "", "amount": "", "align": "left"},
        ],
    },
)


REFERENCE_AGREEMENT = DocumentData(
    fields={
        **COMPANY,
        "doc_title_line1": "RESIDENTIAL ROOFING",
        "doc_title_line2": "AGREEMENT",
        "compliance": (
            "This form complies with professional standards in effect "
            "January 1-December 31, 2024"
        ),
        "agreement_date": "January  2024",
        "buyer_name": "Michaeal",
        "buyer_address": "3360 Ramona st",
        "buyer_city": "Palo Alto",
        "buyer_state_zip": "Ca",
        "buyer_phone": "",
        "alt_address": "",
        "alt_city": "",
        "alt_state_zip": "",
        "alt_phone": "",
        "project_address": "same",
        "project_city": "",
        "project_state": "",
        "project_zip": "",
        "legal_lot": "",
        "legal_tract": "",
        "legal_block": "",
        "legal_book": "",
        "legal_page": "",
        "legal_recorder": "",
        "legal_state": "State of California.",
        "warranty_prefix": "this project is covered with",
        "warranty": "5 yrs workmanship warranty",
        "not_included": "any unit that is not roofing materials and labor",
        "allowance_notes": "<Type and format text here >",
        "start_days": "",
        "start_days_num": "",
        "start_date": "",
        "complete_days": "",
        "complete_days_num": "",
        "complete_date": "",
        "price_words": "Forty four thousand and Two  hundred",
        "price_amount": "$44,200.00",
        "down_payment": "$1,000",
        "progress_schedule": (
            "The Schedule of Progress Payments will be:down paymant of $1,000.00 "
            "remaining$43,200.00\n"
            "When we install underlyment seccond payment of $12,960.00 remaining "
            "$30,240.00\n"
            " to order materials 3rd payment of  $9,072.00 remaining $21,168.00\n"
            "when instalation of panels  start  payment of $10,584.00 remaindimg "
            "$10,584.00\n"
            "when job is90% complete we ask for last progres payment of $6,000.00 "
            "remaining$4,584.00 for final payment  when job is compleate"
        ),
        "consists_of_pages": "",
        "consists_of_attachments": "",
        "owner_sig_date_1": "/24",
        "owner_sig_date_2": "/24",
    },
    checks={
        "space_insufficient": False,
        "plans_attached": False,
        "right_to_cancel": False,
    },
    lists={
        "scope": [
            {
                "text": "DESCRIPTION OF THE ROOFING PROJECT AND DESCRIPTION OF THE "
                "SIGNIFICANT MATERIALS TO BE USED AND EQUIPMENT TO BE INSTALLED:",
                "style": "bullet-bold",
            },
            {
                "text": "Install a layer of sharking self add ultra SA over entire roof "
                "area high temp rated",
                "style": "bullet",
            },
            {
                "text": "Install roof to wall flashings valleys ridges gables and all "
                "plumbing and heating vets 24G custom made Sheffield metal",
                "style": "bullet",
            },
            {
                "text": "Install 24 gauge Standing seam snap lock  With metal clips  color "
                "per owners request Sheffield metal(Dark Bronze",
                "style": "bullet",
            },
            {
                "text": "instal flashings on all chimneys and Skyligts were roof meet",
                "style": "bullet",
            },
            {"text": "Pain all flashing matching roof panels", "style": "bullet"},
            {
                "text": "Install gutters and  downspouts regular sizes 5.5\u201d 360\u2019with "
                "10 downspouts",
                "style": "bullet",
            },
            {
                "text": "12. Clean area of any debris and dump           /pull out city "
                "permit If apply/",
                "style": "plain",
            },
            {
                "text": "ANY EXTRA'S AT OWNER'S EXPENSE (If apply).  CITY FEES not INCLUDED",
                "style": "bullet",
            },
        ],
        "allowances": [
            {"desc1": "", "amt1": "", "desc2": "", "amt2": "", "desc3": "", "amt3": ""},
            {"desc1": "", "amt1": "", "desc2": "", "amt2": "", "desc3": "", "amt3": ""},
        ],
    },
    signatures={},
)


#: Fixed ids so a restart tops the list up instead of duplicating it.
REFERENCE_DOCUMENTS = [
    {
        "id": "reference-invoice",
        "template": "invoice",
        "title": "Reference \u2014 Roofing Job Invoice",
        "data": REFERENCE_INVOICE,
    },
    {
        "id": "reference-agreement",
        "template": "agreement",
        "title": "Reference \u2014 Residential Roofing Agreement",
        "data": REFERENCE_AGREEMENT,
    },
]
