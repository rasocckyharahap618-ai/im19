import pytest
from core.guard.sandbox_guard import SandboxGuard
from core.guard.gates import QualityGates

def test_sandbox_rejects_parent_traversal(tmp_path):
    guard=SandboxGuard(str(tmp_path))
    with pytest.raises(PermissionError): guard.resolve('../outside')

def test_gate_rejects_unsupported_confirmed_claim():
    result=QualityGates().check({}, {'answer':'done','claims':[{'status':'confirmed','evidence':'doc:missing:1-2'}]}, set())
    assert not result.passed and result.violations
