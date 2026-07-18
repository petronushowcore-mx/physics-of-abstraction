# Finite seam reference audit

This directory contains the executable finite model declared in §12 of
`The-Physics-of-Abstraction.md`. It uses only the Python standard library.

## Run

From this directory:

```powershell
python seam_audit.py
python -O seam_audit.py
python check_bundle.py
```

Expected output from the first two commands:

```text
finite seam audit passed: 29 checks
```

Expected output from the bundle command:

```text
bundle checks passed: 14 gates, 4 mutations
```

`seam_transport.py` remains as a compatibility entry point and executes the
same audit in both ordinary and optimised Python modes.

## Gate decomposition

A gate is one named validation section counted at runtime by a live
`gate_count` variable; self-test teeth are included in the total; mutations
are reported separately.

English-only (Russian manuscript absent):

- 7 self-test teeth (AST assert detection, hidden codepoint, process
  metadata, bilingual drift, inventory, English-armed-unconditionally
  — a source inspection proving the English anchors gate sits outside
  the bilingual branch, so it holds in any repository state —
  gate-count integrity);
- 7 unconditional live gates (harness inventory, document inventory with LF
  check, bare-assert absence, public hygiene, English required anchors,
  execution of both entry points in ordinary and optimised Python,
  certificate equality).

Total English-only: **14 gates**.

When `The-Physics-of-Abstraction.ru.md` is present, one additional
conditional gate arms:

- bilingual structure (heading sequence, display-math delimiters,
  fenced-block counts, Russian required anchors).

Total bilingual: **15 gates**.

**Arming rule.** English checks are always armed. Russian and bilingual
checks arm only when the Russian manuscript exists. An English-only green
verdict does not certify a later bilingual bundle: adding the Russian
edition enlarges the audited object and requires a new verdict under the
bilingual gate count.

## What is checked

The reference audit:

- exhaustively enumerates all 182 typed histories of length one through three
  over eight visible seam schemas; word position supplies and verifies the strict
  time lift from position `k` to `k + 1`;
- verifies the shared-trace target fibre with one persistent and one
  non-persistent history;
- computes the declared `H(L | Y)` and `H(J | Y)` values for the target,
  `p/q`, and singleton catalogues;
- checks both failure and success of finite fibre factorisation;
- separates the snapshot view, the audit-only membership view, and the richer
  seam-identifier lineage view;
- verifies terminal cancellation without uninterrupted persistence;
- checks kernel completeness on the declared generator schemas in one sealed
  audit frame and exhibits a blind generator instrument with a false neutral
  certificate;
- constructs the three-way fibre decision: admit, reject, or insufficient
  observation;
- exhibits two distinct wide persistence subcategories compatible with the
  same unlabelled transition category;
- checks finite local-to-global drift, affine-grid equivalence, separated
  identity/adaptive/burden coordinates, and the finite-decimal guard.

The raw seam record is modelled as an audit-only record. The acting observation
contains the snapshot trace, while a minimal categorical emission is derived
outside the acting state. Membership bits determine the persistence verdict;
they do not, in general, reconstruct the full lineage label. Because all views
coexist in one importable module, this is an informational factorisation model,
not an enforced process, API, causal, or security boundary.

## Bundle integrity

`check_bundle.py` verifies:

- required-file inventory and LF-only line endings across the bundle;
- absence of bare Python `assert` statements;
- ordinary and `python -O` execution of both entry points;
- equality of the generated certificate and `seam_certificate.json`;
- English required anchors (always-on);
- English/Russian numbered-heading and display-math structure (when Russian
  is present);
- public-text hygiene and hidden Unicode controls;
- synthetic teeth for the gate itself (including a state-independent source
  inspection that the English anchors gate is armed outside the bilingual
  branch, and gate-count computation integrity);
- and four scratch mutations that must be rejected: alphabet collapse,
  destruction of the target-fibre witness, replacement of the complete generator
  instrument by a blind one, and removal of the audit-membership signal.

To run only the synthetic gate teeth:

```powershell
python check_bundle.py --self-test
```

The bundle verifies this finite declaration only. It does not certify a real
synthetic, biological, or physical persistence claim.
