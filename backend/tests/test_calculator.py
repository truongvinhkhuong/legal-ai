"""Tests for pure Python tax/BHXH/TNCN calculator — no external dependencies."""

from __future__ import annotations

import pytest

from src.calculator.tax_rules import (
    calculate_bhxh,
    calculate_ho_kinh_doanh,
    calculate_tncn,
)


# ---------------------------------------------------------------------------
# Tax (ho kinh doanh)
# ---------------------------------------------------------------------------

class TestHoKinhDoanhTax:
    def test_dich_vu_rates(self):
        """Dich vu: VAT 5%, TNCN 2% → total 7%."""
        result = calculate_ho_kinh_doanh(100_000_000, "dich_vu")
        assert result.vat_rate == 0.05
        assert result.tncn_rate == 0.02
        assert result.vat_amount == 5_000_000
        assert result.tncn_amount == 2_000_000
        assert result.total_tax == 7_000_000

    def test_thuong_mai_rates(self):
        """Thuong mai: VAT 1%, TNCN 0.5%."""
        result = calculate_ho_kinh_doanh(200_000_000, "thuong_mai")
        assert result.vat_rate == 0.01
        assert result.tncn_rate == 0.005
        assert result.total_tax == 3_000_000  # 2M + 1M

    def test_san_xuat_rates(self):
        """San xuat: VAT 3%, TNCN 1.5%."""
        result = calculate_ho_kinh_doanh(50_000_000, "san_xuat")
        assert result.vat_rate == 0.03
        assert result.tncn_rate == 0.015
        assert result.total_tax == 2_250_000

    def test_zero_revenue(self):
        result = calculate_ho_kinh_doanh(0, "dich_vu")
        assert result.total_tax == 0

    def test_effective_rate(self):
        result = calculate_ho_kinh_doanh(100_000_000, "dich_vu")
        assert result.effective_rate == pytest.approx(0.07, abs=0.001)


# ---------------------------------------------------------------------------
# BHXH
# ---------------------------------------------------------------------------

class TestBHXH:
    def test_basic_calculation(self):
        """Basic BHXH calculation with 10M salary."""
        result = calculate_bhxh(10_000_000, 1, "vung_1")
        assert result.luong_dong_bhxh == 10_000_000
        assert result.so_nhan_vien == 1
        # Employee pays: BHXH 8% + BHYT 1.5% + BHTN 1% = 10.5%
        assert result.total_employee == 1_050_000
        # Employer pays: BHXH 17.5% + BHYT 3% + BHTN 1% = 21.5%
        assert result.total_employer == 2_150_000

    def test_salary_cap(self):
        """Salary above 20x base salary (luong co so) should be capped."""
        # luong co so 2024 = 2,340,000 → cap = 20 * 2,340,000 = 46,800,000
        result = calculate_bhxh(200_000_000, 1, "vung_1")
        assert result.luong_dong_bhxh_cap < 200_000_000
        assert result.luong_dong_bhxh_cap == 46_800_000

    def test_multiple_employees(self):
        """Total company monthly should scale with employee count."""
        r1 = calculate_bhxh(10_000_000, 1, "vung_1")
        r5 = calculate_bhxh(10_000_000, 5, "vung_1")
        assert r5.total_company_monthly == r1.total_monthly * 5

    def test_different_regions(self):
        """Different regions have different minimum wages."""
        r1 = calculate_bhxh(5_000_000, 1, "vung_1")
        r4 = calculate_bhxh(5_000_000, 1, "vung_4")
        # Both should calculate but with different caps
        assert r1.min_wage != r4.min_wage


# ---------------------------------------------------------------------------
# TNCN (personal income tax)
# ---------------------------------------------------------------------------

class TestTNCN:
    def test_below_threshold(self):
        """Income below personal deduction → zero tax."""
        result = calculate_tncn(10_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=0)
        assert result.total_tax == 0

    def test_progressive_brackets(self):
        """Tax should be progressive — higher income, higher effective rate."""
        r_low = calculate_tncn(20_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=0)
        r_high = calculate_tncn(100_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=0)
        assert r_high.effective_rate > r_low.effective_rate

    def test_dependents_reduce_tax(self):
        """More dependents → lower taxable income → lower tax."""
        r0 = calculate_tncn(30_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=0)
        r2 = calculate_tncn(30_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=2)
        assert r2.total_tax < r0.total_tax

    def test_no_deduction(self):
        """Without personal deduction, full income is taxable."""
        r_with = calculate_tncn(20_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=0)
        r_without = calculate_tncn(20_000_000, giam_tru_gia_canh=False, so_nguoi_phu_thuoc=0)
        assert r_without.total_tax > r_with.total_tax

    def test_giam_tru_amounts(self):
        """Check deduction amounts: 11M personal + 4.4M per dependent."""
        result = calculate_tncn(50_000_000, giam_tru_gia_canh=True, so_nguoi_phu_thuoc=2)
        assert result.giam_tru_ban_than == 11_000_000
        assert result.giam_tru_phu_thuoc == 8_800_000  # 2 * 4.4M
