# Photon Duel — Game Design Document (v1)

**Created:** 2026-07-25 · **Author:** David Mukuruva (drafted with Claude)
**Parent plan:** `docs/OVERHAUL_PLAN.md` (P2/P6) · pressure-test log:
`docs/OVERHAUL_PLAN_PRESSURE_TEST.md`
**Scope decision (David, 2026-07-25):** opponent is **bot-level (Sage AI)**.
No networked PvP. Hot-seat human-vs-human is a possible later mode; nothing
in this design may preclude it, nothing in v1 builds it.
**Where it's built:** canonical `Qublitz_Draft`
(`QuBlitz Project/quantum_chess.html`) as a new game mode sharing `QPhysics`,
then re-vendored. Never hand-edit `pages/_assets/`.

---

## 1. Pillars (tie-breakers for every design argument)

1. **The sphere IS the game state.** No abstract HP. If a player can't
   explain what happened by pointing at a Bloch sphere, the design is wrong.
2. **Every effect encodes a state change.** Beam color = gate axis, sphere
   swing = the actual rotation applied, shrink = decoherence. No
   decorative-only FX (intrinsic-integration attentional rule — see plan P2).
3. **30 seconds to fun.** First shot fired within 30 s of page load with zero
   required reading. Depth arrives by unlocks, not by tutorial text.

**Elevator pitch:** *A top-down laser duel where your opponent's health bar
is their qubit. Shoot rotations, dodge theirs, and pull the trigger on a
measurement only when the Born rule is on your side.*

---

## 2. Game structure & screens

```
Landing (mode select) ──► DUEL (arcade)  ──► Debrief card ──► next duel / retry
        │                                        ▲
        └────────────────► STORY (existing 7-mission campaign + Physics Lab)
```

- **Landing:** two large cards — "⚡ Duel" (default focus) and "♟ Story".
  One-line descriptor each. Leaderboard strip below (reuses existing
  leaderboard state). Nothing else.
- **Duel screen:** arena canvas + HUD (§5). Esc pauses (bot pauses too).
- **Debrief card (after every round):** 3 lines max, auto-generated from the
  telemetry events (§8): what won ("Rx(π) then MEASURE at P=0.93"), one
  concept name ("Born rule"), one tip keyed to the losing pattern. Buttons:
  Rematch · Next · Story mode link to the matching mission.

---

## 3. Core mechanics (numbers are v1 tuning starts, not law)

### 3.1 Movement & arena
- Top-down 2D arena, 16:10 logical space (1280×800 world units), walls solid.
- Ship: max speed 260 u/s, accel 900 u/s², light drift (friction 0.92/frame
  at 60 Hz). Feels agile, not icy.
- Fixed-timestep simulation at 60 Hz, render via `requestAnimationFrame`
  (same pattern the campaign loop uses).

### 3.2 Beams = gates (the heart of the game)
| Beam | Axis | Color | Unlock | Notes |
|---|---|---|---|---|
| X-beam | Rx(θ) | red | Duel 1 | the workhorse; rotates \|0⟩→\|1⟩ at θ=π |
| Z-beam | Rz(θ) | blue | Duel 2 | phase; invisible on P(\|1⟩) but flips \|+⟩↔\|−⟩ — teaches "phase matters" |
| Y-beam | Ry(θ) | green | Duel 3 | the flanking axis |
| MEASURE | collapse | white, distinct silhouette | Duel 1 | the *only* way to win a round |

- **Charge-to-θ (Rabi made tactile):** hold fire to charge;
  `θ = π · min(t_hold / 1.2 s, 1)`. Tap ≈ π/8 nudge, full hold = π-pulse.
  Charge bar is labeled in π-fractions (¼π, ½π, π) — students *see* pulse
  area. While charging you move at 60% speed (commitment tradeoff).
- Beam projectile speed 700 u/s, width 6 u; cooldown 0.45 s after release.
- **On hit:** apply the rotation to the target's qubit via the existing
  `QPhysics`/`GATES` path (no new math). Sphere animates the great-circle arc
  over 250 ms (the arc *is* the damage number).
- **Eigenstate shield (physically true, teaches eigenstates):** if the
  target's Bloch vector is within 10° of the beam's rotation axis (±n̂), the
  rotation leaves the state invariant → beam visibly refracts around the
  ship, floater "EIGENSTATE!", zero effect. Parking at \|−⟩ tanks X-beams —
  exactly the campaign's Mission-5 concept, now a dodge-free defense you
  *steer into*.

### 3.3 MEASURE (win condition = Born rule)
- Slow projectile (420 u/s), long cooldown (6 s), loud telegraph (1 s spin-up
  whine — reaction window).
- On hit: collapse using the target's true P(|1⟩).
  - Result |1⟩ → **round won**.
  - Result |0⟩ → dud: target's state resets to |0⟩ (they must be re-rotated
    from scratch) and the shooter ate a 6 s cooldown. Firing at P=0.3 is a
    real gamble — the Born rule becomes felt risk management.
- HUD shows live "MEASURE odds: 87%" under the opponent's sphere (§5) —
  the number updates as rotations land, so cause→probability is visible.

### 3.4 Decoherence (pressure that keeps the duel moving)
- Per-frame purity decay toward the mixed state using the engine's existing
  T₂ machinery: baseline effective T₂ = 30 s; vector length shrinks
  accordingly (a shrunken vector caps your opponent's MEASURE odds *and*
  yours — stalling hurts everyone).
- Slow T₁ relaxation toward |0⟩ (effective T₁ = 90 s) so camping decays you
  to the ground state.
- **Echo pickup** (spin-echo refocus): spawns at a random arena point every
  15 s, despawns after 8 s. On pickup: restores vector length to
  min(1, current + 0.5) with a satisfying "refocus" ripple. One on the field
  at a time.

### 3.5 Rounds & match
- Best-of-3 rounds; round ends only by a successful MEASURE (or 90 s timer →
  sudden-death: both T₂ rates triple until someone lands a MEASURE).
- Between rounds: debrief card (§2). Match end: match debrief + leaderboard
  entry (existing leaderboard/stats state: `critCount` analog → measure
  quality, `gateCounts` per axis).

### 3.6 Progressive unlocks (answers "too complicated")
| Duel | New | Concept certified |
|---|---|---|
| 1 | X-beam + MEASURE | rotation ↔ P(\|1⟩), Born rule |
| 2 | Z-beam; opponent starts using eigenstate parking | phase, eigenstates |
| 3 | Y-beam + echo pickups | decoherence, spin echo |
| 4 | Biomes rotation (§4) | local noise, spatial phase |
- Unlocks are *skill* gates (win the prior duel), never grind gates (P6
  economy rule: mastery is the only currency).
- Story-mode mission clears also unlock the matching duel tier (Mission 5
  clear → Duel 2 content) — the meta-loop bridge.

### 3.7 Sage bot (the opponent)
- Reuses the existing offline Sage heuristic infrastructure + `botLastReason`
  (surface it as post-round banter on the debrief card: "I parked at |−⟩
  because you spam X-beams").
- Three chosen levels: **Cadet / Duelist / Decoherent Menace**
  - aim error σ: 14° / 8° / 4°
  - decision tick: 900 ms / 600 ms / 350 ms
  - uses eigenstate parking: never / when threatened / proactively
  - MEASURE policy: fires at P ≥ 0.75 / ≥ 0.85 / optimal-EV timing
- Hidden assist (disclosed in an "Assists" settings line, not silently —
  students distrust fake wins): after 3 consecutive losses, aim error +15%
  and the debrief tip gets specific. No other rubber-banding.

---

## 4. Biomes (arena = physics, merges plan B1/B2)

| Biome | Visual (asset §6) | Physics effect | Duel |
|---|---|---|---|
| **Starfield** | 2-layer parallax starfield | none — the control group | 1–2 |
| **Nebula** | purple nebula tiles, drifting fog patches | inside fog: effective T₂ = 8 s (vector visibly shrinks) — decoherence zone (plan B2) | 3 |
| **Phase Rift** | shimmering vertical bands | any beam crossing a band picks up an extra Rz(π/2) — your X-beam arrives as a tilted rotation; positioning changes *what gate you deliver* (plan B1) | 4 |

Fog patches and rift bands are slow-moving (10 u/s) so they read as terrain,
not bullets. Each biome effect gets one floater the first time it triggers
("NEBULA: decohering ×4!").

---

## 5. HUD & UI layout

```
┌──────────────────────────────────────────────────────────┐
│  [opp sphere ◔ + "MEASURE odds: 87%"]        round ●●○   │
│                                                          │
│                     ARENA (canvas)                       │
│                                                          │
│ [your sphere ◕]  [charge bar ¼π ½π ¾π π]  [1][2][3][SPC] │
└──────────────────────────────────────────────────────────┘
```
- **Two mini Bloch spheres**, 2D orthographic projection (circle + 2
  great-circle ellipses + vector + pole labels |0⟩/|1⟩): yours bottom-left
  (110 px), opponent's top-left (90 px). Drawn on canvas — no three.js in v1
  (plan decision; the campaign already draws spheres this way).
- Charge bar with π-fraction ticks; cooldown rings on the axis-key icons.
- Beam-axis picker shows the axis *on a tiny sphere glyph*, not just a color.
- Typography per plan P4: Press Start 2P ≥ 17 px for "DUEL"/round banners
  only; Space Grotesk for everything dense; Rajdhani SemiBold (digits subset)
  for the odds readout and timers.
- Controls: WASD/arrows move · mouse aim · hold LMB charge, release fire ·
  1/2/3 axis select · Space = MEASURE · Esc pause. Keycap strip always
  visible at bottom (P3.6); remappable later via the a11y branch patterns.

---

## 6. Asset manifest (real, all CC0/OFL, base64-embedded, 2 MB hard cap)

| # | Asset | Source (real pack) | Use | Budget |
|---|---|---|---|---|
| 1 | Ship sprites ×2 (player blue, Sage black), damage variants | **Kenney Space Shooter Redux** (295+ sprites, CC0; ships incl. `playerShip1_blue`, enemy black series) — kenney.nl/assets/space-shooter-redux | player + bot ships | ~30 KB |
| 2 | Beam sprites: `laserRed`/`laserBlue`/`laserGreen` series + white variant recolor for MEASURE | same pack (laser sprites in red/blue/green) | the four beams — colors already match our axis coding | ~25 KB |
| 3 | Muzzle flashes, shield ring (`shield1–3`), power-up glyphs | same pack | fire feedback, eigenstate refraction ring, echo pickup base | ~20 KB |
| 4 | Glow/flare/spark/trace particles | **Kenney Particle Pack** (80 sprites, CC0) — kenney.nl/assets/particle-pack | charge shimmer, hit sparks, measure spin-up, refocus ripple | ~40 KB |
| 5 | Starfield + nebula tiles: 8 purple, 8 blue nebulas + 8 starfields @512² | **Screaming Brain Studios "Seamless Space Backgrounds"** (32 tiling PNGs, CC0) — opengameart.org/content/seamless-space-backgrounds | biome parallax layers (2 layers × 2 tiles per biome; pick 6 tiles total, WebP-recompress) | ~350 KB |
| 6 | Panel/bar/button chrome | **Kenney UI Pack — Sci-Fi** (CC0) | debrief card, landing cards, charge bar frame | ~30 KB |
| 7 | SFX (primary): procedural **jsfxr** (github.com/chr15m/jsfxr, MIT/CC0 lineage) | presets: laserShoot ×3 (base freq 880/440/660 Hz for X/Z/Y), hitHurt (impact), powerUp (echo), explosion (collapse-win), blipSelect (UI) | zero audio files | ~8 KB JS |
| 8 | SFX (flavor, only if budget allows): 3 clips from **Kenney Sci-fi Sounds** (70 clips, CC0) | MEASURE spin-up whine, round-win sting, ambient hum | ≤ 90 KB OGG |
| 9 | Font add: **Rajdhani SemiBold** (Google Fonts, SIL OFL), subset to digits+%.: | HUD numerals | ~14 KB WOFF2 |
| 10 | Existing: Press Start 2P + Space Grotesk (already embedded) | titles/body | 0 (already in file) |

Running total ≈ 610 KB on top of the current 516 KB file → ~1.13 MB, inside
the 2 MB cap with room for D2. Pipeline: same base64 @font-face/data-URI
pattern the fonts already use; add a `scripts/embed_assets.sh` step to the
canonical repo so re-embedding is reproducible, and record pack versions +
licenses in a `CREDITS` block in the HTML header comment (CC0 needs no
attribution, we credit anyway).

---

## 7. Technical architecture

- **One vendored file, two modes.** `quantum_chess.html` gains a
  `MODE = 'duel' | 'story'` top-level switch; landing screen sets it. Shared:
  `QPhysics`, `GATES`, sphere renderer, FX systems (`shake`, `floats`,
  `beamFlash`), leaderboard, Sage plumbing. Duel-only: entity/projectile
  system, biome layer, charge input. Estimated +1,800 lines.
- **Physics bindings (nothing hand-rolled):** beam hit → existing gate
  application with parameterized θ; decoherence → existing T₁/T₂ evolution
  with per-zone rates; MEASURE → existing collapse routine. New
  `duel_harness.test.js` locks this (§9).
- Determinism: seedable RNG for bot decisions + collapse rolls in test mode
  (the campaign's test harness already does this for shields — same pattern).
- Perf budget: ≤ 4 ms/frame sim+draw on a 2020 laptop; particle cap 400;
  no allocation in the hot loop (pool projectiles/particles).

## 8. Telemetry (P6 funnel, instrumented at D0, instructor-export only)

Events (append to the existing gate-log/export path — no third-party
analytics): `duel_load`, `first_shot` (Δt from load — the 30 s KPI),
`first_sphere_read` (opponent vector moved ≥ 15° from a player's beam),
`round_end` {winner, method, P_at_measure, θ_histogram, axis_counts},
`debrief_shown` / `debrief_concept` {concept, correct_line}, `duel_complete`,
`assist_triggered`, `biome_effect_first_seen`. North Star rolls up from
`debrief_concept` per returning session (plan §6.5).

## 9. Test plan (`duel_harness.test.js`, mirrors `mission_shield_harness`)

1. θ-mapping: hold times {0.15, 0.6, 1.2, 2.0} s → θ {π/8, π/2, π, π}.
2. Eigenstate immunity: state at |−⟩ ± 9° takes zero net rotation from
   X-beams; at 11° it doesn't (boundary test).
3. Born-rule wins: 10,000 seeded MEASURE hits at P=0.7 → win rate
   0.7 ± 0.02.
4. Nebula: vector length after 5 s in fog < after 5 s outside (ratio matches
   T₂ 8 s vs 30 s).
5. Phase rift: X-beam through one band ≡ Rz(π/2)·Rx(θ) composite on target.
6. Bot liveness: every level fires ≥ 1 beam per 3 s window over a 60 s
   seeded sim; never NaNs the state.
7. Dud-measure reset: collapse to |0⟩ resets target state and win counter
   unchanged.
8. Existing campaign/physics tests still pass byte-identical.

## 10. Milestones (revised from plan D0–D3; cut-lines explicit)

| Milestone | Contents | Cut-line if slipping |
|---|---|---|
| **D0 — spike (2 days)** | movement, X-beam charge→θ, both spheres live, MEASURE win, jsfxr SFX, starfield, telemetry events 1–4 | biomes, Y/Z beams, debrief (hard-coded card OK) |
| **D1 (1 wk)** | Z+Y beams, eigenstate shield, dud-measure rule, echo pickups, Cadet/Duelist bots, debrief cards, landing screen | Menace bot, sudden-death |
| **D2 (1 wk)** | Nebula + Phase Rift biomes, unlock ladder, Menace bot, assist system, Kenney flavor SFX, full test suite §9 | Phase Rift slips to D3 |
| **D3 (3–4 days)** | polish per RITE findings, a11y pass (merge `arena-accessibility` first), re-vendor, Streamlit landing integration, instructor-export wiring | — |

Gate on every milestone: its funnel step (§8) measured in a playtest and not
regressed; PI plays D0 (playtester #0).

## 11. Risks

- **Charge-while-slowed feels bad on trackpads** → RITE test in D0; fallback:
  tap-to-cycle preset θ (¼π/½π/π) instead of analog hold.
- **Z-beam "does nothing visible"** (it doesn't change P(|1⟩) from |0⟩/|1⟩) —
  by design it teaches phase, but it must *feel* real: sphere shows the
  azimuthal swing prominently, and Duel-2 bot parks at |±⟩ so Z visibly
  matters. If confusion persists in playtests, gate Z behind a 15 s inline
  demo.
- **File-size creep** — CI check: fail re-vendor if `quantum_chess.html`
  > 2 MB.
- **Novelty claim** — one pass over Awesome-Quantum-Games before the PI
  pitch deck (pressure-test finding 4).
