# Phase 11 - KTR Reports, Demo Polish and Operation Procedure

## Scope

Phase 11 makes the command-control system presentable for KTR, jury demo and team operations. It adds report export, interface inventory, safety summary, self-test integration and operational runbooks.

It does not enable physical hardware, motor movement, servo trigger, fire command, YOLO training or production vision algorithms.

## Report Pack Types

- KTR Summary: architecture, interfaces, protocols, safety policy, model/dataset/replay approach and explicit limitations.
- Demo Pack: demo runbook, operation checklist, safety summary, self-test summary, model registry summary and dataset summary.
- Readiness Pack: safety summary, self-test summary, operation checklist and interface inventory.

All exports are written under `exports/reports/<export_id>/`. Runtime export output is ignored by Git.

## Interface Inventory

The generated inventory documents:

- Frontend to Backend REST
- Frontend to Backend WebSocket
- Backend to Pico Serial JSON-line
- Backend binary protocol codec
- Camera to Backend MJPEG/OpenCV
- Vision model to inference adapter
- Motion service dry-run path
- Dataset/replay to vision pipeline
- Self-test to runtime services

Each row includes source, target, protocol, data type, direction, safety critical flag, current implementation status and notes.

## Safety Summary

The report explicitly records:

- `NO_FIRE` default policy
- DISARMED startup
- `dry_run=true`
- `hardware_enabled=false`
- fire request rejection model
- no physical command evidence
- friend target rejection
- unknown team rejection
- balloon/range/stability requirements
- E-stop placeholder/current behavior

KTR export and self-test readiness never change system safety state and never grant physical fire authorization.

## Self-Test Integration

When a self-test run exists, the export includes:

- run id
- status
- readiness level
- critical failure count
- warning count
- step summary
- suggested actions
- no physical command evidence

If no self-test run exists, the report states that `/api/self-test/run` should be executed before final demo.

## Dataset and Model Summary

Model summary separates responsibilities:

- Vision team provides production model file, class list, input size, threshold recommendations and adapter details.
- Interface team provides model registry, active model selection, metadata, test adapter and replay/model-test UI.

Dataset summary includes session count, snapshot/frame count, annotation count, export count, class distribution, distance distribution, lens distribution and recommended next data collection.

## Demo Runbook

The generated demo runbook follows this order:

1. Start backend.
2. Start frontend.
3. Confirm safety lock: `NO_FIRE`, `DRY RUN`, `REAL HARDWARE DISABLED`.
4. Run Self-Test.
5. Check Camera/Vision.
6. Show Pico mock/physical distinction.
7. Show Safety gates and Fire Request dry-run rejection.
8. Start Data Lab session.
9. Save snapshot.
10. Show replay controls.
11. Show YOLO export output.
12. Filter logs.
13. Generate KTR/Demo/Readiness report pack.

## Operation Checklist

The generated checklist includes:

- pre-demo checklist
- pre-field-test checklist
- camera/lens checklist
- model loading checklist
- dataset capture checklist
- safety checklist
- Pico/pin checklist
- motion dry-run checklist
- known limitations checklist

## UI Flow

Reports screen route: `/reports`

The screen provides:

- Generate KTR Summary
- Generate Demo Pack
- Generate Readiness Pack
- Latest self-test summary
- Export list
- Export detail and generated file paths
- "Reports do not enable physical commands" warning

Sidebar is grouped into Operations, Engineering and Data & Reports.

## Updating KTR Text

KTR text is generated in `backend/app/services/report_export_service.py`. Update the markdown writer methods when competition wording changes:

- `_ktr_summary`
- `_interface_inventory`
- `_safety_summary`
- `_self_test_summary`
- `_model_registry_summary`
- `_dataset_summary`
- `_demo_runbook`
- `_operation_checklist`

Keep generated runtime reports out of Git. Only source templates, docs and tests should be committed.
