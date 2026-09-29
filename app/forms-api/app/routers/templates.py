from fastapi import APIRouter, HTTPException

from ..models import TemplateInfo
from ..templates import TEMPLATES, get_template

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateInfo])
def list_templates() -> list[TemplateInfo]:
    return [get_template(template_id) for template_id in TEMPLATES]


@router.get("/{template_id}", response_model=TemplateInfo)
def read_template(template_id: str) -> TemplateInfo:
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown template")
    return get_template(template_id)
