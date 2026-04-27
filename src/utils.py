from datetime import datetime
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi





# Returns a timestamp token so Shiny can poll for fresh MongoDB data.
def getDateTime():
    try:
        now = datetime.now()
        print('Querying Data')
        return now
            
    except Exception as e:
        print(f"Error accessing Datetime: {e}")
        return None
    

# ----------------------------
# Metadata helpers
# ----------------------------

# Parses a user datetime string into a UTC pandas timestamp.
def parse_datetime_input(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value, utc=True)
    except Exception:
        return None

# Expands quantity dict columns into separate value and unit columns.
def flatten_quantities(df: pd.DataFrame) -> pd.DataFrame:
    """
    If a column contains dicts like {"value": x, "unit": y},
    convert to two columns: <col>_value and <col>_unit.
    """
    if df.empty:
        return df

    for col in list(df.columns):
        s = df[col].dropna()
        if s.empty:
            continue
        v = s.iloc[0]
        if isinstance(v, dict) and ("value" in v or "unit" in v):
            df[f"{col}_value"] = df[col].apply(
                lambda x: x.get("value") if isinstance(x, dict) else None
            )
            df[f"{col}_unit"] = df[col].apply(
                lambda x: x.get("unit") if isinstance(x, dict) else None
            )
            df = df.drop(columns=[col])

    return df


# Loads a metadata collection from MongoDB and flattens quantity fields.
def read_metadata_df(
    uri: str,
    server_api: ServerApi,
    dbName: str,
    collectionName: str,
) -> pd.DataFrame:
    """
    Read a metadata collection from MongoDB into a dataframe.
    Flattens {value, unit} quantity fields into *_value / *_unit columns.
    """
    client = MongoClient(host=uri, server_api=server_api)
    db = client[dbName]
    docs = list(db[collectionName].find())
    client.close()

    if not docs:
        return pd.DataFrame()

    df = pd.DataFrame(docs)
    df = df.drop(columns=["_id"], errors="ignore")
    df = flatten_quantities(df)
    return df


# Computes per-batch summary metrics and status flags from part metadata.
def compute_batch_summary(parts_df: pd.DataFrame, batches_df: pd.DataFrame) -> pd.DataFrame:
    parts = parts_df.copy()
    batches = batches_df.copy()

    if "BatchID" not in parts.columns or "PartID" not in parts.columns:
        return pd.DataFrame()

    thickness_col = "PartThickness_value"
    temp_col = "CuringTemperature_value"

    if thickness_col in parts.columns:
        parts[thickness_col] = pd.to_numeric(parts[thickness_col], errors="coerce")
    if temp_col in parts.columns:
        parts[temp_col] = pd.to_numeric(parts[temp_col], errors="coerce")

    agg_dict = {"num_parts": ("PartID", "count")}
    agg_dict["avg_thickness"] = (
        (thickness_col, "mean") if thickness_col in parts.columns
        else ("PartID", lambda s: float("nan"))
    )
    agg_dict["avg_curing_temp"] = (
        (temp_col, "mean") if temp_col in parts.columns
        else ("PartID", lambda s: float("nan"))
    )

    # optional new fields
    if "StrainValue_value" in parts.columns:
        parts["StrainValue_value"] = pd.to_numeric(parts["StrainValue_value"], errors="coerce")
        agg_dict["avg_strain"] = ("StrainValue_value", "mean")

    if "TestDuration_value" in parts.columns:
        parts["TestDuration_value"] = pd.to_numeric(parts["TestDuration_value"], errors="coerce")
        agg_dict["avg_test_duration"] = ("TestDuration_value", "mean")

    summary = parts.groupby("BatchID").agg(**agg_dict).reset_index()

    keep_cols = [c for c in ["BatchID", "PolymerType", "Nanoparticle"] if c in batches.columns]
    if keep_cols:
        summary = summary.merge(batches[keep_cols], on="BatchID", how="left")

    # placeholder thresholds
    summary["thickness_flag"] = (summary["avg_thickness"] < 1.0) | (summary["avg_thickness"] > 4.5)
    summary["temp_flag"] = summary["avg_curing_temp"] > 110.0

    summary["status"] = summary.apply(
        lambda r: "WARNING" if (bool(r["thickness_flag"]) or bool(r["temp_flag"])) else "OK",
        axis=1
    )

    return summary


# Computes top-level dashboard summary values across parts and batches.
def compute_overall_summary(parts_df: pd.DataFrame, batches_df: pd.DataFrame, batch_summary: pd.DataFrame) -> dict:
    out = {
        "total_parts": int(parts_df["PartID"].nunique()) if "PartID" in parts_df.columns else 0,
        "total_batches": int(batches_df["BatchID"].nunique()) if "BatchID" in batches_df.columns else 0,
        "most_common_polymer": "—",
        "avg_thickness_overall": float("nan"),
    }

    if "PolymerType" in batches_df.columns and not batches_df.empty:
        mode_poly = batches_df["PolymerType"].mode(dropna=True)
        if len(mode_poly) > 0:
            out["most_common_polymer"] = str(mode_poly.iloc[0])

    if "PartThickness_value" in parts_df.columns and not parts_df.empty:
        vals = pd.to_numeric(parts_df["PartThickness_value"], errors="coerce")
        out["avg_thickness_overall"] = float(vals.mean())

    return out

# Helper function to translate the selected y metric: Given a metric key, return the corresponding configuration for metadata display
def get_metadata_metric_config(metric_key: str):
    metric_map = {
        "avg_thickness": {
            "source_col": "PartThickness_value",
            "agg": "mean",
            "label": "Average Thickness (mm)",
            "title": "Average Thickness",
        },
        "avg_curing_temp": {
            "source_col": "CuringTemperature_value",
            "agg": "mean",
            "label": "Average Curing Temperature (C)",
            "title": "Average Curing Temperature",
        },
        "avg_test_duration": {
            "source_col": "TestDuration_value",
            "agg": "mean",
            "label": "Average Test Duration (min)",
            "title": "Average Test Duration",
        },
        "avg_strain": {
            "source_col": "StrainValue_value",
            "agg": "mean",
            "label": "Average Strain",
            "title": "Average Strain",
        },
        "count_parts": {
            "source_col": "PartID",
            "agg": "count",
            "label": "Number of Parts",
            "title": "Count of Parts",
        },
    }
    return metric_map.get(metric_key)