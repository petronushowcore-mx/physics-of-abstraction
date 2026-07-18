# The Physics of Abstraction

### Identity at the Seam: Phase Binding, Hidden Lineage, and Exact Persistence through Finite Drift

**Maksim Barziankou (MxBv)**  
PETRONUS™ · The Urgrund Laboratory · research@petronus.eu  
Poznań · July 2026  
License: CC BY-NC-ND 4.0  
This work DOI: [10.17605/OSF.IO/QJ5BR](https://doi.org/10.17605/OSF.IO/QJ5BR)  
Axiomatic core (NC2.5 v2.1): [10.17605/OSF.IO/NHTC5](https://doi.org/10.17605/OSF.IO/NHTC5)

---

> *A state is what can be photographed. Identity is what must survive the cut.*

A line through time appears continuous only because its cuts are too fine to see. The image is
useful, but it is not yet mathematics. The mathematical question is:

> **What structure must be carried across each finite transition for one declared unit to persist
> exactly, even while its state, knowledge, burden, and physical performance change?**

This note answers it finite-first — and ships the executable model that checks its own claims.

## What the note establishes

Temporal identity is typed on **histories**, not on endpoint states: a persistence predicate is a
wide subcategory of identity-admissible transitions — *seams*. From that typing follow results the
usual framing cannot state, let alone separate:

- **Uninterrupted persistence is not terminal recovery.** Every elementary seam admissible ⟹ the
  composite is admissible. The converse fails: non-admissible defects can cancel at the endpoint.
- **Snapshot sufficiency has an exact criterion.** A snapshot-only verdict exists precisely when the
  identity predicate is constant on every observation fibre. One persistent and one non-persistent
  history sharing a visible trace refute every classifier confined to that trace. On a mixed fibre
  the honest output is a third value — *insufficient observation* — not a confidence score.
- **Phase binding measures hidden lineage, not persistence.** Conditional entropy under a sealed
  audit quantifies what the visible trace leaves unresolved. Positive binding blocks uniform exact
  reconstruction under confined Markov access — and still does not mean identity was lost.
- **A cocycle certifies only if its kernel is complete.** A compositional instrument whose neutral
  class exceeds the admitted class is a false certificate; neutral accumulated holonomy certifies
  terminal recovery alone.
- **Audit-only instrumentation is sufficient — constructively.** A persistence-complete membership
  record determines the exact verdict where snapshots cannot, while staying outside the acting
  agent's optimisation surface, and still need not reconstruct the full lineage.
- **Small tolerances accumulate.** Arbitrarily small local defects reach a finite global defect with
  no completed infinity required.
- **Learning and wear coexist with exact persistence** — by typing, and only under explicit
  anti-vacuity obligations.
- **Admissibility cannot be learned from unlabelled transitions.** A grounding channel is necessary.

## What is *not* claimed

*Physics of abstraction* names a **structural programme**, not an empirical result. No physical law
is announced. No formal witness is identified with phenomenal consciousness, biological personhood,
or moral identity. No UUID, database key, or preserved bit is sufficient for identity. No actual
infinity and no nilsquare infinitesimal is assumed by the finite theory. No endpoint equality,
similarity score, or successful terminal repair is treated as evidence of uninterrupted identity.
The note states these boundaries in §0.3 and defends them in §15.

## The executable reference audit

The note does not ask to be trusted on its finite model — it ships it. Standard library only, no
dependencies:

```bash
python harness/seam_audit.py        # → finite seam audit passed: 29 checks
python -O harness/seam_audit.py     # same under optimisation: no check is an `assert`
python harness/check_bundle.py      # → bundle checks passed: 14 gates, 4 mutations
```

The audit exhaustively enumerates **all 182 typed histories** of length one to three over eight
declared seam schemas, computes the declared conditional entropies from exact rational masses,
separates the snapshot / audit-verdict / audit-lineage views, checks generator-level kernel
completeness against a deliberately blind instrument, and emits a deterministic certificate.

The bundle gate re-derives that certificate and compares it byte for byte — then applies four
scratch mutations to the audit source, each of which **must** be rejected by its own marker. An
audit that cannot fail is not evidence.

| Path | Role |
|---|---|
| `The-Physics-of-Abstraction.md` | the note (canonical source) |
| `The Physics of Abstraction — Identity at the Seam (2026).pdf` | typeset edition |
| `harness/seam_audit.py` | the finite model — 29 named checks + certificate emitter |
| `harness/seam_certificate.json` | the sealed deterministic certificate |
| `harness/check_bundle.py` | bundle gate: inventory, hygiene, execution, certificate, mutations |
| `harness/seam_transport.py` | compatibility entry point |
| `harness/README.md` | what each check covers |

## Signed deposit

This repository carries the readable, runnable version. The **signed** deposit — every artifact with
its detached GPG signature, a `SHA256SUMS` manifest, and an OpenTimestamps Bitcoin anchor over that
manifest — lives at the DOI:

**[10.17605/OSF.IO/QJ5BR](https://doi.org/10.17605/OSF.IO/QJ5BR)**

```bash
sha256sum -c SHA256SUMS                                   # integrity
gpg --verify "The-Physics-of-Abstraction.md.sig" "The-Physics-of-Abstraction.md"   # authenticity
ots verify SHA256SUMS.ots                                 # existence in time
```

Signing key: PETRONUS Research, `9E803F8037EE98E5846CE38B0C7F9CBB6D54185D`.

## Corpus

A formal note in **Navigational Cybernetics 2.5**. It extends the temporal side of *Identity Does
Not Drift* and the reconstructive side of *Severance Defect and the Binding Functional*; neither
work is replaced or silently redefined.

| Companion | DOI |
|---|---|
| NC2.5 — Axiomatic Core v2.1 | [10.17605/OSF.IO/NHTC5](https://doi.org/10.17605/OSF.IO/NHTC5) |
| Severance Defect and the Binding Functional | [10.17605/OSF.IO/5VJMR](https://doi.org/10.17605/OSF.IO/5VJMR) |
| Cross-Temporal Coherence | [10.17605/OSF.IO/UQ4AW](https://doi.org/10.17605/OSF.IO/UQ4AW) |
| ONTOΣ XIV — Nested Substrates | [10.17605/OSF.IO/KAGMH](https://doi.org/10.17605/OSF.IO/KAGMH) |
| ONTOΣ XV — Spin-Channel and Nestability | [10.17605/OSF.IO/EAUD5](https://doi.org/10.17605/OSF.IO/EAUD5) |

## License

CC BY-NC-ND 4.0 — share with attribution, no commercial use, no derivatives.
The harness is published under the same terms as the note it verifies.

---

*The physics of abstraction begins at the cut.*
