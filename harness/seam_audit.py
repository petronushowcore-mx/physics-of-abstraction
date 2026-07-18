from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from itertools import product
from math import log2
from pathlib import Path
from typing import Callable, Hashable, Iterable, Sequence, TypeVar


class CheckFailure(RuntimeError):
    pass


CHECK_MARKERS: list[str] = []


def check(condition: bool, marker: str, detail: str) -> None:
    if not condition:
        raise CheckFailure(f"[{marker}] {detail}")
    CHECK_MARKERS.append(marker)


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


@dataclass(frozen=True)
class Seam:
    name: str
    src: str
    dst: str
    defect: int
    admitted: bool


History = tuple[Seam, ...]
K = TypeVar("K", bound=Hashable)
V = TypeVar("V", bound=Hashable)


class GateEmission(str, Enum):
    ADMIT = "admit"
    REJECT = "reject"
    INSUFFICIENT = "insufficient observation"


@dataclass(frozen=True)
class AuditRecord:
    snapshot: tuple[str, ...]
    membership: tuple[int, ...]
    seam_ids: tuple[str, ...]


def well_typed(history: History) -> bool:
    return bool(history) and all(
        left.dst == right.src for left, right in zip(history, history[1:])
    )


def endpoints(history: History) -> tuple[str, str]:
    require(well_typed(history), "history is not a non-empty typed word")
    return history[0].src, history[-1].dst


def trace(history: History) -> tuple[str, ...]:
    require(well_typed(history), "history is not a non-empty typed word")
    return (history[0].src,) + tuple(seam.dst for seam in history)


def seam_word(history: History) -> tuple[str, ...]:
    require(well_typed(history), "history is not a non-empty typed word")
    return tuple(seam.name for seam in history)


def defect_word(history: History) -> tuple[int, ...]:
    require(well_typed(history), "history is not a non-empty typed word")
    return tuple(seam.defect for seam in history)


def membership_word(history: History) -> tuple[int, ...]:
    require(well_typed(history), "history is not a non-empty typed word")
    return tuple(int(seam.admitted) for seam in history)


def uninterrupted(history: History) -> bool:
    return well_typed(history) and all(seam.admitted for seam in history)


def terminal_recovery(history: History) -> bool:
    return well_typed(history) and sum(seam.defect for seam in history) == 0


def complete_delta(seam: Seam) -> int:
    return seam.defect


def blind_delta(seam: Seam) -> int:
    return 0


def factors_through(
    histories: Iterable[History],
    observation: Callable[[History], K],
    value: Callable[[History], V],
) -> bool:
    fibres: dict[K, set[V]] = defaultdict(set)
    for history in histories:
        fibres[observation(history)].add(value(history))
    return bool(fibres) and all(len(values) == 1 for values in fibres.values())


def conditional_entropy(
    weighted_histories: Sequence[tuple[History, Fraction]],
    label: Callable[[History], V],
    observation: Callable[[History], K],
) -> float:
    require(bool(weighted_histories), "history law is empty")
    require(
        all(weight > 0 for _, weight in weighted_histories),
        "the declared finite law must have full support",
    )
    total = sum((weight for _, weight in weighted_histories), Fraction(0))
    require(total > 0, "history law has no mass")

    fibres: dict[K, Counter[V]] = defaultdict(Counter)
    for history, weight in weighted_histories:
        require(well_typed(history), "history law contains an untyped history")
        fibres[observation(history)][label(history)] += weight

    entropy = 0.0
    for label_weights in fibres.values():
        fibre_mass = sum(label_weights.values(), Fraction(0))
        for weight in label_weights.values():
            p_joint = float(weight / total)
            p_conditional = float(weight / fibre_mass)
            entropy -= p_joint * log2(p_conditional)
    return entropy


def uniform(histories: Sequence[History]) -> tuple[tuple[History, Fraction], ...]:
    require(bool(histories), "cannot put a uniform law on an empty catalogue")
    weight = Fraction(1, len(histories))
    return tuple((history, weight) for history in histories)


def fibre_decision(
    histories: Sequence[History],
    observation: Callable[[History], K],
    predicate: Callable[[History], bool],
    attained: K,
) -> GateEmission:
    values = {predicate(history) for history in histories if observation(history) == attained}
    require(bool(values), "requested observation is not attained")
    if values == {True}:
        return GateEmission.ADMIT
    if values == {False}:
        return GateEmission.REJECT
    return GateEmission.INSUFFICIENT


def audit_record(history: History) -> AuditRecord:
    return AuditRecord(trace(history), membership_word(history), seam_word(history))


def acting_observation(history: History) -> tuple[str, ...]:
    return trace(history)


def audit_verdict_view(history: History) -> tuple[tuple[str, ...], tuple[int, ...]]:
    return trace(history), membership_word(history)


def audit_lineage_view(history: History) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return trace(history), seam_word(history)


def emit_from_membership(word: tuple[int, ...]) -> GateEmission:
    require(bool(word), "membership word is empty")
    return GateEmission.ADMIT if all(word) else GateEmission.REJECT


def enumerate_histories(
    seams: Sequence[Seam], max_horizon: int
) -> dict[int, tuple[History, ...]]:
    require(max_horizon >= 1, "max_horizon must be positive")
    by_length: dict[int, tuple[History, ...]] = {}
    for length in range(1, max_horizon + 1):
        typed = tuple(
            word for word in product(seams, repeat=length) if well_typed(word)
        )
        by_length[length] = typed
    return by_length


def affine_grid_bijection(
    a: Fraction,
    b: Fraction,
    c: Fraction,
    d: Fraction,
    subdivisions: int,
) -> dict[Fraction, Fraction]:
    require(subdivisions >= 1, "subdivisions must be positive")
    require(a < b and c < d, "intervals must be positively oriented")
    source = [a + (b - a) * Fraction(i, subdivisions) for i in range(subdivisions + 1)]
    target = [c + (d - c) * Fraction(i, subdivisions) for i in range(subdivisions + 1)]
    return dict(zip(source, target))


def navigate(
    identity: str,
    adaptive: int,
    burden: int,
    updates: Sequence[tuple[int, int]],
    burden_cap: int,
) -> tuple[str, int, int]:
    require(burden_cap >= 0, "burden cap must be non-negative")
    require(0 <= burden <= burden_cap, "initial burden lies outside its cap")
    for adaptive_delta, burden_delta in updates:
        require(burden_delta >= 0, "burden cannot decrease in this model")
        adaptive += adaptive_delta
        burden = min(burden_cap, burden + burden_delta)
    return identity, adaptive, burden


@dataclass(frozen=True)
class TimedSeam:
    schema: Seam
    source_time: int
    target_time: int


def lift_time_tags(history: History) -> tuple[TimedSeam, ...]:
    require(well_typed(history), "history is not a non-empty typed word")
    return tuple(
        TimedSeam(schema=seam, source_time=position, target_time=position + 1)
        for position, seam in enumerate(history)
    )


def strictly_time_typed(history: History) -> bool:
    if not well_typed(history):
        return False
    lifted = lift_time_tags(history)
    return all(
        seam.target_time == seam.source_time + 1 for seam in lifted
    ) and all(
        left.target_time == right.source_time
        for left, right in zip(lifted, lifted[1:])
    )


def is_wide_subcategory(
    subset: set[str],
    identities: set[str],
    composition: dict[tuple[str, str], str],
) -> bool:
    if not identities <= subset:
        return False
    return all(
        composite in subset
        for (first, second), composite in composition.items()
        if first in subset and second in subset
    )


GOOD_AB = Seam("g1", "A", "B", 0, True)
ALT_AB = Seam("p1", "A", "B", 0, True)
BAD_AB = Seam("b1", "A", "B", 1, False)
GOOD_BA = Seam("g2", "B", "A", 0, True)
ALT_BA = Seam("q2", "B", "A", 0, True)
CANCEL_BA = Seam("c2", "B", "A", -1, False)
P_AA = Seam("p", "A", "A", 0, True)
Q_AA = Seam("q", "A", "A", 0, True)

ALPHABET = (
    GOOD_AB,
    ALT_AB,
    BAD_AB,
    GOOD_BA,
    ALT_BA,
    CANCEL_BA,
    P_AA,
    Q_AA,
)

GOOD: History = (GOOD_AB, GOOD_BA)
BAD: History = (BAD_AB, GOOD_BA)
CANCEL: History = (BAD_AB, CANCEL_BA)
P_HISTORY: History = (P_AA,)
Q_HISTORY: History = (Q_AA,)


def run_audit() -> dict[str, object]:
    CHECK_MARKERS.clear()
    check(
        len(set(ALPHABET)) == len(ALPHABET)
        and len({seam.name for seam in ALPHABET}) == len(ALPHABET),
        "ALPHABET_UNIQUE",
        "seam schemas and seam identifiers must both be unique",
    )
    enumerated = enumerate_histories(ALPHABET, 3)
    all_histories = tuple(history for length in enumerated.values() for history in length)
    counts = {str(length): len(histories) for length, histories in enumerated.items()}

    check(counts == {"1": 8, "2": 34, "3": 140}, "TYPED_HISTORY_COUNTS", str(counts))
    check(
        all(strictly_time_typed(history) for history in all_histories),
        "STRICT_TIME_LIFT",
        "every schema word must lift from position k to k+1",
    )
    check(
        all(well_typed(history) for history in all_histories)
        and set(seam for history in all_histories for seam in history) == set(ALPHABET),
        "EXHAUSTIVE_NONVACUOUS",
        "enumeration must be typed and cover the full alphabet",
    )

    admitted_generators = {seam.name for seam in ALPHABET if seam.admitted}
    complete_generator_kernel = {
        seam.name for seam in ALPHABET if complete_delta(seam) == 0
    }
    blind_generator_kernel = {
        seam.name for seam in ALPHABET if blind_delta(seam) == 0
    }
    check(
        complete_generator_kernel == admitted_generators,
        "GENERATOR_KERNEL_COMPLETE",
        "generator kernel must equal generator admission in the sealed frame",
    )
    check(
        admitted_generators < blind_generator_kernel,
        "BLIND_GENERATOR_KERNEL_STRICT",
        "blind instrument must have a strictly larger generator kernel",
    )
    check(
        blind_delta(BAD_AB) == 0 and not BAD_AB.admitted,
        "BLIND_FALSE_NEUTRAL",
        "blind instrument must issue a neutral reading on a prohibited seam",
    )

    gb = (GOOD, BAD)
    gb_law = uniform(gb)
    target_trace = trace(GOOD)
    check(trace(GOOD) == trace(BAD), "TARGET_FIBRE_TRACE", "good and bad traces differ")
    check(
        uninterrupted(GOOD) and not uninterrupted(BAD),
        "TARGET_FIBRE_WITNESS",
        "target fibre must contain both identity verdicts",
    )
    binding_gb = conditional_entropy(gb_law, defect_word, trace)
    verdict_gb = conditional_entropy(gb_law, uninterrupted, trace)
    check(abs(binding_gb - 1.0) < 1e-12, "TARGET_BINDING_BITS", str(binding_gb))
    check(abs(verdict_gb - 1.0) < 1e-12, "TARGET_VERDICT_BITS", str(verdict_gb))
    check(
        not factors_through(gb, trace, uninterrupted)
        and factors_through(gb, audit_verdict_view, uninterrupted),
        "AUDIT_VERDICT_FACTORS",
        "snapshot must fail and audit-verdict view must succeed",
    )
    check(
        acting_observation(GOOD) == acting_observation(BAD)
        and audit_record(GOOD) != audit_record(BAD)
        and emit_from_membership(audit_record(GOOD).membership) == GateEmission.ADMIT
        and emit_from_membership(audit_record(BAD).membership) == GateEmission.REJECT,
        "AUDIT_RECORD_SEPARATES",
        "non-causal audit record must separate histories hidden from the acting view",
    )

    pq = (P_HISTORY, Q_HISTORY)
    pq_law = uniform(pq)
    binding_pq = conditional_entropy(pq_law, seam_word, trace)
    verdict_pq = conditional_entropy(pq_law, uninterrupted, trace)
    check(abs(binding_pq - 1.0) < 1e-12, "PQ_BINDING_BITS", str(binding_pq))
    check(abs(verdict_pq) < 1e-12, "PQ_VERDICT_ZERO", str(verdict_pq))
    check(
        not factors_through(pq, trace, seam_word) and factors_through(pq, trace, uninterrupted),
        "PQ_LINEAGE_HIDDEN_FROM_SNAPSHOT",
        "snapshot should hide p/q lineage while deciding the common verdict",
    )
    check(
        not factors_through(pq, audit_verdict_view, seam_word),
        "VERDICT_LOG_NOT_LINEAGE",
        "membership bits must not be overclaimed as full lineage reconstruction",
    )
    check(
        factors_through(pq, audit_lineage_view, seam_word),
        "LINEAGE_LOG_FACTORS",
        "declared seam-id log must reconstruct the p/q lineage quotient",
    )

    singleton_binding = conditional_entropy(uniform((BAD,)), defect_word, trace)
    check(
        abs(singleton_binding) < 1e-12 and not uninterrupted(BAD),
        "SINGLETON_ZERO_BINDING_BAD",
        "zero binding must coexist with a known prohibited history",
    )
    check(
        terminal_recovery(CANCEL) and not uninterrupted(CANCEL),
        "TERMINAL_CANCELLATION",
        "cancelled defect must not imply uninterrupted persistence",
    )
    check(
        not factors_through(gb, trace, terminal_recovery),
        "RECOVERY_NOT_SNAPSHOT",
        "terminal recovery must not factor through the shared target trace",
    )

    decisions = {
        "mixed": fibre_decision(gb, trace, uninterrupted, target_trace).value,
        "all_good": fibre_decision(pq, trace, uninterrupted, trace(P_HISTORY)).value,
        "all_bad": fibre_decision((BAD,), trace, uninterrupted, trace(BAD)).value,
    }
    check(
        decisions
        == {
            "mixed": GateEmission.INSUFFICIENT.value,
            "all_good": GateEmission.ADMIT.value,
            "all_bad": GateEmission.REJECT.value,
        },
        "FIBRE_TRICHOTOMY",
        str(decisions),
    )

    identities = {"id_X", "id_Y"}
    all_morphisms = identities | {"a"}
    composition = {
        ("id_X", "id_X"): "id_X",
        ("id_Y", "id_Y"): "id_Y",
        ("id_X", "a"): "a",
        ("a", "id_Y"): "a",
    }
    candidate_identity = identities
    candidate_all = all_morphisms
    check(
        is_wide_subcategory(candidate_identity, identities, composition)
        and is_wide_subcategory(candidate_all, identities, composition)
        and ("a" in candidate_all) != ("a" in candidate_identity),
        "PROP_11_1",
        "same unlabelled category must admit two incompatible persistence declarations",
    )

    denominator = 1000
    drift = tuple(Seam(f"d{i}", "A", "A", 1, False) for i in range(denominator))
    local_bound = all(
        abs(Fraction(seam.defect, denominator)) <= Fraction(1, denominator)
        for seam in drift
    )
    global_defect = Fraction(sum(seam.defect for seam in drift), denominator)
    check(
        strictly_time_typed(drift) and local_bound and global_defect == 1,
        "FINITE_DRIFT",
        f"strict time lift or global defect failed: {global_defect}",
    )

    mapping = affine_grid_bijection(
        Fraction(0), Fraction(1), Fraction(0), Fraction(100000), 10
    )
    affine_ok = (
        len(mapping) == 11
        and len(set(mapping.values())) == 11
        and mapping[Fraction(3, 10)] == 30000
        and all(
            y == Fraction(100000) * x for x, y in mapping.items()
        )
    )
    check(affine_ok, "AFFINE_GRID", "finite affine map failed")

    initial = ("unit-1", 0, 0)
    terminal = navigate(
        *initial,
        updates=((2, 1), (-1, 2), (5, 3)),
        burden_cap=10,
    )
    check(
        terminal == ("unit-1", 6, 6)
        and terminal[0] == initial[0]
        and terminal[1] != initial[1]
        and terminal[2] > initial[2],
        "SEPARATED_NAVIGATION",
        str(terminal),
    )

    decimal_places = 12
    finite_decimal = 1 - Fraction(1, 10**decimal_places)
    check(
        finite_decimal != 1 and 1 - finite_decimal == Fraction(1, 10**decimal_places),
        "FINITE_DECIMAL",
        str(finite_decimal),
    )

    check(
        not factors_through(all_histories, trace, uninterrupted),
        "EXHAUSTIVE_SNAPSHOT_INSUFFICIENT",
        "exhaustive catalogue unexpectedly makes identity a trace function",
    )
    check(
        factors_through(all_histories, audit_verdict_view, uninterrupted)
        and not factors_through(all_histories, audit_verdict_view, seam_word)
        and factors_through(all_histories, audit_lineage_view, seam_word),
        "EXHAUSTIVE_AUDIT_BOUNDARY",
        "verdict and lineage audit channels are not separated correctly",
    )

    trace_fibres: dict[tuple[str, ...], list[History]] = defaultdict(list)
    for history in all_histories:
        trace_fibres[trace(history)].append(history)
    mixed_identity_fibres = sum(
        1
        for histories in trace_fibres.values()
        if len({uninterrupted(history) for history in histories}) > 1
    )
    mixed_recovery_fibres = sum(
        1
        for histories in trace_fibres.values()
        if len({terminal_recovery(history) for history in histories}) > 1
    )

    return {
        "schema": "seam-audit-certificate-v1",
        "catalogue": {
            "alphabet_size": len(ALPHABET),
            "max_horizon": 3,
            "history_counts": counts,
            "total_histories": len(all_histories),
            "trace_fibres": len(trace_fibres),
            "mixed_identity_fibres": mixed_identity_fibres,
            "mixed_recovery_fibres": mixed_recovery_fibres,
        },
        "target_fibre": {
            "trace": list(target_trace),
            "phase_binding_bits": binding_gb,
            "verdict_ambiguity_bits": verdict_gb,
            "snapshot_factors_identity": False,
            "audit_membership_factors_identity": True,
            "snapshot_factors_terminal_recovery": False,
        },
        "pq_fibre": {
            "lineage_labels": ["p", "q"],
            "phase_binding_bits": binding_pq,
            "verdict_ambiguity_bits": verdict_pq,
            "membership_log_factors_lineage": False,
            "seam_id_log_factors_lineage": True,
        },
        "instrument": {
            "generator_kernel_equals_generator_admission": (
                complete_generator_kernel == admitted_generators
            ),
            "blind_generator_kernel_strictly_contains_admission": (
                admitted_generators < blind_generator_kernel
            ),
            "blind_false_neutral_seam": BAD_AB.name,
        },
        "fibre_classifier": decisions,
        "grounding": {
            "candidate_wide_subcategories": 2,
            "distinguishing_arrow": "a",
        },
        "checks": CHECK_MARKERS.copy(),
        "check_count": len(CHECK_MARKERS),
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finite reference audit for seam persistence")
    parser.add_argument(
        "--emit-certificate",
        type=Path,
        metavar="PATH",
        help="write the deterministic JSON certificate to PATH",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        certificate = run_audit()
        if args.emit_certificate is not None:
            payload = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
            with args.emit_certificate.open(
                "w", encoding="utf-8", newline="\n"
            ) as stream:
                stream.write(payload)
        print(f"finite seam audit passed: {certificate['check_count']} checks")
        return 0
    except (CheckFailure, ValueError) as exc:
        print(f"finite seam audit failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
