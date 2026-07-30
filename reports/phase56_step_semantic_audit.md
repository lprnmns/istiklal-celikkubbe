# Phase 56 STEP Semantic Audit

- Source: `work/ktr1.step`
- FreeCAD part features: `136`
- STEP assembly records: `39`
- STEP color records: `15`
- Exact assembly tree available: `False`
- Materials preserved: `False`

## Diagnosis

CAD assembly/material/joint semantics are not preserved into the GLB/runtime contracts.

The source geometry is present. The current blocker is CAD semantic extraction: hierarchy, colors, validated joints, pivots and canonical device frame.

## Safety

- `physical_command_enabled=false`
- `serial_tx_enabled=false`
- `no_physical_command_generated=true`
