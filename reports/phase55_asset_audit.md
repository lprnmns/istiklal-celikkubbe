# Phase 55 CAD / Asset Audit

- Source STEP: `ktr1.step`
- FreeCAD import available: `True`
- Imported document objects: `316`
- Valid shape count: `136`
- Solid count: `136`
- Face count: `19710`
- Estimated triangles: `1137356`
- STEP color records: `15`
- Front launcher/camera detail detected: `True`

## Hierarchy Finding

Installed FreeCAD import exposes many Part::Feature objects with labels, but no validated revolute assembly hierarchy or joint metadata. Phase 55 creates explicit curated grouping metadata instead of claiming exact CAD kinematics.

## Kinematic Group Candidates

- `static_root`: 2 nodes. `alt gövde`, `tabla`
- `yaw_group`: 105 nodes. `608zz rulman v1`, `608zz rulman v001`, `608zz rulman v002`, `608zz rulman v003`, `608zz rulman v004`, `608zz rulman v005`, `608zz rulman v006`, `608zz rulman v007`, `608zz rulman v008`, `608zz rulman v010`, `608zz rulman v011`, `608zz rulman v012`
- `pitch_group`: 29 nodes. `üst sol`, `üst dişli kutusu`, `üst sonsuz dişl`, `üst dişli 20`, `608zz rulman v090`, `608zz rulman v091`, `608zz rulman v092`, `608zz rulman v093`, `608zz rulman v094`, `608zz rulman v095`, `608zz rulman v096`, `608zz rulman v097`
- `camera_group`: 1 nodes. `kamera v3`
- `launcher_group`: 1 nodes. `Bileşen13`
- `decorative_static_covers`: 0 nodes. 

## Pivot / Anchor Candidates

- `yaw_pivot`: `[0.0, 1.203106668819954, 0.5256064561003859]` (heuristic from yaw-group and static-root bounding boxes)
- `pitch_pivot`: `[0.015260869055929382, 0.9076110155082193, -0.01325078122931378]` (heuristic center of front pitch/camera/launcher candidates)
- `camera_origin`: `[0.4990517263104269, 0.7325744139457206, 1.0333570163955847]` (camera label/bounding-box center or manual fallback)
- `launcher_origin`: `[-0.3052167867840203, 0.6843420314644938, 1.2640364598206508]` (launcher/long-forward part center or manual fallback)
- `target_projection_anchor`: `[0.4990517263104269, 0.7325744139457206, 0.03335701639558475]` (camera origin forward projection)
- `no_go_zone_anchor`: `[1.62, 0.18, -3.75]` (existing tactical scene visualization anchor)

## Part Samples

| Label | Group | Runtime bbox min | Runtime bbox max | Triangles |
| --- | --- | --- | --- | ---: |
| `608zz rulman v1` | `yaw_group` | `[0.7486070435879222, 0.8458082855664648, 0.1483629344334177]` | `[0.7749032189374933, 0.8721044609160358, 0.17465910978298874]` | 7894 |
| `608zz rulman v001` | `yaw_group` | `[0.7486070435879222, 0.8641430599946582, 0.11029038303194642]` | `[0.7749032189374933, 0.8904392353442292, 0.13658655838151748]` | 7894 |
| `608zz rulman v002` | `yaw_group` | `[0.7486070435879222, 0.9053409241735699, 0.10088723937429829]` | `[0.7749032189374933, 0.9316370995231411, 0.12718341472386935]` | 7894 |
| `608zz rulman v003` | `yaw_group` | `[0.7486070435879222, 0.9383790460932013, 0.12723426242385713]` | `[0.7749032189374933, 0.9646752214427725, 0.1535304377734282]` | 7894 |
| `608zz rulman v004` | `yaw_group` | `[0.7486070435879222, 0.9383790460932011, 0.1694916064429789]` | `[0.7749032189374933, 0.9646752214427721, 0.19578778179254994]` | 7894 |
| `608zz rulman v005` | `yaw_group` | `[0.7486070435879222, 0.9053409241735693, 0.19583862949253716]` | `[0.7749032189374933, 0.9316370995231402, 0.2221348048421082]` | 7894 |
| `608zz rulman v006` | `yaw_group` | `[0.7486070435879222, 0.8641430599946578, 0.18643548583488848]` | `[0.7749032189374933, 0.890439235344229, 0.21273166118445952]` | 7894 |
| `608zz rulman v007` | `yaw_group` | `[0.7385662641114105, 0.8549441514887952, 0.10880217933802386]` | `[0.784943998414005, 0.9603618370291538, 0.21421986487838257]` | 9576 |
| `608zz rulman v008` | `yaw_group` | `[0.7385079606739913, 0.8287690118818354, 0.08262703973106397]` | `[0.7850023018514242, 0.9865369766361138, 0.24039500448534246]` | 11532 |
| `üst sol` | `pitch_group` | `[-0.716649232097225, 0.09493284192894264, -1.339139952111462]` | `[-0.3082801509402735, 1.7199721724318353, 0.019065123893092433]` | 18016 |
| `üst dişli kutusu` | `pitch_group` | `[-0.7321063885598408, 0.20126106036504626, -1.2207817201564946]` | `[-0.3745340570868373, 0.5457813723271936, -0.7238774240572545]` | 19740 |
| `üst sonsuz dişl` | `pitch_group` | `[-0.5787502698036399, 0.2012610603650486, -0.9268040133639597]` | `[-0.4485842469600228, 0.5168142771166413, -0.7992172326988626]` | 8548 |
| `üst dişli 20` | `pitch_group` | `[-0.5732957755265381, 0.23666974872829932, -1.1897900128989007]` | `[-0.4540387444626997, 0.5284821930357613, -0.8979775685914392]` | 4952 |
| `608zz rulman v010` | `yaw_group` | `[0.5779849290155382, 1.3857653687225575, 0.14837094389317976]` | `[0.604276681026968, 1.4120418022181314, 0.17465110032322667]` | 7894 |
| `608zz rulman v011` | `yaw_group` | `[0.5657165702849484, 1.3993907614651648, 0.11029839249170849]` | `[0.5920083222963781, 1.425667194960739, 0.1365785489217555]` | 7894 |
| `608zz rulman v012` | `yaw_group` | `[0.5381498184462238, 1.4300067410504438, 0.10089524883406036]` | `[0.5644415704576535, 1.4562831745460176, 0.12717540526410737]` | 7894 |
| `608zz rulman v013` | `yaw_group` | `[0.5160429998931831, 1.4545588503985094, 0.1272422718836191]` | `[0.542334751904613, 1.4808352838940833, 0.15352242831366614]` | 7894 |
| `608zz rulman v014` | `yaw_group` | `[0.5160429998931833, 1.4545588503985094, 0.16949961590274085]` | `[0.5423347519046132, 1.4808352838940833, 0.19577977233278787]` | 7894 |
| `608zz rulman v015` | `yaw_group` | `[0.5381498184462241, 1.4300067410504433, 0.19584663895229923]` | `[0.5644415704576539, 1.4562831745460174, 0.22212679538234625]` | 7894 |
| `608zz rulman v016` | `yaw_group` | `[0.5657165702849486, 1.3993907614651646, 0.18644349529465043]` | `[0.5920083222963785, 1.4256671949607385, 0.21272365172469745]` | 7894 |
| `608zz rulman v017` | `yaw_group` | `[0.5175951593888726, 1.3926029700868496, 0.12159138064383704]` | `[0.5994932282170587, 1.4775777617744779, 0.2014306635725694]` | 9576 |
| `608zz rulman v018` | `yaw_group` | `[0.4934086190752787, 1.3662769928577332, 0.0886543775441845]` | `[0.6236797685306525, 1.5039037390035943, 0.23436766667222192]` | 11532 |
| `608zz rulman v020` | `yaw_group` | `[-0.7309120468315446, 0.8767156346884231, 0.14837094389317984]` | `[-0.7046238809417356, 0.9030118100379942, 0.17465110032322675]` | 7894 |
| `608zz rulman v021` | `yaw_group` | `[-0.7309120468315446, 0.8950504091166165, 0.11029839249170857]` | `[-0.7046238809417356, 0.9213465844661877, 0.1365785489217556]` | 7894 |
| `608zz rulman v022` | `yaw_group` | `[-0.7309120468315446, 0.9362482732955282, 0.10089524883406036]` | `[-0.7046238809417356, 0.9625444486450991, 0.12717540526410737]` | 7894 |
| `608zz rulman v023` | `yaw_group` | `[-0.7309120468315446, 0.9692863952151596, 0.12724227188361903]` | `[-0.7046238809417356, 0.9955825705647308, 0.15352242831366603]` | 7894 |
| `608zz rulman v024` | `yaw_group` | `[-0.7309120468315446, 0.9692863952151594, 0.16949961590274076]` | `[-0.7046238809417356, 0.9955825705647308, 0.1957797723327878]` | 7894 |
| `608zz rulman v025` | `yaw_group` | `[-0.7309120468315446, 0.9362482732955275, 0.19584663895229923]` | `[-0.7046238809417356, 0.9625444486450989, 0.22212679538234625]` | 7894 |
| `608zz rulman v026` | `yaw_group` | `[-0.7309120468315446, 0.8950504091166163, 0.18644349529465054]` | `[-0.7046238809417356, 0.9213465844661872, 0.21272365172469757]` | 7894 |
| `608zz rulman v027` | `yaw_group` | `[-0.7409528263080564, 0.8986282903157297, 0.12159138064383704]` | `[-0.6945750920054619, 0.9784923964461361, 0.2014306635725694]` | 9576 |
| `608zz rulman v028` | `yaw_group` | `[-0.7409528263080629, 0.8656810466197129, 0.0886543775441845]` | `[-0.6945750920054552, 1.0114396401421528, 0.23436766667222192]` | 11532 |
| `608zz rulman v030` | `yaw_group` | `[-0.5374567255558222, 1.4102499246842086, 0.14837094389317976]` | `[-0.5111625527236882, 1.4365401632885748, 0.17465110032322667]` | 7894 |
| `608zz rulman v031` | `yaw_group` | `[-0.5244920822261209, 1.4232145680139099, 0.11029839249170849]` | `[-0.49819790939398695, 1.449504806618276, 0.1365785489217555]` | 7894 |
| `608zz rulman v032` | `yaw_group` | `[-0.4953607930948105, 1.452345857145221, 0.10089524883406026]` | `[-0.4690666202626764, 1.4786360957495872, 0.12717540526410728]` | 7894 |
| `608zz rulman v033` | `yaw_group` | `[-0.47199931304777143, 1.4757073371922607, 0.12724227188361903]` | `[-0.44570514021563745, 1.5019975757966268, 0.15352242831366603]` | 7894 |
| `608zz rulman v034` | `yaw_group` | `[-0.4719993130477716, 1.4757073371922602, 0.16949961590274076]` | `[-0.4457051402156376, 1.5019975757966266, 0.1957797723327878]` | 7894 |
| `608zz rulman v035` | `yaw_group` | `[-0.495360793094811, 1.4523458571452206, 0.19584663895229915]` | `[-0.4690666202626769, 1.478636095749587, 0.22212679538234617]` | 7894 |
| `608zz rulman v036` | `yaw_group` | `[-0.5244920822261213, 1.4232145680139099, 0.18644349529465043]` | `[-0.4981979093939872, 1.449504806618276, 0.21272365172469745]` | 7894 |
| `608zz rulman v037` | `yaw_group` | `[-0.5316503938930588, 1.4160503196017675, 0.12159138064383694]` | `[-0.44809945998400674, 1.49960125351082, 0.2014306635725694]` | 9576 |
| `608zz rulman v038` | `yaw_group` | `[-0.5569143526894191, 1.390786360805407, 0.0886543775441844]` | `[-0.4228355011876465, 1.5248652123071806, 0.23436766667222192]` | 11532 |

## Asset Inventory

| Path | Ext | Size | Loads | Mesh/triangles |
| --- | --- | ---: | --- | --- |
| `frontend/public/assets/digital-twin/ktr1_binary.stl` | `.stl` | 10025684 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_colored_step_hero.glb` | `.glb` | 29333316 | True | node_count=136; mesh_count=136; triangle_count=406344 |
| `frontend/public/assets/digital-twin/ktr1_colored_step_hero_manifest.json` | `.json` | 4695 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_freecad_fidelity.glb` | `.glb` | 31990320 | True | node_count=136; mesh_count=136; triangle_count=443246 |
| `frontend/public/assets/digital-twin/ktr1_freecad_fidelity_manifest.json` | `.json` | 5795 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54.glb` | `.glb` | 109161316 | True | node_count=137; mesh_count=137; triangle_count=1515048 |
| `frontend/public/assets/digital-twin/ktr1_hybrid_fidelity_phase54_manifest.json` | `.json` | 6370 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55.glb` | `.glb` | 94723640 | True | node_count=136; mesh_count=136; triangle_count=1314536 |
| `frontend/public/assets/digital-twin/ktr1_kinematic_world_phase55_manifest.json` | `.json` | 6609 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_kinematics.json` | `.json` | 11728 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_operator_hero.glb` | `.glb` | 14438560 | True | node_count=1; mesh_count=1; triangle_count=200512 |
| `frontend/public/assets/digital-twin/ktr1_operator_hero_manifest.json` | `.json` | 2651 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_step_hifi_phase54.glb` | `.glb` | 94723640 | True | node_count=136; mesh_count=136; triangle_count=1314536 |
| `frontend/public/assets/digital-twin/ktr1_step_hifi_phase54_manifest.json` | `.json` | 5970 | True | n/a |
| `frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54.glb` | `.glb` | 14437792 | True | node_count=1; mesh_count=1; triangle_count=200512 |
| `frontend/public/assets/digital-twin/ktr1_stl_geometry_phase54_manifest.json` | `.json` | 1619 | True | n/a |
| `ktr1.step` | `.step` | 27237470 | True | advanced_face_count=15600 |
| `ktr1.stl` | `.stl` | 57136553 | True | n/a |
| `reports/cockpit_phase40_ktr_demo_contract.json` | `.json` | 636 | True | n/a |
| `reports/cockpit_phase41_operator_panel_contract.json` | `.json` | 878 | True | n/a |
| `reports/digital_twin_asset_contract.json` | `.json` | 643 | True | n/a |
| `reports/digital_twin_asset_registry.json` | `.json` | 2536 | True | n/a |
| `reports/digital_twin_asset_transform_contract.json` | `.json` | 674 | True | n/a |
| `reports/digital_twin_ktr_story_contract.json` | `.json` | 1574 | True | n/a |
| `reports/digital_twin_live_state_contract.json` | `.json` | 927 | True | n/a |
| `reports/digital_twin_phase32_replay_fixture.json` | `.json` | 6196 | True | n/a |
| `reports/digital_twin_phase39_asset_manifest.json` | `.json` | 395 | True | n/a |
| `reports/digital_twin_phase39_scene_contract.json` | `.json` | 451 | True | n/a |
| `reports/digital_twin_phase40_asset_manifest.json` | `.json` | 607 | True | n/a |
| `reports/digital_twin_phase40_scene_contract.json` | `.json` | 884 | True | n/a |
| `reports/digital_twin_projection_contract.json` | `.json` | 1680 | True | n/a |
| `reports/digital_twin_projection_semantics_contract.json` | `.json` | 566 | True | n/a |
| `reports/digital_twin_state_contract.json` | `.json` | 3700 | True | n/a |
| `reports/hardware_required_next_steps.json` | `.json` | 2168 | True | n/a |
| `reports/operator_panel_data_contract.json` | `.json` | 882 | True | n/a |
| `reports/phase50_colored_step_asset_contract.json` | `.json` | 424 | True | n/a |
| `reports/phase50_step_conversion_manifest_contract.json` | `.json` | 511 | True | n/a |
| `reports/phase51_freecad_visual_reference_contract.json` | `.json` | 342 | True | n/a |
| `reports/phase52_freecad_match_contract.json` | `.json` | 384 | True | n/a |
| `reports/phase54_step_conversion_contract.json` | `.json` | 384 | True | n/a |
| `reports/phase54_stl_fallback_contract.json` | `.json` | 298 | True | n/a |
| `reports/phase55_glb_node_hierarchy.json` | `.json` | 39242 | True | n/a |

## Safety

- This audit is read-only.
- No motor/fire/servo/GPIO/PWM/STEP-DIR/hardware-enable path was added.
- `physical_command_enabled=false`.
- `serial_tx_enabled=false`.
- `no_physical_command_generated=true`.
