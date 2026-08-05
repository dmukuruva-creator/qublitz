# QuBlitz Overhaul Plan — Fixes, Laser-Combat Rework, Assets, Typography

**Created:** 2026-07-25 · **v2 (pressure-tested + engagement framework) same day**
**Author:** David Mukuruva (drafted with Claude)
**v2 changes:** corrections from `docs/OVERHAUL_PLAN_PRESSURE_TEST.md` (Streamlit
upgrade surfaced as a real dependency, `utils` import scope ×10, sig-fig scope ×15,
asset budget tightened, prior-art & pedagogy evidence added) and a new **P6
engagement-economics framework** (MDA / SDT / core-loop / telemetry).
**Inputs:** PI feedback (Mattias Fitzpatrick), two surfaced production bugs, `HANDOFF.md` (2026-07-20), asset/library research (sources at bottom).

**PI's directive, verbatim intent:** the game is too complicated; he wants
"a more interactive game where you shoot lasers and when it hits the other
player it causes a rotation on their Bloch sphere. Those kinds of sequences
make it more engaging." Plus: current typography/fonts are poor and gameplay
is unintuitive.

Priorities are ordered P0 (production is broken) → P5 (platform polish).

---

## P0 — Production fixes (do first, small, independent PRs)

### P0.1 — Streamlit Cloud crash on QuBlitz Arena launch (`KeyError` at import)

**Symptom:** deployed app dies on opening the Arena page with a redacted
`KeyError`; traceback ends in frozen `importlib` frames
(`_find_and_load` → `_find_and_load_unlocked` → `_load_unlocked`) triggered by
`pages/QuBlitz_Arena.py:24` → `from utils.branding import load_logo`.

**Diagnosis (verified locally 2026-07-25):**
- The deployed tree (`/mount/src/qublitz`, i.e. `mvwf/qublitz` main) **does**
  contain `utils/branding.py` and `utils/__init__.py` — this is *not* a
  missing-file `ModuleNotFoundError`.
- The failure signature matches the known Streamlit multipage race: the
  script-runner / LocalSourcesWatcher pops entries (here the `utils` package)
  out of `sys.modules` while another import of the same package is in flight;
  CPython's `_load_unlocked` then hits its final
  `module = sys.modules.pop(spec.name)` and raises `KeyError` from inside
  frozen importlib. It is intermittent — a rerun usually "fixes" it, which is
  exactly why it shows up on cold launches on Cloud.
- Related foot-guns found while diagnosing (fix in the same pass):
  - `dmukuruva-creator/qublitz` (fork) `main` is **missing `utils/branding.py`
    entirely** — any deploy from the fork would hard-crash with
    `ModuleNotFoundError`. Sync fork main with upstream.
  - The fork's `main` has **committed `utils/__pycache__/*.pyc`** files. Stale
    committed bytecode in a deployed tree is asking for exactly this class of
    weirdness. Remove them and add `__pycache__/` to `.gitignore` (upstream
    already dropped them; make sure no branch reintroduces them).

**Fix (belt and suspenders, both cheap):**
1. **Disable the file watcher in deployment** — add `.streamlit/config.toml`:
   ```toml
   [server]
   fileWatcherType = "none"
   ```
   Streamlit Cloud redeploys on push, so the watcher buys nothing in
   production and it is the thread doing the concurrent `sys.modules` pops.
2. **Make the import resilient — this is NOT one page.** Verified 2026-07-25:
   **ten** top-level `from utils…` imports across nine pages plus `home.py`
   (`grep -rn "^from utils" pages/ home.py` — Sonify, IQ_mixer,
   EP_TPD_exploration ×3, Custom_Qubit_Query, Quantum_Measurement_Tutorial,
   Qubit_Simulator, QuBlitz_Arena, home). Every one of them can lose the same
   race. Don't paste ten try/excepts — centralize: a tiny
   `utils/safe_import.py` exposing `resilient(module, name)`:
   ```python
   def resilient(module: str, name: str):
       try:
           return getattr(importlib.import_module(module), name)
       except KeyError:
           # Streamlit's script-runner can pop packages from sys.modules
           # mid-import (multipage race); the retry sees a consistent state.
           return getattr(importlib.import_module(module), name)
   ```
   (the `utils` package itself imports fine by the time this runs — the race
   is on submodule loading; if `utils` itself is the casualty, retry once at
   call sites via the same helper vendored into each page as 3 lines).
3. **Streamlit upgrade is a real workstream, not a checkbox.** Verified:
   `requirements.txt` pins `streamlit==1.39.0`; the theming in P4 needs
   ≥ 1.45 (`[[theme.fontFaces]]`), and newer releases harden the
   script-runner reload path this crash lives in. Treat the bump as its own
   PR with a regression gate: full pytest suite (incl.
   `tests/test_pages_smoke.py`) + manual load of all 9 pages + the Arena
   iframe on the new version, *before* the theming PR stacks on it.

**Acceptance:** Arena page cold-loads cleanly on Streamlit Cloud across ~10
forced reboots; no `KeyError` in Manage-app logs; fork main contains
`utils/branding.py`; no `.pyc` files tracked anywhere.

### P0.2 — Frequency display sig-figs (`4.027000000 GHz`)

**Symptom:** the Ramsey tab shows the reference qubit frequency as
`4.027000000` — nine decimal places of GHz (sub-Hz precision) for a quantity
assigned at MHz-ish precision. Reads as a bug and as false precision.

**Where:** `pages/Custom_Qubit_Query.py`
- `:1093-1100` — `st.number_input(..., step=1e-6, format="%.9f")`
- `:1102` and `:1211` — `st.metric(..., f"{...:.9f} GHz")`
- `:981` — time-domain ωd input, `step=1e-6, format="%.9f"`
- `:855-856` — sweep start/stop use `step=0.01` but `format="%.6f"`
  (format/step mismatch, same class of problem in the other direction).

**Fix:**
- Adopt one rule repo-wide: **the format's decimal places match the step's
  resolution, and displayed precision never exceeds the physics.** Drive/qubit
  frequencies in GHz with `step=1e-6` → `format="%.6f"` (kHz resolution —
  right for Ramsey detuning work); metrics render as
  `f"{x:.6f} GHz"` or, better for readability, `f"{x*1e3:.3f} MHz"` when the
  interesting digits are MHz-scale.
- Sweep start/stop: `step=0.01` → `format="%.2f"` (or raise the step
  resolution if fine control is wanted — pick one, don't mix).
- Audit every `st.number_input`/`st.metric` in `pages/` against the rule.
  Verified scope 2026-07-25: **15 occurrences** of `%.9f`/`:.9f` across
  `pages/` (not just the four lines above) — budget the audit accordingly.
  Laser_Heating_Calculator and Dilution_Refrigerator pages are already
  mostly consistent; Custom_Qubit_Query and Qubit_Simulator are the
  offenders.
- Add a lightweight test: grep-style check or a smoke test asserting no
  `%.9f` remains in `pages/*.py`.

**Acceptance:** reference frequency renders as `4.027000 GHz` (or
`4027.000 MHz`); every numeric widget's format matches its step.

---

## P1 — Ship what's already built (one week of leverage, zero new code)

Branch `feat/freq-fix-and-arena-revendor` (pushed to fork) already contains:
- `fdbffad9` — the Track-A frequency-window fix (default sweep 3.5–5.5 GHz,
  no-peak guard, captions, title de-dup; 22 tests pass).
- `6e17a5af` — the Track-B re-vendor: 7-mission campaign + concept-gating
  shields + Pulse Forge (byte-identical to canonical, physics tests pass).

**Action:** open the PR to `mvwf/qublitz` now, with the P0 fixes either in the
same PR or stacked right behind it. Students currently play a game missing
Missions 4–7 and the entire shield mechanic — this is the single biggest
engagement win available and it is already tested. (Outward-facing: needs
David's explicit go-ahead per HANDOFF policy.)

---

## P2 — "Photon Duel": the laser-combat mode the PI asked for

### Design intent
Do **not** replace the campaign — the 7 missions are the pedagogical payload.
Add a fast, visceral **arcade duel mode** that becomes the *landing*
experience, with the campaign reframed as "Story Mode." The PI's ask maps
beautifully onto real physics — lasers literally *are* how you rotate qubits.

**Why this is pedagogically sound, not chocolate-covered broccoli:** the
mechanic *is* the physics (shooting = driving, dodging = avoiding drive,
shielding = eigenstates). This is textbook **intrinsic integration** — Habgood
& Ainsworth (J. Learning Sciences, 2011) showed intrinsically integrated games
beat extrinsic "quiz-with-a-skin" designs, and follow-up work (CHI PLAY 2022)
identified the mechanism: players attend precisely to the features the game
task needs, so if the game task *is* the physics, attention lands on the
physics. Meta-analyses (Wouters et al. 2013; Clark, Tanner-Smith &
Killingsworth 2016) agree the design, not the medium, carries the learning
effect. Design rule that follows: **every visual effect must encode a state
change** (beam axis = gate axis, sphere swing = actual rotation applied);
decorative-only FX are attention leaks, not juice.

**Prior art (collision check, 2026-07-25):** no shipped game was found that
uses "shots apply Bloch rotations to an opponent whose sphere is their health
bar." Nearest neighbors, worth citing to the PI and stealing UI ideas from:
ScienceAtHome's *Quantum Shooter* (Crimsonland-style shooter whose *reload* is
an optimal-control puzzle — quantum content is bolted on, not the combat
itself), IBM *Hello Quantum* (puzzle), *Quantum Odyssey* (circuit puzzles),
*QubitQuest* (arXiv 2604.24015, Bloch-sphere mini-games, not adversarial),
IQM Academy's Bloch game (guided rotations, no combat). Before pitching
novelty, skim the community list (HuangJunye/Awesome-Quantum-Games) once more.
Differentiator to state explicitly: **adversarial, real-time, and the Bloch
sphere is the game state, not a viewer.**

The mapping:

| Game element | Physics it teaches | Mechanic |
|---|---|---|
| Your ship's "health" | Qubit state | A live mini **Bloch sphere** per player; the state vector *is* your status display |
| Shooting a laser | Drive pulse / gate | Hold-to-charge: rotation angle θ = Ω·t (Rabi!). Tap = small kick, full charge = π-pulse (X gate) |
| Getting hit | Rotation on the Bloch sphere | Opponent's beam applies Rx/Ry/Rz to *your* sphere — exactly the PI's sentence |
| Beam color/type | Gate axis | Red beam = X rotation, blue = Z (phase), green = Y; weapon-switch = axis-switch |
| "Kill shot" | Measurement | A MEASURE beam collapses the target; it only "wins" with probability P(|1⟩) — Born rule as hit chance |
| Dodging | Avoiding drive | Positional dodge (move the ship) — misses apply nothing |
| Shield stance | Phase / eigenstates | Parking your state at |−⟩ makes X-beams do nothing (eigenstate!) — same concept as the campaign's mission shields |
| Vector shrinking over time | T₂ decoherence | Your Bloch vector decays toward the maximally mixed center unless you grab an **echo pickup** (refocus = spin echo) |
| Arena zones (biomes) | Local noise / phase | See "biomes" below — merges with planned B1/B2 mechanics |

Win condition: land a MEASURE beam while the opponent's P(|1⟩) is high (you've
rotated them toward |1⟩ and they failed to rotate back). This makes the core
loop: *rotate them up → stop them rotating you up → measure at the right
moment* — genuinely strategic, and every beat is a real quantum operation.

The existing `QPhysics`/`GATES` engine already computes gates, Bloch vectors,
T₁/T₂ decay, and measurement collapse — the duel mode is a new *presentation*
over the same unit-tested core (same rule as ever: physics engine untouched).

### Where it's built
Author in canonical `Qublitz_Draft` (`QuBlitz Project/quantum_chess.html` or a
sibling `photon_duel.html` sharing the extracted `QPhysics`), then re-vendor.
Never hand-edit `pages/_assets/`.

### Engine/library choices (all MIT/CC0, all inlinable — the game must stay
self-contained, no CDN calls from the Streamlit iframe)
- **Rendering: stay hand-rolled Canvas.** The game already has particles,
  screen shake, beam flash, floating damage text (`quantum_chess.html:2110+`).
  A duel mode is ~1 ship sprite + beams + parallax — Phaser 3 (MIT) is the
  fallback if scope grows, but its ~1.2 MB min bundle inlined into the vendored
  HTML is hard to justify when the juice systems already exist.
- **Particles:** existing in-house FX first; if richer trails/explosions are
  wanted, **Proton** (MIT, lightweight, canvas-friendly) inlines well.
- **Bloch spheres:** for the in-duel mini-spheres, a 2D orthographic
  projection (hand-drawn canvas: circle + great-circle ellipses + vector) is
  cheap, crisp at small sizes, and already matches how the campaign draws
  state. For the big "inspect" view, port ideas from MIT-licensed
  three.js/WebGL Bloch simulators (bits-and-electrons/bloch-sphere-simulator,
  ctokx/blochsphere) — but inlining three.js (~600 KB) is only worth it if we
  make the sphere a marquee visual. Recommendation: 2D projected spheres v1,
  evaluate 3D later.
- **Audio: jsfxr** (procedural 8-bit SFX, a few KB of JS, no audio files) for
  lasers/hits/charge whine — fits the retro aesthetic and keeps the vendored
  file small. For richer sound, Kenney **Sci-fi Sounds** (70 clips, CC0) and
  **Digital Audio** (60 clips, CC0) — pick ≤8 short OGGs, base64-embed,
  budget ≤300 KB total. WebAudio API directly; no howler needed for 8 sounds.

### Asset shopping list (all CC0 unless noted)
| Need | Source | License | Notes |
|---|---|---|---|
| Laser/beam/muzzle sprites | Kenney Particle Pack (80+ sprites); Kenney Space Shooter pack | CC0 | beams, glows, flares; recolorable per gate axis |
| Explosion/spark/trail FX | Kenney Particle Pack; OpenGameArt "Particle Pack 80+" | CC0 | |
| Ship / unit sprites | Kenney Space Shooter, Sci-fi RTS (120+ sprites) | CC0 | match pixel aesthetic |
| Parallax space backgrounds | OpenGameArt "Seamless Space Backgrounds" (32 tiling: 8 purple / 8 blue / 8 green nebulas + 8 starfields, 512² & 1024²); "Stars — parallax backgrounds" | CC0 | 512² tiles compress well for base64 embedding |
| UI chrome (panels, bars, buttons) | Kenney UI Pack — Sci-Fi | CC0 | replaces hand-drawn CSS panels where weak |
| Laser SFX | jsfxr (procedural); Kenney Sci-fi Sounds / Digital Audio; lentikula "Sci-Fi Weapon Shots" (15 × 48 kHz WAV) | CC0 | prefer jsfxr for size |
| Fonts | Google Fonts (OFL) — see P4 | OFL | subset + base64 WOFF2, same pipeline as current |

Budget: $0. Everything above is CC0/OFL. (Paid is only worth revisiting for a
bespoke ship/logo art pass — itch.io asset packs run $5–20 if ever wanted.)

### Biomes / arena backgrounds (merges the PI's "make it visual" with B1/B2)
Give each arena a *biome* that is both scenery and physics:
- **Starfield (calm)** — baseline arena, 2-layer parallax starfield.
- **Nebula (noisy)** — purple nebula tiles = **decoherence zone** (locally
  short T₂; your vector shrinks faster inside). This *is* HANDOFF's B2, now
  with a face. Ties directly to the lab's BCTDS→T₂ research narrative.
- **Phase rift** — shimmer bands that apply a Z-kick when your beam crosses
  them (**B1 interference tiles**, spatialized): shooting *through* a rift
  rotates the beam's axis — positioning starts to matter.
Parallax implementation: 2–3 `<canvas>` layers or CSS `background-position`
scroll, tiles from the CC0 packs above.

### Difficulty / "too complicated" response
- Duel mode opens with **one beam type (X) and the sphere**; Z and Y beams,
  MEASURE, echo pickups unlock across the first three duels (progressive
  disclosure).
- Campaign stays for depth; the duel is the 30-second-to-fun on-ramp.
- Sage AI opponent reuses the offline heuristic at three aggression levels.

### Milestones
- **D0 (spike, ~2 days):** ships + movement + X-beam + 2D Bloch spheres +
  hit-applies-rotation + jsfxr SFX. Playable proof for the PI.
- **D1:** charge-to-θ, beam axes, MEASURE win condition, decoherence decay,
  parallax starfield biome.
- **D2:** nebula + phase-rift biomes (B1/B2), echo pickups, Sage duel AI,
  onboarding overlay, physics regression tests for the new bindings
  (extend `qphysics.test.js`; new `duel_harness.test.js` mirroring
  `mission_shield_harness.test.js` — e.g., "a player parked at |−⟩ takes zero
  net rotation from X-beams").
- **D3:** re-vendor into `qublitz`, wire a mode-select landing screen
  (Duel | Story), instructor export hooks.

**Acceptance:** a new player is shooting and seeing the opponent's Bloch
vector swing within 30 seconds, with no reading required; all existing
campaign/physics tests still pass; vendored file stays under **2 MB**
(currently 516 KB — the HTML is inlined into the iframe srcdoc on every page
load, so the earlier ~7 MB allowance was far too generous; jsfxr-first audio
and 512² tiles keep this easy).

**Scope RESOLVED (David, 2026-07-25):** "the other player" is **bot-level
(Sage AI)** for now — no networked PvP; hot-seat stays a possible later mode
and the design must not preclude it. Full mechanics/asset/bot/test spec now
lives in **`docs/PHOTON_DUEL_DESIGN.md`** — that doc supersedes the sketch
above where they differ.

---

## P3 — Gameplay intuitiveness (campaign + duel)

1. **Pre-roll P(hit) telegraph** (HANDOFF B3 remainder): before an attack
   resolves, show the Born-rule bar filling to P(hit) → roll → crit/miss
   (~400 ms). Combat gets tension *and* the probability becomes legible.
2. **"Why did that happen" feedback:** on every miss/block, a one-line toast
   in plain language ("Blocked: your attacker never passed through
   superposition — apply H first"). The shield missions already know the
   reason; surface it.
3. **First-run tutorial = Mission 0:** 60-second guided duel (move, charge,
   fire, watch the sphere). Skippable, replayable from the help menu.
4. **Gate tooltips everywhere:** hovering X/H/Z shows a 2-frame Bloch
   animation of what it does — reuse the mini-sphere renderer.
5. **Reduce simultaneous UI:** the board + side panels + event log + Sage
   panel all compete. Default-collapse Sage and the event log; one focus
   panel at a time on narrow viewports.
6. **Control hints:** persistent bottom-bar keys/actions strip (the
   arena-accessibility branch's keyboard nav gives this for free — merge it).

---

## P4 — Typography & visual identity (game AND platform)

### The game (authored in canonical, then re-vendored)
Current state: Press Start 2P (pixel) + Space Grotesk, base64-embedded — the
right *pipeline*, wrong *application*: the pixel font is used at 12 px for
dense UI (`quantum_chess.html:155,161,205,248`), which is what reads as "poor
typography." Pixel faces are display faces.
- **Rule: Press Start 2P at ≥17 px, titles/headers/logo only.** Everything
  interactive or dense (stat rows, buttons, log, Sage panel) moves to the body
  face.
- **Add a HUD numerals face:** Rajdhani or Chakra Petch (both OFL, condensed,
  built for dense interfaces) for stats/damage numbers/timers — subset to
  digits+basic Latin, base64 WOFF2, same embedding pattern as now.
- **Type scale:** define 4 sizes (12/14/17/26 → prefer 13/15/18/28) as CSS
  vars; kill ad-hoc `font-size` declarations; line-height ≥1.4 for prose,
  letter-spacing +0.5px on pixel-font headers.
- **Contrast pass:** verify all text ≥4.5:1 against the new nebula
  backgrounds (add a subtle dark scrim behind HUD text over bright biomes).

### The Streamlit platform (whole of QuBlitz, per the PI's note)
Streamlit ≥1.45 supports first-class font theming — no CSS hacks:
- `.streamlit/config.toml`:
  ```toml
  [theme]
  base = "dark"
  font = "Inter"          # or Exo 2 for a sci-fi flavor that stays readable
  headingFont = "Space Grotesk"   # matches the game
  codeFont = "monospace"
  baseFontSize = 16
  [[theme.fontFaces]]
  family = "Space Grotesk"
  url = "app/static/space-grotesk.woff2"
  style = "normal"
  ```
  with font files in `static/` (served by Streamlit) — one theme, every page,
  visually continuous with the embedded game.
- Dark theme palette matched to the game's CSS vars (`--ink`, `--green`,
  etc.) so the iframe no longer looks like a portal into a different product.
- Shared page scaffold: one `utils/page_setup.py` (`set_page(title, icon)`)
  that applies `st.set_page_config`, sidebar branding (via the hardened
  `load_logo`), and the caption footer — kills the per-page copy-paste drift
  that produced the duplicate-title bug.
- Migrate to `st.navigation`/`st.Page` for explicit page ordering, naming,
  and icons (current sidebar order is filename-accidental).
- `home.py` landing: card grid (one card per tool with a thumbnail from
  `images/`), "Start here" ordering for students: Simulator → Arena → Query.

---

## P5 — Platform-wide engineering fixes (exhaustive sweep)

| Item | What / why |
|---|---|
| Repo hygiene | Untrack `.DS_Store`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`; extend `.gitignore`. Fork main is 27 commits divergent — sync with upstream and stop letting fork/upstream drift (P0.1 crash class). |
| Branch triage | ~10 stale local branches (`platform-*`, `arena-pr`, `ci-vendor-check`, …). Merge-or-delete pass with a 15-minute decision per branch. |
| CI | Extend `ci.yml`: run pytest + the node physics test + a vendored-copy freshness check (`diff` canonical vs vendored fails CI when stale — the exact failure mode HANDOFF spent a session on). Add the `%.9f`-style format-lint. |
| Requirements | Pin `streamlit` (≥1.45 for theming), `qutip`, `plotly`; add `requirements-dev.txt` coverage for the node test runner version. |
| Secrets handling | `st.secrets` accesses (`QB_SAGE_PROXY_URL`, hidden ωq) should be `st.secrets.get(...)`-style with explicit fallbacks so a missing secret degrades to a message, never a `KeyError` page crash (same redacted-error class as P0.1). Audit all `st.secrets[...]` bracket accesses. |
| Embed sizing | `_EMBED_HEIGHT = 920` is a fixed guess with a known clipping history (see the comment at `pages/QuBlitz_Arena.py`) — after the duel-mode landing screen exists, re-verify on a 13″ laptop and consider `height` from `st.query_params` or a compact/tall toggle. |
| Accessibility | Merge `arena-accessibility` (keyboard nav + SR announcements) before adding duel mode, so the new mode is built against the a11y patterns rather than retrofitted. |
| Evidence/export | Merge `arena-evidence` (instructor gate-log export) — it is the PI-facing proof-of-learning instrument and pairs with any engagement claim we make about the duel mode. |
| Tests | Port the sig-fig rule, the import-resilience pattern, and the duel harness into the suite; keep the 22-test pytest suite green as the gate for every PR. |
| Naming | Finish the title de-dup (in P1 branch); ensure every page's `st.set_page_config` title matches its sidebar name and URL slug. |

---

## P6 — Engagement & learning-economics framework (v2 addition)

The v1 plan asserted engagement wins ("single biggest engagement win",
"30-seconds-to-fun") without a framework to design against or a way to know
if they landed. This section supplies both. It borrows three lenses from game
development — **MDA** (Hunicke/LeBlanc/Zubek), **SDT/PENS** (Ryan, Rigby &
Przybylski: competence, autonomy, relatedness), and **core-loop / retention
economics** from F2P practice — with one hard constraint the F2P playbook
doesn't have: this is a *course tool for students*, so engagement mechanics
that exploit (variable-ratio reward gambling, streak shame, fear-of-missing-out
timers) are **banned**; the only currency this economy is allowed to mint is
**demonstrated concept mastery**.

### 6.1 MDA ledger — audit every feature at all three layers

| Layer | Question | QuBlitz duel-mode answer |
|---|---|---|
| **Mechanics** (rules) | What can the player *do*? | move, charge (θ=Ω·t), fire per-axis beams, measure, grab echo pickups |
| **Dynamics** (emergent play) | What behavior *emerges*? | rotate-them-up vs. rotate-back races; timing MEASURE around P(\|1⟩); parking at eigenstates to tank; biome positioning |
| **Aesthetics** (felt experience) | What does it *feel* like? | Challenge (duel), Sensation (juice), Discovery (each axis/biome unlock), Expression (loadout of axes), Submission→avoid (no grind) |

Rule: a proposed feature that can't fill all three rows honestly gets cut.
(The campaign's mission shields pass this test; a cosmetic ship-skin shop
would not.)

### 6.2 SDT / PENS — the three needs, mapped

- **Competence** — the sphere gives instant, truthful feedback (PENS:
  "feedback that is clear and consistent" is a top competence driver).
  Mastery curve: X-beam only → Z/Y → MEASURE timing → echo management →
  biome tactics. Each unlock is a *skill* gain, not a stat gain.
- **Autonomy** — mode select (Duel | Story), axis loadout choice, three Sage
  aggression levels chosen by the player, skippable tutorial. Never
  force-funnel through the campaign.
- **Relatedness** — the existing leaderboard + crit/entanglement stats
  (already in the game state: `critCount`, `entanglCount`), hot-seat duels,
  Sage's explanations (`botLastReason` — already tracked, surface it as
  post-round banter), and the instructor debrief making play socially legible
  in class.

### 6.3 Loop economics — three nested loops with explicit sources and sinks

- **Core loop (~10 s):** aim → charge → fire → *read the sphere* → react.
  The "read the sphere" beat is the learning payload; juice exists to make
  that beat legible (P2 rule: every FX encodes a state change).
- **Session loop (~5–10 min):** duel → post-round debrief card ("your killing
  blow: Rx(π) then MEASURE at P=0.93") → unlock/next duel. The debrief is the
  session's reward — it converts a win into an *explanation*, which is the
  transfer instrument the `arena-evidence` branch wants anyway.
- **Meta loop (course-length):** campaign missions certify concepts; concepts
  unlock duel abilities. **Economy design:** the only *source* of duel power
  is clearing a concept mission (Mission 5 phase shield → unlocks Z-beam
  mastery rank); the only *sinks* are cosmetic (beam palettes, ship trim).
  Power never comes from time-grinding or luck — mastery is the currency,
  cosmetics are the spend. This is the engagement-economics inversion of F2P:
  identical loop structure, but the "monetized" resource is understanding.

### 6.4 Difficulty & flow

Keep players in the flow channel with **visible, chosen** difficulty (Sage
levels) plus one hidden assist: if a player loses 3 duels in a row, Sage's
aim error widens ~15% and the debrief says what to try differently. No
invisible rubber-banding beyond that — students talk, and discovered fake
difficulty destroys trust in the physics ("did I really win, or did it let
me?").

### 6.5 Funnel, metrics, and the North Star

Instrument the funnel (the game already logs `gateCounts`, `hitsLanded`,
`guardStats` — extend, don't invent):

```
load → first shot → first sphere-read (opponent vector moved) → first duel
completed → tutorial-free second duel → D1 return → Mission 4+ clear →
debrief exported
```

- **FTUE target:** first shot < 30 s from load, zero reading required
  (industry FTUE practice: meaningful action immediately; sub-30 s tutorials
  correlate with the best D1 numbers).
- **Reference benchmarks** (mobile-game norms, used as *orientation* not
  targets — a course tool's traffic is assignment-driven): D1 35–45%,
  D7 15–25%. For QuBlitz the honest analogs are **return-without-assignment
  rate** and **voluntary session length**.
- **North Star metric:** **concept-evidence per returning session** — count
  of debrief-card events where the winning/losing line correctly names the
  concept (exportable via the instructor gate-log). Raw minutes-played is
  explicitly *not* the North Star; a physics game that maximizes time-on-app
  without mastery evidence is failing, whatever its retention curve says.
- Telemetry stays in the instructor export path (no third-party analytics —
  student data, keep it in the existing CSV/log export the PI already gets).

### 6.6 Playtest cadence (RITE-style)

- D0 spike → PI plays it (the "shoot lasers" sentence came from him; he is
  playtester #0).
- Weekly 3-student think-aloud tests during D1–D3; fix the top observed
  usability break each week before adding features (Rapid Iterative Testing
  & Evaluation, not big-bang playtests).
- Every playtest logs the funnel above; a D-milestone doesn't close if its
  funnel step regresses.

---

## Sequencing summary

1. **Week 1:** P0.1 + P0.2 (small PRs) · open the P1 PR (ships missions 4–7)
   · the Streamlit 1.39→≥1.45 upgrade PR with its regression gate (P0.1.3 —
   everything in P4 stacks on it).
2. **Week 2:** P2 D0 spike **with the P6 funnel events instrumented from day
   one** (retention is designed in, not patched in) → PI plays it
   (playtester #0) · resolve the vs-AI / PvP scope question before D1.
3. **Weeks 3–4:** P2 D1–D2, P3 items 1–3, Streamlit theming (P4), weekly
   RITE playtests (P6.6).
4. **Ongoing:** P5 sweep as PR-sized chores; merge a11y + evidence branches
   before D3 re-vendor; North-Star (concept-evidence per returning session)
   reported to the PI from the first student cohort.

Every game change: author in canonical → test → re-vendor. Every platform
change: branch off `main`, PR to fork, upstream to `mvwf/qublitz`.

---

## Research sources

**Sprites / FX / backgrounds (CC0):**
- Kenney Particle Pack — https://kenney.nl/assets/particle-pack
- Kenney all-CC0 index on OGA — https://opengameart.org/content/all-cc0-uploader-kenney
- OGA Particle Pack (80+ sprites) — https://opengameart.org/content/particle-pack-80-sprites
- OGA Sci-fi RTS (120+ sprites) — https://opengameart.org/content/sci-fi-rts-120-sprites
- OGA Seamless Space Backgrounds (32 tiling nebulas/starfields) — https://opengameart.org/content/seamless-space-backgrounds
- OGA Stars parallax backgrounds — https://opengameart.org/content/stars-parallax-backgrounds
- itch.io CC0 asset collection — https://itch.io/c/965867/cc0-assets

**Audio (CC0):**
- Kenney Sci-fi Sounds (70 clips) — https://kenney.nl/assets/sci-fi-sounds
- Kenney Digital Audio (60 clips) — https://kenney.nl/assets/digital-audio
- lentikula Sci-Fi Weapon Shots (15 WAV) — https://lentikula.itch.io/sci-fi-weapon-shots-sfx-freecc0

**Libraries (MIT):**
- Proton particle engine — https://github.com/drawcall/Proton
- Phaser (fallback engine) — https://phaser.io/download/license
- tsparticles / particles.js — https://github.com/VincentGarreau/particles.js/
- Bloch sphere simulators to port from: https://github.com/bits-and-electrons/bloch-sphere-simulator · https://github.com/ctokx/blochsphere · https://bloch.kherb.io/

**Fonts (SIL OFL via Google Fonts):** Orbitron, Exo 2, Rajdhani, Chakra Petch,
Press Start 2P (already embedded), Space Grotesk (already embedded).
- Gaming font roundups: https://madegooddesigns.com/best-gaming-fonts/ · https://fontadvice.com/font-collections/video-game-ui-fonts/

**Streamlit theming:**
- Customize fonts — https://docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts
- Static font files — https://docs.streamlit.io/develop/tutorials/configuration-and-theming/static-fonts
- config.toml reference — https://docs.streamlit.io/develop/api-reference/configuration/config.toml

**Pedagogy & engagement literature (v2 / P6):**
- Habgood & Ainsworth 2011, intrinsic integration (Zombie Division) — https://www.tandfonline.com/doi/abs/10.1080/10508406.2010.508029
- Cutting & Iacovides 2022, attentional mechanism of intrinsic integration — https://dl.acm.org/doi/abs/10.1145/3549503
- Clark, Tanner-Smith & Killingsworth 2016 / Wouters et al. 2013 meta-analyses (design > medium) — via the Habgood PDF's citations: https://tca2.education.illinois.edu/docs/librariesprovider23/default-document-library/j-of-the-learning-sc-2011-habgood.pdf
- MDA framework — https://en.wikipedia.org/wiki/MDA_framework
- PENS / SDT in games — https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/
- Core loops & retention practice — https://gamedesignskills.com/game-design/core-loops-in-gameplay/ · https://mobilefreetoplay.com/bible/improving-games-retention/ · https://solsten.io/blog/d1-d7-d30-retention-in-gaming
- Retention-metric skepticism (why raw retention isn't the North Star) — https://mobilefreetoplay.com/obsessing-retention-metrics-risks-killing-game/

**Prior-art (collision check):**
- Awesome-Quantum-Games list — https://github.com/HuangJunye/Awesome-Quantum-Games
- ScienceAtHome Quantum Shooter — https://citizensciencegames.com/games/quantum-shooter/
- QubitQuest mini-games — https://arxiv.org/pdf/2604.24015
- IQM Academy Bloch game — https://www.iqmacademy.com/play/bloch/
