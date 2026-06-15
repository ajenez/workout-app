# assets/

Static image assets for the app (allowed as of Phase 4 — the app is no longer a
single file, but it's still a static site with no build step).

## Muscle map artwork (Phase 4 — needed to build the clickable body map)

Drop the front and back anatomical illustrations here with these exact names:

- `body-front.png`
- `body-back.png`

(`.jpg` or `.svg` are fine too — just tell me the names if you use a different
extension.)

### What the images need
- **Two views:** one front, one back (anatomical / muscular).
- **Anatomically correct**, with **visually distinct muscle regions** so the
  clickable zones can be aligned to each muscle.
- Must cover the 13 groups the app uses: **chest, back (lats), shoulders, biceps,
  triceps, forearms, traps, abs, lower back, glutes, quads, hamstrings, calves.**
- **Plain or transparent background** (the app is a dark theme — transparent PNG
  reads best).
- **Tall enough to be crisp:** ~800–1200px tall.
- **Same framing/scale** for front and back if possible (makes the toggle feel
  consistent).

### Licensing
Use artwork you have the rights to (purchased stock, CC-licensed with attribution,
or public domain). That's on you to confirm — I won't source proprietary images.

### What happens next
Once the files are here, I'll: read them, map each of the 13 muscle groups to a
transparent clickable hotspot over the image, add a front/back toggle, and wire taps
to open that muscle's exercises. The existing muscle-chip list stays as the reliable
mobile fallback.
