# Dark-mode support and UI re-centering

**Type:** UI / theming
**Severity:** medium (cosmetic, but the app is unusable-looking in macOS dark mode and screenshots are needed for publicity)
**Stage:** ui/

## Symptom

1. **Dark mode unreadable.** The UI hardcodes light-mode colours. The accent
   navy `#1e3a6e` is used for label text (`Page 1`, status line, headers); on a
   dark system chrome it is near-invisible. Light-grey panel fills (`#f0f0f0`)
   and forced `white` text backgrounds also clash. The app is effectively
   light-mode-only.
2. **Layout off-centre.** The toolbar row (Mask Mode / Clear Masks / Line Break
   Mode / ¶ controls) packs left, leaving the page view visually off-centre.

## Where the colour is hardcoded

Eight files own colour independently (dispersed authority — see CDP §9/§10):

- `src/philocr/ui/ui_composer.py`
- `src/philocr/ui/tab_factory.py`
- `src/philocr/ui/ui_builder.py`
- `src/philocr/ui/widget_factory.py`
- `src/philocr/ui/dialog_form_builder.py`
- `src/philocr/ui/widgets/stage_progress.py`
- `src/philocr/ui/widgets/scan_area_viewer.py`

Representative offenders: `#1e3a6e` accent text in several files;
`setStyleSheet("background-color: white; color: black;")` and
`"background-color: #f0f0f0;"` in `widget_factory.py`;
`QPalette` forcing `Base=white / Text=black` in `widget_factory.py`;
tab styling in `tab_factory.py`.

## Fix (structural — preferred)

Establish a **single colour authority** rather than patching eight files:

1. One module owns the theme: detect the system scheme
   (`QStyleHints.colorScheme()`, Qt 6.5+) and define the handful of semantic
   colours once — `accent`, `panel`, `text_on_chrome`, `surface`.
2. Have all eight files draw from that module. Delete the hardcoded hexes.
   Many `setStyleSheet` calls disappear entirely: the default Qt palette
   already does the right thing per mode, so the forced white/black overrides
   are *adding* the bug. This fix is net-subtractive.
3. Re-test by launching in both light and dark mode.

A minimal "just make labels legible" patch (swap `#1e3a6e` for a palette-derived
mid-tone, drop forced white backgrounds) is possible in ~20 min, but leaves the
dispersed-authority rot in place — prefer the single-authority version.

## Re-centering

Centre the page-view column / toolbar in the scan-area tab — a layout-stretch
adjustment in `ui_composer.py` (`addStretch` already used at lines ~163/239/241;
balance the toolbar row the same way).

## Acceptance

- App is legible and correct in both macOS light and dark mode (screenshot both).
- Page view / toolbar visually centred.
- `guardian_030_ui_purity` and the full guardian suite clean on touched files
  (styling is safe territory, but run them).
- `pytest tests/ -x -q` green.
