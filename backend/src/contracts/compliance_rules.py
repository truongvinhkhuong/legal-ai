"""Hard-coded Vietnamese legal compliance rules.

All calculations are deterministic Python code — NEVER use LLM for math.
Constants are updated when laws change (reviewed via code PRs).
"""

from __future__ import annotations

from datetime import datetime

from src.api.models import ComplianceIssue, ComplianceLevel, ComplianceResult


# ---------------------------------------------------------------------------
# Legal constants (update per legal changes)
# ---------------------------------------------------------------------------

# Luong toi thieu vung — ND 74/2024/ND-CP, hieu luc tu 01/07/2024
MIN_WAGE_2024 = {
    "vung_1": 4_960_000,
    "vung_2": 4_410_000,
    "vung_3": 3_860_000,
    "vung_4": 3_450_000,
}

# BHXH rates — tu 01/07/2025
BHXH_RATES = {
    "employee": {"bhxh": 0.08, "bhyt": 0.015, "bhtn": 0.01},   # tong 10.5%
    "employer": {"bhxh": 0.175, "bhyt": 0.03, "bhtn": 0.01},   # tong 21.5%
}
BHXH_TOTAL_RATE = 0.32  # 32%

# Thoi gian thu viec — BLLD 2019 Dieu 25 Khoan 1
PROBATION_LIMITS = {
    "quan_ly": 180,      # Giam doc, Pho GD doanh nghiep — toi da 180 ngay
    "chuyen_mon": 60,    # Chuyen mon ky thuat cao dang tro len — toi da 60 ngay
    "trung_cap": 30,     # Trung cap, cong nhan ky thuat — toi da 30 ngay
    "khac": 6,           # Cong viec khac — toi da 6 ngay
}

# 10 noi dung bat buoc trong HDLD — BLLD 2019 Dieu 21 Khoan 1
HDLD_REQUIRED_FIELDS = [
    ("employer_name", "Ten nguoi su dung lao dong"),
    ("employer_address", "Dia chi nguoi su dung lao dong"),
    ("employer_representative", "Nguoi dai dien"),
    ("employee_name", "Ho ten nguoi lao dong"),
    ("employee_dob", "Ngay sinh"),
    ("employee_id_number", "So CCCD/CMND"),
    ("job_title", "Cong viec / chuc danh"),
    ("work_location", "Dia diem lam viec"),
    ("salary", "Muc luong"),
    ("hours_per_week", "Thoi gio lam viec"),
]

# Gio lam — BLLD 2019 Dieu 105
MAX_HOURS_PER_WEEK = 48
MAX_HOURS_PER_DAY = 8

# Thu viec — BLLD 2019 Dieu 26
PROBATION_SALARY_MIN_RATIO = 0.85  # Luong thu viec >= 85% luong chinh thuc


# ---------------------------------------------------------------------------
# Compliance Engine
# ---------------------------------------------------------------------------

class ComplianceEngine:
    """Check contract input data against Vietnamese labor and business laws."""

    def check_contract(
        self, template_key: str, input_data: dict, region: str
    ) -> ComplianceResult:
        """Route to appropriate checker based on template type."""
        checkers = {
            "hdld_xdth": self._check_hdld,
            "hdld_kxdth": self._check_hdld,
            "hd_thu_viec": self._check_thu_viec,
            "hd_thue_mat_bang": self._check_thue_mat_bang,
            "hd_dich_vu": self._check_dich_vu,
            "qd_cham_dut_hdld": self._check_generic,
            "bien_ban_vi_pham": self._check_generic,
        }
        checker = checkers.get(template_key, self._check_generic)
        return checker(input_data, region)

    def _check_hdld(self, data: dict, region: str) -> ComplianceResult:
        """Check HDLD against BLLD 2019 + ND 74/2024."""
        issues: list[ComplianceIssue] = []

        min_wage = MIN_WAGE_2024.get(region, MIN_WAGE_2024["vung_1"])

        # Rule: Luong >= luong toi thieu vung
        salary = data.get("salary")
        if salary is not None and salary > 0 and salary < min_wage:
            region_label = region.replace("_", " ").title()
            issues.append(ComplianceIssue(
                rule_id="MIN_WAGE",
                level=ComplianceLevel.error,
                field="salary",
                message_vi=f"Luong {salary:,.0f}d thap hon luong toi thieu {region_label} ({min_wage:,.0f}d)",
                legal_basis="ND 74/2024/ND-CP",
                suggested_value=str(min_wage),
            ))

        # Rule: Luong thu viec >= 85% luong chinh thuc
        probation_salary = data.get("probation_salary")
        if salary and probation_salary and probation_salary > 0:
            min_prob_salary = int(salary * PROBATION_SALARY_MIN_RATIO)
            if probation_salary < min_prob_salary:
                issues.append(ComplianceIssue(
                    rule_id="PROBATION_SALARY_85PCT",
                    level=ComplianceLevel.error,
                    field="probation_salary",
                    message_vi=f"Luong thu viec {probation_salary:,.0f}d thap hon 85% luong chinh thuc ({min_prob_salary:,.0f}d)",
                    legal_basis="BLLD 2019 Dieu 26",
                    suggested_value=str(min_prob_salary),
                ))

        # Rule: Thoi gian thu viec
        probation_days = data.get("probation_days")
        job_level = data.get("job_level", "khac")
        if probation_days and probation_days > 0:
            max_days = PROBATION_LIMITS.get(job_level, PROBATION_LIMITS["khac"])
            if probation_days > max_days:
                issues.append(ComplianceIssue(
                    rule_id="PROBATION_DURATION",
                    level=ComplianceLevel.error,
                    field="probation_days",
                    message_vi=f"Thoi gian thu viec {probation_days} ngay vuot qua muc toi da {max_days} ngay cho loai cong viec '{job_level}'",
                    legal_basis="BLLD 2019 Dieu 25 Khoan 1",
                    suggested_value=str(max_days),
                ))

        # Rule: Gio lam <= 48h/tuan
        hours = data.get("hours_per_week")
        if hours and hours > MAX_HOURS_PER_WEEK:
            issues.append(ComplianceIssue(
                rule_id="WORKING_HOURS_48",
                level=ComplianceLevel.error,
                field="hours_per_week",
                message_vi=f"So gio lam {hours}h/tuan vuot qua muc toi da {MAX_HOURS_PER_WEEK}h/tuan",
                legal_basis="BLLD 2019 Dieu 105",
                suggested_value=str(MAX_HOURS_PER_WEEK),
            ))

        # Rule: 10 noi dung bat buoc (Dieu 21)
        for field_key, label in HDLD_REQUIRED_FIELDS:
            val = data.get(field_key)
            if not val or (isinstance(val, str) and not val.strip()):
                issues.append(ComplianceIssue(
                    rule_id="HDLD_REQUIRED_FIELD",
                    level=ComplianceLevel.warning,
                    field=field_key,
                    message_vi=f"Thieu noi dung bat buoc: {label}",
                    legal_basis="BLLD 2019 Dieu 21 Khoan 1",
                ))

        return ComplianceResult(
            is_compliant=not any(i.level == ComplianceLevel.error for i in issues),
            issues=issues,
            checked_at=datetime.now().isoformat(),
        )

    def _check_thu_viec(self, data: dict, region: str) -> ComplianceResult:
        """Check HD thu viec — mostly same as HDLD but focused on probation rules."""
        issues: list[ComplianceIssue] = []
        min_wage = MIN_WAGE_2024.get(region, MIN_WAGE_2024["vung_1"])

        salary = data.get("salary")
        if salary and salary > 0 and salary < int(min_wage * PROBATION_SALARY_MIN_RATIO):
            issues.append(ComplianceIssue(
                rule_id="PROBATION_MIN_WAGE",
                level=ComplianceLevel.error,
                field="salary",
                message_vi=f"Luong thu viec {salary:,.0f}d thap hon 85% luong toi thieu vung ({int(min_wage * PROBATION_SALARY_MIN_RATIO):,.0f}d)",
                legal_basis="BLLD 2019 Dieu 26 + ND 74/2024",
                suggested_value=str(int(min_wage * PROBATION_SALARY_MIN_RATIO)),
            ))

        probation_days = data.get("probation_days")
        job_level = data.get("job_level", "khac")
        if probation_days:
            max_days = PROBATION_LIMITS.get(job_level, PROBATION_LIMITS["khac"])
            if probation_days > max_days:
                issues.append(ComplianceIssue(
                    rule_id="PROBATION_DURATION",
                    level=ComplianceLevel.error,
                    field="probation_days",
                    message_vi=f"Thu viec {probation_days} ngay vuot muc toi da {max_days} ngay",
                    legal_basis="BLLD 2019 Dieu 25 Khoan 1",
                    suggested_value=str(max_days),
                ))

        return ComplianceResult(
            is_compliant=not any(i.level == ComplianceLevel.error for i in issues),
            issues=issues,
            checked_at=datetime.now().isoformat(),
        )

    def _check_thue_mat_bang(self, data: dict, region: str) -> ComplianceResult:
        """Check HD thue mat bang — basic clause checks."""
        issues: list[ComplianceIssue] = []

        # Recommend essential clauses
        recommended = [
            ("rental_price", "Gia thue"),
            ("deposit_amount", "Tien dat coc"),
            ("rental_duration_months", "Thoi han thue"),
            ("payment_method", "Phuong thuc thanh toan"),
        ]
        for field_key, label in recommended:
            val = data.get(field_key)
            if not val or (isinstance(val, str) and not val.strip()):
                issues.append(ComplianceIssue(
                    rule_id="LEASE_RECOMMENDED_FIELD",
                    level=ComplianceLevel.warning,
                    field=field_key,
                    message_vi=f"Nen co dieu khoan: {label}",
                    legal_basis="Bo luat Dan su 2015 Dieu 472",
                ))

        # Deposit check: typically <= 3 months rent
        deposit = data.get("deposit_amount", 0)
        rent = data.get("rental_price", 0)
        if deposit and rent and deposit > rent * 3:
            issues.append(ComplianceIssue(
                rule_id="LEASE_HIGH_DEPOSIT",
                level=ComplianceLevel.warning,
                field="deposit_amount",
                message_vi=f"Tien dat coc ({deposit:,.0f}d) cao hon 3 thang tien thue. Can xem xet lai.",
                legal_basis="Thong le thi truong",
            ))

        return ComplianceResult(
            is_compliant=not any(i.level == ComplianceLevel.error for i in issues),
            issues=issues,
            checked_at=datetime.now().isoformat(),
        )

    def _check_dich_vu(self, data: dict, region: str) -> ComplianceResult:
        """Check HD dich vu — basic clause checks."""
        issues: list[ComplianceIssue] = []

        recommended = [
            ("service_description", "Mo ta dich vu"),
            ("service_fee", "Phi dich vu"),
            ("payment_terms", "Dieu khoan thanh toan"),
            ("service_duration", "Thoi han thuc hien"),
        ]
        for field_key, label in recommended:
            val = data.get(field_key)
            if not val or (isinstance(val, str) and not val.strip()):
                issues.append(ComplianceIssue(
                    rule_id="SERVICE_RECOMMENDED_FIELD",
                    level=ComplianceLevel.warning,
                    field=field_key,
                    message_vi=f"Nen co dieu khoan: {label}",
                    legal_basis="Bo luat Dan su 2015",
                ))

        return ComplianceResult(
            is_compliant=True,
            issues=issues,
            checked_at=datetime.now().isoformat(),
        )

    def _check_generic(self, data: dict, region: str) -> ComplianceResult:
        """Generic check — no specific rules, just return compliant."""
        return ComplianceResult(
            is_compliant=True,
            issues=[],
            checked_at=datetime.now().isoformat(),
        )
