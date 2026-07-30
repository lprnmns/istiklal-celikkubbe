# Phase 44 3D Scene Rebuild

The Digital Twin panel was rebuilt for readability and KTR presentation value. The panel remains read-only and does not influence the tracker, serial protocol, Pico, motor control, or fire gate.

## Phase 43 Issue

- The turret was too small and the scene felt like a debug grid.
- The FOV cone visually competed with the device model.
- Target projection, optical axis, launcher axis, and depth context were not immediately understandable.

## Phase 44 Fix

- The Three.js camera is moved closer with a front-right/top view.
- The simplified STL-derived twin is scaled up for KTR demo readability.
- The FOV cone is shorter and more transparent, with wireframe-dominant edges.
- Scene depth is reinforced with grid, horizon, range rings, projection ray, and compact HUD cards.
- Target depth remains labelled as a relative estimate, not a calibrated metric range.

## Truth Boundary

Visible model label: `STL-derived simplified digital twin` when KTR/demo readability uses simplified geometry.

Safety invariant: `no_physical_command_generated=true`.
