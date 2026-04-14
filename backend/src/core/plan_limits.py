"""Feature limits by pricing plan.

Values:
  -1  = unlimited
  int = monthly quota
  False = feature disabled
  True  = feature enabled (no monthly limit)
"""

from __future__ import annotations

PLAN_LIMITS: dict[str, dict[str, int | bool]] = {
    "free": {
        "chat": 10,
        "contract": 1,
        "calculator": False,
        "risk_review": False,
        "calendar": False,
        "compliance_check": False,
    },
    "basic": {
        "chat": -1,
        "contract": 5,
        "calculator": True,
        "risk_review": False,
        "calendar": False,
        "compliance_check": False,
    },
    "professional": {
        "chat": -1,
        "contract": 20,
        "calculator": True,
        "risk_review": True,
        "calendar": True,
        "compliance_check": True,
    },
    "enterprise": {
        "chat": -1,
        "contract": -1,
        "calculator": True,
        "risk_review": True,
        "calendar": True,
        "compliance_check": True,
    },
}

# Features that show in the sidebar per plan tier
PLAN_FEATURES: dict[str, list[str]] = {
    "free": ["chat", "contract"],
    "basic": ["chat", "contract", "calculator"],
    "professional": [
        "chat", "contract", "calculator",
        "calendar", "compliance_check", "risk_review",
    ],
    "enterprise": [
        "chat", "contract", "calculator",
        "calendar", "compliance_check", "risk_review",
    ],
}
