# -*- coding: utf-8 -*-
"""
Tests for hyperlink
"""

from __future__ import annotations

__all = ()


def _init_hypothesis() -> None:
    from os import environ

    if "CI" in environ:
        try:
            from hypothesis import HealthCheck, settings
        except ImportError:
            return

        settings.register_profile(
            "patience",
            settings(
                suppress_health_check=[
                    HealthCheck.too_slow,
                    HealthCheck.filter_too_much,
                ]
            ),
        )
        settings.load_profile("patience")


_init_hypothesis()
