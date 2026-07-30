# Phase 41 KTR Cockpit Visual Polish

Phase 41 focuses on a cleaner KTR screenshot mode at `/cockpit?ktr_demo=1`.

Visual improvements:

- Top bar includes the read-only digital twin subtitle.
- KTR mode is shown only when the `ktr_demo=1` query parameter is present.
- Camera panel uses truth-first fixture labelling in KTR mode.
- Digital twin scene shows STL asset status, estimated camera/launcher anchors, 30 mm offset, target projection semantics and no-physical-command labels.
- Bottom operator panels now expose useful evidence values rather than repeated placeholder rows.

The cockpit remains a software/evidence/readiness layer. It does not control hardware.

Safety: `physical_command_enabled=false`, `serial_tx_enabled=false`, `no_physical_command_generated=true`.
