"""
Mission Control Client SDK

A Python SDK for agents to register with and report into the Mission Control
observability platform.
"""

from .client import MissionControlClient
from .decorators import mc_task, mc_tool

__all__ = ["MissionControlClient", "mc_task", "mc_tool"]
__version__ = "1.0.0"
