# Build 07-C Planning Note

Date: 2026-09-23

This note records the agreed follow-up scope after Build 07-B Stage 3 runtime acceptance.

## Planned 07-C straight-stair finish work

Build 07-C remains the planned home for straight-stair finish variants and detail work, including:

- `SLOPED_CLOSED` underside alongside the accepted `STEPPED_CLOSED` body,
- tread front overhang / nosing,
- basic front-edge Bevel / Round,
- the straight `SLOPED` Side Board variant,
- preservation of Material and Managed Stair lifecycle contracts.

## User-facing closed-body depth control

Add a user-facing control for the visible closed stair-body depth / soffit depth used by the residential closed-body geometry.

The intent is to let the user make the stair body visually thinner or deeper without changing the Side Board reveal or the 9.5 mm underbody shell thickness.

The current Build 07-B implementation keeps an internal compatibility depth field (`side_board_band_width_mm`, default 150 mm) for the accepted Stage 2 closed body. Build 07-C should review the naming and expose this concept with a clear user-facing label such as:

- `本体下面深さ (mm)` / closed-body depth,

while preserving compatibility with accepted 07-B files.

Important separation of meanings:

- Side Board thickness = Y-direction board thickness,
- Side Board reveal = how far the Side Board projects beyond the stair walking-step contour,
- Underbody shell thickness = physical shell thickness of the underside surface,
- Closed-body depth = visible depth of the closed residential stair body from the walking-step contour toward the soffit.

The 07-C specification must define validation and migration/compatibility behavior before exposing the control.

## Scope boundary

This planning note does not modify Build 07-B production geometry. Build 07-B Stage 4 remains lifecycle/full-regression closure work, not a new geometry-feature stage.
