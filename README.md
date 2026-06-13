# Workout Finder

A simple web app that helps a gym beginner figure out what to do: tap a muscle
group on a diagram of the human body and get a list of beginner-friendly
exercises that train it, each with a link to a YouTube demo of proper form.

Built for the author's girlfriend, who recently started going to the gym and is
sometimes unsure which exercises to do.

---

## Status: v1, working

The whole app is a **single self-contained file: [`index.html`](index.html)**.
No build step, no dependencies, no framework. Open it in any browser, or host it
anywhere static.

Everything below has been built and verified working (front/back view switching,
clicking muscle regions, the quick-pick chips, and the exercise panel).

---

## How to run / share

It's a static file, so any of these work:

- **Locally:** double-click `index.html`, or run a static server in the folder:
  ```bash
  python3 -m http.server 4173
  # then open http://localhost:4173
  ```
- **GitHub Pages (how the author plans to share it):** push the folder to a repo,
  go to Settings → Pages, set source to the `main` branch root. The app will be
  served at `https://<user>.github.io/<repo>/`.
- Or drop it on Netlify / any static host.

> There is also a `.claude/launch.json` configured to serve the folder with
> `python3 -m http.server 4173` for the Claude Code preview tool. Harmless to
> keep or delete.

---

## What it does (features)

- **Body diagram** with a **Front / Back** toggle (two inline SVG figures).
  Major muscle regions are clickable and highlight when selected.
- **Quick-pick chips**: a labeled button for every muscle group below the figure.
  These exist because (a) tapping small SVG regions on a phone is fiddly and
  (b) a beginner may not know where a given muscle is. The chips are the most
  reliable way to navigate; the SVG is the nice-to-have visual.
- **Exercise panel**: when a group is selected it shows that group's exercises,
  each with a plain-English description, a **Beginner / Intermediate** badge, and
  a **▶ Watch** button.
- **Mobile-first** dark UI (she uses it on her phone at the gym). On narrow
  screens the results auto-scroll into view after a selection.

### Covered muscle groups (13)
chest, back (lats), shoulders, biceps, triceps, forearms, core (abs),
lower back, traps, glutes, quads, hamstrings, calves — ~55 exercises total,
weighted toward machines / dumbbells / bodyweight that are easy to learn.

---

## Key design decisions (please preserve unless asked otherwise)

1. **YouTube "Watch" buttons open a search query, not a hardcoded video ID.**
   The link is `https://www.youtube.com/results?search_query=<exercise>+proper+form+tutorial`.
   This was deliberate so links **never go dead**. Do not swap to specific video
   IDs unless the user explicitly asks for curated videos.
2. **Major muscle groups only** (not individual muscles like medial vs lateral
   head) — kept simple because the user is a beginner.
3. **Single self-contained HTML file**, no build tooling — chosen for trivial
   sharing and GitHub Pages compatibility. Don't introduce a framework/build
   step unless the user wants ongoing feature growth.
4. **Chips + SVG both drive the same `show(group)` function** and stay in sync
   (selecting via either highlights both the chip and the muscle region).

---

## Code map (all inside `index.html`)

- **`<style>`** — all CSS. Theme variables are at the top under `:root`
  (`--accent` is the red/coral brand color). Layout is a 2-column grid that
  collapses to 1 column under 760px.
- **Two `<svg>` figures** — `#svg-front` and `#svg-back`. Clickable parts have
  `class="muscle"` and a `data-group="..."` attribute. Non-interactive body
  outline parts use `class="body-base"`. The SVGs are stylized (ellipses /
  rounded paths positioned anatomically), not anatomically precise.
- **`<script>`**:
  - **`DATA`** — the single source of truth for content. An object keyed by
    group id; each entry has `title`, `sub` (subtitle), and `ex` (array of
    `{ name, desc, level }`). **Edit this object to add/remove/change exercises.**
  - **`show(group)`** — renders the exercise panel, highlights the matching
    muscle region(s) and chip.
  - **`setView('front'|'back')`** — toggles which SVG and toggle button is active.
  - **`CHIP_ORDER`** — array controlling the order chips appear; chips are built
    from `DATA` at the bottom of the script.

### To add a new exercise
Find the group in `DATA` and add an object to its `ex` array, e.g.:
```js
{ name: "Incline Push-up", desc: "Hands on a bench, easier than the floor.", level: "Beginner" }
```
That's it — the Watch link and rendering are automatic.

### To add a whole new muscle group
1. Add an entry to `DATA` with a new `group` id.
2. Add a clickable shape with `class="muscle" data-group="<id>"` to the front
   and/or back `<svg>`.
3. Add the `<id>` to `CHIP_ORDER`.

---

## Ideas / backlog (not built)

- Curated specific demo videos instead of search links.
- "Workout of the day" or a beginner full-body routine.
- Favorite / save exercises (localStorage).
- Set/rep guidance per exercise.
- More anatomically detailed SVG figures.
- Personalize (e.g. her name in the title).
