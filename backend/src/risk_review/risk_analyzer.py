"""Contract risk analyzer — deterministic rules + LLM semantic analysis.

3-pass approach:
1. Legal violations: keyword + LLM detection
2. Missing clauses: keyword match against required clause list
3. Unfair terms: LLM identification of one-sided clauses
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import openai

from src.config.settings import settings
from src.risk_review.risk_rules import RISK_RULES, RiskRule

logger = logging.getLogger(__name__)


@dataclass
class RiskIssue:
    rule_id: str
    category: str       # "vi_pham" | "thieu" | "bat_loi"
    severity: str       # "high" | "medium" | "low"
    title_vi: str
    description_vi: str
    legal_basis: str
    matched_clause: str = ""
    suggestion_vi: str = ""


@dataclass
class RiskReport:
    contract_type: str
    risk_score: int          # 1-10, higher = safer
    total_rules: int
    issues_count: int
    high_count: int
    medium_count: int
    low_count: int
    summary_vi: str = ""
    issues: list[RiskIssue] = field(default_factory=list)


def _normalize(text: str) -> str:
    return text.lower().replace("\n", " ").replace("\r", " ")


def _keyword_found(text_normalized: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        if kw.lower() in text_normalized:
            return kw
    return None


async def analyze_risk(
    file_content: str,
    contract_type: str,
) -> RiskReport:
    """Analyze contract risks using deterministic rules + optional LLM."""
    rules = RISK_RULES.get(contract_type, RISK_RULES.get("chung", []))
    text_normalized = _normalize(file_content)

    issues: list[RiskIssue] = []
    llm_rules: list[RiskRule] = []

    # Pass 1 & 2: keyword-based checks
    for rule in rules:
        if rule.check_type == "keyword":
            found = _keyword_found(text_normalized, rule.keywords)
            if not found:
                # Missing clause
                issues.append(RiskIssue(
                    rule_id=rule.rule_id,
                    category=rule.category,
                    severity=rule.severity,
                    title_vi=rule.title_vi,
                    description_vi=rule.description_vi,
                    legal_basis=rule.legal_basis,
                    suggestion_vi=f"Bổ sung: {rule.description_vi}",
                ))
        elif rule.check_type in ("llm", "numeric"):
            llm_rules.append(rule)

    # Pass 3: LLM analysis for complex rules
    if llm_rules and settings.deepseek_api_key:
        try:
            llm_issues = await _llm_risk_analysis(file_content, llm_rules)
            issues.extend(llm_issues)
        except Exception:
            logger.warning("LLM risk analysis failed", exc_info=True)
            # Fall back: flag all LLM rules as needing manual review
            for rule in llm_rules:
                issues.append(RiskIssue(
                    rule_id=rule.rule_id,
                    category=rule.category,
                    severity=rule.severity,
                    title_vi=rule.title_vi,
                    description_vi=rule.description_vi,
                    legal_basis=rule.legal_basis,
                    suggestion_vi="Cần kiểm tra thủ công",
                ))

    # Calculate risk score (1-10, 10 = safest)
    high_count = sum(1 for i in issues if i.severity == "high")
    medium_count = sum(1 for i in issues if i.severity == "medium")
    low_count = sum(1 for i in issues if i.severity == "low")

    penalty = high_count * 2.5 + medium_count * 1.0 + low_count * 0.3
    risk_score = max(1, min(10, round(10 - penalty)))

    summary = _build_summary(risk_score, high_count, medium_count, low_count, len(issues))

    return RiskReport(
        contract_type=contract_type,
        risk_score=risk_score,
        total_rules=len(rules),
        issues_count=len(issues),
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        summary_vi=summary,
        issues=issues,
    )


def _build_summary(score: int, high: int, medium: int, low: int, total: int) -> str:
    if score >= 8:
        level = "Hợp đồng tương đối an toàn"
    elif score >= 5:
        level = "Hợp đồng có một số rủi ro cần lưu ý"
    else:
        level = "Hợp đồng có nhiều rủi ro nghiêm trọng"

    parts = []
    if high > 0:
        parts.append(f"{high} vấn đề nghiêm trọng")
    if medium > 0:
        parts.append(f"{medium} vấn đề trung bình")
    if low > 0:
        parts.append(f"{low} lưu ý nhỏ")

    detail = ", ".join(parts) if parts else "không phát hiện vấn đề"
    return f"{level}. Phát hiện {total} vấn đề: {detail}."


async def _llm_risk_analysis(
    doc_text: str,
    rules: list[RiskRule],
) -> list[RiskIssue]:
    """Use LLM to check complex risk rules (violations, unfair terms)."""
    doc_excerpt = doc_text[:6000]

    rules_desc = "\n".join(
        f"- {r.rule_id}: {r.title_vi} — {r.description_vi} (co so phap ly: {r.legal_basis})"
        for r in rules
    )

    prompt = f"""\
Phan tich hop dong sau de kiem tra cac rui ro phap ly:

Hop dong:
\"\"\"
{doc_excerpt}
\"\"\"

Cac rui ro can kiem tra:
{rules_desc}

Voi moi rui ro, tra ve:
- "rule_id": ma rui ro
- "found": true neu phat hien vi pham hoac van de, false neu khong co van de
- "matched_clause": trich doan lien quan trong hop dong (toi da 150 ky tu)
- "explanation": giai thich ngan (toi da 100 ky tu)

Chi tra ve JSON array, khong giai thich them.
"""

    client = openai.AsyncOpenAI(
        base_url=settings.deepseek_base_url,
        api_key=settings.deepseek_api_key,
    )

    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=800,
    )

    raw = response.choices[0].message.content or "[]"
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    results = json.loads(raw)

    # Build lookup
    rule_map = {r.rule_id: r for r in rules}
    issues: list[RiskIssue] = []

    for r in results:
        rid = r.get("rule_id", "")
        if rid in rule_map and r.get("found", False):
            rule = rule_map[rid]
            issues.append(RiskIssue(
                rule_id=rid,
                category=rule.category,
                severity=rule.severity,
                title_vi=rule.title_vi,
                description_vi=r.get("explanation", rule.description_vi)[:200],
                legal_basis=rule.legal_basis,
                matched_clause=r.get("matched_clause", "")[:200],
                suggestion_vi=f"Xem xét lại: {rule.title_vi}",
            ))

    return issues
