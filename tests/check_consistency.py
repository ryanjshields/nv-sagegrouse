# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "numpy"]
# ///
"""check_consistency.py -- verify every numeric claim in the reports against the artifacts.

The manuscript and the findings document quote numbers that are produced by the
pipeline and written to reports/v4/. Nothing keeps those two in step: a refit
changes a CSV, the prose keeps the old value, and the paper ships a number that no
longer exists anywhere in the analysis. This script closes that loop.

Three checks run, in order:

  1. TARGETED   -- each registered claim (betas + 85% CIs, AUC, Boyce, Spearman,
                   counts, percentages) is resolved against its artifact and
                   compared at the precision the prose actually quotes.
  2. COHERENCE  -- artifacts are checked against each other, catching the case
                   where two committed CSVs disagree because they were written by
                   different runs.
  3. SWEEP      -- every remaining number in the prose is listed as UNTRACED, so a
                   claim that no rule covers is surfaced rather than assumed fine.

Exit codes:
  0  no failures (warnings may be present)
  1  at least one claim FAILED, or --strict was given and warnings exist
  2  required artifacts are missing, so the check could not run

Run:  uv run tests/check_consistency.py
      uv run tests/check_consistency.py --strict     # untraced numbers also fail
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
V4 = ROOT / "reports" / "v4"
TABLES = V4 / "tables"
REPORTS = [ROOT / "reports" / "paper.qmd", ROOT / "reports" / "findings.qmd"]

# Artifacts the targeted checks cannot run without.
REQUIRED_ARTIFACTS = [
    V4 / "averaged_betas.csv",
    V4 / "diagnostics.csv",
    V4 / "spatial_validation.csv",
    V4 / "boyce_pe.csv",
    V4 / "calibration.csv",
    V4 / "model_selection.csv",
]

# Unicode the manuscript uses that plain float parsing chokes on.
MINUS_SIGNS = {"−": "-", "–": "-", "—": "-", "‐": "-", "‑": "-"}


@dataclass
class Result:
    status: str  # "PASS" | "FAIL" | "WARN"
    label: str
    detail: str
    location: str = ""


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, status: str, label: str, detail: str, location: str = "") -> None:
        self.results.append(Result(status, label, detail, location))

    def count(self, status: str) -> int:
        return sum(1 for r in self.results if r.status == status)


def normalise(text: str) -> str:
    """Replace typographic minus/dash characters so numbers parse as floats."""
    for bad, good in MINUS_SIGNS.items():
        text = text.replace(bad, good)
    return text


def to_float(token: str) -> float:
    cleaned = normalise(token).replace(",", "").replace("%", "").strip()
    if not cleaned:
        raise ValueError("Cannot convert an empty token to float")
    return float(cleaned)


def quoted_decimals(token: str) -> int:
    """How many decimal places the prose used, so we compare at ITS precision."""
    cleaned = normalise(token).replace(",", "").replace("%", "").strip()
    if "." not in cleaned:
        return 0
    return len(cleaned.split(".", 1)[1])


def matches_at_quoted_precision(quoted: str, actual: float) -> bool:
    """A claim is honest if rounding the artifact to the quoted precision reproduces it."""
    places = quoted_decimals(quoted)
    return round(float(actual), places) == round(to_float(quoted), places)


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------

CODE_FENCE = re.compile(r"^\s*```")
FRONTMATTER_DELIM = re.compile(r"^---\s*$")


def prose_lines(path: Path) -> list[tuple[int, str]]:
    """Return (line_number, text) for prose lines only: no YAML header, no code fences."""
    if not path.exists():
        raise FileNotFoundError(f"Report source not found: {path}")
    raw = path.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []
    in_code = False
    in_frontmatter = False
    for index, line in enumerate(raw, start=1):
        if index == 1 and FRONTMATTER_DELIM.match(line):
            in_frontmatter = True
            continue
        if in_frontmatter:
            if FRONTMATTER_DELIM.match(line):
                in_frontmatter = False
            continue
        if CODE_FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        out.append((index, line))
    return out


def load_artifacts() -> dict[str, object]:
    """Load every artifact the checks need, keyed by a short name."""
    betas = pd.read_csv(V4 / "averaged_betas.csv", index_col=0)
    diagnostics = pd.read_csv(V4 / "diagnostics.csv").set_index("metric")["value"]
    spatial = pd.read_csv(V4 / "spatial_validation.csv").set_index("metric")["value"]
    boyce = pd.read_csv(V4 / "boyce_pe.csv")
    calibration = pd.read_csv(V4 / "calibration.csv")
    selection = pd.read_csv(V4 / "model_selection.csv", index_col=0)
    artifacts: dict[str, object] = {
        "betas": betas,
        "diagnostics": diagnostics,
        "spatial": spatial,
        "boyce": boyce,
        "calibration": calibration,
        "selection": selection,
    }
    optional = {
        "vif": V4 / "vif.csv",
        "sensitivity": V4 / "sensitivity_fire.csv",
    }
    for name, path in optional.items():
        artifacts[name] = pd.read_csv(path) if path.exists() else None
    text_sources = {
        "usgs_txt": V4 / "usgs_validation.txt",
        "contingency_md": TABLES / "usgs_contingency_plain.md",
        "veg_change_md": TABLES / "veg_change.md",
        "summary_md": TABLES / "summary_stats.md",
        "boyce_md": TABLES / "boyce.md",
    }
    for name, path in text_sources.items():
        artifacts[name] = path.read_text(encoding="utf-8") if path.exists() else None
    return artifacts


# ---------------------------------------------------------------------------
# 1. Targeted claim checks
# ---------------------------------------------------------------------------

BETA_WITH_CI = re.compile(
    r"β\s*=\s*(?P<beta>[−–-]?\d+\.\d+)\s*,\s*85%\s*CI\s*"
    r"(?P<low>[−–-]?\d+\.\d+)\s*[–−-]+\s*(?P<high>[−–-]?\d+\.\d+)"
)

SIMPLE_METRICS: list[tuple[str, re.Pattern[str], str]] = [
    ("AUC (full model average)", re.compile(r"AUC\s*=\s*(\d\.\d+)"), "diagnostics"),
    ("Boyce index", re.compile(r"continuous Boyce index was (\d\.\d+)"), "boyce"),
    ("Boyce index (findings)", re.compile(r"Ours is \*\*(\d\.\d+)\*\*"), "boyce"),
    ("USGS Spearman", re.compile(r"ρ\s*=\s*(\d\.\d+)\s*(?:at|across)"), "usgs"),
    ("lek-size Spearman", re.compile(r"peak male counts(?:[^.]*?)(\d\.\d\d)"), "leksize"),
]


def check_beta_claims(lines: list[tuple[int, str]], path: Path, betas: pd.DataFrame, report: Report) -> None:
    """Every 'β = x, 85% CI lo – hi' triple must reproduce exactly one row of averaged_betas.csv."""
    for number, line in lines:
        for match in BETA_WITH_CI.finditer(line):
            quoted_beta = match.group("beta")
            quoted_low = match.group("low")
            quoted_high = match.group("high")
            location = f"{path.relative_to(ROOT)}:{number}"
            hits = []
            for term, row in betas.iterrows():
                if (
                    matches_at_quoted_precision(quoted_beta, row["Estimate"])
                    and matches_at_quoted_precision(quoted_low, row["ci85_low"])
                    and matches_at_quoted_precision(quoted_high, row["ci85_high"])
                ):
                    hits.append(str(term))
            claim = f"β = {normalise(quoted_beta)}, 85% CI {normalise(quoted_low)} – {normalise(quoted_high)}"
            if len(hits) == 1:
                report.add("PASS", claim, f"matches averaged_betas.csv row '{hits[0]}'", location)
            elif len(hits) > 1:
                report.add("PASS", claim, f"matches rows {hits} (ambiguous but present)", location)
            else:
                report.add(
                    "FAIL",
                    claim,
                    "no row of reports/v4/averaged_betas.csv reproduces this estimate and interval",
                    location,
                )


def check_simple_metrics(lines: list[tuple[int, str]], path: Path, art: dict[str, object], report: Report) -> None:
    diagnostics = art["diagnostics"]
    spatial = art["spatial"]
    boyce = art["boyce"]
    usgs_txt = art["usgs_txt"]

    for label, pattern, kind in SIMPLE_METRICS:
        for number, line in lines:
            for match in pattern.finditer(line):
                quoted = match.group(1)
                location = f"{path.relative_to(ROOT)}:{number}"
                if kind == "diagnostics":
                    actual = float(diagnostics["AUC (full model average)"])
                    source = "diagnostics.csv[AUC (full model average)]"
                elif kind == "boyce":
                    actual = float(boyce["boyce"].iloc[0])
                    source = "boyce_pe.csv[boyce]"
                elif kind == "usgs":
                    if usgs_txt is None:
                        report.add("WARN", label, "usgs_validation.txt absent", location)
                        continue
                    found = re.search(r"Spearman\(ours, USGS\):\s*([\d.]+)", usgs_txt)
                    if found is None:
                        report.add("WARN", label, "no Spearman line in usgs_validation.txt", location)
                        continue
                    actual = float(found.group(1))
                    source = "usgs_validation.txt"
                elif kind == "leksize":
                    actual = float(spatial["lek-size Spearman (p_hat vs PEAKMALE)"])
                    source = "spatial_validation.csv[lek-size Spearman]"
                else:
                    raise ValueError(f"Unknown metric kind {kind!r}")

                status = "PASS" if matches_at_quoted_precision(quoted, actual) else "FAIL"
                report.add(status, f"{label} = {quoted}", f"{source} = {actual}", location)


# Both documents quote a "mean ± sd" for the random-fold CV and again for the
# spatially blocked CV, in the same sentence and with the same mean (0.80). The
# patterns must therefore be anchored on the qualifier ("random" / "spatially
# blocked"), never on the bare phrase "5-fold cross-validation", or the two
# claims get checked against each other's artifact.
MEAN_SD_PATTERNS: list[tuple[list[re.Pattern[str]], str, str, str]] = [
    (
        [
            re.compile(r"random\s+5-fold\s+cross-?\s*validation\s+(\d\.\d+)\s*±\s*(\d\.\d+)", re.IGNORECASE),
            re.compile(r"(\d\.\d+)\s*±\s*(\d\.\d+)\*\*\s*under\s+5-fold", re.IGNORECASE),
        ],
        "AUC (5-fold CV, top model)",
        "CV sd",
        "diagnostics",
    ),
    (
        [
            re.compile(r"spatially blocked(?:(?!spatially blocked).){0,200}?(\d\.\d+)\s*±\s*(\d\.\d+)", re.IGNORECASE | re.DOTALL),
        ],
        "spatial-block AUC mean",
        "spatial-block AUC sd",
        "spatial",
    ),
]


def check_mean_sd_claims(lines: list[tuple[int, str]], path: Path, art: dict[str, object], report: Report) -> None:
    """'0.80 ± 0.01' style claims must match the mean AND the sd, not just the mean."""
    joined = "\n".join(text for _, text in lines)
    line_of_offset: list[int] = []
    for number, text in lines:
        line_of_offset.extend([number] * (len(text) + 1))

    for patterns, mean_key, sd_key, source_name in MEAN_SD_PATTERNS:
        source = art[source_name]
        matches = [m for pattern in patterns for m in pattern.finditer(normalise(joined))]
        for match in matches:
            offset = match.start()
            number = line_of_offset[offset] if offset < len(line_of_offset) else 0
            location = f"{path.relative_to(ROOT)}:{number}"
            quoted_mean, quoted_sd = match.group(1), match.group(2)
            actual_mean = float(source[mean_key])
            actual_sd = float(source[sd_key])
            mean_ok = matches_at_quoted_precision(quoted_mean, actual_mean)
            sd_ok = matches_at_quoted_precision(quoted_sd, actual_sd)
            status = "PASS" if mean_ok and sd_ok else "FAIL"
            report.add(
                status,
                f"{mean_key} {quoted_mean} ± {quoted_sd}",
                f"{source_name}: mean={actual_mean}, sd={actual_sd}"
                + ("" if mean_ok else " [MEAN MISMATCH]")
                + ("" if sd_ok else " [SD MISMATCH]"),
                location,
            )


def check_counts_and_shares(art: dict[str, object], report: Report) -> None:
    """Counts and percentages quoted in the prose, resolved against their artifacts."""
    spatial = art["spatial"]
    selection = art["selection"]
    boyce = art["boyce"]
    calibration = art["calibration"]

    used_leks = int(spatial["n leks with counts"])
    report.add(
        "PASS" if used_leks == 718 else "FAIL",
        "used leks n = 718",
        f"spatial_validation.csv[n leks with counts] = {used_leks}",
        "reports/paper.qmd (n = 718, repeated)",
    )
    report.add(
        "PASS" if used_leks * 10 == 7180 else "FAIL",
        "available points n = 7,180 (ten per used lek)",
        f"10 x {used_leks} = {used_leks * 10}",
        "reports/paper.qmd:227",
    )

    n_models = len(selection)
    report.add(
        "PASS" if n_models == 15 else "FAIL",
        "fifteen candidate models",
        f"model_selection.csv has {n_models} rows",
        "reports/paper.qmd:316-320",
    )
    top3 = list(selection.index[:3])
    report.add(
        "PASS" if top3 == ["m13", "m14", "m15"] else "FAIL",
        "the three road-class models lead the ranking",
        f"model_selection.csv top three = {top3}",
        "reports/paper.qmd:394",
    )

    max_pe = float(boyce["pe"].max())
    report.add(
        "PASS" if max_pe > 6.0 else "FAIL",
        "highest class holds leks at more than six times its areal share",
        f"boyce_pe.csv max P/E = {max_pe:.4f}",
        "reports/paper.qmd:457-459",
    )

    n_deciles = len(calibration)
    report.add(
        "PASS" if n_deciles == 10 else "FAIL",
        "calibration by decile",
        f"calibration.csv has {n_deciles} rows",
        "reports/paper.qmd:445",
    )

    vif = art["vif"]
    if vif is None:
        report.add("WARN", "VIF <= 1.8", "reports/v4/vif.csv absent", "reports/paper.qmd:330")
    else:
        vif_max = float(vif["vif"].max())
        vif_min = float(vif["vif"].min())
        report.add(
            "PASS" if vif_max <= 1.8 else "FAIL",
            "all variables in all top models had VIF <= 1.8",
            f"vif.csv max = {vif_max:.4f}",
            "reports/paper.qmd:330",
        )
        report.add(
            "PASS" if (1.0 <= vif_min and vif_max <= 1.8) else "FAIL",
            "VIF range 1.0-1.8",
            f"vif.csv range = {vif_min:.4f}-{vif_max:.4f}",
            "reports/paper.qmd:399",
        )

    contingency = art["contingency_md"]
    if contingency is None:
        report.add("WARN", "USGS contingency 46% / 41%", "usgs_contingency_plain.md absent")
    else:
        rows = {
            "USGS non-habitat": ("46%", "lowest bin", 0),
            "USGS high habitat": ("41%", "highest bin", -1),
        }
        for row_label, (quoted, description, column_index) in rows.items():
            line = next((l for l in contingency.splitlines() if l.startswith(f"| {row_label}")), None)
            if line is None:
                report.add("FAIL", f"{row_label} {quoted} in our {description}", "row absent from contingency table")
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            actual = cells[1:][column_index]
            report.add(
                "PASS" if actual == quoted else "FAIL",
                f"{quoted} of {row_label} falls in our {description}",
                f"usgs_contingency_plain.md -> {actual}",
                "reports/paper.qmd:461-462, 487-488",
            )

    veg_change = art["veg_change_md"]
    if veg_change is None:
        report.add("WARN", "35 of 718 leks changed class (4.9%)", "veg_change.md absent")
    else:
        header = veg_change.splitlines()[0]
        expectations = [
            (r"Used leks:\s*(\d+)", "718", "718 used leks"),
            (r"class changed LF2016->LF2025:\s*(\d+)", "35", "35 leks changed physiognomy class"),
            (r"class changed LF2016->LF2025:\s*\d+\s*\(([\d.]+)%\)", "4.9", "4.9% changed"),
            (r"fire signature\):\s*(\d+)", "8", "8 with the fire signature"),
        ]
        for pattern, expected, label in expectations:
            found = re.search(pattern, header)
            if found is None:
                report.add("FAIL", label, f"pattern {pattern!r} not found in veg_change.md header")
                continue
            report.add(
                "PASS" if found.group(1) == expected else "FAIL",
                label,
                f"veg_change.md -> {found.group(1)}",
                "reports/paper.qmd:466",
            )

    sensitivity = art["sensitivity"]
    if sensitivity is None:
        report.add("WARN", "grassland attenuates from 0.43 to 0.21", "sensitivity_fire.csv absent")
    else:
        row = sensitivity[sensitivity["term"] == "VegetationGrassland"]
        if row.empty:
            report.add("FAIL", "grassland attenuates from 0.43 to 0.21", "no VegetationGrassland row")
        else:
            all_leks = float(row["all_leks"].iloc[0])
            excluded = float(row["excl_changed"].iloc[0])
            ok = matches_at_quoted_precision("0.43", all_leks) and matches_at_quoted_precision("0.21", excluded)
            report.add(
                "PASS" if ok else "FAIL",
                "grassland coefficient attenuated from 0.43 to 0.21",
                f"sensitivity_fire.csv -> {all_leks} then {excluded}",
                "reports/paper.qmd:470-471",
            )

    summary = art["summary_md"]
    if summary is None:
        report.add("WARN", "VRM 0.00046 used vs 0.00197 available", "summary_stats.md absent")
    else:
        vrm_rows = [l for l in summary.splitlines() if l.startswith("| Ruggedness (VRM)")]
        if len(vrm_rows) != 2:
            report.add("FAIL", "VRM used/available means", f"expected 2 VRM rows, found {len(vrm_rows)}")
        else:
            for row_text, quoted, which in zip(vrm_rows, ("0.00046", "0.00197"), ("used", "available")):
                cells = [c.strip() for c in row_text.split("|") if c.strip()]
                actual = float(cells[2])
                report.add(
                    "PASS" if matches_at_quoted_precision(quoted, actual) else "FAIL",
                    f"mean VRM at {which} sites = {quoted}",
                    f"summary_stats.md -> {actual}",
                    "reports/paper.qmd:428",
                )


# ---------------------------------------------------------------------------
# 2. Cross-artifact coherence
# ---------------------------------------------------------------------------


def check_artifact_coherence(art: dict[str, object], report: Report) -> None:
    """Artifacts must agree with each other; disagreement means they came from different runs."""
    diagnostics = art["diagnostics"]
    spatial = art["spatial"]
    boyce = art["boyce"]
    selection = art["selection"]

    # validate_spatial.R:63 copies diagnostics.csv$value[2] verbatim into
    # spatial_validation.csv. If the two disagree, one file is stale.
    cv_auc = float(diagnostics["AUC (5-fold CV, top model)"])
    copied = float(spatial["random-fold AUC (reference)"])
    report.add(
        "PASS" if abs(cv_auc - copied) < 5e-4 else "FAIL",
        "spatial_validation.csv random-fold reference == diagnostics.csv CV AUC",
        f"diagnostics.csv = {cv_auc}, spatial_validation.csv = {copied} "
        "(validate_spatial.R:63 copies the value, so any gap means one CSV is from an older run)",
        "pipeline/validate_spatial.R:63",
    )

    boyce_column = boyce["boyce"].to_numpy()
    report.add(
        "PASS" if len(set(boyce_column.tolist())) == 1 else "FAIL",
        "boyce_pe.csv carries one constant index value",
        f"{len(set(boyce_column.tolist()))} distinct values in the boyce column",
        "pipeline/boyce.py:48-49",
    )

    boyce_md = art["boyce_md"]
    if boyce_md is None:
        report.add("WARN", "boyce.md headline matches boyce_pe.csv", "boyce.md absent")
    else:
        found = re.search(r"Continuous Boyce index:\s*([\d.]+)", boyce_md)
        if found is None:
            report.add("FAIL", "boyce.md headline matches boyce_pe.csv", "no headline in boyce.md")
        else:
            report.add(
                "PASS" if matches_at_quoted_precision(found.group(1), float(boyce_column[0])) else "FAIL",
                "boyce.md headline matches boyce_pe.csv",
                f"boyce.md = {found.group(1)}, boyce_pe.csv = {boyce_column[0]}",
                "pipeline/boyce.py:48-51",
            )

    weight_sum = float(selection["weight"].sum())
    report.add(
        "PASS" if abs(weight_sum - 1.0) < 1e-6 else "FAIL",
        "model_selection.csv Akaike weights sum to 1",
        f"sum = {weight_sum:.9f}",
        "pipeline/fit_models.R:62",
    )

    deltas = selection["delta"].to_numpy()
    report.add(
        "PASS" if deltas[0] == 0 and all(deltas[i] <= deltas[i + 1] for i in range(len(deltas) - 1)) else "FAIL",
        "model_selection.csv is sorted by ascending delta with the top model at 0",
        f"first delta = {deltas[0]}, sorted = {all(deltas[i] <= deltas[i + 1] for i in range(len(deltas) - 1))}",
        "pipeline/fit_models.R:62-65",
    )


# ---------------------------------------------------------------------------
# 3. Untraced-number sweep
# ---------------------------------------------------------------------------

NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\w])")

# Tokens that are structural, bibliographic or vocabulary rather than results.
SWEEP_SKIP_LINE = re.compile(
    r"^\s*(\||!\[|\{\{<|:::|#|\[\d+\])"
)
SWEEP_SKIP_CONTEXT = [
    re.compile(r"\[\d+(?:,\s*\d+)*\]"),          # bibliography markers
    re.compile(r"(?:Fig(?:ure)?\.?|Table|Eq\.?)\s*\d+", re.IGNORECASE),
    re.compile(r"\{width=\d+%\}"),
    re.compile(r"EPSG:\d+"),
    re.compile(r"S\d{4}"),                       # MTFCC road classes
    re.compile(r"LF\d{4}"),
    re.compile(r"\b(?:19|20)\d{2}\b"),           # years
]
# Values already verified by a targeted rule, or that are definitional constants.
SWEEP_KNOWN = {
    "718", "7,180", "7180", "15", "12", "10", "5", "3", "1", "0", "2", "4", "8", "35", "4.9", "1.1",
    "0.5", "1.5", "0.9", "0.8", "0.81", "0.80", "0.92", "0.53", "0.04", "0.01", "46", "41",
    "1.0", "1.8", "0.6", "0.99", "0.40", "0.43", "0.21", "6", "20", "30", "90", "85",
}


def sweep_untraced_numbers(lines: list[tuple[int, str]], path: Path, report: Report) -> None:
    """List numbers no targeted rule covers, so an unverifiable claim is visible rather than silent."""
    seen: set[tuple[str, int]] = set()
    for number, line in lines:
        if SWEEP_SKIP_LINE.match(line):
            continue
        cleaned = line
        for pattern in SWEEP_SKIP_CONTEXT:
            cleaned = pattern.sub(" ", cleaned)
        for match in NUMBER.finditer(normalise(cleaned)):
            token = match.group(1)
            if token in SWEEP_KNOWN:
                continue
            key = (token, number)
            if key in seen:
                continue
            seen.add(key)
            report.add(
                "WARN",
                f"untraced number {token}",
                "no artifact rule claims this value; verify by hand or add a rule",
                f"{path.relative_to(ROOT)}:{number}",
            )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def emit(report: Report, show_warnings: bool) -> None:
    width = 0
    for result in report.results:
        width = max(width, len(result.label))
    for result in report.results:
        if result.status == "WARN" and not show_warnings:
            continue
        location = f"  [{result.location}]" if result.location else ""
        print(f"{result.status:4}  {result.label:<{min(width, 70)}}  {result.detail}{location}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="treat untraced numbers as failures")
    parser.add_argument("--quiet-warnings", action="store_true", help="hide WARN lines in the listing")
    args = parser.parse_args()

    missing = [p for p in REQUIRED_ARTIFACTS if not p.exists()]
    if missing:
        print("ARTIFACTS MISSING -- cannot verify the reports against the analysis outputs:")
        for path in missing:
            print(f"  - {path.relative_to(ROOT)}")
        print(
            "\nreports/v4/*.csv are excluded by the repo's .gitignore rule `*.csv`, so a fresh\n"
            "clone (including CI) has no artifacts to check against. Either run the pipeline\n"
            "locally (`make v4`) or commit the result CSVs -- they hold aggregate statistics\n"
            "only, no lek coordinates. See tests/FINDINGS.md (F1)."
        )
        return 2

    artifacts = load_artifacts()
    report = Report()

    for path in REPORTS:
        lines = prose_lines(path)
        check_beta_claims(lines, path, artifacts["betas"], report)
        check_simple_metrics(lines, path, artifacts, report)
        check_mean_sd_claims(lines, path, artifacts, report)

    check_counts_and_shares(artifacts, report)
    check_artifact_coherence(artifacts, report)

    for path in REPORTS:
        sweep_untraced_numbers(prose_lines(path), path, report)

    emit(report, show_warnings=not args.quiet_warnings)

    passed, failed, warned = report.count("PASS"), report.count("FAIL"), report.count("WARN")
    print(f"\n{passed} passed, {failed} failed, {warned} untraced/warning")

    if failed:
        print("\nFAILURES:")
        for result in report.results:
            if result.status == "FAIL":
                print(f"  {result.label}  ->  {result.detail}  [{result.location}]")
        return 1
    if args.strict and warned:
        print("\n--strict: untraced numbers are treated as failures")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
