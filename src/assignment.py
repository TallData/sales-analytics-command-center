"""Shared definitions for the illustrative synthetic assignment framework."""

from __future__ import annotations


def confidence_band(confidence: float) -> str:
    if not 0 <= confidence <= 1:
        raise ValueError("assignment confidence must be between 0 and 1")
    if confidence >= 0.90:
        return "HIGH"
    if confidence >= 0.70:
        return "MEDIUM"
    return "LOW"
