"""Hard-coded risk rules for Vietnamese contract types.

Rules are categorized as:
- vi_pham: legal violations (exceeds legal limits)
- thieu: missing required/recommended clauses
- bat_loi: unfairly one-sided terms
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskRule:
    rule_id: str
    category: str  # "vi_pham" | "thieu" | "bat_loi"
    title_vi: str
    description_vi: str
    check_type: str  # "keyword" | "llm" | "numeric"
    keywords: list[str] = field(default_factory=list)
    legal_basis: str = ""
    severity: str = "high"  # "high" | "medium" | "low"


# ---------------------------------------------------------------------------
# Lease (hd_thue_mat_bang) rules
# ---------------------------------------------------------------------------

LEASE_RULES: list[RiskRule] = [
    RiskRule(
        rule_id="lease_penalty_30pct",
        category="vi_pham",
        title_vi="Mức phạt vi phạm vượt 30%",
        description_vi="Mức phạt vi phạm hợp đồng không được vượt 30% giá trị phần nghĩa vụ vi phạm",
        check_type="llm",
        keywords=["phat vi pham", "phạt vi phạm", "phat", "boi thuong"],
        legal_basis="BLDS 2015 Điều 418 Khoản 2",
        severity="high",
    ),
    RiskRule(
        rule_id="lease_force_majeure",
        category="thieu",
        title_vi="Thiếu điều khoản bất khả kháng",
        description_vi="Hợp đồng nên có điều khoản về sự kiện bất khả kháng",
        check_type="keyword",
        keywords=["bat kha khang", "bất khả kháng", "force majeure",
                   "su kien bat kha khang", "sự kiện bất khả kháng"],
        legal_basis="BLDS 2015 Điều 156",
        severity="medium",
    ),
    RiskRule(
        rule_id="lease_deposit_limit",
        category="vi_pham",
        title_vi="Đặt cọc quá cao",
        description_vi="Tiền đặt cọc thông thường không vượt 3 tháng tiền thuê",
        check_type="llm",
        keywords=["dat coc", "đặt cọc", "tien coc"],
        legal_basis="Thông lệ thị trường",
        severity="medium",
    ),
    RiskRule(
        rule_id="lease_term_renewal",
        category="thieu",
        title_vi="Thiếu điều khoản gia hạn",
        description_vi="Nên quy định rõ điều kiện và thời hạn gia hạn hợp đồng",
        check_type="keyword",
        keywords=["gia han", "gia hạn", "tai ky", "tái ký", "renew"],
        legal_basis="BLDS 2015 Điều 472",
        severity="low",
    ),
    RiskRule(
        rule_id="lease_dispute_resolution",
        category="thieu",
        title_vi="Thiếu điều khoản giải quyết tranh chấp",
        description_vi="Hợp đồng nên quy định phương thức giải quyết tranh chấp",
        check_type="keyword",
        keywords=["tranh chap", "tranh chấp", "giai quyet", "giải quyết",
                   "trong tai", "trọng tài", "toa an", "tòa án"],
        legal_basis="BLDS 2015 Điều 14",
        severity="medium",
    ),
]


# ---------------------------------------------------------------------------
# Service (hd_dich_vu) rules
# ---------------------------------------------------------------------------

SERVICE_RULES: list[RiskRule] = [
    RiskRule(
        rule_id="svc_payment_terms",
        category="thieu",
        title_vi="Thiếu điều khoản thanh toán chi tiết",
        description_vi="Nên quy định rõ thời hạn, phương thức, điều kiện thanh toán",
        check_type="keyword",
        keywords=["thanh toan", "thanh toán", "payment", "tra tien", "trả tiền"],
        legal_basis="BLDS 2015 Điều 398",
        severity="medium",
    ),
    RiskRule(
        rule_id="svc_liability_cap",
        category="bat_loi",
        title_vi="Không giới hạn trách nhiệm bồi thường",
        description_vi="Hợp đồng dịch vụ nên quy định giới hạn mức bồi thường tối đa",
        check_type="keyword",
        keywords=["gioi han trach nhiem", "giới hạn trách nhiệm", "muc boi thuong",
                   "mức bồi thường", "liability"],
        legal_basis="BLDS 2015 Điều 360",
        severity="medium",
    ),
    RiskRule(
        rule_id="svc_ip_ownership",
        category="thieu",
        title_vi="Thiếu điều khoản sở hữu trí tuệ",
        description_vi="Nên quy định rõ quyền sở hữu kết quả công việc, sở hữu trí tuệ",
        check_type="keyword",
        keywords=["so huu tri tue", "sở hữu trí tuệ", "ban quyen", "bản quyền",
                   "quyen so huu", "quyền sở hữu"],
        legal_basis="Luật SHTT 2005",
        severity="low",
    ),
    RiskRule(
        rule_id="svc_confidentiality",
        category="thieu",
        title_vi="Thiếu điều khoản bảo mật",
        description_vi="Hợp đồng dịch vụ nên có điều khoản bảo mật thông tin",
        check_type="keyword",
        keywords=["bao mat", "bảo mật", "bi mat", "bí mật", "confidential"],
        legal_basis="BLDS 2015 Điều 387",
        severity="medium",
    ),
    RiskRule(
        rule_id="svc_force_majeure",
        category="thieu",
        title_vi="Thiếu điều khoản bất khả kháng",
        description_vi="Hợp đồng nên có điều khoản về sự kiện bất khả kháng",
        check_type="keyword",
        keywords=["bat kha khang", "bất khả kháng", "force majeure"],
        legal_basis="BLDS 2015 Điều 156",
        severity="medium",
    ),
    RiskRule(
        rule_id="svc_dispute",
        category="thieu",
        title_vi="Thiếu điều khoản giải quyết tranh chấp",
        description_vi="Nên quy định phương thức giải quyết tranh chấp",
        check_type="keyword",
        keywords=["tranh chap", "tranh chấp", "trong tai", "trọng tài",
                   "toa an", "tòa án"],
        legal_basis="BLDS 2015 Điều 14",
        severity="medium",
    ),
]


# ---------------------------------------------------------------------------
# General rules (apply to all contract types)
# ---------------------------------------------------------------------------

GENERAL_RULES: list[RiskRule] = [
    RiskRule(
        rule_id="gen_governing_law",
        category="thieu",
        title_vi="Thiếu điều khoản luật áp dụng",
        description_vi="Hợp đồng nên ghi rõ luật áp dụng (pháp luật Việt Nam)",
        check_type="keyword",
        keywords=["luat ap dung", "luật áp dụng", "phap luat viet nam",
                   "pháp luật việt nam", "governing law"],
        legal_basis="BLDS 2015 Điều 398",
        severity="low",
    ),
    RiskRule(
        rule_id="gen_termination",
        category="thieu",
        title_vi="Thiếu điều khoản chấm dứt hợp đồng",
        description_vi="Nên quy định rõ các trường hợp và thủ tục chấm dứt",
        check_type="keyword",
        keywords=["cham dut", "chấm dứt", "huy bo", "hủy bỏ",
                   "don phuong", "đơn phương", "termination"],
        legal_basis="BLDS 2015 Điều 422-428",
        severity="medium",
    ),
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

RISK_RULES: dict[str, list[RiskRule]] = {
    "thue_mat_bang": LEASE_RULES + GENERAL_RULES,
    "dich_vu": SERVICE_RULES + GENERAL_RULES,
    "chung": GENERAL_RULES,
}

CONTRACT_TYPE_LABELS: dict[str, str] = {
    "thue_mat_bang": "Hợp đồng thuê mặt bằng",
    "dich_vu": "Hợp đồng dịch vụ",
    "chung": "Hợp đồng chung",
}
