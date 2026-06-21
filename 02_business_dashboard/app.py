"""Dashboard hasil scoring Customer Churn at Beauti Clinic."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

APP_TITLE = "Customer Churn at Beauti Clinic"

COLUMN_CANDIDATES = {
    "customer_id": ["ID", "ID Customer", "customer_id", "CUSTOMER_ID"],
    "score": ["churn_proba", "Skor Churn", "score_churn"],
    "segment": ["risk_segment", "Segmen Risiko"],
    "rank": ["risk_rank", "Peringkat Risiko"],
    "prediction": ["pred_churn_label", "Prediksi Churn"],
}


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    exact = {str(column).strip(): column for column in df.columns}
    lower = {str(column).strip().lower(): column for column in df.columns}

    for candidate in candidates:
        if candidate in exact:
            return exact[candidate]
        if candidate.lower() in lower:
            return lower[candidate.lower()]

    return None


def load_scoring_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(uploaded_file)
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)

    raise ValueError("Format file harus .xlsx, .xls, atau .csv.")


def infer_segment(scores: pd.Series) -> pd.Series:
    ranked_index = scores.rank(method="first", ascending=False)
    total_rows = len(scores)
    high_limit = max(1, int(np.ceil(total_rows * 0.10)))
    medium_limit = high_limit + max(1, int(np.ceil(total_rows * 0.20)))

    return np.select(
        [ranked_index <= high_limit, ranked_index <= medium_limit],
        ["Risiko Tinggi", "Risiko Sedang"],
        default="Risiko Rendah",
    )


def action_note(segment: str) -> str:
    notes = {
        "Risiko Tinggi": "Cek riwayat kunjungan lalu hubungi customer lebih dulu.",
        "Risiko Sedang": "Masukkan ke daftar follow-up periode ini.",
        "Risiko Rendah": "Pantau pada scoring periode berikutnya.",
    }
    return notes.get(segment, "Cek ulang data customer.")


def prepare_dashboard_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    df = raw_df.copy()
    columns = {
        name: find_column(df, candidates)
        for name, candidates in COLUMN_CANDIDATES.items()
    }

    if columns["score"] is None:
        raise ValueError(
            "Kolom skor churn tidak ditemukan. Gunakan file hasil scoring dari notebook "
            "atau siapkan kolom churn_proba / Skor Churn."
        )

    dashboard = pd.DataFrame(index=df.index)
    if columns["customer_id"] is None:
        dashboard["ID Customer"] = [f"ROW-{index + 1:05d}" for index in range(len(df))]
    else:
        dashboard["ID Customer"] = df[columns["customer_id"]].astype(str)

    dashboard["Skor Churn"] = pd.to_numeric(df[columns["score"]], errors="coerce")
    dashboard = dashboard.dropna(subset=["Skor Churn"]).copy()
    dashboard["Skor Churn"] = dashboard["Skor Churn"].clip(lower=0, upper=1)

    if columns["segment"] is None:
        dashboard["Segmen Risiko"] = infer_segment(dashboard["Skor Churn"])
    else:
        dashboard["Segmen Risiko"] = df.loc[dashboard.index, columns["segment"]].astype(str)

    if columns["rank"] is None:
        dashboard["Peringkat Risiko"] = dashboard["Skor Churn"].rank(
            method="first", ascending=False
        ).astype(int)
    else:
        rank_values = pd.to_numeric(df.loc[dashboard.index, columns["rank"]], errors="coerce")
        dashboard["Peringkat Risiko"] = rank_values.fillna(
            dashboard["Skor Churn"].rank(method="first", ascending=False)
        ).astype(int)

    if columns["prediction"] is None:
        dashboard["Prediksi"] = np.where(
            dashboard["Skor Churn"] >= 0.50,
            "Prediksi Churn",
            "Prediksi Non-Churn",
        )
    else:
        dashboard["Prediksi"] = df.loc[dashboard.index, columns["prediction"]].astype(str)

    for number in range(1, 4):
        driver_column = find_column(
            df,
            [f"driver_{number}_feature", f"Driver {number}", f"driver {number}"],
        )
        if driver_column is not None:
            dashboard[f"Driver {number}"] = df.loc[dashboard.index, driver_column].astype(str)

    dashboard["Tindakan Awal"] = dashboard["Segmen Risiko"].map(action_note)
    dashboard = dashboard.sort_values(
        ["Skor Churn", "Peringkat Risiko"],
        ascending=[False, True],
    ).reset_index(drop=True)

    return dashboard, columns


def dataframe_to_excel(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Prioritas Follow-up")
    return buffer.getvalue()


st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")
st.title(APP_TITLE)
st.caption("Dashboard internal untuk membaca hasil scoring customer aktif.")

with st.sidebar:
    st.header("File input")
    uploaded_file = st.file_uploader(
        "Unggah hasil scoring (.xlsx, .xls, atau .csv)",
        type=["xlsx", "xls", "csv"],
    )
    st.caption("Gunakan file Scoring_Customer_Aktif_Lengkap.xlsx dari notebook.")

if uploaded_file is None:
    st.info("Unggah file hasil scoring untuk menampilkan daftar follow-up customer.")
    st.stop()

try:
    raw_scoring = load_scoring_file(uploaded_file)
    dashboard_df, matched_columns = prepare_dashboard_data(raw_scoring)
except Exception as error:
    st.error(f"File belum bisa dibaca: {error}")
    st.stop()

if dashboard_df.empty:
    st.warning("Tidak ada skor churn yang dapat dipakai dari file ini.")
    st.stop()

high_risk_count = int(
    (dashboard_df["Segmen Risiko"] == "Risiko Tinggi").sum()
)

prediksi_text = (
    dashboard_df["Prediksi"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

predicted_churn_mask = (
    prediksi_text.str.contains("churn", na=False)
    & ~prediksi_text.str.contains("non", na=False)
)

predicted_churn_count = int(predicted_churn_mask.sum())

metric_a, metric_b, metric_c, metric_d = st.columns(4)
metric_a.metric("Customer diproses", f"{len(dashboard_df):,}".replace(",", "."))
metric_b.metric("Risiko tinggi", f"{high_risk_count:,}".replace(",", "."))
metric_c.metric("Prediksi churn", f"{predicted_churn_count:,}".replace(",", "."))
metric_d.metric("Rata-rata skor", f"{dashboard_df['Skor Churn'].mean():.2%}")

st.subheader("Jumlah customer per segmen")
segment_counts = (
    dashboard_df["Segmen Risiko"]
    .value_counts()
    .reindex(["Risiko Tinggi", "Risiko Sedang", "Risiko Rendah"], fill_value=0)
)
st.bar_chart(segment_counts)

st.subheader("Daftar prioritas follow-up")
segment_options = ["Semua"] + [
    segment for segment in ["Risiko Tinggi", "Risiko Sedang", "Risiko Rendah"]
    if segment in set(dashboard_df["Segmen Risiko"])
]
selected_segment = st.selectbox("Filter segmen", segment_options)

shown_df = dashboard_df.copy()
if selected_segment != "Semua":
    shown_df = shown_df[shown_df["Segmen Risiko"] == selected_segment].copy()

st.dataframe(shown_df, use_container_width=True, hide_index=True)

st.download_button(
    label="Unduh daftar follow-up (.xlsx)",
    data=dataframe_to_excel(shown_df),
    file_name="Prioritas_Follow_Up_Beauti_Clinic.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("Kolom yang terbaca dari file"):
    st.json(matched_columns)
