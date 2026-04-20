import argparse
import pandas as pd
from app.services.loader import read_csv_any, ensure_cols, TARGET_COLS

TIMESTAMP_COLS = [
    "lead_created_at", "sale_ts", "lead_Дата перехода в Сборку",
    "handed_to_delivery_ts", "lead_Дата перехода Передан в доставку",
    "issued_or_pvz_ts", "received_ts", "rejected_ts", "returned_ts", "closed_ts"
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    df = read_csv_any(args.csv)
    df = ensure_cols(df)

    report_rows = []
    total = len(df)

    for col in TIMESTAMP_COLS:
        nulls = int(df[col].isna().sum()) if col in df.columns else total
        report_rows.append({
            "column": col,
            "null_count": nulls,
            "null_share": round(nulls / total, 4),
            "recommended_action": (
                "exclude_from_terminal_sla_if_unknown"
                if col in {"received_ts", "rejected_ts", "returned_ts", "closed_ts"}
                else "treat_as_not_reached_stage_or_missing_source"
            )
        })

    out = pd.DataFrame(report_rows)
    print(out.to_string(index=False))

    print("\nSpecial flags:")
    for col in ["lifecycle_incomplete", "outcome_unknown"]:
        if col in df.columns:
            print(col, int(df[col].astype(str).str.lower().isin(["true", "1"]).sum()))

if __name__ == "__main__":
    main()
