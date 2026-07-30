# Phase 48 Performance and Rendering Strategy

Rendering strategy:
- Three.js is loaded with dynamic import inside the cockpit digital twin panel.
- Raw STL parsing is not used at runtime.
- No postprocessing is used.
- No high-poly CAD mesh is rendered as the hero scene.
- Low-poly primitives use simple materials.
- Render loop is capped by mode.

Caps:
- LOW / KTR demo: 10 FPS.
- Balanced: 15 FPS.

Bundle result:
- Cockpit chunk remains small; Three.js is emitted as a separate lazy chunk.
- Camera responsiveness is protected by avoiding heavy STL parsing and postprocessing.

