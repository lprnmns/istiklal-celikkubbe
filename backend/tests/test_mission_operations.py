from pathlib import Path

from fastapi.testclient import TestClient


def test_mission_status_update_reset_and_score(client: TestClient) -> None:
    response = client.post("/api/mission/reset")
    assert response.status_code == 200
    initial = response.json()
    assert initial["no_physical_command_generated"] is True
    assert initial["state"]["active_stage"] == "stage1"

    assert client.put("/api/mission/status", json={"stage1_hits": 4}).status_code == 409
    invalid = client.put("/api/mission/stage1/plan", json={"order": ["F16", "Balistik Füze", "Helikopter", "Mini/Micro İHA"]})
    assert invalid.status_code == 409
    assert client.put("/api/mission/stage1/plan", json={"order": ["Balistik Füze", "Helikopter", "F16", "Mini/Micro İHA"]}).status_code == 200
    assert client.post("/api/mission/stage1/start").status_code == 200
    assert client.put("/api/mission/status", json={"elapsed_s": 75}).status_code == 200
    for target in ["Balistik Füze", "Helikopter", "F16", "Mini/Micro İHA"]:
        assert client.post("/api/mission/stage1/hit", json={"target": target, "score_awarded": 20}).status_code == 200
    updated = client.post("/api/mission/stage1/wrong-target", json={"target": "F16"}).json()
    assert updated["score"]["stage1_raw_points"] == 80
    assert updated["score"]["stage1_penalty_points"] == 5
    assert updated["score"]["stage1_bonus_points"] == 15
    assert updated["score"]["stage1_score"] == 90
    assert updated["score"]["stage1_next_target"] is None

    response = client.post("/api/mission/reset")
    assert response.status_code == 200
    reset = response.json()
    assert reset["state"]["stage1_hits"] == 0
    assert reset["score"]["total_estimated_score"] == 0


def test_ktr_export_contains_mission_evidence(client: TestClient) -> None:
    client.put("/api/mission/status", json={"active_stage": "stage2"})
    assert client.post("/api/mission/stage2/round/complete", json={"confirmed_hits": 3}).status_code == 200
    response = client.post("/api/reports/generate-ktr-summary", json={"notes": "mission evidence pytest"})
    assert response.status_code == 200
    body = response.json()
    output_dir = Path(body["output_dir"])
    evidence_md = output_dir / "mission_evidence.md"
    evidence_json = output_dir / "mission_evidence.json"
    assert evidence_md.exists()
    assert evidence_json.exists()
    assert "Active stage: stage2" in evidence_md.read_text(encoding="utf-8")
    assert body["summary"]["mission"]["state"]["stage2_hits"] == 3


def test_stage2_round_score_table_and_three_zero_hit_failure(client: TestClient) -> None:
    assert client.post("/api/mission/reset").status_code == 200
    assert client.put("/api/mission/status", json={"active_stage": "stage2"}).status_code == 200
    assert client.put("/api/mission/status", json={"stage2_hits": 1}).status_code == 409
    for hits in (3, 3, 3, 2):
        snapshot = client.post("/api/mission/stage2/round/complete", json={"confirmed_hits": hits}).json()
    assert snapshot["score"]["stage2_round_scores"] == [30, 30, 30, 15]
    assert snapshot["score"]["stage2_score"] == 105
    assert snapshot["score"]["stage2_passing_threshold_met"] is True

    assert client.post("/api/mission/reset").status_code == 200
    assert client.put("/api/mission/status", json={"active_stage": "stage2"}).status_code == 200
    for _ in range(3):
        snapshot = client.post("/api/mission/stage2/round/complete", json={"confirmed_hits": 0}).json()
    assert snapshot["score"]["stage2_failed"] is True
    assert snapshot["score"]["stage2_score"] == 0
    assert client.post("/api/mission/stage2/round/complete", json={"confirmed_hits": 3}).status_code == 409


def test_stage3_class_score_penalty_and_three_miss_failure(client: TestClient) -> None:
    assert client.post("/api/mission/reset").status_code == 200
    assert client.put("/api/mission/status", json={"active_stage": "stage3"}).status_code == 200
    assert client.put("/api/mission/status", json={"stage3_hits": 1}).status_code == 409
    assert client.post("/api/mission/stage3/round/complete", json={"enemy_class": "f16", "enemy_hit": True, "friend_hit": False}).status_code == 200
    snapshot = client.post("/api/mission/stage3/round/complete", json={"enemy_class": "helicopter", "enemy_hit": True, "friend_hit": True}).json()
    assert snapshot["score"]["stage3_round_scores"] == [30, 10]
    assert snapshot["score"]["stage3_score"] == 40

    assert client.post("/api/mission/reset").status_code == 200
    assert client.put("/api/mission/status", json={"active_stage": "stage3"}).status_code == 200
    for _ in range(3):
        snapshot = client.post("/api/mission/stage3/round/complete", json={"enemy_class": "mini_micro_uav", "enemy_hit": False, "friend_hit": False}).json()
    assert snapshot["score"]["stage3_failed"] is True
    assert snapshot["score"]["stage3_score"] == 0


def test_performance_diagnosis_contract(client: TestClient) -> None:
    status = client.app.state.runtime.performance.status(client.app.state.runtime)
    payload = status.model_dump(mode="json")
    assert "primary_bottleneck" in payload
    assert "bottleneck_summary" in payload
    assert isinstance(payload["recommended_actions"], list)
    assert payload["recommended_actions"]
