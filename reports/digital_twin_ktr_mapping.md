# Digital Twin KTR Mapping

Safety invariant: `no_physical_command_generated=true`

| KTR area | Phase 31/32 evidence | Value |
| --- | --- | --- |
| 4.1 System architecture | `digital_twin_state_contract.json`, cockpit panel | Shows the read-only data path from camera/tracker state to visual twin. |
| 4.2 Software architecture | backend schemas/service/API, frontend store/component | Separates evidence UI from command services. |
| 4.3 Algorithms | tracker error and target pose mirror | Makes aim/tracking behavior inspectable without changing the tracker. |
| 4.4 Interface design | optional cockpit panel with fallback | Reduces demo confusion while keeping old flow intact. |
| 5 Testing | deterministic fixture/replay tests | Device-unavailable validation remains reproducible. |
| 6 Safety | command-authority false invariant | Proves 3D UI cannot fire or move hardware. |
| 9 Reporting | screenshots and markdown summaries | Report-ready artifacts for jury review. |

Boundary statement: the digital twin is an observability and evidence layer. It
does not own command authority and cannot bypass existing safety contracts.
