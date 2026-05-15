"""
AI Engine package.

This package contains computer-vision pipelines used by the Drone Inventory
Management System (e.g., barcode detection/decoding).
"""

from .barcode_pipeline import BarcodePipelineMVP, BarcodePipelineConfig

__all__ = ["BarcodePipelineMVP", "BarcodePipelineConfig"]

