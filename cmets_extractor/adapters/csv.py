from __future__ import annotations

import pandas as pd


def save_to_csv(records, filename="extracted_data.csv"):
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    print(f"\nAlso saved to CSV: {filename}")
    return df


__all__ = ["save_to_csv"]
