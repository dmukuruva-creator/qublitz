# QuBlitz — Session Handoff

**Purpose:** Let a fresh session pick up the work without re-deriving context.
**Created:** 2026-07-20 · **Updated: 2026-07-25** by David Mukuruva (dmukuruva@gmail.com)
**Repo:** `/Users/davidmukuruva/Developer/qublitz`  ·  **Branch as of 2026-07-25:** `feat/freq-fix-and-arena-revendor` (pushed to origin)
**Origin:** Slack request from Mattias Fitzpatrick (PI, Fitzpatrick Lab, Dartmouth):
1. "Not sure why the qubit frequency cannot be tuned here" → diagnose + fix.
2. "Make the battle sequence more engaging" in QuBlitz Arena → design + build new game mechanics.
David committed to opening a PR + report for #1 and brainstorming mechanics for #2.

---

## ⚡ SESSION 2026-07-25 — EXECUTION QUEUE (start here; written for a lighter model)

Two new production bugs were surfaced (screenshots from David), a
pressure-tested overhaul plan was written, and the game rework was fully
specced. **Your job is to execute the queue below, in order.** Everything
you need is in these three docs — read them before the task that cites them,
not all up front:

| Doc | What it holds |
|---|---|
| `docs/OVERHAUL_PLAN.md` (v2) | P0 bug fixes → P6 engagement framework; the master plan |
| `docs/OVERHAUL_PLAN_PRESSURE_TEST.md` | verified findings + what is/isn't load-bearing |
| `docs/PHOTON_DUEL_DESIGN.md` | complete game spec: mechanics numbers, CC0 asset manifest, Sage bot spec, telemetry schema, test cases, D0–D3 milestones |

**Decisions already made (do NOT re-litigate):**
- Duel opponent = **Sage bot only**. No networked PvP. Design must not
  preclude hot-seat, but don't build it.
- Duel = landing mode; existing 7-mission campaign = "Story Mode".
- Asset budget: vendored `quantum_chess.html` ≤ **2 MB** (currently 516 KB).
  All assets CC0/OFL, base64-embedded, jsfxr-first audio.
- North Star metric: concept-evidence per returning session (not minutes).
- Display precision rule: a widget's `format` decimals == its `step`
  resolution; never exceed physical precision.

**Hard guardrails (violating any of these is worse than doing nothing):**
1. 🚫 **Never `git push`, open a PR, or touch remotes without David's
   explicit go-ahead in the current conversation.** Commit locally freely.
2. 🚫 **Never hand-edit `pages/_assets/quantum_chess.html`.** Game changes go
   in canonical `/Users/davidmukuruva/Developer/QuBlitz Project/`, then
   re-vendor via its `scripts/sync_vendor.sh`.
3. If `pytest` fails after your change and the fix isn't obvious in
   ~2 attempts, revert the change and log what happened under "Executor log"
   below instead of forcing it.
4. Don't commit `.DS_Store`, `__pycache__/`, or any `.venv*`.
5. When a task is done: mark it ✅ here with the commit SHA. Keep this file
   truthful.

### T1 — Fix the Streamlit Cloud crash (KeyError on Arena launch) — P0.1 ✅ done — `cb03ee24` on `fix/arena-import-race`
**Diagnosis (already verified — trust it):** traceback ends at
`pages/QuBlitz_Arena.py:24` (`from utils.branding import load_logo`) inside
frozen importlib. The deployed repo HAS `utils/branding.py`, so it is NOT a
missing file: it's the known Streamlit multipage race — the script-runner/
file-watcher pops `utils` from `sys.modules` mid-import and CPython's
`_load_unlocked` raises `KeyError`. Intermittent; worst on cold loads.
**Steps:**
1. Branch off `main`: `git checkout main && git checkout -b fix/arena-import-race`
2. Create `.streamlit/config.toml`:
   ```toml
   [server]
   fileWatcherType = "none"
   ```
3. Create `utils/safe_import.py`:
   ```python
   """Retry-once import helper for Streamlit's multipage sys.modules race."""
   import importlib


   def resilient(module: str, name: str):
       try:
           return getattr(importlib.import_module(module), name)
       except KeyError:
           # Streamlit's script-runner can pop packages from sys.modules
           # mid-import; a retry sees a consistent state.
           return getattr(importlib.import_module(module), name)
   ```
4. Re-verify the import sites: `grep -rn "^from utils" pages/ home.py`
   (expected 10 hits: Sonify.py:2, IQ_mixer.py:23,
   EP_TPD_exploration.py:10,13,14, Custom_Qubit_Query.py:24,
   Quantum_Measurement_Tutorial.py:11, Qubit_Simulator.py:19,
   QuBlitz_Arena.py:24, home.py:2). Convert each to the helper, e.g.:
   `from utils.safe_import import resilient` then
   `load_logo = resilient("utils.branding", "load_logo")`
   (EP_TPD_exploration needs 5 symbols across its 3 imports — same pattern.)
5. Harden the one bracket-secrets crash of the same class:
   `pages/Qubit_Simulator.py:118` `st.secrets["params"]` →
   `params = st.secrets.get("params")` + if `None`:
   `st.error("Deployment secrets missing [params] — see README."); st.stop()`
6. `pytest` → all tests must pass (suite was 22 green on 2026-07-20).
7. Commit. **Stop — do not push (guardrail 1).**
**Acceptance:** grep from step 4 returns only `safe_import` lines; pytest
green; `.streamlit/config.toml` exists.

### T2 — Sig-fig / number-format fix — P0.2 ✅ done — `bedc7b21` on `fix/sigfigs`
**Symptom:** UI shows `4.027000000 GHz` (nine decimals = sub-Hz false
precision).
**Steps:**
1. Same branch as T1 (or `fix/sigfigs` off main — your call, keep commits
   separate).
2. Find all offenders: `grep -rn "%\.9f\|:\.9f" pages/` (expected 15).
   Known anchors: `pages/Custom_Qubit_Query.py:981, 1097, 1102, 1211`.
3. Apply the precision rule: GHz inputs with `step=1e-6` get
   `format="%.6f"`; metrics become `f"{x:.6f} GHz"` (or
   `f"{x*1e3:.3f} MHz"` where the doc's P0.2 says so). Zero `%.9f`/`:.9f`
   may remain.
4. Fix the inverse mismatch at `pages/Custom_Qubit_Query.py:855-856`
   (`step=0.01` but `format="%.6f"`) → `format="%.2f"`, keep `step=0.01`.
5. Add `tests/test_display_formats.py`: walk `pages/*.py`, assert the
   string `%.9f` and `:.9f` appear nowhere.
6. `pytest` green → commit → **stop, don't push.**

### T3 — Streamlit upgrade with regression gate (unblocks theming) ✅ done — `14f10597` on `chore/streamlit-upgrade`
`requirements.txt` pins `streamlit==1.39.0`; theming (P4) needs ≥ 1.45 and
newer builds harden the T1 race. **Own branch** `chore/streamlit-upgrade`.
**Steps:** bump the pin to the latest 1.x stable → fresh venv → install →
`pytest` (incl. `tests/test_pages_smoke.py`) → `streamlit run home.py` and
manually load every page incl. the Arena iframe. If anything breaks beyond a
trivial API rename: **revert, log findings below, move on** — David decides.

### T4 — Ship the already-built work ⛔ BLOCKED on David
`feat/freq-fix-and-arena-revendor` (commits `fdbffad9` freq-window fix +
`6e17a5af` 7-mission re-vendor) is pushed to origin and ready. Opening the PR
to `mvwf/qublitz` is outward-facing: **ask David, then** open it with a short
report paragraph (A1-by-design vs A2-actual-bug — see Track A below). T1/T2
fixes stack behind it as separate PRs.

### T5 — Streamlit theming + typography (P4) — after T3 lands ⚠️ ATTEMPTED THEN REVERTED — see executor log
**David's correction (2026-07-26): this task was mis-scoped by this doc, or mis-read by the
executor, or both.** The platform-theming half (`.streamlit/config.toml` theme block matching
the platform to the game) touches all 9 Streamlit pages — real, PR-shaped, outward-facing
surface area that needs maintainer sign-off before it's built, not after. The actual intent was
the other direction: fix the **game's own** typography/fonts for readability, in canonical. Do
not restart the platform-theming half without explicit go-ahead. The game-typography half (P4's
first paragraph, "The game (authored in canonical, then re-vendored)") is the correct next step
if this is picked back up — see the executor log for what was learned about it before this was
paused.
Follow `docs/OVERHAUL_PLAN.md` §P4 exactly: `.streamlit/config.toml` theme
block, font files under `static/`, shared `utils/page_setup.py`, dark palette
matched to the game's CSS vars. Game-side type-scale rules are P4's first
half — those edits go in **canonical** (guardrail 2) and can wait for T6.

### T6 — Photon Duel D0 spike — needs a capable session, don't attempt casually
The full spec is `docs/PHOTON_DUEL_DESIGN.md` (§3 mechanics numbers, §6
asset manifest, §10 D0 contents + cut-lines). Work happens in canonical
`QuBlitz Project/`, new mode inside `quantum_chess.html` sharing `QPhysics`;
telemetry events §8 items 1–4 are **in scope for D0**, not later. If you are
a lighter model reading this: T1–T3 + T5 are your lane; leave T6 for David
with a heavier session unless told otherwise. PI (Mattias) is playtester #0
for the D0 build.

### Executor log (append here)
- **2026-07-26 — T1/T2/T3/T5 executed by a lighter session, in order.** All
  four branches created off `main` (T5 stacked on T3), each committed
  locally, **none pushed** (guardrail 1 — no go-ahead was given this pass).
  - **T1** (`fix/arena-import-race`, `cb03ee24`): matched the doc exactly —
    10 import sites converted, `.streamlit/config.toml` created (note:
    `*.toml` is gitignored except `ruff.toml`, so it needed `git add -f`;
    flag this for whoever writes `.gitignore` in P5). Baseline suite on
    `main` is **19 tests**, not 22 — the RESOLUTION LOG's 22-count includes
    `tests/test_freq_window.py`, which only exists on the still-unmerged
    `fix/custom-query-freq-window` branch. 19 passed.
  - **T2** (`fix/sigfigs`, `bedc7b21`): 15 `%.9f`/`:.9f` hits confirmed by
    grep, all fixed. Also applied the same start/stop `step=0.01` →
    `format="%.2f"` fix to `Qubit_Simulator.py:792-793` (the doc only
    named the `Custom_Qubit_Query.py` instance, but `Qubit_Simulator.py` is
    its free-play mirror with the identical bug — fixing one and not the
    other would've reintroduced the inconsistency this task exists to
    kill). `tests/test_display_formats.py` added. 20 passed.
  - **T3** (`chore/streamlit-upgrade`, `14f10597`): bumped to **1.60.0**
    (latest 1.x at time of writing). Fresh venv, 19 passed. "Manually load
    every page" done via headless Chromium (Playwright) against a live
    `streamlit run` — every page incl. the Arena iframe screenshotted, zero
    exceptions, only benign favicon-class 404s in the console. No API
    breakage found — nothing to revert.
  - **T5 — attempted, then REVERTED at David's explicit instruction.** Built
    (branch `feat/streamlit-theming`, stacked on T3): a `[theme]` block
    pulled from `quantum_chess.html`'s `:root` CSS vars, Inter + Space
    Grotesk self-hosted under `static/`, a shared `utils/page_setup.py`
    scaffold, migrated onto all 9 `pages/*.py`. This was **the wrong
    direction** — David's correction: the task was to fix the *game's*
    typography for readability, not re-theme the Streamlit platform to
    match the game. Platform-wide theming across every page is real,
    outward-facing, PR-shaped surface area that needed maintainer sign-off
    *before* being built, not after — same class of mistake guardrail 1
    exists to prevent, just on the "build it" side instead of the "ship it"
    side. **Reverted cleanly**: nothing was ever pushed, so `git branch -D
    feat/streamlit-theming` off `chore/streamlit-upgrade` fully restored all
    9 pages, removed `static/`, `utils/page_setup.py`, and the config theme
    block — verified by `git status` (clean) and a fresh pytest run
    (19 passed, matching the pre-T5 baseline).
  - **What was learned before the revert, relevant to whoever does the real
    game-typography task next:** the canonical game repo
    (`QuBlitz Project/`) already ran its own typography pass —
    `FE-6 — Typography system: pixel font is a headline voice, not a body
    font` (done 2026-07-08, i.e. *before* `OVERHAUL_PLAN.md`'s P4 section was
    written). FE-6 made a deliberate, reasoned call that differs from P4's
    rule: it kept Press Start 2P on buttons/log/modal-titles/Sage-panel
    "flavor" text (floored at a 12px minimum) and moved only four specific
    numeric displays (`.srow .val`, `.gcnt span`, `#sel-eq`, `#timer-chip`)
    to Space Grotesk — not the wholesale "≥17px, titles/headers/logo only,
    everything else to body face" rule P4 states. This means **P4's
    game-typography section is written against a stale premise**, the same
    class of problem the rewritten Track B section already flagged for the
    mission system — whoever picks this up should treat FE-6 as prior art
    to reconcile with, not code to discover from scratch. David's own
    direction (given mid-session, before this got far enough to commit
    anything in the game repo): push P4's stricter rule through anyway,
    overriding FE-6. That work had not yet started when this session ended
    — no canonical-repo files were touched, only read (a `quantum_chess.html`
    boot-screen screenshot was taken for reference, no edits). It also needs
    to respect that repo's own governance: `QuBlitz Project/CLAUDE.md` runs
    under the project-cycle-loop skill (currently cycle 03, `goals_locked:
    true`) — read `.cycle/STATE.md` before editing there.
  - **Not attempted:** T4 (blocked on David) and T6 (explicitly out of a
    lighter session's lane per the doc).
  - **For whoever reviews next:** three branches are ready for PRs once
    David gives the go-ahead — `fix/arena-import-race`, `fix/sigfigs`,
    `chore/streamlit-upgrade`. T5 needs to be redone from scratch, scoped to
    the game repo only (see above), not attempted again as platform theming.

---

## ✅ RESOLUTION LOG — 2026-07-20 (both tracks resolved)

**Track A — RESOLVED.** Frequency-tuning bug fixed, tested, committed (local, not pushed).
- Branch `fix/custom-query-freq-window` (off `main`), commit `9cb12e7a`.
- Root cause confirmed at the physics level with the real Lindblad engine: with the old
  4.8–5.2 GHz default window and a qubit at 4.027 GHz, peak `max P(|1⟩)=0.062` (flat); with
  the new 3.5–5.5 GHz window, peak `=0.987` at ω_q. (See `tests/test_freq_window.py`.)
- Changes (both `pages/Custom_Qubit_Query.py` and `pages/Qubit_Simulator.py`):
  (1) non-debug default window widened 4.8–5.2 → **3.5–5.5 GHz**;
  (2) **no-peak guard** — flat sweep now prints an explicit "widen your range" hint;
  (3) **caption** clarifying ω_q is fixed/hidden and ω_d is the tunable quantity;
  (4) **title de-dup** — free-play page retitled "Qubit Simulator (Free Play)".
- Tests: `22 passed` (full suite), incl. 3 new physics regressions. Run with a venv that has
  `qutip==4.7.6 streamlit plotly pandas` (a throwaway `.venv-run/` was used; it is gitignored-by-name
  intent — delete it, do NOT commit).
- **Remaining for David:** push `fix/custom-query-freq-window` and open the PR to `mvwf/qublitz`
  (outward-facing — deliberately left for an explicit go-ahead).

**Track B — B0 DONE; the rest is delivered-by-vendor or genuinely-future.**
- Branch `chore/re-vendor-game-7-missions` (off `main`), commit `85f5dcf8`.
- Re-vendored the canonical game (`scripts/sync_vendor.sh`). Vendored copy is now
  **byte-identical to canonical** (5,555 lines), `VENDOR_SHA` updated, and the node physics
  regression (`pages/_assets/tests/qphysics.test.js`) reports **ALL CHECKS PASSED**.
- This alone takes the Streamlit-facing game from **3 missions → 7**, and adds the mission-shield
  concept-gating, Pulse Forge, glossary/onboarding, and the instructor gate-log export.
- **B3 (attack juice) reassessed:** already implemented in canonical — screen shake, floating
  crit/damage text, beam flash, particle FX (`quantum_chess.html:2110-2121`). Arrives with the
  re-vendor. Only a *pre-roll P(hit) telegraph* would be net-new polish (optional).
- **Genuinely future (net-new, author in canonical `Qublitz_Draft` then re-vendor):**
  B1 interference tiles (spatial phase) and B2 decoherence zones (local T₂, ties to BCTDS→T₂).
- **Remaining for David:** push `chore/re-vendor-game-7-missions` + PR; decide if/when to build B1/B2.

**Evidence for the PI:** `trackA_before_after.png`, `trackB_before_missions.png`,
`trackB_after_missions.png`, `trackB_after_cards.png` (session scratchpad) + the published report artifact.

---

## 0. Orientation (read first)

- Streamlit multipage app. Engine: `quantum_simulator.py` (single two-level qubit, Lindblad T₁/T₂).
- Pages live in `pages/`. The Arena game is a self-contained HTML embedded via `st.components.v1.html`.
- **Naming trap:** BOTH `pages/Qubit_Simulator.py` and `pages/Custom_Qubit_Query.py` set their page title to **"Custom Qubit Query"** (`Qubit_Simulator.py:786`). The deployed link Mattias sent, `.../Qubit_Simulator`, is `Qubit_Simulator.py`. This mismatch is part of the confusion — fix in Track A step 4.
- Run locally: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && streamlit run home.py`
- Verify pages tool availability: this env has no network to the backend; use `INSTRUCTOR_DEBUG` / secrets paths (below) for local testing.

---

## TRACK A — Frequency-tuning bug (Custom Qubit Query / Qubit Simulator)

### Root-cause summary
Two stacked issues:

**(A1) Intended behavior mistaken for a bug.** `omega_q` (qubit frequency) is NOT a UI input by design — it's a hidden per-student/secret property to be *recovered*, not dialed. You tune the **drive** frequency ωd and read ωq off the resonance peak.
- Custom Query loads it from the student's API record: `pages/Custom_Qubit_Query.py:815`
- Free-play loads it from deployment secrets, labeled "Hidden qubit parameters… intentionally not shown": `pages/Qubit_Simulator.py:772`, `:780-781`
- Pedagogical intent stated at `pages/Custom_Qubit_Query.py:825`.
- The screenshot fields "Start/Stop ωd/2π" are DRIVE controls, not qubit-frequency controls.

**(A2) The real bug — default sweep window doesn't contain the assigned qubit.**
Default drive-sweep window is hardcoded **4.8–5.2 GHz**:
- `pages/Qubit_Simulator.py:790`
- `pages/Custom_Qubit_Query.py:843` (non-debug branch)

But assigned qubit frequencies sit BELOW that window:
- secrets example ωq = **4.027 GHz** (`pages/Qubit_Simulator.py:107`, and `:113`)
- debug test student ωq = **4.671 GHz** (`pages/Custom_Qubit_Query.py:55`)

→ A non-debug student runs the default sweep, the resonance peak is off-screen, and the plot is **flat with no feedback** = looks exactly like "the qubit can't be tuned / doesn't respond."
The DEBUG path hides the bug because it centers the window on `omega_q ± 0.25` (`pages/Custom_Qubit_Query.py:840-841`), which is why whoever tested in debug mode never saw it.

### Fix plan (order matters)
1. **Widen/recenter default window** (the actual fix). In both files, change the non-debug default from `4.8, 5.2` to a window that contains the assigned band — e.g. `3.5, 5.5` GHz — or derive it from the backend's assigned band if one is exposed. Files/lines: `pages/Qubit_Simulator.py:790`, `pages/Custom_Qubit_Query.py:843`.
2. **"No peak found" guard.** After a sweep, if `max(prob_1)` never rises meaningfully above baseline (e.g. peak − median < ~0.1), show `st.info("No resonance in this window — widen your ωd range or lower the start frequency.")` instead of a silent flat plot. Sweep runs at: `Custom_Qubit_Query.py:851+` (`Run Frequency Sweep` button), analogous block in `Qubit_Simulator.py:798+`.
3. **Clarifying caption** under the sweep inputs: "ωq is a fixed hidden property of your qubit. Sweep the **drive** ωd to find it — resonance appears where P(|1⟩) peaks."
4. **De-duplicate page title.** Give free-play `Qubit_Simulator.py` a distinct title (e.g. "Qubit Simulator (Free Play)") so a shared link is self-describing. Change at `pages/Qubit_Simulator.py:786`.

### Acceptance criteria
- Non-debug run on defaults shows a visible resonance peak for a qubit at 4.0–4.7 GHz, OR an explicit "no peak, widen range" message. No silent flat plot.
- Debug mode (`QUBLITZ_INSTRUCTOR_DEBUG=1`, key `b8e60fc199646f8e712948304a65d52cd43b9bc3`) still centers correctly.
- Two pages no longer share the identical title.
- Existing tests pass: `pytest` (config in `pytest.ini`, tests in `tests/`). Add a test asserting the default window contains the debug student's ωq.

### Deliverable
Open the PR David promised Mattias. Branch off `main` (not `simulator-bridges`). Include a short report paragraph explaining A1 vs A2 so Mattias understands the "can't tune ωq" is by-design and what actually broke.

---

## TRACK B — Battle Arena engagement (REWRITTEN 2026-07-20 to factor in existing work)

> ⚠️ **Read this first — most of the original Track B proposal is ALREADY BUILT in canonical.**
> Do NOT rebuild a mission system from scratch. The canonical game (`QuBlitz Project/quantum_chess.html`,
> 5,555 lines) already has a full 7-mission campaign + a "structurally-unwinnable-without-the-concept"
> shield mechanic. The gap is that the **Streamlit-facing vendored copy is a generation behind** and
> students only ever see a fraction of it. Verified with `grep`/`diff` this session.

### What ALREADY EXISTS in canonical (`CAMPAIGN_MISSIONS`, `quantum_chess.html:4358`)
A designed 7-mission campaign, each `{title, intro, winText, setup(game)}`, launched via `startMission(n)` (`:4457`):
1. **The Born Rule** — charge = P(hit); pre-charged enemy forces an X-then-strike (`:4360`)
2. **Decoherence Race** — `turnCap=8`, pre-charged units decay each turn (T₁) (`:4371`)
3. **Bell Pair Trap** — two enemies share |Φ+⟩; correlated collapse, no-signalling (`:4382`)
4. **Superposition Gambit** — target shielded unless attacker has passed through |+⟩ (`shieldNeedsSuperposedAttacker`) (`:4403`)
5. **Phase Gambit** — Knight starts |−⟩, must apply Z→|+⟩ (`shieldNeedsPlusPhaseAttacker`) (`:4413`)
6. **Entanglement Split** — hit the FRONT Bell half to splash the phase-locked rear (`shieldNeedsEntangledSplash`) (`:4425`)
7. **Pulse Forge** — no X gate; BUILD one by tuning amplitude×duration to θ=π (Rabi Ω_R·t=π) (`pulseForgeOnly`, `:4446`)

**Key already-built mechanic — mission shields (GD-3):** `missionShieldBlocks` makes an attack deal 0 dmg / never collapse unless the attacker used the *one* concept-defining gate — a hard gate, not a balance nudge. Proven by `tests/mission_shield_harness.test.js` (X-only policy can NEVER clear missions 4–6; a scripted correct solution always can). **This is stronger than the original doc's "win using only GUARD kills" idea — use it, don't reinvent it.**

Also already in canonical (unmerged branches, see repo topology below): pedagogy/onboarding pass (`arena-pedagogy`), simulator bridges + T₁ import + MEASURE/entanglement deep links (`arena-bridges`), keyboard nav + SR announcements (`arena-accessibility`), evidence-of-learning / transfer instrument / export (`arena-evidence`).

### The actual delta students see today (the real problem)
The **vendored** `qublitz/pages/_assets/quantum_chess.html` (4,325 lines) has **only Missions 1–3**, **zero `missionShield`**, and **no Pulse Forge** (`grep` confirmed: 3 mission titles, 0 shields). So the Streamlit deployment — the thing Mattias plays — is missing the entire pedagogical payload (Missions 4–7 + the concept-gating shields). **`checkWinner` already handles missions; there is nothing to "add a win condition" to — it exists upstream and just hasn't reached the deployment.**

### Reconciliation of the original proposal against what's built
| Original Track-B idea | Status | Action |
|---|---|---|
| B-A mission ladder (First Light, Hold the Line, Phase Lock, Bell Run, Blitz) | **DONE & better** — Missions 1–7 + shields cover Born rule, T₁ race, phase, superposition, entanglement, control | Drop. Re-vendor instead. |
| B-B.3 Bell-pair combo (splash on partner) | **DONE** — Mission 6 `shieldNeedsEntangledSplash` | Drop. |
| B-B.5 Measurement gambit / control layer | **DONE-ish** — Pulse Forge (Mission 7) is the control-layer minigame | Drop as separate item. |
| B-B.1 Interference tiles (spatial phase) | **NOT built** — phase is taught via shields, not board geography | Keep — genuinely additive. |
| B-B.2 Decoherence zones (spatial local T₂) | **NOT built** — ties to lab BCTDS→T₂ research | Keep — genuinely additive. |
| B-B.4 Action-point economy | **NOT built** (Pulse Forge adds a resource feel in 1 mission only) | Keep, but franchise-scope — needs a proposal (see the BR-3 scope note at `:4441`). |
| B-C attack resolution beat | **Partly** — `resolveAttack` (`:1815`) is pure/instant logic returning `{fired,crit,dmg,collapsed}`; check the CALLER for an animation beat before claiming it's missing | Verify, then add juice if absent. |

### Revised plan (priority order)
- **B0 — RE-VENDOR (highest leverage, do first).** Bring the 5,555-line canonical game into `qublitz/pages/_assets/quantum_chess.html` via `QuBlitz Project/scripts/sync_vendor.sh`, as a `chore: re-vendor quantum_chess.html` commit. This alone unlocks Missions 4–7 + shields + Pulse Forge for every student — the single biggest engagement win, and it's already built and tested. Confirm the vendored physics test still passes (`node pages/_assets/tests/qphysics.test.js …`, `ci.yml:42`).
- **B1 — Interference tiles.** Board tiles that apply a Z/phase kick on entry → relative phase gains spatial, tactical meaning beyond the shield missions. New mechanic; author in canonical, then re-vendor.
- **B2 — Decoherence zones ("hot tiles").** Tiles with locally shortened T₂ ("noisy chip region"); directly dramatizes the lab's BCTDS→T₂ research and makes the Dilution-Fridge page's physics playable.
- **B3 — Attack juice** (only if the `resolveAttack` caller has no resolution beat): telegraph P(hit) as a filling bar → roll → crit/miss (~400ms) so combat has tension.
- **B4 — Action-point economy** — franchise-scope tradeoff layer (recharge vs. tempo). Needs its own proposal per the existing BR-3 scope discipline; do not slip it in unscoped.

### Acceptance criteria
- **B0:** Streamlit Arena shows all 7 missions + shield gating; `diff` between canonical and vendored is empty; vendored physics + `mission_shield_harness` tests pass.
- **B1/B2:** new tile types author in canonical with their own physics/regression note; phase-kick / local-T₂ effects derive from the existing `QPhysics`/`GATES` engine, not hand-rolled.
- Physics engine (Lindblad T₁/T₂) untouched; in-game Physics Lab + regression assertions still hold.
- All new game work lands in canonical `Qublitz_Draft` first, then re-vendored — never hand-edited into `pages/_assets/`.

---

## Repo topology & where edits belong (RESOLVED 2026-07-20)

**Two repos, two remotes.**
- **This repo** `qublitz` — local `/Users/davidmukuruva/Developer/qublitz`.
  - `origin` = `https://github.com/dmukuruva-creator/qublitz` (David's fork)
  - `upstream` = `https://github.com/mvwf/qublitz` (the lab's canonical Streamlit repo; `mvwf` = Fitzpatrick lab)
- **Canonical GAME repo** `Qublitz_Draft` — local `/Users/davidmukuruva/Developer/QuBlitz Project`.
  - remote `QuBlitz` = `https://github.com/dmukuruva-creator/Qublitz_Draft`
  - This is where `quantum_chess.html` is authored. Currently on branch `arena-evidence`.

**The game is VENDORED, and the vendored copy is STALE.**
- Canonical `QuBlitz Project/quantum_chess.html` = **5,555 lines**.
- Vendored `qublitz/pages/_assets/quantum_chess.html` = **4,325 lines** → `diff` confirms they DIFFER (~1,230 lines behind).
- CI enforces the vendored physics test (`.github/workflows/ci.yml:42`, `scripts/verify.sh:32-34`); re-vendoring is done by hand via `chore: re-vendor quantum_chess.html` commits. Editing `pages/_assets/quantum_chess.html` directly is WRONG — it gets clobbered on the next re-vendor.

**=> Where each track's edits belong:**
- **Track A (frequency bug)** → `qublitz` repo only. `pages/Custom_Qubit_Query.py` + `pages/Qubit_Simulator.py` are Streamlit pages that exist ONLY here, not in the game repo. Branch off `main`, PR to `origin`, then upstream to `mvwf/qublitz` (same path the merged Arena PRs took).
- **Track B (battle mechanics)** → author in the **canonical game repo `Qublitz_Draft`** (`QuBlitz Project/quantum_chess.html`), THEN re-vendor into `qublitz/pages/_assets/quantum_chess.html` as a separate `chore: re-vendor` commit. Never hand-edit the vendored copy.

**Much of Track B ALREADY EXISTS in canonical branches — check before building:**
The canonical repo predates the vendored snapshot, and already has mission/mechanics work on unmerged branches:
- `arena-pulse-forge` — "Pulse Forge control-layer minigame — **Mission 7** (BR-3)" (missions already exist!)
- `arena-pedagogy` — onboarding/jargon pass, Bloch labels, glossary (PED-1..5)
- `arena-bridges` — T1 import + MEASURE/entanglement deep links (BR-1/2/4)
- `arena-accessibility` — keyboard nav + announcements (GOV-4)
- `arena-evidence` (current) — transfer instrument / export / instructor guide (EV-1..3)
- `c03-cleanup-final` — C03 incentives + input batch, X-lock removal
⇒ **Before implementing Track B, `git -C "QuBlitz Project" log --all` and read the existing mission system.** The design in this doc should be reconciled with (not duplicated over) `arena-pulse-forge`'s Mission framework. The real near-term Track B task may simply be: finish/merge the canonical mission branches, then **re-vendor the current 5,555-line game into `qublitz`** (the Streamlit-facing copy is a full generation behind).

## Current git state (snapshot 2026-07-20 — STALE, see 2026-07-25 queue above)
> 2026-07-25 delta: work now lives on `feat/freq-fix-and-arena-revendor`
> (pushed to origin; combines both resolved tracks). PR still not opened (T4).
- **No open PRs** on either `dmukuruva-creator/qublitz` or `mvwf/qublitz`.
- Arena already **merged to upstream** via PR #28 (`arena-pr`, 2026-07-04) + #27.
- `qublitz` local `main` is **ahead of `origin/main` by 27** (unpushed local commits).
- Current branch `simulator-bridges` has **no upstream tracking** (local-only WIP). Uncommitted: `HANDOFF.md` (new), `.DS_Store`.
- Many unmerged local WIP branches: `platform-home/-page-contract/-perf-gating`, `feature/qublitz-arena` (ahead of origin by 6), `arena-pr`, `ci-vendor-check`, `fix-stale-sage-proxy-refs`.
- Canonical repo on `arena-evidence`, clean except untracked `.claude/`.

## Open decisions for David (updated 2026-07-25)
> Status: PR-opening = T4 above (still awaiting go-ahead) · window choice:
> fixed 3.5–5.5 shipped in `fdbffad9` · B0 re-vendor: done in `6e17a5af` ·
> duel vs PvP: RESOLVED, bot-level. Original 2026-07-20 items below kept for
> history.
- Track A: open the PR now, or bundle A+B into one report to Mattias first? (David's Slack msg implied PR + report for A, brainstorm for B.)
- Track A step 1: pick a fixed wide window (3.5–5.5) vs. deriving from the backend's assigned band — needs to confirm whether the backend exposes a band.
- Track B: reconciliation with the existing 7-mission campaign is DONE (see rewritten Track B). Decision left for David: approve **B0 (re-vendor the canonical game — unlocks Missions 4–7 + shields for students)** as the first move, before any net-new mechanics (B1 interference tiles / B2 decoherence zones). Recommended: yes, re-vendor first — biggest engagement win, already built and tested.

## Quick reference — key files
| File | Role |
|---|---|
| `pages/Custom_Qubit_Query.py` | Login-gated assigned-qubit query (Track A) |
| `pages/Qubit_Simulator.py` | Secrets-based free-play, titled "Custom Qubit Query" (Track A) |
| `pages/QuBlitz_Arena.py` | Streamlit wrapper + academic framing for the game |
| `pages/_assets/quantum_chess.html` | The actual battle game (Track B) |
| `quantum_simulator.py` | Physics engine (do not break) |
| `tests/`, `pytest.ini` | Regression suite |
| `docs/OVERHAUL_PLAN.md` | Master plan v2 (P0 fixes → P6 engagement framework) |
| `docs/OVERHAUL_PLAN_PRESSURE_TEST.md` | Pressure-test findings + load-bearing verdict |
| `docs/PHOTON_DUEL_DESIGN.md` | Full duel-mode game spec (mechanics/assets/bot/tests) |
| `utils/branding.py` | Cached logo loader — subject of the T1 crash fix |
