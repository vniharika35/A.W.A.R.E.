"""Isolation state machine for orchestrating valve actuation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class IsolationStatus(str, Enum):
    NORMAL = "NORMAL"
    SUSPECTED = "SUSPECTED"
    ISOLATING = "ISOLATING"
    ISOLATED = "ISOLATED"
    RECOVERY = "RECOVERY"


VALID_TRANSITIONS: Dict[IsolationStatus, set[IsolationStatus]] = {
    IsolationStatus.NORMAL: {IsolationStatus.SUSPECTED},
    IsolationStatus.SUSPECTED: {IsolationStatus.ISOLATING, IsolationStatus.NORMAL},
    IsolationStatus.ISOLATING: {IsolationStatus.ISOLATED, IsolationStatus.RECOVERY},
    IsolationStatus.ISOLATED: {IsolationStatus.RECOVERY},
    IsolationStatus.RECOVERY: {IsolationStatus.NORMAL},
}


@dataclass
class IsolationStateMachine:
    status: IsolationStatus = IsolationStatus.NORMAL

    def transition(self, new_status: IsolationStatus) -> IsolationStatus:
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
        self.status = new_status
        return self.status
