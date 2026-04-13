"""Jinja2 template engine for rendering contracts."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import jinja2


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _format_vnd(value: int | float | None) -> str:
    """Format number as VND: 4960000 -> '4.960.000'."""
    if value is None:
        return "___"
    return f"{int(value):,}".replace(",", ".")


def _format_date_vi(value: str | date | None) -> str:
    """Format date Vietnamese style: 'ngay 15 thang 04 nam 2026'."""
    if value is None:
        return "ngay ___ thang ___ nam ___"
    if isinstance(value, str):
        try:
            parts = value.split("-")
            return f"ngay {int(parts[2]):02d} thang {int(parts[1]):02d} nam {parts[0]}"
        except (IndexError, ValueError):
            return value
    return f"ngay {value.day:02d} thang {value.month:02d} nam {value.year}"


def _number_to_words_vi(value: int | None) -> str:
    """Convert number to Vietnamese words (simplified for contract amounts)."""
    if value is None:
        return "___"

    ones = ["", "mot", "hai", "ba", "bon", "nam", "sau", "bay", "tam", "chin"]
    units = ["", "nghin", "trieu", "ty"]

    if value == 0:
        return "khong dong"

    result = []
    group_idx = 0
    n = abs(value)

    while n > 0:
        group = n % 1000
        if group > 0:
            hundreds = group // 100
            tens = (group % 100) // 10
            unit = group % 10

            group_str = ""
            if hundreds > 0:
                group_str += ones[hundreds] + " tram "
            if tens > 0:
                if tens == 1:
                    group_str += "muoi "
                else:
                    group_str += ones[tens] + " muoi "
            if unit > 0:
                if tens == 0 and hundreds > 0:
                    group_str += "le "
                if unit == 1 and tens > 1:
                    group_str += "mot"
                elif unit == 5 and tens > 0:
                    group_str += "lam"
                else:
                    group_str += ones[unit]

            group_str = group_str.strip()
            if group_idx < len(units) and units[group_idx]:
                group_str += " " + units[group_idx]
            result.insert(0, group_str)

        n //= 1000
        group_idx += 1

    text = " ".join(result).strip()
    return text + " dong"


class TemplateEngine:
    """Render contract templates with Jinja2."""

    def __init__(self) -> None:
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
            undefined=jinja2.Undefined,
        )
        self._env.filters["vnd"] = _format_vnd
        self._env.filters["date_vi"] = _format_date_vi
        self._env.filters["number_to_words_vi"] = _number_to_words_vi

    def render(self, template_key: str, input_data: dict) -> str:
        """Render a contract template with input data."""
        template = self._env.get_template(f"{template_key}.jinja2")
        return template.render(**input_data)

    def template_exists(self, template_key: str) -> bool:
        """Check if a template file exists."""
        return (TEMPLATES_DIR / f"{template_key}.jinja2").exists()
