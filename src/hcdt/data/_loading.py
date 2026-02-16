"""Shared helpers for mapping tabular data to BuildingRecord."""

import pandas as pd

from .schemas import BuildingRecord


def map_columns_to_building_record(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Rename columns using map; id is coerced to str."""
    rename = {}
    for col in df.columns:
        key = col.strip() if isinstance(col, str) else col
        if key in column_map:
            rename[col] = column_map[key]
    out = df.rename(columns=rename)
    if "id" in out.columns:
        out["id"] = out["id"].astype(str)
    return out


def to_building_record_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Select and order columns to match BuildingRecord."""
    field_names = list(BuildingRecord.model_fields.keys())
    cols = [c for c in field_names if c in df.columns]
    return df[cols].copy()
