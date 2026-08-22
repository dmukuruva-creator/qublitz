# HANDOFF — QuBlitz platform/host repository

**Updated:** 2026-08-22
**Scope:** current execution state only; historical ledger archived at
[`docs/HANDOFF_HISTORY_2026-08-20.md`](docs/HANDOFF_HISTORY_2026-08-20.md).
**Cross-repository authority:** [`../HANDOFF.md`](../HANDOFF.md). Read project governance before work.

## Stop state

No integration baseline has been authorized. The project is at Gate 0 and the maintenance exception
does not authorize a feature merge, vendor replacement, upstream PR, push, or deployment. The
current branch contains six branch-only commits while the locally known `upstream/main` contains ten
commits absent here. A human must choose the base and disposition both sets before integration.

## Verified checkout

| Field | Value |
|---|---|
| Branch | `chore/streamlit-upgrade` tracking `origin/chore/streamlit-upgrade` |
| HEAD | `ed90e28c301e5351f6864eb1352cd63f4e8547c6` |
| Pre-handoff-edit state | clean; 0 ahead / 0 behind tracking branch |
| Versus locally known `upstream/main` | 6 branch-only / 10 upstream-only commits |
| Vendored game | `pages/_assets/quantum_chess.html`, 4,325 lines |
| Vendor SHA-256 | `4d7bf7ef09f5e60aafdb3145440b8fca4a193e8d912d4969f30bd45c88086a33` |
| Candidate standalone SHA-256 | `8d0585a47eaf2a1088d8c9c15c54d8b765d4f79101089f0afb750ea0857009e2` |

Online remote state was not fetched during the audit. The divergence statement is about local refs,
not a claim about the server today.

## Executive defect

The host serves the retired board/campaign while the sibling game is the adversarial arcade.
The vendor contains `CAMPAIGN_MISSIONS`, `PLAY vs BOT`, Sage proxy/fetch logic, and old controls.
The candidate standalone contains `DuelCore`, Photon Duel, Bell Trial, and Echo Siege and has no
live Sage service. The files differ by thousands of lines and are not an acceptable release pair.

`pages/QuBlitz_Arena.py` also injects/describes old proxy/Sage behavior and fixes an iframe at 920 px.
Its user-facing copy and controls do not match the current game.

## Verification ledger — last executed 2026-08-20

- `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider` — 19 PASS;
  Matplotlib/pyparsing deprecation warnings only.
- `./.venv/bin/ruff check --no-cache .` — PASS.
- `node pages/_assets/tests/qphysics.test.js pages/_assets/quantum_chess.html` — PASS against the
  stale board vendor.

The current green gate does not prove integration correctness. `tests/test_qublitz_arena.py` checks
only that a vendor exists and exceeds 100 KB. `scripts/verify.sh` can report safe-to-push without
vendor equality or the full current game harness. CI push filters omit chore branches.

## Known integration history

The locally known `upstream/main` contains merged PR29/30 work, including frequency correction,
re-vendoring, shared page contract, performance gating, consent/bridge updates, Sage removal, and
vendor equality. The current checkout does not contain that integrated baseline. Several other local
branches also contain overlapping fixes, including `ci-vendor-check` at `30285c57`.

Do not reimplement those changes from memory. The human baseline decision must say whether to start
from current upstream, preserve/cherry-pick the six branch-only upgrade/docs commits, and how to
dispose of the re-vendor/fix branches.

## Ordered integration packet after authorization

### P-A01 — select and prove the base

1. Fetch remotes only with live approval.
2. Record branch/commit graph and human disposition for every unique current/upstream commit.
3. Create an integration worktree; never merge directly into this dirty-by-design working context.
4. Run the full pre-change platform gate and preserve results.

**Falsifier:** a branch-only fix or merged-upstream correction disappears without a recorded decision.

### P-A02 — cut and bind one game release

1. Receive the human-approved duel commit and its standalone test ledger.
2. Remove obsolete Sage injection/copy from `pages/QuBlitz_Arena.py`.
3. Re-vendor with the existing sync/vendor-check work rather than handwritten copying.
4. Record source repo/commit, source SHA, vendor SHA, modes, control-manifest version, and export
   schema in a machine-readable vendor manifest.
5. Enforce byte equality and run the full duel harness against the vendored artifact in CI.

**Acceptance:** source and vendor bytes match; manifest identifies the exact commit; wrapper enters
the same current hub/modes as standalone; either repo changing the game breaks CI.
**Falsifier:** physics-only tests stay green after vendor drift or a retired entry point remains.

### P-A03 — update the host contract

- Replace fixed-height/old-board copy with a responsive page contract and current controls from the
  approved manifest.
- Preserve consent/no-network boundaries and remove any unsupported live-service claim.
- Add wrapper tests for mode entry, iframe messaging/focus, responsive desktop/tablet layouts,
  reduced motion, offline behavior, and export schema.
- Update home information architecture so the arena is not an unexplained item in a flat nine-link list.

### P-A04 — make the release gate truthful

- One platform command must run ruff, pytest, vendored qphysics, the complete duel/browser harness,
  vendor equality/manifest validation, current contrast/offline/live checks, and artifact pollution.
- CI must run on the actual integration/release branches and fail on skipped mandatory runtimes.
- Capture screenshots and release evidence from the same game/vendor/platform SHAs.

## Documentation repairs after integration

- Arena wrapper/about/home copy: remove retired army/gates/Sage/hotkeys.
- Architecture and provenance: identify sibling source, vendor mechanism, schema/mode/control versions.
- Data/consent and instructor guide: describe current local schema-v3 export, not deleted board/Sage
  storage.
- Release/rollback runbooks: source/vendor/platform hashes, owner, environment, verification, rollback.

## Human-only queue

- Ratify/edit goals or issue a feature-scoped exception.
- Record the PI demo/product-direction result.
- Approve remote fetch and select the authoritative platform integration baseline.
- Name the approved duel release commit and branch dispositions.
- Approve supported device matrix, telemetry/retention/server posture, public copy/identity,
  push/upstream PR/deployment owner and window.
- Clear licenses/provenance for any public assets or packaged media.

## Stop conditions

- Do not re-vendor from the current duel candidate until it is ratified as a release.
- Do not claim `upstream/main` is current online without fetching.
- Do not retain Sage proxy/fetch behavior for a service that does not exist.
- Do not call the current physics/pytest gate a vendor or product-integration test.
- Do not publish, deploy, push, open a PR, or delete integration branches without live approval.

The historical handoff is evidence, not a live queue. Do not append new work below the archive.
