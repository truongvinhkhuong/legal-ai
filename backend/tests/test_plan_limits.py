"""Tests for plan limits and feature gate logic."""

from __future__ import annotations

import pytest

from src.core.plan_limits import PLAN_LIMITS


class TestPlanLimits:
    def test_free_plan_has_chat_limit(self):
        """Free plan should have a chat limit of 10."""
        assert PLAN_LIMITS["free"]["chat"] == 10

    def test_free_plan_disables_calculator(self):
        """Free plan should disable calculator."""
        assert PLAN_LIMITS["free"]["calculator"] is False

    def test_professional_plan_enables_all(self):
        """Professional plan should enable all features."""
        pro = PLAN_LIMITS["professional"]
        assert pro["chat"] == -1  # unlimited
        assert pro["calculator"] is True
        assert pro["risk_review"] is True
        assert pro["calendar"] is True
        assert pro["compliance_check"] is True

    def test_enterprise_unlimited_contracts(self):
        """Enterprise plan should have unlimited contracts."""
        assert PLAN_LIMITS["enterprise"]["contract"] == -1

    def test_all_plans_exist(self):
        """All expected plan tiers should be defined."""
        expected = {"free", "basic", "professional", "enterprise"}
        assert set(PLAN_LIMITS.keys()) == expected

    def test_basic_plan_has_more_than_free(self):
        """Basic plan should have more features than free."""
        free = PLAN_LIMITS["free"]
        basic = PLAN_LIMITS["basic"]
        # Basic should have calculator enabled
        assert free["calculator"] is False
        assert basic["calculator"] is True
        # Basic should have more contract quota
        assert basic["contract"] > free["contract"]
