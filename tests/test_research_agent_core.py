import unittest
from integrations.research_agent.contracts import AgentPlan, AgentTask, RunStatus
from integrations.research_agent.evidence import EvidenceLedger, EvidenceRecord
from integrations.research_agent.guard import EvidenceGuard, GuardViolation
from integrations.research_agent.orchestrator import ResearchOrchestrator
from integrations.research_agent.skills import RESEARCH_SKILLS

class ResearchAgentCoreTests(unittest.TestCase):
    def test_skill_catalogue_has_twenty_unique_keys(self):
        keys = [skill.key for skill in RESEARCH_SKILLS]
        self.assertEqual(len(keys), 20)
        self.assertEqual(len(keys), len(set(keys)))

    def test_evidence_record_is_added_and_exported(self):
        ledger = EvidenceLedger()
        record = EvidenceRecord(source="Crossref", title="Example paper", locator="https://doi.org/10.1000/example", doi="10.1000/example", excerpt="Abstract excerpt")
        ledger.add(record)
        self.assertEqual(ledger.get(record.evidence_id), record)
        self.assertEqual(len(ledger.export()), 1)
        self.assertEqual(len(record.content_sha256), 64)

    def test_guard_rejects_missing_citation_and_unknown_id(self):
        guard = EvidenceGuard(EvidenceLedger())
        with self.assertRaises(GuardViolation):
            guard.validate("An unsupported claim.")
        with self.assertRaises(GuardViolation):
            guard.validate("Claim [EV-not-in-ledger].")

    def test_guard_accepts_known_evidence_marker(self):
        ledger = EvidenceLedger()
        ledger.add(EvidenceRecord(source="OpenAlex", title="A study", locator="https://example.org/paper", evidence_id="EV-paper-1"))
        report = EvidenceGuard(ledger).validate("Finding [EV-paper-1].")
        self.assertTrue(report.valid)
        self.assertEqual(report.referenced_evidence_ids, ("EV-paper-1",))

    def test_orchestrator_executes_registered_handler_and_emits_events(self):
        orchestrator = ResearchOrchestrator({"literature-search": lambda data: {"query": data["query"], "count": 3}})
        plan = AgentPlan.create("Find literature", [AgentTask("task-1", "Search", "literature-search", {"query": "AI research"})])
        result = orchestrator.run(plan)
        self.assertEqual(result.status, RunStatus.SUCCEEDED)
        self.assertEqual(result.outputs[0]["output"]["count"], 3)
        self.assertEqual(orchestrator.events[-1].event_type, "run.succeeded")

    def test_orchestrator_fails_closed_for_unregistered_handler(self):
        plan = AgentPlan.create("Do work", [AgentTask("task-1", "Search", "unknown-skill", {})])
        result = ResearchOrchestrator().run(plan)
        self.assertEqual(result.status, RunStatus.FAILED)
        self.assertIn("no handler registered", result.errors[0])

if __name__ == "__main__":
    unittest.main()
