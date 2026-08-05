# Pressure-test — docs/OVERHAUL_PLAN.md (v1 → v2)

**Date:** 2026-07-25 · **Target:** non-research (plan) — adapted axes per
`/pressure-test`: correctness = plan vs. artifacts on disk · currency = has
reality moved · collision = does something already do this · internal
consistency = do the plan's own numbers cohere.
**Disposition:** all findings below were folded into OVERHAUL_PLAN.md v2 the
same day (user asked for iteration, so report-then-revise).

## Findings (severity-ordered)

### 🟠 Material

1. **[correctness] Streamlit theming silently depended on a framework
   upgrade.** Plan v1 treated P4 theming as config-only; `requirements.txt`
   pins `streamlit==1.39.0`, and `[[theme.fontFaces]]`/`headingFont` need
   ≥ 1.45 (https://docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts,
   community thread on v1.45 fontFaces). The upgrade also intersects the P0.1
   crash (script-runner hardening landed after 1.39). → v2: upgrade is its
   own PR with a regression gate (pytest + `tests/test_pages_smoke.py` + all
   pages manual load), sequenced Week 1.

2. **[correctness] P0.1 import-hardening scope was understated ×10.** Plan v1
   said the resilient-import pattern applied to "currently the Arena page."
   `grep -rn "^from utils" pages/ home.py` → **10 top-level import sites**
   (Sonify.py:2, IQ_mixer.py:23, EP_TPD_exploration.py:10,13,14,
   Custom_Qubit_Query.py:24, Quantum_Measurement_Tutorial.py:11,
   Qubit_Simulator.py:19, QuBlitz_Arena.py:24, home.py:2). Any page can lose
   the same `sys.modules` race. → v2: centralized `utils/safe_import.py`
   helper instead of ten pasted try/excepts.

3. **[unverified-claim → now sourced] The plan's central pedagogical bet
   ("mechanic = physics is the right design") was asserted without
   evidence.** Now grounded: intrinsic integration outperforms bolt-on
   designs (Habgood & Ainsworth 2011,
   https://www.tandfonline.com/doi/abs/10.1080/10508406.2010.508029), the
   mechanism is attentional (Cutting & Iacovides 2022,
   https://dl.acm.org/doi/abs/10.1145/3549503), and design-not-medium carries
   learning effects (Wouters et al. 2013; Clark et al. 2016 meta-analyses).
   Corollary adopted as a design rule: every FX must encode a state change;
   decorative juice is an attention leak.

4. **[collision] Prior art exists and was uncited.** ScienceAtHome's
   *Quantum Shooter* is literally a quantum-themed shooter
   (https://citizensciencegames.com/games/quantum-shooter/) — but its quantum
   content is an optimal-control reload puzzle, not the combat. QubitQuest
   (arXiv 2604.24015), IQM Academy's Bloch game, Hello Quantum, Quantum
   Odyssey are adjacent but none are adversarial-with-Bloch-sphere-as-health.
   Not scooped, but novelty claims to the PI must cite and differentiate;
   check https://github.com/HuangJunye/Awesome-Quantum-Games before pitching.

5. **[internal-consistency] No measurement layer.** v1 claimed engagement
   outcomes ("single biggest engagement win") with zero instrumentation to
   falsify them, while the game already logs `gateCounts`, `hitsLanded`,
   `guardStats`, `critCount`, `botLastReason`
   (pages/_assets/quantum_chess.html:2110-2121). → v2 P6: funnel events from
   D0, North Star = concept-evidence per returning session (explicitly not
   raw minutes; cf.
   https://mobilefreetoplay.com/obsessing-retention-metrics-risks-killing-game/).

6. **[correctness/scope] PvP ambiguity in the PI's ask.** "hits the other
   player" could mean human-vs-human; v1 silently assumed vs-AI. Real-time
   PvP inside the Streamlit iframe needs a relay service — different project.
   → v2: flagged as a blocking scope question before D1; hot-seat is the
   cheap middle ground.

### 🟡 Minor

7. **[internal-consistency] Sig-fig audit undercounted.** v1 listed 4 lines;
   `grep -rn "%.9f|:.9f" pages/ | wc -l` → **15 occurrences**. Acceptance
   criterion unchanged; effort estimate corrected.

8. **[internal-consistency] Asset-size budget was arbitrary.** v1 allowed
   "~7 MB"; the vendored HTML is 516 KB and is inlined into the iframe
   srcdoc on every page load. → v2: 2 MB cap.

9. **[correctness — verified ✓, no change] Spot-checks that held:** juice
   systems exist at quantum_chess.html:2110-2121 (`shake`, `floats`,
   `beamFlash`); `_EMBED_HEIGHT = 920` at pages/QuBlitz_Arena.py:39;
   canonical repo present at `QuBlitz Project/quantum_chess.html`;
   `st.secrets["params"]` bracket-access offender confirmed at
   pages/Qubit_Simulator.py:118; fonts base64-embedded as claimed.

## Open questions for the author

- Who controls the `mvwf/qublitz` Streamlit Cloud deployment settings (needed
  for the `fileWatcherType` config and to read the un-redacted logs)?
- Will upstream accept a Streamlit 1.39→1.4x bump, or does the lab pin for a
  reason (e.g., another course app on the same account)?
- ~~PvP vs vs-AI (finding 6)~~ — **RESOLVED 2026-07-25: bot-level (Sage)
  for now**, per David; design keeps hot-seat possible
  (`docs/PHOTON_DUEL_DESIGN.md`).

## Verdict

Load-bearing after v2: the two P0 diagnoses (both artifact-verified), the P1
"ship the built branch" move, the intrinsic-integration design rationale
(now literature-backed), and the P6 measurement plan. **Not** load-bearing:
any retention *number* (benchmarks are mobile-F2P orientation only), the
novelty claim until the Awesome-Quantum-Games sweep is done, and the D0–D3
effort estimates (unvalidated until the spike).
