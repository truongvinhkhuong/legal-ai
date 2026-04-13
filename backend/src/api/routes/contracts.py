"""Contract drafting API: templates, compliance validation, CRUD, export."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models import (
    ComplianceResult,
    ContractCreateRequest,
    ContractDetail,
    ContractListItem,
    ContractResponse,
    ContractValidateRequest,
    FormStep,
    TemplateDetail,
    TemplateListItem,
)
from src.config.database import get_db
from src.contracts.compliance_rules import ComplianceEngine
from src.contracts.export_engine import to_docx, to_pdf
from src.contracts.form_schemas import TEMPLATE_FORM_SCHEMAS, TEMPLATE_METADATA
from src.contracts.template_engine import TemplateEngine
from src.db.models.contract import Contract, ContractTemplate

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

# Singletons
_template_engine = TemplateEngine()
_compliance_engine = ComplianceEngine()


# ---------------------------------------------------------------------------
# Template endpoints
# ---------------------------------------------------------------------------

@router.get("/templates")
async def list_templates() -> list[TemplateListItem]:
    """List all available contract templates."""
    return [
        TemplateListItem(
            template_key=key,
            name_vi=meta["name_vi"],
            description_vi=meta["description_vi"],
            category=meta["category"],
        )
        for key, meta in TEMPLATE_METADATA.items()
    ]


@router.get("/templates/{template_key}")
async def get_template_detail(template_key: str) -> TemplateDetail:
    """Get template detail including form wizard steps."""
    meta = TEMPLATE_METADATA.get(template_key)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Template '{template_key}' not found")

    steps = TEMPLATE_FORM_SCHEMAS.get(template_key, [])

    return TemplateDetail(
        template_key=template_key,
        name_vi=meta["name_vi"],
        description_vi=meta["description_vi"],
        category=meta["category"],
        form_steps=steps,
    )


# ---------------------------------------------------------------------------
# Compliance validation
# ---------------------------------------------------------------------------

@router.post("/validate")
async def validate_contract(req: ContractValidateRequest) -> ComplianceResult:
    """Validate contract input data against compliance rules.

    Called per wizard step for real-time feedback.
    """
    return _compliance_engine.check_contract(
        template_key=req.template_key.value,
        input_data=req.input_data,
        region=req.region.value,
    )


# ---------------------------------------------------------------------------
# Contract CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=ContractResponse)
async def create_contract(
    req: ContractCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """Create a new contract: render template + compliance check + save."""
    template_key = req.template_key.value

    if not _template_engine.template_exists(template_key):
        raise HTTPException(status_code=400, detail=f"Template '{template_key}' not found")

    # Render contract
    rendered = _template_engine.render(template_key, req.input_data)

    # Compliance check
    compliance = _compliance_engine.check_contract(
        template_key=template_key,
        input_data=req.input_data,
        region=req.region.value,
    )

    # Find or create template row in DB
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.template_key == template_key)
    )
    tpl = result.scalar_one_or_none()
    if not tpl:
        meta = TEMPLATE_METADATA[template_key]
        tpl = ContractTemplate(
            template_key=template_key,
            name_vi=meta["name_vi"],
            description_vi=meta["description_vi"],
            category=meta["category"],
        )
        db.add(tpl)
        await db.flush()

    # Determine title
    title = req.title
    if not title:
        meta = TEMPLATE_METADATA.get(template_key, {})
        employee = req.input_data.get("employee_name", "")
        title = f"{meta.get('name_vi', template_key)}"
        if employee:
            title += f" — {employee}"

    # Create contract record
    contract = Contract(
        tenant_id=tpl.id,  # Simplified: use template id as tenant for now
        template_id=tpl.id,
        title=title,
        status="draft",
        input_data=req.input_data,
        rendered_content=rendered,
        compliance_result=compliance.model_dump(),
    )
    db.add(contract)
    await db.flush()

    return ContractResponse(
        contract_id=str(contract.id),
        status=contract.status,
        rendered_content=rendered,
        compliance=compliance,
        created_at=contract.created_at.isoformat() if contract.created_at else "",
    )


@router.get("/", response_model=list[ContractListItem])
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    status: str | None = None,
    template_key: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ContractListItem]:
    """List user's contracts."""
    query = (
        select(Contract)
        .join(ContractTemplate)
        .order_by(Contract.created_at.desc())
    )

    if status:
        query = query.where(Contract.status == status)
    if template_key:
        query = query.where(ContractTemplate.template_key == template_key)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    contracts = result.scalars().all()

    return [
        ContractListItem(
            contract_id=str(c.id),
            template_key=c.template.template_key,
            title=c.title,
            status=c.status,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in contracts
    ]


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContractDetail:
    """Get contract detail by ID."""
    contract = await db.get(Contract, uuid.UUID(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Load template relationship
    tpl = await db.get(ContractTemplate, contract.template_id)

    compliance = None
    if contract.compliance_result:
        compliance = ComplianceResult(**contract.compliance_result)

    return ContractDetail(
        contract_id=str(contract.id),
        template_key=tpl.template_key if tpl else "",
        title=contract.title,
        status=contract.status,
        input_data=contract.input_data,
        rendered_content=contract.rendered_content,
        compliance=compliance,
        version=contract.version,
        created_at=contract.created_at.isoformat() if contract.created_at else "",
        updated_at=contract.updated_at.isoformat() if contract.updated_at else "",
    )


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: str,
    req: ContractCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """Update a contract: re-render + re-check compliance."""
    contract = await db.get(Contract, uuid.UUID(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    template_key = req.template_key.value

    # Re-render
    rendered = _template_engine.render(template_key, req.input_data)

    # Re-check compliance
    compliance = _compliance_engine.check_contract(
        template_key=template_key,
        input_data=req.input_data,
        region=req.region.value,
    )

    # Update contract
    contract.input_data = req.input_data
    contract.rendered_content = rendered
    contract.compliance_result = compliance.model_dump()
    contract.version += 1
    if req.title:
        contract.title = req.title

    return ContractResponse(
        contract_id=str(contract.id),
        status=contract.status,
        rendered_content=rendered,
        compliance=compliance,
        created_at=contract.created_at.isoformat() if contract.created_at else "",
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/{contract_id}/export")
async def export_contract(
    contract_id: str,
    format: str = "pdf",
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export contract as PDF or DOCX."""
    contract = await db.get(Contract, uuid.UUID(contract_id))
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if format == "docx":
        content = to_docx(contract.rendered_content, title=contract.title)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="contract_{contract_id[:8]}.docx"'},
        )
    elif format == "pdf":
        content = to_pdf(contract.rendered_content, title=contract.title)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="contract_{contract_id[:8]}.pdf"'},
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use 'pdf' or 'docx'.")
