import hashlib
import json
import pandas as pd

def stable_row_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def parse_bool(value):
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    mapping = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False}
    return mapping.get(s, None)

def parse_dt(value):
    if pd.isna(value):
        return None
    try:
        # unix seconds or datetime string
        num = pd.to_numeric(value, errors="coerce")
        if pd.notna(num):
            return pd.to_datetime(num, unit="s", errors="coerce").to_pydatetime()
    except Exception:
        pass
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()
