import unittest
from integrations.ugai_runtime.config import ConfigurationError, RuntimeConfig
from integrations.ugai_runtime.mode_router import Mode, ModeRouter
from integrations.ugai_runtime.plan import PlanStep, TaskPlan, PlanValidationError
from integrations.ugai_runtime.policy import PolicyDecision, PolicyEngine
from integrations.ugai_runtime.verifier import ClaimVerifier, GateChecker
from integrations.ugai_runtime.skills import SKILL_REGISTRY, SKILLS_BY_ID

class UGAIRuntimeTests(unittest.TestCase):
    def test_twelve_skills_have_unique_ids_and_contracts(self):
        self.assertEqual(len(SKILL_REGISTRY), 12)
        self.assertEqual(len(SKILLS_BY_ID), 12)
        self.assertTrue(all(skill.trigger and skill.input_contract and skill.output_contract and skill.failure_mode for skill in SKILL_REGISTRY))

    def test_model_must_come_from_environment(self):
        with self.assertRaises(ConfigurationError):
            RuntimeConfig.from_env({})
        self.assertEqual(RuntimeConfig.from_env({"ANTHROPIC_MODEL":"claude-test"}).model, "claude-test")

    def test_mode_router_boundaries(self):
        self.assertEqual(ModeRouter.select(1), Mode.FAST)
        self.assertEqual(ModeRouter.select(2), Mode.PLANNED)
        self.assertEqual(ModeRouter.select(11), Mode.ORCHESTRATED)
        self.assertEqual(ModeRouter.select(11, pattern_expressible_as_script=True), Mode.DYNAMIC)
        self.assertEqual(ModeRouter.select(1, requires_specialists=True), Mode.ORCHESTRATED)

    def test_plan_requires_evidence_and_abort_conditions(self):
        plan = TaskPlan(Mode.PLANNED, "review", (PlanStep(0, "read", {}, ("doc:a:1-2",)),), abort_conditions=("missing source",))
        plan.validate()
        invalid = TaskPlan(Mode.PLANNED, "review", (PlanStep(0, "read", {}, ()),), abort_conditions=("stop",))
        with self.assertRaises(PlanValidationError):
            invalid.validate()

    def test_plan_rejects_blank_evidence_tags_and_negative_ids(self):
        blank = TaskPlan(Mode.PLANNED, "bad", (PlanStep(0, "read", {}, (" ",)),), abort_conditions=("stop",))
        with self.assertRaises(PlanValidationError):
            blank.validate()
        negative = TaskPlan(Mode.PLANNED, "bad", (PlanStep(-1, "read", {}, ("doc:x:1",)),), abort_conditions=("stop",))
        with self.assertRaises(PlanValidationError):
            negative.validate()

    def test_plan_enforces_planned_limit_and_unique_ids(self):
        steps = tuple(PlanStep(i, "tool", {}, ("cmd:tool",)) for i in range(21))
        with self.assertRaises(PlanValidationError):
            TaskPlan(Mode.PLANNED, "too many", steps, abort_conditions=("stop",)).validate()
        duplicate = TaskPlan(Mode.PLANNED, "dupe", (PlanStep(0,"a",{},("x",)), PlanStep(0,"b",{},("y",))), abort_conditions=("stop",))
        with self.assertRaises(PlanValidationError):
            duplicate.validate()

    def test_policy_sensitive_action_and_budget(self):
        policy = PolicyEngine()
        self.assertEqual(policy.evaluate(action="modify_supabase", spent_usd=0, budget_usd=2).decision, PolicyDecision.REQUIRE_HUMAN)
        self.assertEqual(policy.evaluate(action="read_file", spent_usd=2.01, budget_usd=2).decision, PolicyDecision.ABORT)
        self.assertEqual(policy.evaluate(action="read_file", spent_usd=1.6, budget_usd=2).decision, PolicyDecision.WARN)

    def test_claim_verifier_rejects_missing_doc_evidence_and_downgrades_assumption(self):
        result = ClaimVerifier.verify([
            {"text":"found", "evidence":"doc:README.md:1-2", "status":"confirmed"},
            {"text":"guess", "evidence":"[assume]", "status":"confirmed"}
        ], set())
        self.assertEqual(result.missing, ("doc:README.md:1-2",))
        self.assertEqual(result.rejected[0]["status"], "unverified")
        self.assertEqual(result.verified[0]["status"], "probable")

    def test_gate_checker_rejects_unledgered_artifact_reference(self):
        result = GateChecker.check({}, set(), {"answer":"See integrations/ugai_runtime/config.py", "claims":[]})
        self.assertTrue(any(v.startswith("G2") for v in result.violations))

    def test_gate_checker_rejects_hedge_on_confirmed_claim(self):
        result = GateChecker.check({}, set(), {"answer":"This probably works.", "claims":[{"status":"confirmed"}]})
        self.assertTrue(any(v.startswith("G4") for v in result.violations))

    def test_gate_checker_reports_missing_execution_and_coverage(self):
        result = GateChecker.check(
            {"required_sections":["analysis","risk"]}, set(),
            {"answer":"Tests passed. We recommend a score: 8.", "claims":[], "covered_sections":["analysis"]}
        )
        self.assertFalse(result.passed)
        self.assertTrue(any(v.startswith("G1") for v in result.violations))
        self.assertTrue(any(v.startswith("G3") for v in result.violations))
        self.assertTrue(any(v.startswith("G5") for v in result.violations))
        self.assertTrue(any(v.startswith("G6") for v in result.violations))
        self.assertTrue(any(v.startswith("G7") for v in result.violations))

if __name__ == "__main__":
    unittest.main()
