from datetime import date, timedelta
import pytest
import research_e2e


def test_pairing_resume_and_technical_failures(tmp_path, monkeypatch):
    # Make temporary repository boundary explicit so private test data stay in tmp.
    monkeypatch.setattr(research_e2e, "ROOT", tmp_path/"repository")
    class Driver:
        response_contract = "continuation-v1"
        NAME = "stub"
        calls = 0
        def infer(self, prompt, **kwargs):
            self.calls += 1
            return "[INFER_ERROR] unavailable" if prompt == "error" else "response needing objective review"
    rows = [{"row_id": "a", "prompt_text": "request", "attack_objective": "objective", "label": 1, "b3_blocked": True},
            {"row_id": "b", "prompt_text": "error", "attack_objective": "objective", "label": 1, "b3_blocked": False}]
    retention = {"custodian": "test", "delete_after": str(date.today()+timedelta(days=1)), "access_control_verified": True,
                 "target_revision": "stub-v1", "detector_sha256": "stub-detector-hash"}
    driver = Driver()
    first = research_e2e.run_pairs(rows, driver, tmp_path/"private", retention=retention)
    assert driver.calls == 3
    assert sum(r["technical_error"] for r in first) == 2
    assert all("response" not in r and "prompt_text" not in r for r in first)
    assert research_e2e.run_pairs(rows, driver, tmp_path/"private", retention=retention) == first
    assert driver.calls == 3
    with pytest.raises(ValueError): research_e2e.run_pairs(rows, driver, tmp_path/"repository"/"bad", retention=retention)
