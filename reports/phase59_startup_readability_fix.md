# Phase 59: Startup Readability Fix

## Changes Summary
All panel dimensions, font sizes, LED indicators, and button scales increased for comfortable readability at 1920x1080.

| Element | Before | After |
|---------|--------|-------|
| Brand title | 22px | 30px |
| Brand subtitle | 11px | 14px |
| Panel title | 10px | 13px |
| Left panel width | 370px | 420px |
| Right panel width | 320px | 380px |
| Diag row title | 11px | 14px |
| Diag row subtitle | 9px | 11px |
| Diag row min-height | — | 60px |
| Status badge font | 8px | 11px |
| LED dot size | 8px | 10px |
| Detail text | 10px | 12px |
| Summary label | 10px | 12px |
| Summary value | 10px | 13px |
| Safety row font | 11px | 13px |
| Primary button font | 14px | 16px |
| Primary button padding | 16px 48px | 22px 56px |
| Primary button min-width | — | 300px |
| Secondary button font | 10px | 12px |
| Secondary button padding | 14px 28px | 20px 36px |
| Clock font | 22px | 26px |
| Mode value font | 12px | 14px |

## Responsive Behavior
Added `@media (max-width: 1400px)` breakpoint that stacks panels vertically with scrollable viewport.

## Background Image
Unchanged — `ilk_acilis_ekrani.png` remains as fullscreen cinematic hero. Device visibility preserved.
