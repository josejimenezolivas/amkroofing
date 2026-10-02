"""Template registry.

A new document carries only the parts of the form that are the same every
time: the letterhead, the printed headings and the standing legal wording.
Everything specific to a client or a job starts empty so the editor shows a
placeholder to fill in. Placeholders are screen-only, so a half-filled form
still exports cleanly.
"""

from datetime import date

from .models import DocumentData, TemplateInfo

#: AMK's own details, which head every document.
COMPANY = {
    "company_email": "amkroofing@amkroofing.com",
    "company_name": "AMK ROOFING",
    "company_license": "C-39 863875",
    "company_street": "184 TALMADGE AVE",
    "company_city": "SAN JOSE CA 95127",
    "company_phone": "PHONE/FAX (408) 937-6972",
    "company_cell": "CELL (408) 591-0733",
}


def compliance() -> str:
    """The standing compliance line, for the calendar year a form is drawn up in."""
    return (
        "This form complies with professional standards in effect "
        f"January 1-December 31, {date.today().year}"
    )


def _blanks(*names: str) -> dict[str, str]:
    return {name: "" for name in names}


INVOICE_DEFAULTS = DocumentData(
    fields={
        **COMPANY,
        "doc_title": "ROOFING JOB INVOICE",
        "summary_heading": "SUMMARY",
        "warranty_prefix": "this project is covered with",
        "closing": "Thank You!",
        **_blanks(
            "invoice_number",
            "invoice_date",
            "job_id",
            "job_location",
            "client_name",
            "project_address",
            "project_city",
            "project_state_zip",
            "project_phone",
            "alt_address",
            "alt_city",
            "alt_state_zip",
            "alt_phone",
            "terms",
            "warranty",
            "subtotal",
            "scheduled_payment",
            "less_credits",
            "grand_total",
        ),
    },
    checks={
        "down_payment": False,
        "progress_payment": False,
        "final_payment": False,
    },
    lists={
        "scope": [{"text": ""} for _ in range(3)],
        # Seven rows because that is how many the printed grid has: the short
        # divider inside the box is placed against that count.
        "summary": [{"label": "", "amount": "", "align": "left"} for _ in range(7)],
    },
)


AGREEMENT_DEFAULTS = DocumentData(
    fields={
        **COMPANY,
        "doc_title_line1": "RESIDENTIAL ROOFING",
        "doc_title_line2": "AGREEMENT",
        "warranty_prefix": "this project is covered with",
        "legal_state": "State of California.",
        **_blanks(
            "agreement_date",
            "buyer_name",
            "buyer_address",
            "buyer_city",
            "buyer_state_zip",
            "buyer_phone",
            "alt_address",
            "alt_city",
            "alt_state_zip",
            "alt_phone",
            "project_address",
            "project_city",
            "project_state",
            "project_zip",
            "legal_lot",
            "legal_tract",
            "legal_block",
            "legal_book",
            "legal_page",
            "legal_recorder",
            "warranty",
            "not_included",
            "allowance_notes",
            "start_days",
            "start_days_num",
            "start_date",
            "complete_days",
            "complete_days_num",
            "complete_date",
            "price_words",
            "price_amount",
            "down_payment",
            "progress_schedule",
            "consists_of_pages",
            "consists_of_attachments",
            "owner_sig_date_1",
            "owner_sig_date_2",
        ),
    },
    checks={
        "space_insufficient": False,
        "plans_attached": False,
        "right_to_cancel": False,
    },
    lists={
        # The first line is the form's own printed heading, not job detail.
        "scope": [
            {
                "text": "DESCRIPTION OF THE ROOFING PROJECT AND DESCRIPTION OF THE "
                "SIGNIFICANT MATERIALS TO BE USED AND EQUIPMENT TO BE INSTALLED:",
                "style": "bullet-bold",
            },
            *({"text": "", "style": "bullet"} for _ in range(4)),
        ],
        "allowances": [
            {"desc1": "", "amt1": "", "desc2": "", "amt2": "", "desc3": "", "amt3": ""}
            for _ in range(2)
        ],
    },
    signatures={},
)


TEMPLATES: dict[str, TemplateInfo] = {
    "invoice": TemplateInfo(
        id="invoice",
        name="Roofing Job Invoice",
        description="Single-page itemized invoice with scope of work and summary table.",
        pages=1,
        defaults=INVOICE_DEFAULTS,
    ),
    "agreement": TemplateInfo(
        id="agreement",
        name="Residential Roofing Agreement",
        description="Seven-page contract with payment schedule, signatures and terms.",
        pages=7,
        defaults=AGREEMENT_DEFAULTS,
    ),
}


def get_template(template_id: str) -> TemplateInfo:
    """A template whose defaults are dated today, never the day the server started."""
    template = TEMPLATES[template_id]
    defaults = template.defaults.model_copy(deep=True)
    defaults.fields["compliance"] = compliance()
    return template.model_copy(update={"defaults": defaults})


#: Filled in as the owners sign, alongside the drawn signatures.
SIGNING_DATES = ("owner_sig_date_1", "owner_sig_date_2")


def copy_data(data: DocumentData) -> DocumentData:
    """A copy is a new document: unsigned, and dated this year."""
    copy = data.model_copy(deep=True)
    copy.signatures = {}
    for name in SIGNING_DATES:
        if name in copy.fields:
            copy.fields[name] = ""
    if "compliance" in copy.fields:
        copy.fields["compliance"] = compliance()
    return copy


def copy_title(title: str) -> str:
    return f"{title} (copy)"


def default_title(template_id: str, data: DocumentData) -> str:
    """Name a document after its client and project address."""
    if template_id == "invoice":
        who = data.fields.get("client_name") or "Untitled"
        where = data.fields.get("project_address") or ""
    else:
        who = data.fields.get("buyer_name") or "Untitled"
        where = data.fields.get("buyer_address") or ""
    return f"{who} \u2014 {where}".strip(" \u2014") or "Untitled"
