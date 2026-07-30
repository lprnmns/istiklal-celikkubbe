# Phase 40 Real Asset Digital Twin Integration

Phase 40 found the project CAD/model files `ktr1.step` and `ktr1.stl` in the repository root. The original CAD sources were not modified. The ASCII STL was converted into a browser-ready binary STL copy at `frontend/public/assets/digital-twin/ktr1_binary.stl`.

Selected asset status: `REAL_STL`

Selected asset path: `/assets/digital-twin/ktr1_binary.stl`

CAD source: `ktr1.step`

Conversion status: `ASCII_STL_CONVERTED_TO_BINARY_STL_FOR_BROWSER`

The STEP file is documented as CAD source only. The cockpit uses the derived STL for read-only visualization in the digital twin scene. The mesh is normalized and centered by the Three.js viewer; camera FOV, launcher axis and 30 mm camera-to-launcher offset remain visualization overlays, not fire-control data.

Safety boundary: no motor, fire, servo, GPIO, PWM, STEP/DIR, hardware-enable or serial TX path was added. `no_physical_command_generated=true`.
