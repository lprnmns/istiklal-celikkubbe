# Target Model Asset Inventory

Phase: 31/32

Safety invariant: `no_physical_command_generated=true`

The uploaded `.model` files are inventoried as 3MF model candidates. Their
semantic target classes are intentionally not invented in Phase 31/32. Phase 33
may bind validated competition classes after model conversion and calibration.

| Source file | Size bytes | SHA-256 | Draft class id | Planned GLB path | Status |
| --- | ---: | --- | --- | --- | --- |
| `object_18.model` | 1,593,671 | `5a87103883f89d92206c9c2703ec63068a73403998d5df6dcf66b49490e50a08` | `class_01_candidate` | `frontend/public/models/targets/class_01.glb` | planned |
| `object_19.model` | 50,215,966 | `fc15f070f50663d813d7863df84a415aa732c410e9f121a7e9a7e8a36f37602e` | `class_02_candidate` | `frontend/public/models/targets/class_02.glb` | planned |
| `object_20.model` | 57,120,249 | `20d7b043c78ddc50d36f47b199b7b6a52b81bf233a58fd158ec1daee592929bf` | `class_03_candidate` | `frontend/public/models/targets/class_03.glb` | planned |
| `object_21.model` | 58,943,183 | `2ddf78ff54b12b59d142f8895d7d85959f0a343ba227a75b2627cc6455f42f0b` | `class_04_candidate` | `frontend/public/models/targets/class_04.glb` | planned |
| generated fallback | n/a | n/a | `balloon_fallback` | `frontend/public/models/targets/balloon_fallback.glb` | procedural fallback |
| generated fallback | n/a | n/a | `unknown_target` | `frontend/public/models/targets/unknown_target.glb` | procedural fallback |

## Path Convention

- Device rig: `frontend/public/models/istiklal_c2/istiklal_c2_rigged.glb`
- Target GLBs: `frontend/public/models/targets/<class_id>.glb`
- Fallback GLBs: `frontend/public/models/targets/balloon_fallback.glb`,
  `frontend/public/models/targets/unknown_target.glb`

## Registry Contract

Each registry entry must include `class_id`, `label`, `model_path`,
`source_file`, `source_sha256`, `scale`, `rotation_offset_deg`,
`position_offset_m`, `confidence_min`, and `status`.

No model conversion or viewer action may generate a physical command.
