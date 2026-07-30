# Phase 56 Revision - Single Engagement Ray Fix

Status: implemented.

Primary engagement ray:
- Exactly one primary ray is rendered in Clean/Tactical when `Engagement Ray On`.
- Origin: `launcher_muzzle_anchor`.
- End: selected target world position.
- Visual style: yellow, thicker cylinder-like geometry.

Debug-only helpers:
- Camera-to-target helper rays are only shown in Debug.
- Camera axis and launcher axis extension lines are only shown in Tactical/Debug helper mode.

The primary ray is named in code as:

`primary_virtual_engagement_ray_launcher_muzzle_to_selected_target`

