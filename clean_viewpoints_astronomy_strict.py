#!/usr/bin/env python3
"""
Vytvori astronomy strict variantu vyhlidkovych mist.

Cil:
- zachovat jen mista vhodna pro pozorovani oblohy
- vyhodit rozhledny/veze, byvale objekty, lesni body bez overitelneho vyhledu
- ponechat puvodni *_clean data beze zmen

Vystupy:
- vyhlidkova_mista_cr_astronomystrict.csv
- vyhlidkova_mista_cr_astronomystrict_named.csv
- output/astronomystrict_filter_report.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "vyhlidkova_mista_cr.csv"
REFERENCE_CLEAN_FILE = BASE_DIR / "vyhlidkova_mista_cr_clean.csv"
OUTPUT_FILE = BASE_DIR / "vyhlidkova_mista_cr_astronomystrict.csv"
OUTPUT_NAMED_FILE = BASE_DIR / "vyhlidkova_mista_cr_astronomystrict_named.csv"
REPORT_FILE = BASE_DIR / "output" / "astronomystrict_filter_report.csv"

TOWER_MAN_MADE = {"observation_tower", "tower", "windmill"}
TOWER_TYPES = {"tower", "observation", "watchtower", "lookout"}

# Nazvy, ktere typicky znamenaji objekt nevhodny pro nocni pozorovani oblohy.
TOWER_NAME_KEYWORDS = {
    "rozhledna",
    "rozhledny",
    "rozhledna",
    "vez",
    "věž",
    "tower",
    "watchtower",
    "zvonice",
    "radnicni vez",
    "radniční věž",
    "minirozhledna",
    "pidirozhledna",
    "vyhlidkova vez",
    "vyhlídková věž",
}

NOT_ASTRONOMY_NAME_KEYWORDS = {
    "byvala",
    "bývalá",
    "zricenina",
    "zřícenina",
    "ruina",
    "ruins",
    "tribuna",
    "spotting point",
    "fotopoint",
    "camera obscura",
    "trznice",
    "tržnice",
    "narodni muzeum",
    "národní muzeum",
}

FOREST_LIKE_KEYWORDS = {
    "les",
    "haj",
    "háj",
    "obora",
    "raseliniste",
    "rašeliniště",
}


def normalize(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"unknown", "nan", "none"}:
        return ""
    return text


def is_named_place(name: str) -> bool:
    lowered = name.lower()
    if not lowered:
        return False
    if lowered in {"unnamed poi", "unknown", "nan"}:
        return False
    if lowered.isdigit():
        return False
    return True


def matches_any_keyword(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def classify_row(row: pd.Series) -> Tuple[bool, str]:
    name = normalize(row.get("name", ""))
    tourism = normalize(row.get("tourism", "")).lower()
    natural = normalize(row.get("natural", "")).lower()
    man_made = normalize(row.get("man_made", "")).lower()
    tower_type = normalize(row.get("tower:type", "")).lower()
    access = normalize(row.get("access", "")).lower()

    if tourism != "viewpoint" and natural != "peak":
        return False, "not_viewpoint_or_peak"

    if man_made in TOWER_MAN_MADE or tower_type in TOWER_TYPES:
        return False, "tower_tag"

    if not is_named_place(name):
        return False, "unnamed_or_unusable_name"

    if matches_any_keyword(name, TOWER_NAME_KEYWORDS):
        return False, "tower_like_name"

    if matches_any_keyword(name, NOT_ASTRONOMY_NAME_KEYWORDS):
        return False, "non_astronomy_name"

    if matches_any_keyword(name, FOREST_LIKE_KEYWORDS):
        return False, "forest_like_name"

    if access in {"private", "no", "customers"}:
        return False, "restricted_access"

    return True, "kept"


def round_coordinates(lat: float, lon: float, decimals: int = 4) -> Tuple[float, float]:
    return round(float(lat), decimals), round(float(lon), decimals)


def build_report(
    total_input: int,
    total_clean_reference: int,
    kept_count: int,
    reason_counts: Dict[str, int],
) -> pd.DataFrame:
    dropped_count = total_input - kept_count
    strict_drop_vs_input = (dropped_count / total_input * 100) if total_input else 0.0
    strict_drop_vs_clean = (
        ((total_clean_reference - kept_count) / total_clean_reference * 100)
        if total_clean_reference
        else 0.0
    )

    rows: List[Dict[str, object]] = [
        {
            "metric": "input_total",
            "value": total_input,
        },
        {
            "metric": "clean_reference_total",
            "value": total_clean_reference,
        },
        {
            "metric": "astronomystrict_total",
            "value": kept_count,
        },
        {
            "metric": "drop_vs_input_count",
            "value": dropped_count,
        },
        {
            "metric": "drop_vs_input_pct",
            "value": round(strict_drop_vs_input, 2),
        },
        {
            "metric": "drop_vs_clean_count",
            "value": total_clean_reference - kept_count,
        },
        {
            "metric": "drop_vs_clean_pct",
            "value": round(strict_drop_vs_clean, 2),
        },
    ]

    for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
        rows.append({"metric": f"filtered_reason::{reason}", "value": count})

    return pd.DataFrame(rows)


def main() -> None:
    print(f"Nacitam data: {INPUT_FILE.name}")
    df = pd.read_csv(INPUT_FILE)

    print(f"Nacteno celkem: {len(df)}")

    kept_rows: List[pd.Series] = []
    reason_counts: Dict[str, int] = {}

    for _, row in df.iterrows():
        keep, reason = classify_row(row)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if keep:
            kept_rows.append(row)

    strict_df = pd.DataFrame(kept_rows)

    output_df = pd.DataFrame()
    output_df["name"] = strict_df["name"].map(normalize)
    output_df["lat"] = strict_df.apply(lambda r: round_coordinates(r["lat"], r["lon"])[0], axis=1)
    output_df["lon"] = strict_df.apply(lambda r: round_coordinates(r["lat"], r["lon"])[1], axis=1)

    # Deduplicate strict points by rounded coordinates + name.
    output_df = output_df.drop_duplicates(subset=["name", "lat", "lon"]).reset_index(drop=True)

    named_df = output_df[output_df["name"].map(is_named_place)].copy()

    output_df.to_csv(OUTPUT_FILE, index=False)
    named_df.to_csv(OUTPUT_NAMED_FILE, index=False)

    clean_reference_count = len(pd.read_csv(REFERENCE_CLEAN_FILE)) if REFERENCE_CLEAN_FILE.exists() else 0

    REPORT_FILE.parent.mkdir(exist_ok=True)
    report_df = build_report(
        total_input=len(df),
        total_clean_reference=clean_reference_count,
        kept_count=len(output_df),
        reason_counts=reason_counts,
    )
    report_df.to_csv(REPORT_FILE, index=False)

    print("\n=== Astronomy strict summary ===")
    print(f"Output strict: {OUTPUT_FILE.name} -> {len(output_df)} zaznamu")
    print(f"Output strict named: {OUTPUT_NAMED_FILE.name} -> {len(named_df)} zaznamu")
    print(f"Reference clean: {clean_reference_count} zaznamu")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
