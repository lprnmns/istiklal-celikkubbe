# Phase 40 KTR-Grade Cockpit Scene

The right-side digital twin panel now supports the real STL device asset and clearly labels the selected model as `ASSET: STL_MODEL`. The scene keeps the professional dark grid, camera FOV volume, optical/launcher axis visualization, target projection markers, no-go/person-safety overlay and pose-source badges.

KTR demo mode remains available at `/cockpit?ktr_demo=1`. It presents a deterministic evidence-oriented view with `DISARMED`, `DRY_RUN`, `NO-FIRE`, `USB OFFLINE_EXPECTED`, `PICO OFFLINE_EXPECTED` and `NO PHYSICAL COMMAND GENERATED` visible.

The launcher axis annotation is explicitly labelled as visualization only: `launcher axis / no physical command`.

This phase improves visual evidence quality only. It does not change the tracker, YOLO path, safety gates, serial protocol or any physical actuation path.
