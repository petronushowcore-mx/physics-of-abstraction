from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


class BundleFailure(RuntimeError):
    pass


HERE = Path(__file__).resolve().parent
BUNDLE_ROOT = HERE.parent
EXPECTED_HARNESS = {
    "README.md",
    "check_bundle.py",
    "seam_audit.py",
    "seam_certificate.json",
    "seam_transport.py",
}
ENGLISH = BUNDLE_ROOT / "The-Physics-of-Abstraction.md"
RUSSIAN = BUNDLE_ROOT / "The-Physics-of-Abstraction.ru.md"
RULE_28 = re.compile(
    r"Tier [12]|Tier 1[AB]|0 HIGH|[0-9]+ HIGH|MEDIUM × [0-9]|ten rounds?|"
    r"[0-9]+ rounds?|post-audit|external review|cards-first|Plan v[0-9]|wt-append|"
    r"tier-protocol|cascade-audit|META-Q|source_layer|verbatim_relay|"
    r"adversarial_check_observation|kind:(?:card|tier_seal|coherence_map|fix|finding|decision)|"
    r"main-loop-tier|mechanical-§",
    re.IGNORECASE,
)
PATENT_PREFIX = re.compile(r"6[34]/[0-9]{3},?[0-9]{3}")
HIDDEN_CODEPOINTS = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\u2060",
    "\ufeff",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
}

# Pinned manuscript strings — always checked against the English manuscript.
ENGLISH_ANCHORS = (
    "Corollary 3.4 (Fibre trichotomy)",
    "Corollary 5.5 (Audit-only seam sufficiency)",
    "Cross-Temporal Coherence",
    "seam_certificate.json",
)

# Russian anchors — checked only when the Russian manuscript exists.
RUSSIAN_ANCHORS = (
    "Следствие 3.4 (Трихотомия слоя)",
    "Следствие 5.5 (Достаточность швов только для аудита)",
    "Кросс-темпоральная когерентность",
    "seam_certificate.json",
)


def check(condition: bool, marker: str, detail: str) -> None:
    if not condition:
        raise BundleFailure(f"[{marker}] {detail}")


def run(command: Sequence[str], cwd: Path = HERE) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def bare_assert_sites(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sorted(node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert))


def missing_inventory(root: Path) -> set[str]:
    present = {path.name for path in root.iterdir() if path.is_file()}
    return EXPECTED_HARNESS - present


def non_lf_files(paths: Sequence[Path]) -> set[str]:
    return {path.name for path in paths if bytes((13,)) in path.read_bytes()}


def hygiene_findings(text: str) -> list[str]:
    findings: list[str] = []
    if any(character in text for character in HIDDEN_CODEPOINTS):
        findings.append("hidden-codepoint")
    if RULE_28.search(text):
        findings.append("process-metadata")
    if PATENT_PREFIX.search(text):
        findings.append("patent-prefix")
    if re.search(r'\."|,"', text):
        findings.append("logical-quote-punctuation")
    return findings


def numbered_headings(text: str) -> list[str]:
    return re.findall(r"(?m)^#{2,6}\s+(?:§)?([0-9]+(?:\.[0-9]+)*)\b", text)


def validate_bilingual_structure(english: str, russian: str) -> None:
    check(
        numbered_headings(english) == numbered_headings(russian),
        "BILINGUAL_HEADINGS",
        "English and Russian numbered heading sequences differ",
    )
    check(
        english.count("$$") == russian.count("$$"),
        "BILINGUAL_DISPLAY_MATH",
        "display-math delimiter counts differ",
    )
    check(
        english.count("```") == russian.count("```"),
        "BILINGUAL_FENCES",
        "fenced-block counts differ",
    )
    required = (
        *((english, anchor) for anchor in ENGLISH_ANCHORS),
        *((russian, anchor) for anchor in RUSSIAN_ANCHORS),
    )
    missing = [needle for text, needle in required if needle not in text]
    check(not missing, "BILINGUAL_REQUIRED_ANCHORS", f"missing anchors: {missing}")


def compare_certificate(
    generated: dict[str, object],
    checked_in: dict[str, object],
    generated_bytes: bytes = b"",
    checked_in_bytes: bytes = b"",
) -> None:
    # Byte equality, not merely semantic JSON equality: the sealed certificate is a
    # byte-level artefact, and the manuscript states the gate verifies exactly that.
    if generated_bytes or checked_in_bytes:
        check(generated_bytes == checked_in_bytes, "CERTIFICATE_DRIFT", "checked certificate differs byte-for-byte")
    check(generated == checked_in, "CERTIFICATE_DRIFT", "checked certificate differs")
    catalogue = generated.get("catalogue")
    check(isinstance(catalogue, dict), "CERTIFICATE_SCHEMA", "catalogue is missing")
    check(
        catalogue.get("history_counts") == {"1": 8, "2": 34, "3": 140}
        and catalogue.get("total_histories") == 182,
        "CERTIFICATE_COUNTS",
        str(catalogue),
    )
    check(
        generated.get("check_count") == 29
        and len(generated.get("checks", [])) == 29
        and len(set(generated.get("checks", []))) == 29,
        "CERTIFICATE_MARKERS",
        "expected 29 distinct executable checks",
    )


def mutation_run(
    source: str,
    old: str,
    new: str,
    expected_marker: str,
) -> None:
    check(source.count(old) == 1, "MUTATION_ANCHOR", f"anchor count for {expected_marker}")
    mutated = source.replace(old, new)
    with tempfile.TemporaryDirectory(prefix="seam-mutation-") as directory:
        script = Path(directory) / "seam_audit.py"
        script.write_text(mutated, encoding="utf-8")
        result = run((sys.executable, str(script)), Path(directory))
    check(result.returncode != 0, "MUTATION_SURVIVED", expected_marker)
    check(expected_marker in result.stderr, "MUTATION_WRONG_TOOTH", result.stderr.strip())


def self_test_gate() -> int:
    synthetic = ast.parse("def nested():\n    if True:\n        assert False\n")
    check(
        any(isinstance(node, ast.Assert) for node in ast.walk(synthetic)),
        "SELFTEST_AST_ASSERT",
        "nested assert was not detected",
    )
    check(
        all(
            "hidden-codepoint" in hygiene_findings(sample)
            for sample in ("clean\u200btext", "clean\u2066text")
        ),
        "SELFTEST_HIDDEN_CODEPOINT",
        "hidden codepoint survived",
    )
    check(
        all(
            "process-metadata" in hygiene_findings(sample)
            for sample in ("ready for Tier 2 external review", "main-loop-tier-1A")
        ),
        "SELFTEST_PROCESS_METADATA",
        "process metadata survived",
    )
    check(
        numbered_headings("## §1 One\n### 1.1 A\n")
        != numbered_headings("## §1 Один\n### 1.2 Б\n"),
        "SELFTEST_BILINGUAL_DRIFT",
        "heading drift was not detected",
    )
    with tempfile.TemporaryDirectory(prefix="inventory-tooth-") as directory:
        root = Path(directory)
        for name in EXPECTED_HARNESS - {"README.md"}:
            (root / name).write_text("", encoding="utf-8")
        missing_ok = missing_inventory(root) == {"README.md"}
        (root / "README.md").write_bytes(bytes((97, 13, 10, 98, 13)))
        non_lf_ok = non_lf_files(
            tuple(root / name for name in sorted(EXPECTED_HARNESS))
        ) == {"README.md"}
        check(
            missing_ok and non_lf_ok,
            "SELFTEST_INVENTORY",
            "missing-file or non-LF inventory drift was not detected",
        )
    # Tooth (c): the English anchors gate is armed unconditionally.
    # Source inspection of this very file proves that the
    # ENGLISH_REQUIRED_ANCHORS check sits at the top level of run_bundle,
    # outside every `if` statement (in particular outside the bilingual
    # branch), so the tooth holds in any repository state.
    own_source = Path(__file__).resolve().read_text(encoding="utf-8")
    bundle_tree = ast.parse(own_source, filename=__file__)
    run_bundle_def = next(
        (
            node
            for node in bundle_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_bundle"
        ),
        None,
    )
    armed_unconditionally = run_bundle_def is not None and any(
        not isinstance(statement, ast.If)
        and any(
            isinstance(leaf, ast.Constant) and leaf.value == "ENGLISH_REQUIRED_ANCHORS"
            for leaf in ast.walk(statement)
        )
        for statement in run_bundle_def.body
    )
    check(
        armed_unconditionally and len(ENGLISH_ANCHORS) > 0,
        "SELFTEST_ENGLISH_ARMED_WITHOUT_RUSSIAN",
        "ENGLISH_REQUIRED_ANCHORS must be armed outside the bilingual branch of run_bundle",
    )
    # Tooth (d): gate count is computed at runtime, not hardcoded.
    check(
        "gate_count" in run_bundle.__code__.co_varnames,
        "SELFTEST_GATE_COUNT_INTEGRITY",
        "run_bundle must use a live gate_count variable, not a hardcoded return",
    )
    return 7


def run_bundle() -> tuple[int, int]:
    # A gate is one named validation section counted at runtime by the live
    # gate_count variable; self-test teeth are counted individually and
    # included in the total; mutations are reported separately, not as gates.
    gate_count = 0

    self_tests = self_test_gate()
    gate_count += self_tests

    # --- Inventory gate ---
    missing = missing_inventory(HERE)
    check(not missing, "INVENTORY", f"missing files: {sorted(missing)}")
    gate_count += 1

    # --- Document inventory gate (English mandatory; Russian optional) ---
    bilingual = RUSSIAN.is_file()
    check(ENGLISH.is_file(), "DOCUMENT_INVENTORY", "English manuscript missing")
    tracked = [HERE / name for name in sorted(EXPECTED_HARNESS)]
    tracked.append(ENGLISH)
    if bilingual:
        tracked.append(RUSSIAN)
    non_lf = non_lf_files(tracked)
    check(not non_lf, "DOCUMENT_INVENTORY", f"non-LF files: {sorted(non_lf)}")
    gate_count += 1

    # --- Bare assert gate ---
    python_files = sorted(HERE.glob("*.py"))
    assert_sites = {path.name: bare_assert_sites(path) for path in python_files}
    assert_sites = {name: sites for name, sites in assert_sites.items() if sites}
    check(not assert_sites, "BARE_ASSERT", str(assert_sites))
    gate_count += 1

    # --- Public hygiene gate (English + README always; Russian when present) ---
    english = ENGLISH.read_text(encoding="utf-8")
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    hygiene_targets = [(ENGLISH.name, english), ("README.md", readme)]
    if bilingual:
        russian = RUSSIAN.read_text(encoding="utf-8")
        hygiene_targets.append((RUSSIAN.name, russian))
    for name, text in hygiene_targets:
        check(not hygiene_findings(text), "PUBLIC_HYGIENE", f"{name}: {hygiene_findings(text)}")
    gate_count += 1

    # --- English required anchors gate (always-on) ---
    missing_english = [a for a in ENGLISH_ANCHORS if a not in english]
    check(
        not missing_english,
        "ENGLISH_REQUIRED_ANCHORS",
        f"missing English anchors: {missing_english}",
    )
    gate_count += 1

    # --- Bilingual structure gate (conditional on Russian) ---
    if bilingual:
        validate_bilingual_structure(english, russian)
        gate_count += 1

    # --- Execution gate ---
    expected = "finite seam audit passed: 29 checks"
    commands = (
        (sys.executable, str(HERE / "seam_audit.py")),
        (sys.executable, "-O", str(HERE / "seam_audit.py")),
        (sys.executable, str(HERE / "seam_transport.py")),
        (sys.executable, "-O", str(HERE / "seam_transport.py")),
    )
    for command in commands:
        result = run(command)
        check(result.returncode == 0, "EXECUTION", result.stderr.strip())
        check(result.stdout.strip() == expected, "EXECUTION_OUTPUT", result.stdout.strip())
    gate_count += 1

    # --- Certificate gate ---
    with tempfile.TemporaryDirectory(prefix="seam-certificate-") as directory:
        generated_path = Path(directory) / "certificate.json"
        result = run(
            (
                sys.executable,
                "-O",
                str(HERE / "seam_audit.py"),
                "--emit-certificate",
                str(generated_path),
            )
        )
        check(result.returncode == 0 and generated_path.is_file(), "CERTIFICATE_EMIT", result.stderr)
        generated_bytes = generated_path.read_bytes()
        generated = json.loads(generated_bytes.decode("utf-8"))
    checked_in_bytes = (HERE / "seam_certificate.json").read_bytes()
    checked_in = json.loads(checked_in_bytes.decode("utf-8"))
    compare_certificate(generated, checked_in, generated_bytes, checked_in_bytes)
    gate_count += 1

    # --- Mutation gate ---
    source = (HERE / "seam_audit.py").read_text(encoding="utf-8")
    mutations = (
        (
            'ALT_AB = Seam("p1", "A", "B", 0, True)',
            'ALT_AB = Seam("g1", "A", "B", 0, True)',
            "ALPHABET_UNIQUE",
        ),
        (
            "BAD: History = (BAD_AB, GOOD_BA)",
            "BAD: History = (GOOD_AB, GOOD_BA)",
            "TARGET_FIBRE_WITNESS",
        ),
        (
            "def complete_delta(seam: Seam) -> int:\n    return seam.defect",
            "def complete_delta(seam: Seam) -> int:\n    return 0",
            "GENERATOR_KERNEL_COMPLETE",
        ),
        (
            "return trace(history), membership_word(history)",
            "return trace(history), tuple(1 for _ in history)",
            "AUDIT_VERDICT_FACTORS",
        ),
    )
    for old, new, marker in mutations:
        mutation_run(source, old, new, marker)

    return gate_count, len(mutations)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the finite seam audit bundle")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run only synthetic teeth for the bundle gate",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.self_test:
            count = self_test_gate()
            print(f"bundle gate self-test passed: {count} teeth")
        else:
            gates, mutations = run_bundle()
            print(f"bundle checks passed: {gates} gates, {mutations} mutations")
        return 0
    except (BundleFailure, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        print(f"bundle checks failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
