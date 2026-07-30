# Phase 51 - YOLO Toggle Verification

The camera panel keeps the perception controls:

- YOLO ON: detection active
- YOLO OFF: camera-only mode

When YOLO is OFF:
- camera UI remains available
- live target detection is not claimed
- physical command state is unchanged

This toggle is perception/inference UI only. It does not enable fire, motion, serial TX or hardware commands.

no_physical_command_generated=true
