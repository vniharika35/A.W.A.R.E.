"""Lightweight in-memory event bus for coordinating agents."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Callable
from typing import DefaultDict
from typing import Iterable


@dataclass(slots=True)
class AgentEvent:
    type: str
    payload: dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """Simple pub/sub bus with history for replay + testing."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, list[Callable[[AgentEvent], None]]] = defaultdict(list)
        self._history: list[AgentEvent] = []

    def subscribe(self, event_type: str, callback: Callable[[AgentEvent], None]) -> None:
        self._subscribers[event_type].append(callback)

    def publish(self, event: AgentEvent) -> None:
        self._history.append(event)
        listeners = list(self._subscribers.get(event.type, [])) + list(
            self._subscribers.get("*", [])
        )
        for callback in listeners:
            callback(event)

    def history(self) -> Iterable[AgentEvent]:
        return list(self._history)

    def replay(self, events: Iterable[AgentEvent]) -> None:
        for event in events:
            self.publish(event)
