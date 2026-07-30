# Phase 56 Root Cause Diagnosis and Digital Twin Rebuild Plan

## Scope

This diagnosis focuses only on the real CAD-to-kinematic-digital-twin problem observed after Phase 55. It does not propose dashboard redesign as the primary solution. The target remains a read-only digital twin of the real ISTIKLAL C2 device:

- same visible geometry as the real/FreeCAD model
- same static/yaw/pitch moving subassemblies
- camera and launcher axes attached to the correct physical parts
- target balloon placed in 3D from YOLO bbox center and bbox area
- no physical command generation

## Evidence Reviewed

User screenshots compared:

- browser FreeCAD Match and side views
- FreeCAD top/rear/left/front-like views of the same STEP model

Local diagnostic data:

- `reports/phase55_asset_audit.json`
- `reports/phase55_glb_node_hierarchy.json`
- `frontend/public/assets/digital-twin/ktr1_kinematics.json`
- `frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55_manifest.json`
- `scripts/convert_ktr_step_to_glb.py`
- `scripts/export_ktr_kinematic_glb_phase55.py`
- `frontend/src/components/digital-twin/DigitalTwinPanel.vue`

## Small Diagnostic Tests

### Test 1: STEP geometry exists

Result:

- STEP import found `136` shapes/solids.
- Front launcher/camera detail was detected.
- `Bileşen13` exists as a launcher-like part.
- `kamera v3` exists as a camera-like part.

Diagnosis:

The source CAD is not missing the weapon/camera geometry. The problem is downstream conversion/runtime interpretation.

### Test 2: STEP has assembly/color records

Counts from `ktr1.step`:

- `COLOUR_RGB`: 15
- `PRESENTATION_STYLE_ASSIGNMENT`: 16
- `MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION`: 1
- `NEXT_ASSEMBLY_USAGE_OCCURRENCE`: 39
- `PRODUCT`: 221

Diagnosis:

The STEP file contains presentation and assembly relationship information, but the current conversion path does not extract it into a real assembly tree. The GLB is a flat list of mesh nodes.

### Test 3: Current GLB hierarchy

Result:

- GLB node count: `136`
- mesh count: `136`
- key nodes such as `kamera v3` and `Bileşen13` are root scene children.
- hierarchy preservation is reported as `false`.

Diagnosis:

The browser is not operating on the same assembly semantics FreeCAD uses. It receives tessellated mesh parts without validated parent/child transform hierarchy or real joints.

### Test 4: Material preservation

Result:

- manifest: `material_preserved=false`
- `materials_reconstructed=true`
- `kamera v3` is assigned `sensor_camera_bright_cyan`
- `Bileşen13` is assigned `freecad_body_warm_white`

Diagnosis:

The browser colors are not the authoritative FreeCAD/STEP colors. The cyan camera color is a reconstruction decision, not a verified CAD material. This causes visual mismatch and makes the camera/anchor look artificial or floating.

### Test 5: Kinematic grouping and pivots

Result:

- `static_root`: 2 nodes
- `yaw_group`: 105 nodes
- `pitch_group`: 29 nodes
- `camera_group`: 1 node (`kamera v3`)
- `launcher_group`: 1 node (`Bileşen13`)
- yaw pivot source: `phase55_audit_bbox_heuristic`
- pitch pivot source: `phase55_audit_front_group_bbox_heuristic`

Diagnosis:

Current motion semantics are not mechanically validated. They are bbox/name heuristics. This is not sufficient for “the same parts move by the same amount as the real X/Y step motors.”

### Test 6: Coordinate and view semantics

Current converter states:

- source CAD: `+Z` up
- runtime world: `+Y` up
- conversion: `X = CAD X`, `Y = CAD Z`, `Z = -CAD Y`

Diagnosis:

The transform may be mathematically consistent, but the runtime lacks a canonical device frame definition:

- which direction is physical front?
- which axis is launcher forward?
- which axis is camera optical forward?
- which view corresponds to FreeCAD front/rear/left/top?

Without this, the browser can show the correct mesh from a misleading side/rear angle, making the weapon appear under or beside the device.

## Root Causes

### 1. CAD semantics are lost before runtime

FreeCAD uses CAD kernel and STEP assembly semantics. The browser receives a flattened tessellated GLB. The pipeline does not preserve:

- STEP assembly tree
- part usage transforms
- real parent-child relationships
- joint candidates
- color assignments
- canonical front/top/side view metadata

### 2. Visual fidelity is being reconstructed, not preserved

The converter reconstructs colors from names/geometry roles. This is useful as a temporary visualization, but it cannot be treated as FreeCAD-fidelity.

Example:

- `kamera v3` becomes cyan in browser.
- FreeCAD visual reference shows camera/weapon internals closer to dark/gray mechanical materials.

### 3. Kinematic grouping is heuristic

The current `ktr1_kinematics.json` is structurally useful, but the assignments are not proven against the real mechanism. For a real digital twin, each moving group must be manually validated against the physical device and CAD part list.

### 4. Pivots and axes are estimated

Yaw and pitch pivots are derived from bounding boxes, not from CAD joints, motor shafts, bearing centerlines, or explicit construction geometry.

This is the main blocker for matching real step motor motion.

### 5. Overlay/anchor markers can be confused with CAD parts

Runtime markers and reconstructed colors are visually mixed with real CAD geometry. This makes it unclear what is actual device geometry and what is an explanatory overlay.

### 6. Target projection logic exists conceptually, but is not anchored to validated camera/launcher frames

Mapping YOLO bbox to a 3D balloon is straightforward only after the camera origin, camera optical axis, launcher origin, launcher axis and device coordinate frame are validated.

## Is Web/Three.js the Problem?

No, not primarily.

Three.js can render this kind of model. The current GLB is heavy but within browser capability on a capable machine. The problem is not that the web “cannot handle” the model.

The problem is that the asset pipeline is not a CAD-grade semantic pipeline. The browser is being asked to infer mechanical truth from flattened meshes.

Desktop can help if it embeds FreeCAD/OCCT directly, but moving to desktop does not automatically solve the problem unless we use the CAD kernel semantics there. A web solution is still possible if the offline pipeline exports correct assembly, materials, pivots and anchors.

## Correct Rebuild Plan

### Stage 1: Establish the authoritative device coordinate frame

Deliverables:

- `ktr1_device_frame.json`
- front direction
- up direction
- right direction
- yaw axis
- pitch axis
- launcher forward axis
- camera optical axis
- FreeCAD view preset mapping: front/rear/left/right/top/operator

This must be validated visually against FreeCAD screenshots.

### Stage 2: Extract a real assembly tree from STEP

Preferred tools:

- OCCT XDE / `STEPCAFControl_Reader`
- FreeCAD document object tree plus STEP product/assembly usage map

Deliverables:

- `reports/phase56_step_assembly_tree.json`
- `reports/phase56_part_table.md`

Each part must include:

- STEP product/name/label
- parent assembly
- local transform
- global transform
- color/material if available
- bounding box
- visible/hidden state
- role candidate

### Stage 3: Preserve or correctly reconstruct materials

Deliverables:

- `ktr1_materials.json`
- material table from STEP color records where possible
- manual color override table only where STEP extraction fails

Rule:

Manual colors must be marked as manual and must match FreeCAD screenshots, not arbitrary tactical colors.

### Stage 4: Manual mechanical grouping pass

Create a curated file:

`frontend/public/assets/digital-twin/ktr1_mechanical_groups.json`

Required groups:

- `static_base`
- `yaw_rotor`
- `pitch_cradle`
- `launcher_assembly`
- `camera_assembly`
- `decorative_covers`
- `fasteners_optional`

Each part must be assigned once. Unknown parts must remain `unclassified`, not silently forced into yaw or pitch.

Validation:

- yaw preview rotates only the real azimuth-moving parts.
- pitch preview rotates only the real elevation-moving parts.
- base/legs remain static.
- decorative covers move only if physically mounted to moving group.

### Stage 5: Author real pivots and axes

Create:

`frontend/public/assets/digital-twin/ktr1_joint_calibration.json`

Required:

- yaw pivot point
- yaw axis
- pitch pivot point
- pitch axis
- motor step-to-degree calibration for yaw and pitch
- camera origin
- camera optical axis
- launcher origin
- launcher axis
- camera-to-launcher offset vector

Source priority:

1. CAD construction/shaft/bearing centerline if available
2. Manual pick in FreeCAD/inspector
3. Physical measurement
4. bbox heuristic only as temporary fallback

### Stage 6: Export GLB with semantic nodes

Output:

- `ktr1_digital_twin_phase56.glb`
- `ktr1_digital_twin_phase56_manifest.json`

The GLB should contain named containers:

- `static_base`
- `yaw_pivot`
- `yaw_rotor`
- `pitch_pivot`
- `pitch_cradle`
- `launcher_assembly`
- `camera_assembly`
- `anchors`

No runtime guessing should be needed for primary grouping.

### Stage 7: Runtime digital twin

Runtime behavior:

- load semantic GLB
- load device frame
- load mechanical groups
- load joint calibration
- apply yaw/pitch preview from actual telemetry or UI preview
- overlays attach to anchor nodes

Important:

Yaw/pitch preview remains visualization-only unless real telemetry is explicitly read. It must not send hardware commands.

### Stage 8: YOLO bbox to 3D balloon

Inputs:

- bbox center `(x_norm, y_norm)`
- bbox area ratio
- camera horizontal/vertical FOV
- calibrated/estimated balloon physical size if available
- current yaw/pitch pose

Logic:

- convert normalized image coordinates to camera ray
- estimate relative depth from bbox area
- place red sphere/balloon along camera ray
- transform from camera frame into world frame using current digital twin pose
- show target relative to camera FOV and launcher axis

Outputs:

- `target_world_position`
- `bearing`
- `elevation`
- `relative_depth`
- `inside_camera_fov`
- `launcher_axis_error`
- `fire_gate_visual_status`

### Stage 9: Validation gates

Phase cannot be accepted until:

- browser top/front/side/rear views match FreeCAD reference views
- camera part color/position matches FreeCAD or is explicitly overlay-only
- no browser overlay is mistaken for real CAD geometry
- yaw motion moves the same group as physical X/azimuth step motor
- pitch motion moves the same group as physical Y/elevation step motor
- balloon appears on the same side as YOLO bbox
- balloon depth changes with bbox area
- all safety flags remain read-only

## Recommendation

Continue with web as the operator cockpit, but stop treating GLB conversion as sufficient. Build a CAD-semantic offline authoring pipeline first.

Desktop/FreeCAD integration becomes useful if:

- OCCT XDE extraction cannot be run reliably in scripts
- manual joint/pivot picking is faster in a FreeCAD macro/workbench
- the project needs direct STEP inspection/editing by the operator

Best architecture:

- FreeCAD/OCCT offline authoring and validation
- exported semantic GLB + JSON contracts
- web cockpit for live operator visualization and KTR presentation

## Safety Boundary

This plan is visualization-only.

- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path.
- No serial TX.
- No Pico command sending.
- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`

