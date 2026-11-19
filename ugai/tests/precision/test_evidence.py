import sqlite3,pytest
from core.evidence.ledger import EvidenceLedger
from core.evidence.verifier import EvidenceVerifier
from core.errors import EvidenceMissing
def test_missing_evidence_rejected():
 with pytest.raises(EvidenceMissing): EvidenceVerifier(EvidenceLedger(sqlite3.connect(":memory:"))).verify_tags(["cmd:missing"])
