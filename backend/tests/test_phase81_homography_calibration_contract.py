def _enable_homography(client) -> None:
    config = client.get("/api/calibration/config").json()
    config["homography_enabled"] = True
    response = client.put("/api/calibration/config", json=config)
    assert response.status_code == 200


def _add(client, label: str, world_x: float, world_y: float, image_x: float, image_y: float) -> None:
    response = client.post(
        "/api/calibration/points",
        json={
            "label": label,
            "world_x_m": world_x,
            "world_y_m": world_y,
            "image_x_px": image_x,
            "image_y_px": image_y,
        },
    )
    assert response.status_code == 200


def test_compute_uses_real_projective_homography_and_reports_reprojection_evidence(client) -> None:
    _enable_homography(client)
    # A non-identity trapezoid: world plane -> camera image pixels.
    _add(client, "near-left", 0, 0, 104, 92)
    _add(client, "near-right", 2, 0, 330, 118)
    _add(client, "far-right", 2, 2, 286, 330)
    _add(client, "far-left", 0, 2, 126, 292)

    computed = client.post("/api/calibration/compute")
    body = computed.json()

    assert computed.status_code == 200
    assert body["valid"] is True
    assert body["inlier_count"] == 4
    assert body["reprojection_error_px"] is not None and body["reprojection_error_px"] < 0.01
    assert body["homography_direction"] == "world_plane_to_image_px"
    assert body["calibration_hash"]
    assert body["homography_matrix"] != [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def test_collinear_or_changed_points_fail_closed_and_invalidate_previous_solution(client) -> None:
    _enable_homography(client)
    for index in range(4):
        _add(client, f"line-{index}", index, index, 100 + index * 40, 100 + index * 40)

    invalid = client.post("/api/calibration/compute").json()

    assert invalid["valid"] is False
    assert invalid["homography_matrix"] is None
    assert invalid["reprojection_error_px"] is None
    assert invalid["calibration_hash"] is None
    assert "homography_degenerate_points" in invalid["warnings"]
