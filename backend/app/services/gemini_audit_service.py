import json
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.schemas.hardware import (
    InventoryAuditAiSummary,
    InventoryAuditFinding,
    InventoryAuditSummary,
)

ISSUE_ACTION_MAP = {
    "FUTURE_PURCHASE_DATE": "Review items with future purchase dates and correct the source data before issuing them.",
    "INVALID_STATUS": "Fix invalid inventory statuses so the rental workflow can rely on clean state transitions.",
    "SAFETY_NOTE_BLOCK": "Review safety-blocked items and keep them unavailable until an admin confirms they are safe to issue.",
    "MALFORMED_PURCHASE_DATE": "Normalize malformed purchase dates to the YYYY-MM-DD format.",
    "MISSING_BRAND": "Fill in missing brand values to improve filtering and audit accuracy.",
    "MISSING_PURCHASE_DATE": "Backfill missing purchase dates where the source record is incomplete.",
    "DAMAGE_HISTORY": "Inspect devices with damage-related history before allowing them back into normal circulation.",
    "SUSPICIOUS_BRAND": "Review suspicious brand spellings and normalize obvious typos.",
    "DUPLICATE_SEED_ID_SKIPPED": "Document or clean duplicate source IDs so future imports are deterministic and easier to audit.",
}


class GeminiAuditStructuredResponse(BaseModel):
    risk_level: Literal["high", "medium", "low"]
    summary_text: str
    priority_actions: list[str]


def infer_risk_level(summary: InventoryAuditSummary) -> str:
    if summary.high_severity_count > 0:
        return "high"
    if summary.medium_severity_count > 0:
        return "medium"
    return "low"


def build_fallback_priority_actions(
    findings: list[InventoryAuditFinding],
) -> list[str]:
    actions: list[str] = []

    for finding in findings:
        action = ISSUE_ACTION_MAP.get(finding.issue_code)
        if action and action not in actions:
            actions.append(action)

        if len(actions) == 3:
            break

    if actions:
        return actions

    return ["No urgent admin actions were identified by the deterministic audit."]


def build_fallback_summary(
    summary: InventoryAuditSummary,
    findings: list[InventoryAuditFinding],
    error_message: str,
) -> InventoryAuditAiSummary:
    risk_level = infer_risk_level(summary)
    priority_actions = build_fallback_priority_actions(findings)

    if summary.total_findings == 0:
        summary_text = (
            "Deterministic audit completed without findings. Inventory currently "
            "looks clean based on the implemented validation rules."
        )
    else:
        summary_text = (
            "Gemini summary is unavailable, so this response falls back to a "
            "deterministic overview. Review the high-severity findings first, then "
            "work through medium-severity data quality issues."
        )

    return InventoryAuditAiSummary(
        provider="gemini",
        model=settings.gemini_model,
        fallback_used=True,
        risk_level=risk_level,  # type: ignore[arg-type]
        summary_text=summary_text,
        priority_actions=priority_actions,
        error_message=error_message,
    )


def build_prompt(
    summary: InventoryAuditSummary,
    findings: list[InventoryAuditFinding],
) -> str:
    findings_payload = [
        {
            "hardware_id": finding.hardware_id,
            "hardware_name": finding.hardware_name,
            "issue_code": finding.issue_code,
            "severity": finding.severity,
            "message": finding.message,
        }
        for finding in findings
    ]

    summary_payload = {
        "total_items": summary.total_items,
        "total_findings": summary.total_findings,
        "high_severity_count": summary.high_severity_count,
        "medium_severity_count": summary.medium_severity_count,
        "low_severity_count": summary.low_severity_count,
    }

    return f"""
You are helping an admin review an internal hardware inventory audit.

Use the deterministic audit data below as the source of truth.
Do not invent new findings.
Do not contradict the deterministic findings.
Prioritize safety and operational risk over cosmetic data issues.
Always list all high-severity findings before medium-severity findings in priority_actions.

Return:
- risk_level as high, medium, or low
- summary_text as 2 to 4 sentences
- exactly 3 priority_actions focused on admin next steps

Deterministic summary:
{json.dumps(summary_payload, ensure_ascii=False)}

Deterministic findings:
{json.dumps(findings_payload, ensure_ascii=False)}
""".strip()


def summarize_inventory_audit(
    summary: InventoryAuditSummary,
    findings: list[InventoryAuditFinding],
) -> InventoryAuditAiSummary:
    if not settings.gemini_api_key:
        return build_fallback_summary(
            summary,
            findings,
            "Gemini API key is not configured.",
        )

    prompt = build_prompt(summary, findings)

    try:
        with genai.Client(api_key=settings.gemini_api_key) as client:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiAuditStructuredResponse,
                ),
            )

        parsed_response = response.parsed

        if parsed_response is None:
            raise ValueError("Gemini returned no parsed structured response.")

        if isinstance(parsed_response, GeminiAuditStructuredResponse):
            parsed = parsed_response
        else:
            parsed = GeminiAuditStructuredResponse.model_validate(parsed_response)

        priority_actions = [
            action.strip()
            for action in parsed.priority_actions
            if isinstance(action, str) and action.strip()
        ][:3]

        if not priority_actions:
            raise ValueError("Gemini returned no usable priority actions.")

        return InventoryAuditAiSummary(
            provider="gemini",
            model=settings.gemini_model,
            fallback_used=False,
            risk_level=parsed.risk_level,
            summary_text=parsed.summary_text.strip(),
            priority_actions=priority_actions,
            error_message=None,
        )
    except Exception as exc:
        return build_fallback_summary(summary, findings, str(exc))