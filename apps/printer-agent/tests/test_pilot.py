import copy
import hashlib

from rodada_printer_agent.pilot import SCENARIOS, evaluate


def record(tmp_path):
    content = b"Synthetic verifier fixture, NOT hardware evidence"
    (tmp_path / "fixture.txt").write_bytes(content)
    proof = {"status": "PASS", "evidence": [{"path": "fixture.txt", "sha256": hashlib.sha256(content).hexdigest()}]}
    return {
        "schema_version": 1, "commit": "a" * 40, "operator": "Synthetic operator",
        "mode": "PHYSICAL", "owner_rollout_authorized": True,
        **dict.fromkeys(("windows_build", "printer_model", "driver_version", "connection", "profile_id"), "Synthetic"),
        "release_gates": dict.fromkeys(("authenticode", "antivirus_smartscreen", "signed_installer_sha256"), proof),
        "scenarios": {name: copy.deepcopy(proof) for name in SCENARIOS},
    }


def test_completeness_is_not_hardware_certification(tmp_path):
    data = record(tmp_path)
    assert evaluate(data, tmp_path) == []
    data["mode"] = "SIMULATOR"
    assert "physical_execution" in evaluate(data, tmp_path)
    data["owner_rollout_authorized"] = False
    assert "owner_rollout_authorized" in evaluate(data, tmp_path)


def test_missing_or_tampered_evidence_fails_closed(tmp_path):
    data = record(tmp_path)
    del data["scenarios"]["two_agents"]
    data["scenarios"]["computer_restart"]["evidence"] = []
    (tmp_path / "fixture.txt").write_bytes(b"changed")
    gaps = evaluate(data, tmp_path)
    assert "scenario:two_agents" in gaps
    assert "evidence:computer_restart" in gaps
    assert "integrity:pairing" in gaps


def test_outside_evidence_and_unsigned_release_rejected(tmp_path):
    data = record(tmp_path)
    data["scenarios"]["pairing"]["evidence"][0]["path"] = "../outside"
    data["release_gates"]["authenticode"] = {"status": "NOT_RUN", "evidence": []}
    assert "integrity:pairing" in evaluate(data, tmp_path)
    assert "release:authenticode" in evaluate(data, tmp_path)
