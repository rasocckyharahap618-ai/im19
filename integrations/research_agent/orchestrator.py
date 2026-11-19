"""Deterministic sequential orchestrator using injected task handlers."""
from __future__ import annotations
from collections.abc import Callable
from typing import Any
from .contracts import AgentEvent, AgentPlan, AgentRun, RunStatus

TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]

class ResearchOrchestrator:
    """Executes an approved plan; no model or tool is invoked implicitly."""
    def __init__(self, handlers: dict[str, TaskHandler] | None = None) -> None:
        self.handlers = handlers or {}
        self.events: list[AgentEvent] = []

    def register(self, skill: str, handler: TaskHandler) -> None:
        if not skill.strip():
            raise ValueError("skill name must not be empty")
        self.handlers[skill] = handler

    def run(self, plan: AgentPlan) -> AgentRun:
        run = AgentRun(plan=plan, status=RunStatus.RUNNING)
        self._emit(plan.run_id, "run.started", {"objective": plan.objective})
        try:
            for task in plan.tasks:
                handler = self.handlers.get(task.skill)
                if handler is None:
                    raise LookupError(f"no handler registered for skill: {task.skill}")
                self._emit(plan.run_id, "task.started", {"task_id": task.task_id, "skill": task.skill})
                output = handler(dict(task.input))
                if not isinstance(output, dict):
                    raise TypeError(f"handler for {task.skill} must return a dict")
                run.outputs.append({"task_id": task.task_id, "skill": task.skill, "output": output})
                self._emit(plan.run_id, "task.completed", {"task_id": task.task_id})
            run.status = RunStatus.SUCCEEDED
            self._emit(plan.run_id, "run.succeeded", {"task_count": len(plan.tasks)})
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.errors.append(f"{type(exc).__name__}: {exc}")
            self._emit(plan.run_id, "run.failed", {"error_type": type(exc).__name__})
        return run

    def _emit(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append(AgentEvent(run_id=run_id, event_type=event_type, payload=payload))
