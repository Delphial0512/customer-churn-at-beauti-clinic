"""Pipeline Customer Churn at Beauti Clinic.

Jalankan dari folder proyek:
    python src/customer_churn_pipeline.py

Simpan tiga file input dalam data/raw atau atur PATH_TRX, PATH_SURVEY,
dan PATH_PATIENT sebelum menjalankan file ini.
"""

from __future__ import annotations

import os

# Script tidak perlu membuka jendela grafik. Gambar tree XGBoost nonaktif secara default agar proses lokal tidak berat.
os.environ.setdefault("SHOW_PLOTS", "0")
os.environ.setdefault("GENERATE_TREE_PLOT", "0")
os.environ.setdefault("GENERATE_SHAP_PLOTS", "0")

# =========================================================
# BLOK 1 - KONFIGURASI PROYEK
# =========================================================

# ---------------------------------------------------------
# 1.1 PENGATURAN UMUM
# ---------------------------------------------------------
from pathlib import Path
import os
import sys

PROJECT_NAME = "Customer Churn at Beauti Clinic"
RANDOM_SEED = 42
N_JOBS = max(1, int(os.getenv("N_JOBS", "1")))


def env_flag(name: str, default: bool) -> bool:
    """Membaca nilai boolean dari environment variable."""
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "y"}


SAVE_OUTPUT = env_flag("SAVE_OUTPUT", True)
SHOW_AUDIT_TABLES = env_flag("SHOW_AUDIT_TABLES", True)
SHOW_PLOTS = env_flag("SHOW_PLOTS", True)
USE_COMPACT_CURRENCY_FORMAT = True


# ---------------------------------------------------------
# 1.2 PATH PROYEK, DATA, DAN OUTPUT
# ---------------------------------------------------------
def find_project_root(start_dir: Path) -> Path:
    """Mencari folder repository saat kode dijalankan di laptop."""
    for candidate in [start_dir, *start_dir.parents]:
        if (candidate / "requirements.txt").exists() and (candidate / ".gitignore").exists():
            return candidate

    return start_dir


IS_COLAB = "google.colab" in sys.modules
GENERATE_TREE_PLOT = env_flag("GENERATE_TREE_PLOT", True)
GENERATE_SHAP_PLOTS = env_flag("GENERATE_SHAP_PLOTS", True)
RUNTIME_DIR = (
    Path(__file__).resolve().parents[1]
    if "__file__" in globals()
    else Path.cwd().resolve()
)
DEFAULT_PROJECT_ROOT = Path("/content") if IS_COLAB else find_project_root(RUNTIME_DIR)
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", str(DEFAULT_PROJECT_ROOT))).resolve()

# File yang diunggah lewat panel Files Colab berada di /content.
# Pada laptop, simpan file input di data/raw dalam folder proyek.
DEFAULT_DATA_DIR = (
    Path("/content")
    if IS_COLAB
    else PROJECT_ROOT / "data" / "raw"
)

DATA_DIR = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
OUTPUT_ROOT = Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))

PATH_TRX = Path(os.getenv("PATH_TRX", str(DATA_DIR / "TRANSAKSI.xlsx")))
PATH_SURVEY = Path(os.getenv("PATH_SURVEY", str(DATA_DIR / "SURVEY.xlsx")))
PATH_PATIENT = Path(os.getenv("PATH_PATIENT", str(DATA_DIR / "PATIENT.xlsx")))

OUTPUT_TABLE_DIR = OUTPUT_ROOT / "tabel"
OUTPUT_FIG_DIR = OUTPUT_ROOT / "gambar"
OUTPUT_DATASET_DIR = OUTPUT_ROOT / "dataset"
OUTPUT_SCORING_DIR = OUTPUT_ROOT / "scoring"
OUTPUT_LOG_DIR = OUTPUT_ROOT / "log"


# ---------------------------------------------------------
# 1.4 PARAMETER WINDOW DAN COHORT
# ---------------------------------------------------------
# Draft memakai observasi 6 bulan, prediksi 3 bulan, slide 3 bulan.
OBS_MONTH = 6
PRED_MONTH = 3
SLIDE_MONTH = 3

LIFETIME_MIN_VISIT_DAYS = 2
MIN_TRX_OBS = 1
MIN_CUSTOMER_PER_WINDOW = 50

WINDOW_AUDIT_CONFIGS = [
    (3, 3, 3),
    (6, 3, 3),
    (9, 3, 3),
    (12, 3, 3),
]

PRED_HORIZON_DAYS = [30, 60, 90, 120, 180]


# ---------------------------------------------------------
# 1.5 PARAMETER SENTIMEN
# ---------------------------------------------------------
SENTIMENT_DEFAULT_SCORE = 0
SENTIMENT_EMPTY_LABEL = "empty"
SENTIMENT_UNCERTAIN_LABEL = "uncertain"
SENTIMENT_MANUAL_LABEL = "manual"


# ---------------------------------------------------------
# 1.6 PARAMETER MODELING
# ---------------------------------------------------------
# True  : tuning ulang memakai Optuna.
# False : memakai hyperparameter hasil draft.
USE_OPTUNA_TUNING = False

N_ESTIMATORS_CAP = int(os.getenv("N_ESTIMATORS_CAP", "5000"))
EARLY_STOPPING_ROUNDS = int(os.getenv("EARLY_STOPPING_ROUNDS", "100"))
N_OPTUNA_TRIALS = int(os.getenv("N_OPTUNA_TRIALS", "150"))
OPTUNA_TIMEOUT = (
    int(os.environ["OPTUNA_TIMEOUT"])
    if os.getenv("OPTUNA_TIMEOUT")
    else None
)

MIN_TRAIN_END = 4
THRESHOLD_SELECTION_METHOD = "balanced_accuracy"

# Threshold draft digunakan bila THRESHOLD_SELECTION_METHOD = "draft".
DRAFT_FINAL_THRESHOLD = 0.80

# Segmentasi scoring: 10% risiko tinggi, 20% berikutnya risiko sedang.
HIGH_RISK_TOP_PCT = 0.10
MEDIUM_RISK_NEXT_PCT = 0.20

# Search space mengikuti Tabel 4.8.
XGB_SEARCH_SPACE = {
    "max_depth": (2, 8),
    "learning_rate": (0.005, 0.2),
    "subsample": (0.5, 1.0),
    "colsample_bytree": (0.5, 1.0),
    "min_child_weight": (1, 30),
    "gamma": (0.0, 10.0),
    "reg_alpha": (0.0, 10.0),
    "reg_lambda": (0.1, 20.0),
    "scale_pos_weight": (0.1229, 0.4915),
}

# Hyperparameter hasil draft.
# Dipakai saat USE_OPTUNA_TUNING = False.
DRAFT_BEST_XGB_PARAMS = {
    "max_depth": 2,
    "learning_rate": 0.12,
    "subsample": 0.86,
    "colsample_bytree": 0.79,
    "min_child_weight": 25.15,
    "gamma": 0.74,
    "reg_alpha": 4.75,
    "reg_lambda": 0.40,
    "scale_pos_weight": 0.48,
}

DRAFT_BEST_N_ESTIMATORS = int(os.getenv("DRAFT_BEST_N_ESTIMATORS", "54"))


# ---------------------------------------------------------
# 1.7 PARAMETER OUTPUT
# ---------------------------------------------------------
DISPLAY_DECIMAL_GENERAL = 2
DISPLAY_DECIMAL_METRIC = 4
MAX_DISPLAY_ROWS = 20


# ---------------------------------------------------------
# 1.8 NAMA KOLOM INPUT
# ---------------------------------------------------------
# Kolom input mengikuti file mentah.
COL_ID = "ID"
COL_DATE_TRX = "TX_DATE"
COL_TOTAL = "TOTAL"
COL_DISC = "DISCOUNT_RP"
COL_QTY_RAW = "JLH"
COL_FEEDBACK = "FEEDBACK_TEXT"

# Kolom mentah bisa berbeda kapitalisasinya.
# Nanti dibakukan menjadi fitur final: age dan gender_code.
COL_AGE_RAW = "AGE"
COL_GENDER_RAW = "GENDER"

ASPECT_COLS = [
    "ASPECT_FRONTLINER",
    "ASPECT_DOCTOR",
    "ASPECT_NURSE_BEAUTICIAN",
    "ASPECT_PHARMACY",
    "ASPECT_FACILITY",
]


# ---------------------------------------------------------
# 1.9 NAMA KOLOM TURUNAN INTERNAL
# ---------------------------------------------------------
COL_QTY = "JUMLAH"

COL_AGE = "age"
COL_GENDER_CODE = "gender_code"

FEATURE_COLS = [
    "frequency",
    "monetary",
    "recency_m",
    "tenure_m",
    "promo_ratio",
    "promo_usage_rate",
    "satisfaction_mean",
    "sentiment_mean",
    "age",
    "gender_code",
]

PRED_FREQ_COL = "frequency_pred"
PRED_PROBA_COL = "churn_proba"
PRED_LABEL_COL = "pred_churn_label"


# ---------------------------------------------------------
# 1.10 NAMA TAMPILAN, LABEL, DAN DESKRIPSI
# ---------------------------------------------------------
# Nama fitur pada tabel/gambar tetap snake_case agar sama dengan draft dan SHAP.
DISPLAY_NAME_MAP = {
    "ID": "ID Customer",
    "slice_number": "Slice",
    "slice": "Slice",
    "is_labeled": "Status Data",
    "data_role": "Status Data",
    "obs_start": "Awal Observasi",
    "obs_end": "Akhir Observasi",
    "pred_start": "Awal Prediksi",
    "pred_end": "Akhir Prediksi",

    "frequency": "frequency",
    "monetary": "monetary",
    "recency_m": "recency_m",
    "tenure_m": "tenure_m",
    "promo_ratio": "promo_ratio",
    "promo_usage_rate": "promo_usage_rate",
    "satisfaction_mean": "satisfaction_mean",
    "sentiment_mean": "sentiment_mean",
    "age": "age",
    "gender_code": "gender_code",

    "frequency_pred": "frequency_pred",
    "monetary_pred": "monetary_pred",
    "churn": "churn",
    "churn_proba": "Skor Churn",
    "risk_rank": "Peringkat Risiko",
    "risk_segment": "Segmen Risiko",
    "pred_churn_label": "Prediksi Churn",
    "used_threshold": "Threshold",
    "n_customers": "Jumlah Customer",
    "count": "Jumlah",
    "missing_count": "Jumlah Missing",
    "missing_pct": "Persentase Missing",
}

# Deskripsi dipakai untuk Tabel 4.12 dan driver scoring.
# Ini bukan input model.
FEATURE_DESCRIPTION_MAP = {
    "frequency": "Frekuensi kunjungan",
    "monetary": "Total nilai transaksi",
    "recency_m": "Jarak waktu sejak kunjungan terakhir",
    "tenure_m": "Lama hubungan customer dengan klinik",
    "promo_ratio": "Rasio diskon terhadap belanja",
    "promo_usage_rate": "Rasio penggunaan promo",
    "satisfaction_mean": "Rata-rata kepuasan",
    "sentiment_mean": "Rata-rata sentimen",
    "age": "Umur",
    "gender_code": "Jenis kelamin",
}

GENDER_LABEL_MAP = {
    1: "Perempuan",
    2: "Laki-laki",
    3: "Tidak Diketahui",
}

CHURN_LABEL_MAP = {
    0: "Non-Churn",
    1: "Churn",
}

PRED_CHURN_LABEL_MAP = {
    0: "Prediksi Non-Churn",
    1: "Prediksi Churn",
}

RISK_SEGMENT_SHORT_MAP = {
    "Risiko Tinggi": "Tinggi",
    "Risiko Sedang": "Sedang",
    "Risiko Rendah": "Rendah",
}


# ---------------------------------------------------------
# 1.11 PENAMAAN FILE TABEL
# ---------------------------------------------------------
TABLE_FILE_MAP = {
    "table_4_1": "Tabel_4_1_Jumlah_Data_per_Sumber",
    "table_4_2": "Tabel_4_2_Duplikasi_Transaksi_Harian",
    "table_4_3": "Tabel_4_3_Missing_Value_Data_Mentah",
    "table_4_4": "Tabel_4_4_Coverage_Dataset_Final",
    "table_4_5": "Tabel_4_5_Evaluasi_Konfigurasi_Periode",
    "table_4_6": "Tabel_4_6_Statistik_Deskriptif_Fitur_Final",
    "table_4_7": "Tabel_4_7_Skema_Walk_Forward_Validation",
    "table_4_8": "Tabel_4_8_Search_Space_Hyperparameter_XGBoost",
    "table_4_9": "Tabel_4_9_Best_Hyperparameter_XGBoost",
    "table_4_10": "Tabel_4_10_Perbandingan_Performa_Sebelum_dan_Sesudah_Tuning",
    "table_4_11": "Tabel_4_11_Evaluasi_Threshold_pada_Data_Testing",
    "table_4_12": "Tabel_4_12_Mean_Absolute_Fitur",
    "table_4_13": "Tabel_4_13_Ringkasan_Hasil_Scoring",
    "table_4_14": "Tabel_4_14_Segmentasi_Risiko_Customer_Berdasarkan_Skor_Churn",
    "table_4_15": "Tabel_4_15_Contoh_Customer_pada_Segmen_Risiko_Churn_Tinggi",
}


# ---------------------------------------------------------
# 1.12 PENAMAAN FILE GAMBAR
# ---------------------------------------------------------
FIG_FILE_MAP = {
    "fig_4_1":  "Gambar_4_1_Distribusi_Cohort_Customer",
    "fig_4_2":  "Gambar_4_2_Distribusi_Missing_Value_pada_Fitur_Final",
    "fig_4_3":  "Gambar_4_3_Struktur_Periode",
    "fig_4_4":  "Gambar_4_4_ECDF_Gap_Antar_Kunjungan_Customer",
    "fig_4_5":  "Gambar_4_5_Boxplot_Fitur_Utama",
    "fig_4_6":  "Gambar_4_6_Heatmap_Korelasi_Fitur",
    "fig_4_7":  "Gambar_4_7_Distribusi_Churn_dan_Non_Churn",
    "fig_4_8":  "Gambar_4_8_Churn_Rate_per_Slice",
    "fig_4_9":  "Gambar_4_9_Perbandingan_Churn_Rate_Training_Validation_dan_Testing",
    "fig_4_10": "Gambar_4_10_Diagram_Walk_Forward_Validation",
    "fig_4_11": "Gambar_4_11_Optuna_Optimization_History",
    "fig_4_12": "Gambar_4_12_XGBoost_Tree_Iterasi_Awal_Tengah_dan_Akhir",
    "fig_4_13": "Gambar_4_13_ROC_Curve_pada_Data_Testing",
    "fig_4_14": "Gambar_4_14_Confusion_Matrix_pada_Threshold_Final",
    "fig_4_15": "Gambar_4_15_SHAP_Importance_Plot",
    "fig_4_16": "Gambar_4_16_SHAP_Summary_Plot",
    "fig_4_17": "Gambar_4_17_SHAP_Local_Waterfall_Plot",
    "fig_4_18": "Gambar_4_18_SHAP_Local_Force_Plot",
    "fig_4_19": "Gambar_4_19_Histogram_Skor_Churn_pada_Data_Scoring",
    "fig_4_20": "Gambar_4_20_Jumlah_Customer_per_Segmen_Risiko",
}


# ---------------------------------------------------------
# 1.13 VALIDASI KONFIGURASI
# ---------------------------------------------------------
missing_feature_desc = [
    col for col in FEATURE_COLS
    if col not in FEATURE_DESCRIPTION_MAP
]

missing_display_name = [
    col for col in FEATURE_COLS
    if col not in DISPLAY_NAME_MAP
]

if len(missing_feature_desc) > 0:
    raise ValueError(f"Fitur belum ada di FEATURE_DESCRIPTION_MAP: {missing_feature_desc}")

if len(missing_display_name) > 0:
    raise ValueError(f"Fitur belum ada di DISPLAY_NAME_MAP: {missing_display_name}")

if HIGH_RISK_TOP_PCT + MEDIUM_RISK_NEXT_PCT >= 1:
    raise ValueError("Total persentase risiko tinggi dan sedang harus kurang dari 1.")


# ---------------------------------------------------------
# 1.14 RINGKASAN PARAMETER AKTIF
# ---------------------------------------------------------
print("=" * 70)
print("BLOK 1 - KONFIGURASI PROYEK")
print("=" * 70)
print(f"Project                : {PROJECT_NAME}")
print(f"Mode runtime           : {'Google Colab' if IS_COLAB else 'Laptop / local'}")
print(f"Folder data            : {DATA_DIR}")
print(f"File transaksi         : {PATH_TRX}")
print(f"File survei            : {PATH_SURVEY}")
print(f"File demografi         : {PATH_PATIENT}")
print(f"Folder output          : {OUTPUT_ROOT}")
print(f"Random seed            : {RANDOM_SEED}")
print(f"N jobs                 : {N_JOBS}")
print(f"Observation window     : {OBS_MONTH} bulan")
print(f"Prediction window      : {PRED_MONTH} bulan")
print(f"Slide window           : {SLIDE_MONTH} bulan")
print(f"Label churn            : {PRED_FREQ_COL} = 0")
print(f"Sentimen final         : rule-based/context lexicon")
print(f"Optuna tuning          : {USE_OPTUNA_TUNING}")
print(f"Optuna trials          : {N_OPTUNA_TRIALS}")
print(f"N estimators cap       : {N_ESTIMATORS_CAP}")
print(f"Early stopping rounds  : {EARLY_STOPPING_ROUNDS}")
print(f"Threshold selection    : {THRESHOLD_SELECTION_METHOD}")
print(f"Threshold draft        : {DRAFT_FINAL_THRESHOLD}")
print(f"Segmentasi risiko      : top {int(HIGH_RISK_TOP_PCT * 100)}% tinggi, {int(MEDIUM_RISK_NEXT_PCT * 100)}% berikutnya sedang")
print(f"Jumlah fitur           : {len(FEATURE_COLS)}")
print("Gambar 1.1 dan 1.2     : berasal dari draft, tidak dibuat notebook")
print("=" * 70)


# =========================================================
# BLOK 2 - IMPORT LIBRARY DAN FUNGSI UMUM
# =========================================================

# ---------------------------------------------------------
# 2.1 IMPORT LIBRARY DASAR
# ---------------------------------------------------------
import json
import random
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display
from pandas.tseries.offsets import DateOffset


# ---------------------------------------------------------
# 2.2 IMPORT LIBRARY MODELING
# ---------------------------------------------------------
import xgboost as xgb
import optuna
import shap

from optuna.samplers import TPESampler

from sklearn.metrics import (
    roc_auc_score,
    roc_curve,
    auc,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    balanced_accuracy_score,
    average_precision_score,
    brier_score_loss,
)

optuna.logging.set_verbosity(optuna.logging.WARNING)


# ---------------------------------------------------------
# 2.3 FONT UNTUK GRAFIK
# ---------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})


# ---------------------------------------------------------
# 2.4 RANDOM SEED
# ---------------------------------------------------------
os.environ["PYTHONHASHSEED"] = str(RANDOM_SEED)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ---------------------------------------------------------
# 2.5 FOLDER OUTPUT
# ---------------------------------------------------------
def ensure_directories(paths: List[str]) -> None:
    for path in paths:
        os.makedirs(path, exist_ok=True)


ensure_directories([
    OUTPUT_ROOT,
    OUTPUT_TABLE_DIR,
    OUTPUT_FIG_DIR,
    OUTPUT_DATASET_DIR,
    OUTPUT_SCORING_DIR,
    OUTPUT_LOG_DIR,
])

print("=" * 70)
print("FOLDER OUTPUT SIAP")
print("=" * 70)


# ---------------------------------------------------------
# 2.6 FUNGSI CLEANING DASAR
# ---------------------------------------------------------
def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = out.columns.astype(str).str.strip()
    return out


def standardize_id(series: pd.Series, width: int = 7) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.replace({
        "nan": "",
        "NaN": "",
        "None": "",
        "NONE": "",
        "<NA>": "",
        "": "",
    })
    s = s.apply(lambda x: x.zfill(width) if x != "" else np.nan)
    return s


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def encode_gender(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({
        "NAN": "U",
        "NONE": "U",
        "<NA>": "U",
        "": "U",
    })

    gender_map = {
        "P": 1,
        "F": 1,
        "PEREMPUAN": 1,
        "WANITA": 1,
        "L": 2,
        "M": 2,
        "LAKI-LAKI": 2,
        "LAKI LAKI": 2,
        "PRIA": 2,
        "U": 3,
        "UNKNOWN": 3,
        "OTHER": 3,
        "TIDAK DIKETAHUI": 3,
        "TIDAK MENGISI": 3,
    }

    return s.map(gender_map).fillna(3).astype(int)


def check_required_columns(
    df: pd.DataFrame,
    required_cols: List[str],
    df_name: str,
) -> None:
    missing_cols = [col for col in required_cols if col not in df.columns]

    if len(missing_cols) == 0:
        print(f"[OK] {df_name}: semua kolom wajib tersedia")
    else:
        raise ValueError(f"{df_name}: kolom wajib belum ditemukan -> {missing_cols}")


def check_file_exists(path: Path | str, label: str) -> None:
    input_path = Path(path)

    if input_path.exists():
        print(f"[OK] {label}: {input_path}")
    else:
        print(f"[BELUM ADA] {label}: {input_path}")


def check_all_input_files() -> None:
    print("Pemeriksaan file input:")
    check_file_exists(PATH_TRX, "Data transaksi")
    check_file_exists(PATH_SURVEY, "Data survei")
    check_file_exists(PATH_PATIENT, "Data demografi")


# ---------------------------------------------------------
# 2.7 FUNGSI MISSING VALUE
# ---------------------------------------------------------
def build_missing_table(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    columns = [
        "Sumber Data",
        "Variabel",
        "Jumlah Missing",
        "Persentase Missing",
    ]

    if len(df) == 0:
        return pd.DataFrame(columns=columns)

    miss = df.isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)

    if len(miss) == 0:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame({
        "Sumber Data": dataset_name,
        "Variabel": miss.index,
        "Jumlah Missing": miss.values,
        "Persentase Missing": (miss.values / len(df) * 100).round(4),
    })


# ---------------------------------------------------------
# 2.8 FORMAT ANGKA
# ---------------------------------------------------------
def _fmt_comma(value, decimals: int) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_decimal(x, decimals: int = DISPLAY_DECIMAL_GENERAL) -> str:
    if pd.isna(x):
        return "-"
    return _fmt_comma(float(x), decimals)


def format_metric(x, decimals: int = DISPLAY_DECIMAL_METRIC) -> str:
    if pd.isna(x):
        return "-"
    return f"{float(x):.{decimals}f}".replace(".", ",")


def format_percent(x, decimals: int = DISPLAY_DECIMAL_GENERAL) -> str:
    if pd.isna(x):
        return "-"
    return f"{float(x):.{decimals}f}%".replace(".", ",")


def format_int(x) -> str:
    if pd.isna(x):
        return "-"
    return f"{int(round(float(x))):,}".replace(",", ".")


def format_compact_number(x, decimals: int = DISPLAY_DECIMAL_GENERAL) -> str:
    if pd.isna(x):
        return "-"

    x = float(x)
    abs_x = abs(x)

    if abs_x >= 1_000_000_000:
        return format_decimal(x / 1_000_000_000, decimals) + " miliar"
    if abs_x >= 1_000_000:
        return format_decimal(x / 1_000_000, decimals) + " juta"
    if abs_x >= 1_000:
        return format_decimal(x / 1_000, decimals) + " ribu"

    return format_decimal(x, decimals)


# ---------------------------------------------------------
# 2.9 RENAME DAN LABEL OUTPUT
# ---------------------------------------------------------
def rename_output_columns(
    df: pd.DataFrame,
    name_map: Optional[Dict] = None,
) -> pd.DataFrame:
    if name_map is None:
        name_map = DISPLAY_NAME_MAP

    out = df.copy()
    selected_map = {k: v for k, v in name_map.items() if k in out.columns}
    return out.rename(columns=selected_map)


def apply_label_mapping(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "gender_code" in out.columns:
        out["gender_code"] = out["gender_code"].map(GENDER_LABEL_MAP).fillna(out["gender_code"])

    if "churn" in out.columns:
        out["churn"] = out["churn"].map(CHURN_LABEL_MAP).fillna(out["churn"])

    if "pred_churn_label" in out.columns:
        out["pred_churn_label"] = (
            out["pred_churn_label"]
            .map(PRED_CHURN_LABEL_MAP)
            .fillna(out["pred_churn_label"])
        )

    return out


def prepare_display_table(
    df: pd.DataFrame,
    rename_cols: bool = True,
    apply_labels: bool = True,
) -> pd.DataFrame:
    out = df.copy()

    if apply_labels:
        out = apply_label_mapping(out)

    if rename_cols:
        out = rename_output_columns(out)

    return out


# ---------------------------------------------------------
# 2.10 EXPORT TABEL DAN GAMBAR
# ---------------------------------------------------------
def _is_registered_output_key(
    file_key: str,
    file_map: Dict[str, str],
    output_type: str,
) -> bool:
    if file_key in file_map:
        return True

    print(f"[SKIP] {output_type} '{file_key}' tidak ada pada daftar output draft.")
    return False


def save_table(
    df: pd.DataFrame,
    file_key: str,
    rename_cols: bool = False,
    apply_labels: bool = False,
    allow_unlisted: bool = False,
) -> None:
    if not SAVE_OUTPUT:
        return

    if not allow_unlisted and not _is_registered_output_key(file_key, TABLE_FILE_MAP, "Tabel"):
        return

    file_name = TABLE_FILE_MAP.get(file_key, file_key)

    out = df.copy()
    if apply_labels:
        out = apply_label_mapping(out)
    if rename_cols:
        out = rename_output_columns(out)

    out.to_excel(f"{OUTPUT_TABLE_DIR}/{file_name}.xlsx", index=False)
    out.to_csv(f"{OUTPUT_TABLE_DIR}/{file_name}.csv", index=False, encoding="utf-8-sig")


def save_figure(
    fig: plt.Figure,
    file_key: str,
    dpi: int = 200,
    allow_unlisted: bool = False,
) -> None:
    if not SAVE_OUTPUT:
        return

    if not allow_unlisted and not _is_registered_output_key(file_key, FIG_FILE_MAP, "Gambar"):
        return

    file_name = FIG_FILE_MAP.get(file_key, file_key)
    fig.savefig(f"{OUTPUT_FIG_DIR}/{file_name}.png", dpi=dpi, bbox_inches="tight")


def finalize_plot(
    fig: plt.Figure,
    file_key: Optional[str] = None,
    show: bool = True,
    allow_unlisted: bool = False,
) -> None:
    plt.tight_layout()

    if file_key is not None:
        save_figure(fig, file_key=file_key, allow_unlisted=allow_unlisted)

    if show and SHOW_PLOTS:
        plt.show()

    plt.close(fig)


def print_chart_title(title: str) -> None:
    print(f"\n{title}")


# ---------------------------------------------------------
# 2.11 LABEL ANGKA PADA BAR CHART
# ---------------------------------------------------------
def add_value_labels_to_bars(ax, fmt: str = "int") -> None:
    for p in ax.patches:
        height = p.get_height()

        if pd.isna(height):
            continue

        if fmt == "percent":
            label = format_percent(height)
        elif fmt == "decimal":
            label = format_decimal(height)
        else:
            label = format_int(height)

        ax.annotate(
            label,
            (p.get_x() + p.get_width() / 2, height),
            ha="center",
            va="bottom",
            fontsize=9,
            xytext=(0, 3),
            textcoords="offset points",
        )


def add_value_labels_to_horizontal_bars(ax, fmt: str = "int") -> None:
    for p in ax.patches:
        width = p.get_width()

        if pd.isna(width):
            continue

        if fmt == "percent":
            label = format_percent(width)
        elif fmt == "decimal":
            label = format_decimal(width)
        else:
            label = format_int(width)

        ax.annotate(
            label,
            (width, p.get_y() + p.get_height() / 2),
            ha="left",
            va="center",
            fontsize=9,
            xytext=(4, 0),
            textcoords="offset points",
        )


# ---------------------------------------------------------
# 2.12 ECDF PLOT
# ---------------------------------------------------------
def plot_ecdf(values, xlabel: str, file_key: str) -> None:
    v = np.asarray(values)
    v = v[np.isfinite(v)]
    v = np.sort(v)

    if len(v) == 0:
        print("Data ECDF kosong.")
        return

    y = np.arange(1, len(v) + 1) / len(v)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(v, y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Empirical CDF")
    ax.grid(alpha=0.3)

    finalize_plot(fig, file_key=file_key, show=True)


# ---------------------------------------------------------
# 2.13 WINDOWING
# ---------------------------------------------------------
def generate_window_calendar(
    start_date,
    max_date,
    obs_m,
    pred_m,
    slide_m,
    include_scoring: bool = True,
) -> pd.DataFrame:
    rows = []
    s = pd.Timestamp(start_date)
    slice_number = 1

    while True:
        obs_start = s
        obs_end = obs_start + DateOffset(months=obs_m) - DateOffset(days=1)
        pred_start = obs_end + DateOffset(days=1)
        pred_end = pred_start + DateOffset(months=pred_m) - DateOffset(days=1)

        if obs_end > max_date:
            break

        is_labeled = pred_end <= max_date

        rows.append({
            "slice_number": slice_number,
            "obs_start": obs_start,
            "obs_end": obs_end,
            "pred_start": pred_start,
            "pred_end": pred_end,
            "is_labeled": is_labeled,
            "data_role": "labeled" if is_labeled else "scoring",
        })

        if not is_labeled:
            break

        s += DateOffset(months=slide_m)
        slice_number += 1

    cal = pd.DataFrame(rows)

    if not include_scoring and len(cal) > 0:
        cal = cal[cal["is_labeled"]].copy()

    return cal.reset_index(drop=True)


def overlap_jaccard(set_a: set, set_b: set) -> float:
    if len(set_a) == 0 and len(set_b) == 0:
        return 1.0
    if len(set_a) == 0 or len(set_b) == 0:
        return 0.0

    return len(set_a & set_b) / len(set_a | set_b)


# ---------------------------------------------------------
# 2.14 EVALUASI MODEL
# ---------------------------------------------------------
def safe_roc_auc(y_true, y_proba) -> float:
    y_true_arr = np.asarray(y_true)
    y_proba_arr = np.asarray(y_proba)

    if len(np.unique(y_true_arr)) < 2:
        return np.nan

    return roc_auc_score(y_true_arr, y_proba_arr)


def calculate_binary_metrics(y_true, y_proba, threshold: float) -> dict:
    y_true_arr = np.asarray(y_true)
    y_proba_arr = np.asarray(y_proba)
    y_pred = (y_proba_arr >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true_arr,
        y_pred,
        labels=[0, 1],
    ).ravel()

    precision = precision_score(y_true_arr, y_pred, zero_division=0)
    recall = recall_score(y_true_arr, y_pred, zero_division=0)
    f1 = f1_score(y_true_arr, y_pred, zero_division=0)

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    balanced_acc = balanced_accuracy_score(y_true_arr, y_pred)
    youden_j = recall + specificity - 1

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0

    return {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1_score": f1,
        "balanced_accuracy": balanced_acc,
        "youden_j": youden_j,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def build_threshold_table(y_true, y_proba, thresholds=None) -> pd.DataFrame:
    if thresholds is None:
        thresholds = np.linspace(0.01, 0.99, 99)

    rows = [
        calculate_binary_metrics(y_true, y_proba, float(t))
        for t in thresholds
    ]

    return pd.DataFrame(rows)


def select_threshold(threshold_table: pd.DataFrame, method: str) -> float:
    if method == "balanced_accuracy":
        idx = threshold_table["balanced_accuracy"].idxmax()
    elif method == "f1":
        idx = threshold_table["f1_score"].idxmax()
    elif method == "youden_j":
        idx = threshold_table["youden_j"].idxmax()
    elif method == "draft":
        return float(DRAFT_FINAL_THRESHOLD)
    else:
        raise ValueError(f"Metode threshold belum dikenali: {method}")

    return float(threshold_table.loc[idx, "threshold"])


# ---------------------------------------------------------
# 2.15 PARAMETER XGBOOST
# ---------------------------------------------------------

# ---------------------------------------------------------
# 2.16 SCORING DAN SEGMENTASI RISIKO
# ---------------------------------------------------------
def assign_risk_segment(
    df: pd.DataFrame,
    score_col: str = PRED_PROBA_COL,
    high_pct: float = HIGH_RISK_TOP_PCT,
    medium_next_pct: float = MEDIUM_RISK_NEXT_PCT,
) -> pd.DataFrame:
    out = df.copy().sort_values(score_col, ascending=False).reset_index(drop=True)

    n = len(out)
    high_n = int(np.ceil(n * high_pct))
    medium_n = int(np.ceil(n * medium_next_pct))

    out["risk_rank"] = np.arange(1, n + 1)
    out["risk_segment"] = "Risiko Rendah"

    if n > 0:
        out.loc[:high_n - 1, "risk_segment"] = "Risiko Tinggi"
        out.loc[high_n:high_n + medium_n - 1, "risk_segment"] = "Risiko Sedang"

    return out


print("=" * 70)
print("BLOK 2 - LIBRARY DAN FUNGSI UMUM SIAP")
print("=" * 70)


# =========================================================
# BLOK 3 - LOAD DATA
# =========================================================

print("=" * 70)
print("BLOK 3 - LOAD DATA")
print("=" * 70)

check_all_input_files()


# ---------------------------------------------------------
# 3.1 FUNGSI BACA FILE INPUT
# ---------------------------------------------------------
def read_input_file(path: Path | str) -> pd.DataFrame:
    input_path = Path(path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File input tidak ditemukan: {input_path}. "
            "Simpan file di data/raw atau atur PATH_TRX, PATH_SURVEY, dan PATH_PATIENT."
        )

    suffix = input_path.suffix.lower()

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(input_path)

    if suffix == ".csv":
        try:
            return pd.read_csv(input_path)
        except UnicodeDecodeError:
            return pd.read_csv(input_path, encoding="latin1")

    raise ValueError(f"Format file belum didukung: {input_path}")


# ---------------------------------------------------------
# 3.2 LOAD DATA MENTAH
# ---------------------------------------------------------
df_trx = read_input_file(PATH_TRX)
df_survey = read_input_file(PATH_SURVEY)
df_patient = read_input_file(PATH_PATIENT)

df_trx = standardize_columns(df_trx)
df_survey = standardize_columns(df_survey)
df_patient = standardize_columns(df_patient)

print(f"\nData transaksi : {format_int(len(df_trx))} baris | {df_trx.shape[1]} kolom")
print(f"Data survei    : {format_int(len(df_survey))} baris | {df_survey.shape[1]} kolom")
print(f"Data demografi : {format_int(len(df_patient))} baris | {df_patient.shape[1]} kolom")


# ---------------------------------------------------------
# 3.3 RESOLUSI NAMA KOLOM INPUT
# ---------------------------------------------------------
# Kolom final model tetap lowercase snake_case.
# Bagian ini hanya mencari nama kolom pada data mentah.

def find_existing_column(
    df: pd.DataFrame,
    candidates: List[str],
    required: bool = False,
    label: str = "kolom",
) -> Optional[str]:
    exact_cols = set(df.columns)

    for col in candidates:
        if col in exact_cols:
            return col

    lower_map = {str(col).lower(): col for col in df.columns}
    for col in candidates:
        key = str(col).lower()
        if key in lower_map:
            return lower_map[key]

    if required:
        raise ValueError(f"{label} belum ditemukan. Kandidat: {candidates}")

    return None


COL_ID_TRX = find_existing_column(
    df_trx,
    [COL_ID, "id", "CUSTOMER_ID", "customer_id"],
    required=True,
    label="ID pada data transaksi",
)

COL_DATE_TRX_INPUT = find_existing_column(
    df_trx,
    [COL_DATE_TRX, "tx_date", "TANGGAL", "tanggal", "DATE", "date"],
    required=True,
    label="tanggal transaksi",
)

COL_TOTAL_INPUT = find_existing_column(
    df_trx,
    [COL_TOTAL, "total", "TOTAL_BAYAR", "total_bayar"],
    required=True,
    label="total transaksi",
)

COL_DISC_INPUT = find_existing_column(
    df_trx,
    [COL_DISC, "discount_rp", "DISKON", "diskon", "DISC", "disc"],
    required=False,
    label="diskon transaksi",
)

COL_QTY_INPUT = find_existing_column(
    df_trx,
    [COL_QTY_RAW, COL_QTY, "jlh", "jumlah", "QTY", "qty"],
    required=False,
    label="jumlah item",
)

COL_ID_SURVEY = find_existing_column(
    df_survey,
    [COL_ID, "id", "CUSTOMER_ID", "customer_id"],
    required=True,
    label="ID pada data survei",
)

COL_DATE_SURVEY_INPUT = find_existing_column(
    df_survey,
    [COL_DATE_TRX, "tx_date", "TANGGAL", "tanggal", "DATE", "date"],
    required=True,
    label="tanggal survei",
)

COL_FEEDBACK_INPUT = find_existing_column(
    df_survey,
    [COL_FEEDBACK, "feedback_text", "FEEDBACK", "feedback", "KRITIK_SARAN", "kritik_saran"],
    required=False,
    label="teks feedback",
)

COL_ID_PATIENT = find_existing_column(
    df_patient,
    [COL_ID, "id", "CUSTOMER_ID", "customer_id"],
    required=True,
    label="ID pada data demografi",
)

COL_AGE_INPUT = find_existing_column(
    df_patient,
    [COL_AGE_RAW, COL_AGE, "Age", "AGE", "age", "UMUR", "umur"],
    required=False,
    label="umur",
)

COL_GENDER_INPUT = find_existing_column(
    df_patient,
    [COL_GENDER_RAW, "Gender", "GENDER", "gender", "JK", "jk", "JENIS_KELAMIN", "jenis_kelamin"],
    required=False,
    label="jenis kelamin",
)

COL_DOB_INPUT = find_existing_column(
    df_patient,
    ["DOB", "dob", "DATE_OF_BIRTH", "date_of_birth", "TANGGAL_LAHIR", "tanggal_lahir"],
    required=False,
    label="tanggal lahir",
)


# ---------------------------------------------------------
# 3.4 VALIDASI KOLOM WAJIB
# ---------------------------------------------------------
print("\nValidasi kolom wajib:")
check_required_columns(df_trx, [COL_ID_TRX, COL_DATE_TRX_INPUT, COL_TOTAL_INPUT], "Data transaksi")
check_required_columns(df_survey, [COL_ID_SURVEY, COL_DATE_SURVEY_INPUT], "Data survei")
check_required_columns(df_patient, [COL_ID_PATIENT], "Data demografi")


# ---------------------------------------------------------
# 3.5 AUDIT NAMA KOLOM INPUT
# ---------------------------------------------------------
input_column_map = pd.DataFrame({
    "Sumber Data": [
        "Transaksi",
        "Transaksi",
        "Transaksi",
        "Transaksi",
        "Transaksi",
        "Survei",
        "Survei",
        "Survei",
        "Demografi",
        "Demografi",
        "Demografi",
        "Demografi",
    ],
    "Kebutuhan": [
        "ID customer",
        "Tanggal transaksi",
        "Total transaksi",
        "Diskon",
        "Jumlah item",
        "ID customer",
        "Tanggal survei",
        "Feedback text",
        "ID customer",
        "Umur",
        "Jenis kelamin",
        "Tanggal lahir",
    ],
    "Kolom pada File": [
        COL_ID_TRX,
        COL_DATE_TRX_INPUT,
        COL_TOTAL_INPUT,
        COL_DISC_INPUT,
        COL_QTY_INPUT,
        COL_ID_SURVEY,
        COL_DATE_SURVEY_INPUT,
        COL_FEEDBACK_INPUT,
        COL_ID_PATIENT,
        COL_AGE_INPUT,
        COL_GENDER_INPUT,
        COL_DOB_INPUT,
    ],
})

print("\nAudit nama kolom input")
display(input_column_map)


# ---------------------------------------------------------
# 3.6 TABEL 4.1 - JUMLAH DATA PER SUMBER
# ---------------------------------------------------------
def get_basic_summary(
    df: pd.DataFrame,
    source_name: str,
    id_col: Optional[str] = None,
) -> dict:
    out = {
        "Sumber Data": source_name,
        "Jumlah Baris": len(df),
        "Jumlah Customer Unik": np.nan,
    }

    if id_col is not None and id_col in df.columns:
        out["Jumlah Customer Unik"] = df[id_col].nunique(dropna=True)

    return out


summary_sources = pd.DataFrame([
    get_basic_summary(df_trx, "Transaksi", id_col=COL_ID_TRX),
    get_basic_summary(df_survey, "Survei", id_col=COL_ID_SURVEY),
    get_basic_summary(df_patient, "Demografi", id_col=COL_ID_PATIENT),
])

table_4_1 = summary_sources[
    ["Sumber Data", "Jumlah Baris", "Jumlah Customer Unik"]
].copy()

display_t41 = table_4_1.copy()
display_t41["Jumlah Baris"] = display_t41["Jumlah Baris"].apply(format_int)
display_t41["Jumlah Customer Unik"] = display_t41["Jumlah Customer Unik"].apply(format_int)

print("\nTabel 4.1 - Jumlah Data per Sumber")
display(display_t41)

save_table(df=table_4_1, file_key="table_4_1")


# ---------------------------------------------------------
# 3.7 RINGKASAN BLOK 3
# ---------------------------------------------------------
print("=" * 70)
print("RINGKASAN BLOK 3")
print("=" * 70)
print(f"- Transaksi : {format_int(len(df_trx))} baris | {format_int(df_trx[COL_ID_TRX].nunique(dropna=True))} customer unik")
print(f"- Survei    : {format_int(len(df_survey))} baris | {format_int(df_survey[COL_ID_SURVEY].nunique(dropna=True))} customer unik")
print(f"- Demografi : {format_int(len(df_patient))} baris | {format_int(df_patient[COL_ID_PATIENT].nunique(dropna=True))} customer unik")
print("=" * 70)


# =========================================================
# BLOK 4 - DATA CLEANING & PREPROCESSING
# =========================================================

print("=" * 70)
print("BLOK 4 - DATA CLEANING & PREPROCESSING")
print("=" * 70)


# ---------------------------------------------------------
# 4.1 SALIN DATA MENTAH
# ---------------------------------------------------------
trx_raw_original = standardize_columns(df_trx.copy())
survey_raw_original = standardize_columns(df_survey.copy())
patient_raw_original = standardize_columns(df_patient.copy())


# ---------------------------------------------------------
# 4.2 TABEL 4.3 - MISSING VALUE DATA MENTAH
# ---------------------------------------------------------
# Tabel ini memakai nama variabel dari file mentah.
# Bagian cleaning setelah ini baru membakukan nama kolom untuk proses berikutnya.

table_4_3 = pd.concat([
    build_missing_table(trx_raw_original, "Transaksi"),
    build_missing_table(survey_raw_original, "Survei"),
    build_missing_table(patient_raw_original, "Demografi"),
], ignore_index=True)

table_4_3 = table_4_3.rename(columns={
    "Jumlah Missing": "Jumlah Missing Value",
    "Persentase Missing": "Persentase Missing Value",
})

print("\nTabel 4.3 - Missing Value Data Mentah")
if len(table_4_3) > 0:
    d43 = table_4_3.copy()
    d43["Jumlah Missing Value"] = d43["Jumlah Missing Value"].apply(format_int)
    d43["Persentase Missing Value"] = d43["Persentase Missing Value"].apply(format_percent)
    display(d43.head(MAX_DISPLAY_ROWS))
else:
    print("Tidak ada missing value pada data mentah.")

save_table(df=table_4_3, file_key="table_4_3")


# ---------------------------------------------------------
# 4.3 BAKUKAN NAMA KOLOM UNTUK PROSES INTERNAL
# ---------------------------------------------------------
trx_raw = trx_raw_original.copy()
survey_raw = survey_raw_original.copy()
patient_raw = patient_raw_original.copy()

trx_raw[COL_ID] = standardize_id(trx_raw[COL_ID_TRX])
trx_raw[COL_DATE_TRX] = safe_to_datetime(trx_raw[COL_DATE_TRX_INPUT])
trx_raw[COL_TOTAL] = safe_to_numeric(trx_raw[COL_TOTAL_INPUT])

if COL_DISC_INPUT is not None:
    trx_raw[COL_DISC] = safe_to_numeric(trx_raw[COL_DISC_INPUT])
else:
    trx_raw[COL_DISC] = 0

if COL_QTY_INPUT is not None:
    trx_raw[COL_QTY] = safe_to_numeric(trx_raw[COL_QTY_INPUT])
else:
    trx_raw[COL_QTY] = np.nan

survey_raw[COL_ID] = standardize_id(survey_raw[COL_ID_SURVEY])
survey_raw[COL_DATE_TRX] = safe_to_datetime(survey_raw[COL_DATE_SURVEY_INPUT])

if COL_FEEDBACK_INPUT is not None:
    survey_raw[COL_FEEDBACK] = survey_raw[COL_FEEDBACK_INPUT]
else:
    survey_raw[COL_FEEDBACK] = np.nan

patient_raw[COL_ID] = standardize_id(patient_raw[COL_ID_PATIENT])

if COL_AGE_INPUT is not None:
    patient_raw[COL_AGE] = safe_to_numeric(patient_raw[COL_AGE_INPUT])
else:
    patient_raw[COL_AGE] = np.nan

if COL_GENDER_INPUT is not None:
    patient_raw[COL_GENDER_CODE] = encode_gender(patient_raw[COL_GENDER_INPUT])
else:
    patient_raw[COL_GENDER_CODE] = 3

# Jika age kosong tetapi DOB ada, age dihitung dari tanggal transaksi terakhir.
if COL_DOB_INPUT is not None:
    patient_raw["dob_clean"] = safe_to_datetime(patient_raw[COL_DOB_INPUT])

    reference_date = trx_raw[COL_DATE_TRX].max()
    if pd.notna(reference_date):
        age_from_dob = np.floor(
            (reference_date - patient_raw["dob_clean"]).dt.days / 365.25
        )
        patient_raw[COL_AGE] = patient_raw[COL_AGE].fillna(age_from_dob)

# Filter umur tidak wajar. Nilai seperti ini diperlakukan sebagai missing.
patient_raw.loc[
    (patient_raw[COL_AGE] < 0) | (patient_raw[COL_AGE] > 100),
    COL_AGE,
] = np.nan


# ---------------------------------------------------------
# 4.4 BUANG BARIS TANPA INFORMASI UTAMA
# ---------------------------------------------------------
df_trx_clean = trx_raw.dropna(subset=[COL_ID, COL_DATE_TRX]).copy()
df_survey_clean = survey_raw.dropna(subset=[COL_ID, COL_DATE_TRX]).copy()
df_patient_clean = patient_raw.dropna(subset=[COL_ID]).copy()

df_trx_clean[COL_TOTAL] = df_trx_clean[COL_TOTAL].fillna(0)
df_trx_clean[COL_DISC] = df_trx_clean[COL_DISC].fillna(0)

# Nilai transaksi negatif tidak dipakai untuk membentuk monetary.
df_trx_clean.loc[df_trx_clean[COL_TOTAL] < 0, COL_TOTAL] = 0
df_trx_clean.loc[df_trx_clean[COL_DISC] < 0, COL_DISC] = 0


# ---------------------------------------------------------
# 4.5 TABEL 4.2 - DUPLIKASI TRANSAKSI HARIAN
# ---------------------------------------------------------
# Data transaksi diubah dari level item/faktur menjadi customer per hari.

trx_source = df_trx_clean.copy()

dup_before = int(
    trx_source.duplicated(subset=[COL_ID, COL_DATE_TRX], keep=False).sum()
)

pair_before = (
    trx_source
    .groupby([COL_ID, COL_DATE_TRX], dropna=False)
    .size()
    .reset_index(name="n_rows")
)

n_dup_groups_before = int((pair_before["n_rows"] > 1).sum())

agg_dict = {
    COL_TOTAL: "sum",
    COL_DISC: "sum",
    COL_QTY: "sum",
}

df_trx_day = (
    trx_source
    .groupby([COL_ID, COL_DATE_TRX], as_index=False)
    .agg(agg_dict)
)

raw_line_count = (
    trx_source
    .groupby([COL_ID, COL_DATE_TRX], as_index=False)
    .size()
    .rename(columns={"size": "raw_line_count"})
)

df_trx_day = df_trx_day.merge(
    raw_line_count,
    on=[COL_ID, COL_DATE_TRX],
    how="left",
)

df_trx_day["promo_flag"] = (df_trx_day[COL_DISC] > 0).astype(int)

dup_after = int(
    df_trx_day.duplicated(subset=[COL_ID, COL_DATE_TRX], keep=False).sum()
)

pair_after = (
    df_trx_day
    .groupby([COL_ID, COL_DATE_TRX], dropna=False)
    .size()
    .reset_index(name="n_rows")
)

n_dup_groups_after = int((pair_after["n_rows"] > 1).sum())

table_4_2 = pd.DataFrame({
    "Tahap": ["Sebelum agregasi", "Sesudah agregasi"],
    "Jumlah Baris": [len(trx_source), len(df_trx_day)],
    "Jumlah Customer-Hari": [len(pair_before), len(pair_after)],
    "Baris Duplikat Harian": [dup_before, dup_after],
    "Kelompok Duplikat Harian": [n_dup_groups_before, n_dup_groups_after],
})

print("\nTabel 4.2 - Duplikasi Transaksi Harian")
d42 = table_4_2.copy()
for col in [
    "Jumlah Baris",
    "Jumlah Customer-Hari",
    "Baris Duplikat Harian",
    "Kelompok Duplikat Harian",
]:
    d42[col] = d42[col].apply(format_int)

display(d42)
save_table(df=table_4_2, file_key="table_4_2")


# ---------------------------------------------------------
# 4.6 SELEKSI COHORT CUSTOMER
# ---------------------------------------------------------
lifetime_freq = (
    df_trx_day
    .groupby(COL_ID, as_index=False)
    .agg(lifetime_visit_days=(COL_DATE_TRX, "count"))
)

n_total = len(lifetime_freq)
n_visit_1 = int((lifetime_freq["lifetime_visit_days"] == 1).sum())
n_qualified = int(
    (lifetime_freq["lifetime_visit_days"] >= LIFETIME_MIN_VISIT_DAYS).sum()
)

pct_qualified = (n_qualified / n_total * 100) if n_total > 0 else 0

eligible_ids = set(
    lifetime_freq.loc[
        lifetime_freq["lifetime_visit_days"] >= LIFETIME_MIN_VISIT_DAYS,
        COL_ID,
    ]
)

df_trx_day_cohort = df_trx_day[df_trx_day[COL_ID].isin(eligible_ids)].copy()
df_survey_cohort = df_survey_clean[df_survey_clean[COL_ID].isin(eligible_ids)].copy()
df_patient_cohort = df_patient_clean[df_patient_clean[COL_ID].isin(eligible_ids)].copy()


# ---------------------------------------------------------
# 4.7 GAMBAR 4.1 - DISTRIBUSI COHORT CUSTOMER
# ---------------------------------------------------------
cohort_plot_df = pd.DataFrame({
    "Kategori": [
        "1 hari kunjungan",
        f">= {LIFETIME_MIN_VISIT_DAYS} hari kunjungan",
    ],
    "Jumlah Customer": [
        n_visit_1,
        n_qualified,
    ],
})

print_chart_title("Gambar 4.1 - Distribusi Cohort Customer")

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(cohort_plot_df["Kategori"], cohort_plot_df["Jumlah Customer"])
ax.set_xlabel("Kategori Cohort")
ax.set_ylabel("Jumlah Customer")
ax.grid(axis="y", alpha=0.3)

add_value_labels_to_bars(ax, fmt="int")
finalize_plot(fig, file_key="fig_4_1", show=True)


# ---------------------------------------------------------
# 4.8 TABEL 4.4 - COVERAGE DATASET FINAL
# ---------------------------------------------------------
# Coverage dihitung pada customer yang masuk cohort awal.
# Dataset final customer-period baru terbentuk pada Blok 5,
# tapi cakupan survei, umur, dan jenis kelamin sudah bisa dicek di sini.

base_customer = pd.DataFrame({
    COL_ID: sorted(df_trx_day_cohort[COL_ID].dropna().unique())
})

survey_ids = set(df_survey_cohort[COL_ID].dropna().unique())
base_customer["survey_available"] = base_customer[COL_ID].isin(survey_ids).astype(int)

patient_profile_coverage = (
    df_patient_cohort[[COL_ID, COL_AGE, COL_GENDER_CODE]]
    .sort_values(COL_ID)
    .groupby(COL_ID, as_index=False)
    .agg(
        age=(COL_AGE, "first"),
        gender_code=(COL_GENDER_CODE, "first"),
    )
)

df_integrated_coverage = base_customer.merge(
    patient_profile_coverage,
    on=COL_ID,
    how="left",
)

n_customer_cohort = df_integrated_coverage[COL_ID].nunique()
survey_rate = (
    df_integrated_coverage["survey_available"].mean() * 100
    if len(df_integrated_coverage) > 0 else 0
)
age_rate = (
    df_integrated_coverage["age"].notna().mean() * 100
    if len(df_integrated_coverage) > 0 else 0
)
gender_rate = (
    df_integrated_coverage["gender_code"].notna().mean() * 100
    if len(df_integrated_coverage) > 0 else 0
)

table_4_4 = pd.DataFrame({
    "Metrik": [
        "Jumlah Customer Cohort",
        "Cakupan Survei",
        "Cakupan Umur",
        "Cakupan Jenis Kelamin",
    ],
    "Nilai": [
        n_customer_cohort,
        round(survey_rate, 4),
        round(age_rate, 4),
        round(gender_rate, 4),
    ],
})

print("\nTabel 4.4 - Coverage Dataset Final")
d44 = table_4_4.copy()
d44["Nilai"] = d44["Nilai"].astype(object)
d44.loc[d44["Metrik"] == "Jumlah Customer Cohort", "Nilai"] = (
    d44.loc[d44["Metrik"] == "Jumlah Customer Cohort", "Nilai"]
    .apply(format_int)
)
d44.loc[d44["Metrik"] != "Jumlah Customer Cohort", "Nilai"] = (
    d44.loc[d44["Metrik"] != "Jumlah Customer Cohort", "Nilai"]
    .apply(format_percent)
)

display(d44)
save_table(df=table_4_4, file_key="table_4_4")


# ---------------------------------------------------------
# 4.9 SIMPAN DATA HASIL CLEANING
# ---------------------------------------------------------
if SAVE_OUTPUT:
    df_trx_clean.to_excel(f"{OUTPUT_DATASET_DIR}/Data_Transaksi_Clean.xlsx", index=False)
    df_survey_clean.to_excel(f"{OUTPUT_DATASET_DIR}/Data_Survei_Clean.xlsx", index=False)
    df_patient_clean.to_excel(f"{OUTPUT_DATASET_DIR}/Data_Demografi_Clean.xlsx", index=False)
    df_trx_day.to_excel(f"{OUTPUT_DATASET_DIR}/Data_Transaksi_Customer_Harian.xlsx", index=False)
    df_trx_day_cohort.to_excel(f"{OUTPUT_DATASET_DIR}/Data_Transaksi_Cohort.xlsx", index=False)


# ---------------------------------------------------------
# 4.10 RINGKASAN BLOK 4
# ---------------------------------------------------------
print("=" * 70)
print("RINGKASAN BLOK 4")
print("=" * 70)
print(f"- Baris transaksi setelah cleaning : {format_int(len(df_trx_clean))}")
print(f"- Baris transaksi setelah agregasi : {format_int(len(df_trx_day))}")
print(f"- Customer yang masuk cohort       : {format_int(n_qualified)} ({format_percent(pct_qualified)})")
print(f"- Cakupan survei pada cohort       : {format_percent(survey_rate)}")
print(f"- Cakupan umur pada cohort         : {format_percent(age_rate)}")
print(f"- Cakupan jenis kelamin pada cohort: {format_percent(gender_rate)}")
print("=" * 70)


# =========================================================
# BLOK 5 - FEATURE ENGINEERING DAN OBSERVASI BERBASIS WAKTU
# =========================================================
print("=" * 70)
print("BLOK 5 - FEATURE ENGINEERING DAN OBSERVASI BERBASIS WAKTU")
print("=" * 70)

# ---------------------------------------------------------
# 5.1 SIAPKAN DATA DASAR
# ---------------------------------------------------------
trx_feat     = df_trx_day_cohort.copy()
survey_feat  = df_survey_cohort.copy()
patient_feat = df_patient_cohort.copy()

trx_feat[COL_DATE_TRX] = safe_to_datetime(trx_feat[COL_DATE_TRX])
trx_feat[COL_TOTAL]    = safe_to_numeric(trx_feat[COL_TOTAL]).fillna(0)
trx_feat[COL_DISC]     = safe_to_numeric(trx_feat[COL_DISC]).fillna(0)

if COL_QTY in trx_feat.columns:
    trx_feat[COL_QTY] = safe_to_numeric(trx_feat[COL_QTY])
else:
    trx_feat[COL_QTY] = np.nan

# Konsisten dengan Blok 4: promo_flag memakai lowercase.
if "promo_flag" not in trx_feat.columns:
    trx_feat["promo_flag"] = (trx_feat[COL_DISC] > 0).astype(int)

survey_feat[COL_DATE_TRX] = safe_to_datetime(survey_feat[COL_DATE_TRX])

patient_feat[COL_AGE] = safe_to_numeric(patient_feat[COL_AGE]) if COL_AGE in patient_feat.columns else np.nan
patient_feat[COL_GENDER_CODE] = (
    safe_to_numeric(patient_feat[COL_GENDER_CODE]).fillna(3).astype(int)
    if COL_GENDER_CODE in patient_feat.columns
    else 3
)

min_date   = trx_feat[COL_DATE_TRX].min()
max_date   = trx_feat[COL_DATE_TRX].max()
START_DATE = pd.Timestamp(min_date.year, min_date.month, 1)

print(f"Periode transaksi cohort: {min_date.date()} - {max_date.date()}")
print(f"Jumlah customer cohort  : {format_int(trx_feat[COL_ID].nunique())}")

# ---------------------------------------------------------
# 5.2 SENTIMEN RULE-BASED
# ---------------------------------------------------------
POSITIVE_TERMS = sorted(set([
    "aamiin","amin","alhamdulillah","terimakasih","terima kasih","makasih","makasi",
    "thanks","thank you","bagus","baguss","bagusss","bgs","baik","baikk","baikkk",
    "recommended","rekomen","rekomendasi","nyaman","ramah","telaten","profesional",
    "memuaskan","mantap","mantapp","keren","best","perfect","great","good","top",
    "cepat","detail","bersih","aman","senang","suka","puas","worth it","worthit",
    "cocok","bagus banget","pelayanan baik",
]), key=len, reverse=True)

NEGATIVE_TERMS = sorted(set([
    "antri","antre","nunggu","nunggunya","menunggu","lama","ramai","penuh","berisik",
    "bising","panas","mahal","kecewa","mengecewakan","buruk","bohong","masalah",
    "keluhan","komplain","iritasi","kasar","bau","berbau","apek","bengkak",
    "berjerawat","bopeng","alergi","aneh","bosen","tidak nyaman","kurang nyaman",
    "kurang ramah","tidak ramah","kurang bersih",
]), key=len, reverse=True)

NEUTRAL_TERMS   = sorted(set(["-","ok","oke","okey","tidak ada","ga ada","gak ada","ngga ada"]), key=len, reverse=True)
NEGATION_WORDS  = ["tidak","tdk","gak","ga","nggak","ngga","kurang","bukan","jangan"]

def normalize_text_for_sentiment(text) -> str:
    if pd.isna(text):
        return ""
    s = str(text).lower().strip()
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase.lower().strip())}\b", text) is not None

def is_negated(text: str, phrase: str, window_words: int = 3) -> bool:
    tokens = text.split()
    phrase_tokens = phrase.split()
    for idx in range(len(tokens)):
        if tokens[idx:idx + len(phrase_tokens)] == phrase_tokens:
            left_context = tokens[max(0, idx - window_words):idx]
            if any(w in NEGATION_WORDS for w in left_context):
                return True
    return False

def rule_based_sentiment(text):
    text_norm = normalize_text_for_sentiment(text)
    if text_norm == "":
        return SENTIMENT_DEFAULT_SCORE, SENTIMENT_EMPTY_LABEL
    if any(contains_phrase(text_norm, t) for t in NEUTRAL_TERMS):
        return 0, SENTIMENT_MANUAL_LABEL

    score = 0
    match_count = 0

    for term in POSITIVE_TERMS:
        if contains_phrase(text_norm, term):
            score += -1 if is_negated(text_norm, term) else 1
            match_count += 1

    for term in NEGATIVE_TERMS:
        if contains_phrase(text_norm, term):
            score += 1 if is_negated(text_norm, term) else -1
            match_count += 1

    if "mahal tapi" in text_norm or "mahal namun" in text_norm:
        if any(contains_phrase(text_norm, t) for t in POSITIVE_TERMS):
            score += 1
            match_count += 1

    if match_count == 0:
        return SENTIMENT_DEFAULT_SCORE, SENTIMENT_UNCERTAIN_LABEL

    return (1 if score > 0 else (-1 if score < 0 else 0)), SENTIMENT_MANUAL_LABEL

if COL_FEEDBACK in survey_feat.columns:
    sentiment_result = survey_feat[COL_FEEDBACK].apply(rule_based_sentiment)
    survey_feat["sentiment_score"]  = sentiment_result.apply(lambda x: x[0])
    survey_feat["sentiment_source"] = sentiment_result.apply(lambda x: x[1])
else:
    survey_feat["sentiment_score"]  = SENTIMENT_DEFAULT_SCORE
    survey_feat["sentiment_source"] = SENTIMENT_EMPTY_LABEL

# ---------------------------------------------------------
# 5.3 KALENDER WINDOW FINAL
# ---------------------------------------------------------
window_calendar_all = generate_window_calendar(
    start_date=START_DATE, max_date=max_date,
    obs_m=OBS_MONTH, pred_m=PRED_MONTH, slide_m=SLIDE_MONTH,
    include_scoring=True
)

if len(window_calendar_all) == 0:
    raise ValueError("Kalender window tidak terbentuk. Periksa parameter window.")


# ---------------------------------------------------------
# 5.4 GAMBAR 4.4 - ECDF GAP ANTAR KUNJUNGAN CUSTOMER
# ---------------------------------------------------------
trx_gap = trx_feat[[COL_ID, COL_DATE_TRX]].copy()
trx_gap = trx_gap.sort_values([COL_ID, COL_DATE_TRX]).reset_index(drop=True)
trx_gap["next_date"] = trx_gap.groupby(COL_ID)[COL_DATE_TRX].shift(-1)
trx_gap["gap_days"]  = (trx_gap["next_date"] - trx_gap[COL_DATE_TRX]).dt.days
gaps = trx_gap["gap_days"].dropna()

print_chart_title("Gambar 4.4 - ECDF Gap Antar Kunjungan Customer")
plot_ecdf(values=gaps.values, xlabel="Jarak antar kunjungan (hari)", file_key="fig_4_4")

# Tabel ECDF horizon - audit, tidak masuk daftar tabel utama draft.
horizon_table = pd.DataFrame({
    "Horizon (hari)": PRED_HORIZON_DAYS,
    "Proporsi <= Horizon (%)": [
        round(float((gaps <= h).mean() * 100), 4) for h in PRED_HORIZON_DAYS
    ],
})

if SHOW_AUDIT_TABLES:
    print("\nProporsi kunjungan berikutnya berdasarkan horizon")
    d_horizon = horizon_table.copy()
    d_horizon["Proporsi <= Horizon (%)"] = d_horizon["Proporsi <= Horizon (%)"].apply(format_percent)
    display(d_horizon)

# ---------------------------------------------------------
# 5.5 FUNGSI PEMBENTUKAN FITUR PER WINDOW
# ---------------------------------------------------------
first_visit = (trx_feat.groupby(COL_ID, as_index=False)
                        .agg(first_visit_date=(COL_DATE_TRX, "min")))

patient_profile = (patient_feat[[COL_ID, COL_AGE, COL_GENDER_CODE]]
                   .groupby(COL_ID, as_index=False)
                   .agg(age=(COL_AGE, "first"), gender_code=(COL_GENDER_CODE, "first")))

available_aspect_cols = [c for c in ASPECT_COLS if c in survey_feat.columns]

if len(available_aspect_cols) > 0:
    for col in available_aspect_cols:
        survey_feat[col] = safe_to_numeric(survey_feat[col])
    survey_feat["satisfaction_row_mean"] = survey_feat[available_aspect_cols].mean(axis=1)
else:
    survey_feat["satisfaction_row_mean"] = np.nan

def build_features_for_calendar(calendar_df, trx_df, survey_df, patient_df) -> pd.DataFrame:
    rows = []

    for _, win in calendar_df.iterrows():
        slice_number = int(win["slice_number"])
        obs_start    = win["obs_start"]
        obs_end      = win["obs_end"]
        pred_start   = win["pred_start"]
        pred_end     = win["pred_end"]
        is_labeled   = bool(win["is_labeled"])
        data_role    = win["data_role"]

        obs_trx = trx_df[
            (trx_df[COL_DATE_TRX] >= obs_start) &
            (trx_df[COL_DATE_TRX] <= obs_end)
        ].copy()

        if len(obs_trx) == 0:
            continue

        obs_agg = (obs_trx.groupby(COL_ID, as_index=False).agg(
            frequency=(COL_DATE_TRX, "count"),
            monetary=(COL_TOTAL, "sum"),
            promo_total=(COL_DISC, "sum"),
            promo_days=("promo_flag", "sum"),
            last_visit_date=(COL_DATE_TRX, "max"),
        ))

        obs_agg = obs_agg[obs_agg["frequency"] >= MIN_TRX_OBS].copy()

        if len(obs_agg) < MIN_CUSTOMER_PER_WINDOW:
            continue

        obs_agg["recency_m"] = ((obs_end - obs_agg["last_visit_date"]).dt.days / 30).round(4)

        obs_agg = obs_agg.merge(first_visit, on=COL_ID, how="left")
        obs_agg["tenure_m"] = ((obs_end - obs_agg["first_visit_date"]).dt.days / 30).round(4)

        obs_agg["promo_ratio"] = np.where(
            obs_agg["monetary"] > 0,
            obs_agg["promo_total"] / obs_agg["monetary"],
            0
        )

        obs_agg["promo_usage_rate"] = np.where(
            obs_agg["frequency"] > 0,
            obs_agg["promo_days"] / obs_agg["frequency"],
            0
        )

        obs_survey = survey_df[
            (survey_df[COL_DATE_TRX] >= obs_start) &
            (survey_df[COL_DATE_TRX] <= obs_end)
        ].copy()

        if len(obs_survey) > 0:
            survey_agg = (obs_survey.groupby(COL_ID, as_index=False).agg(
                satisfaction_mean=("satisfaction_row_mean", "mean"),
                sentiment_mean=("sentiment_score", "mean"),
            ))
        else:
            survey_agg = pd.DataFrame(columns=[COL_ID, "satisfaction_mean", "sentiment_mean"])

        pred_trx = trx_df[
            (trx_df[COL_DATE_TRX] >= pred_start) &
            (trx_df[COL_DATE_TRX] <= pred_end)
        ].copy()

        if is_labeled and len(pred_trx) > 0:
            pred_agg = (pred_trx.groupby(COL_ID, as_index=False).agg(
                frequency_pred=(COL_DATE_TRX, "count"),
                monetary_pred=(COL_TOTAL, "sum"),
            ))
        else:
            pred_agg = pd.DataFrame(columns=[COL_ID, "frequency_pred", "monetary_pred"])

        feature_df = (obs_agg
                      .merge(survey_agg, on=COL_ID, how="left")
                      .merge(patient_profile, on=COL_ID, how="left")
                      .merge(pred_agg, on=COL_ID, how="left"))

        feature_df["frequency_pred"] = pd.to_numeric(
            feature_df["frequency_pred"],
            errors="coerce",
        ).fillna(0)
        feature_df["monetary_pred"] = pd.to_numeric(
            feature_df["monetary_pred"],
            errors="coerce",
        ).fillna(0)

        feature_df["slice_number"] = slice_number
        feature_df["obs_start"]    = obs_start
        feature_df["obs_end"]      = obs_end
        feature_df["pred_start"]   = pred_start
        feature_df["pred_end"]     = pred_end
        feature_df["is_labeled"]   = is_labeled
        feature_df["data_role"]    = data_role

        keep_cols = [
            COL_ID, "slice_number", "obs_start", "obs_end", "pred_start", "pred_end",
            "is_labeled", "data_role", "frequency", "monetary", "recency_m", "tenure_m",
            "promo_ratio", "promo_usage_rate", "satisfaction_mean", "sentiment_mean",
            "age", "gender_code", "frequency_pred", "monetary_pred"
        ]

        rows.append(feature_df[keep_cols].copy())

    if len(rows) == 0:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True)

df_customer_period = build_features_for_calendar(
    calendar_df=window_calendar_all,
    trx_df=trx_feat, survey_df=survey_feat, patient_df=patient_feat
)

if len(df_customer_period) == 0:
    raise ValueError("Dataset customer-period tidak terbentuk. Periksa parameter window.")

df_labeled_base = df_customer_period[df_customer_period["is_labeled"]].copy()
df_scoring_base = df_customer_period[~df_customer_period["is_labeled"]].copy()

print(f"\nObservasi berlabel : {format_int(len(df_labeled_base))}")
print(f"Observasi scoring  : {format_int(len(df_scoring_base))}")

# ---------------------------------------------------------
# 5.6 TABEL 4.5 - EVALUASI KONFIGURASI PERIODE
# ---------------------------------------------------------
def audit_window_config(obs_m, pred_m, slide_m) -> dict:
    cal = generate_window_calendar(
        start_date=START_DATE, max_date=max_date,
        obs_m=obs_m, pred_m=pred_m, slide_m=slide_m,
        include_scoring=False
    )

    if len(cal) == 0:
        return {
            "Konfigurasi": f"{obs_m}-{pred_m}-{slide_m}",
            "Obs. Window": obs_m, "Pred. Window": pred_m, "Slide Window": slide_m,
            "Jumlah Slice": 0, "Total Observasi": 0,
            "Rata-rata Obs./Slice": np.nan, "Median Frequency": np.nan,
            "% Frequency = 1": np.nan, "Churn Rate Proxy (%)": np.nan,
            "Rata-rata Overlap": np.nan,
        }

    temp_df = build_features_for_calendar(
        calendar_df=cal, trx_df=trx_feat, survey_df=survey_feat, patient_df=patient_feat
    )

    if len(temp_df) == 0:
        return {
            "Konfigurasi": f"{obs_m}-{pred_m}-{slide_m}",
            "Obs. Window": obs_m, "Pred. Window": pred_m, "Slide Window": slide_m,
            "Jumlah Slice": len(cal), "Total Observasi": 0,
            "Rata-rata Obs./Slice": np.nan, "Median Frequency": np.nan,
            "% Frequency = 1": np.nan, "Churn Rate Proxy (%)": np.nan,
            "Rata-rata Overlap": np.nan,
        }

    obs_per_slice = temp_df.groupby("slice_number")[COL_ID].size()
    churn_proxy   = (temp_df["frequency_pred"] <= 0).mean() * 100

    slice_sets = [
        set(temp_df.loc[temp_df["slice_number"] == s, COL_ID])
        for s in sorted(temp_df["slice_number"].unique())
    ]

    overlaps = [
        overlap_jaccard(slice_sets[i], slice_sets[i + 1])
        for i in range(len(slice_sets) - 1)
    ]

    return {
        "Konfigurasi": f"{obs_m}-{pred_m}-{slide_m}",
        "Obs. Window": obs_m,
        "Pred. Window": pred_m,
        "Slide Window": slide_m,
        "Jumlah Slice": int(temp_df["slice_number"].nunique()),
        "Total Observasi": int(len(temp_df)),
        "Rata-rata Obs./Slice": float(obs_per_slice.mean()),
        "Median Frequency": float(temp_df["frequency"].median()),
        "% Frequency = 1": float((temp_df["frequency"] == 1).mean() * 100),
        "Churn Rate Proxy (%)": float(churn_proxy),
        "Rata-rata Overlap": float(np.mean(overlaps)) if overlaps else np.nan,
    }

table_4_5 = pd.DataFrame([
    audit_window_config(obs, pred, slide)
    for obs, pred, slide in WINDOW_AUDIT_CONFIGS
])

print("\nTabel 4.5 - Evaluasi Konfigurasi Periode")
d45 = table_4_5.copy()
d45["Total Observasi"]      = d45["Total Observasi"].apply(format_int)
d45["Jumlah Slice"]         = d45["Jumlah Slice"].apply(format_int)
d45["Rata-rata Obs./Slice"] = d45["Rata-rata Obs./Slice"].apply(format_decimal)
d45["Median Frequency"]     = d45["Median Frequency"].apply(format_decimal)
d45["Rata-rata Overlap"]    = d45["Rata-rata Overlap"].apply(format_decimal)
d45["% Frequency = 1"]      = d45["% Frequency = 1"].apply(format_percent)
d45["Churn Rate Proxy (%)"] = d45["Churn Rate Proxy (%)"].apply(format_percent)

display(d45)
save_table(df=table_4_5, file_key="table_4_5")

# ---------------------------------------------------------
# 5.7 TABEL 4.6 - STATISTIK DESKRIPTIF FITUR FINAL
# ---------------------------------------------------------
feature_summary_rows = []

for col in FEATURE_COLS:
    if col not in df_labeled_base.columns:
        continue

    s = df_labeled_base[col]

    if pd.api.types.is_numeric_dtype(s):
        feature_summary_rows.append({
            "Fitur": col,
            "Min": s.min(),
            "Q1": s.quantile(0.25),
            "Median": s.median(),
            "Rataan": s.mean(),
            "Q3": s.quantile(0.75),
            "Maks": s.max(),
            "Missing": s.isna().sum(),
            "Persentase Missing": s.isna().mean() * 100,
        })

table_4_6 = pd.DataFrame(feature_summary_rows)

print("\nTabel 4.6 - Statistik Deskriptif Fitur Final")
d46 = table_4_6.copy()

for col in ["Min","Q1","Median","Rataan","Q3","Maks"]:
    d46[col] = d46[col].apply(format_decimal)

d46["Missing"] = d46["Missing"].apply(format_int)
d46["Persentase Missing"] = d46["Persentase Missing"].apply(format_percent)

display(d46)
save_table(df=table_4_6, file_key="table_4_6")

# ---------------------------------------------------------
# 5.8 GAMBAR 4.2 - DISTRIBUSI MISSING VALUE PADA FITUR FINAL
# ---------------------------------------------------------
missing_feature = build_missing_table(df_labeled_base[FEATURE_COLS].copy(), "Fitur Final")

if len(missing_feature) > 0:
    print_chart_title("Gambar 4.2 - Distribusi Missing Value pada Fitur Final")

    plot_missing = missing_feature.copy()
    plot_missing["Variabel"] = plot_missing["Variabel"].replace(DISPLAY_NAME_MAP)
    plot_missing = plot_missing.sort_values("Persentase Missing", ascending=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(plot_missing["Variabel"], plot_missing["Persentase Missing"])
    ax.set_xlabel("Persentase Missing (%)")
    ax.set_ylabel("Fitur")
    ax.grid(axis="x", alpha=0.3)

    add_value_labels_to_horizontal_bars(ax, fmt="percent")
    finalize_plot(fig, file_key="fig_4_2", show=True)
else:
    print("\nGambar 4.2 - Tidak ada missing value pada fitur final.")

# ---------------------------------------------------------
# 5.9 GAMBAR 4.3 - STRUKTUR PERIODE
# ---------------------------------------------------------
print_chart_title("Gambar 4.3 - Struktur Periode")

cal_plot = window_calendar_all.head(4).copy()
fig, ax  = plt.subplots(figsize=(11, 4))
y_pos    = np.arange(len(cal_plot))[::-1]

for idx, (_, row) in enumerate(cal_plot.iterrows()):
    y = y_pos[idx]

    ax.barh(y=y, width=(row["obs_end"] - row["obs_start"]).days + 1,
            left=row["obs_start"].toordinal(), height=0.35,
            label="Observasi" if idx == 0 else None)

    ax.barh(y=y, width=(row["pred_end"] - row["pred_start"]).days + 1,
            left=row["pred_start"].toordinal(), height=0.35,
            label="Prediksi" if idx == 0 else None)

ax.set_yticks(y_pos)
ax.set_yticklabels([f"Slice {int(s)}" for s in cal_plot["slice_number"]])
ax.set_xlabel("Periode")
ax.set_ylabel("Slice")

tick_dates = pd.date_range(start=cal_plot["obs_start"].min(),
                           end=cal_plot["pred_end"].max(), freq="2MS")
ax.set_xticks([d.toordinal() for d in tick_dates])
ax.set_xticklabels([d.strftime("%Y-%m") for d in tick_dates], rotation=45, ha="right")
ax.grid(axis="x", alpha=0.3)
ax.legend()

finalize_plot(fig, file_key="fig_4_3", show=True)

# ---------------------------------------------------------
# 5.10 GAMBAR 4.5 - BOXPLOT FITUR UTAMA
# ---------------------------------------------------------
print_chart_title("Gambar 4.5 - Boxplot Fitur Utama")

boxplot_specs = [
    {"col": "frequency",  "ylabel": "Jumlah Kunjungan"},
    {"col": "monetary",   "ylabel": "Rupiah"},
    {"col": "recency_m",  "ylabel": "Bulan"},
]

fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(14, 5))

for ax, spec in zip(axes, boxplot_specs):
    col = spec["col"]
    values = pd.to_numeric(df_labeled_base[col], errors="coerce").dropna().values

    ax.boxplot(values)
    ax.set_ylabel(spec["ylabel"])
    ax.set_xticks([1])
    ax.set_xticklabels([DISPLAY_NAME_MAP.get(col, col)])
    ax.grid(axis="y", alpha=0.3)

    if col == "monetary" and USE_COMPACT_CURRENCY_FORMAT:
        ticks = ax.get_yticks()
        ax.set_yticks(ticks)
        ax.set_yticklabels([format_compact_number(t, 1) for t in ticks])

finalize_plot(fig, file_key="fig_4_5", show=True)

# ---------------------------------------------------------
# 5.11 GAMBAR 4.6 - HEATMAP KORELASI FITUR
# ---------------------------------------------------------
print_chart_title("Gambar 4.6 - Heatmap Korelasi Fitur")

corr_cols   = [c for c in FEATURE_COLS if c in df_labeled_base.columns]
corr_matrix = df_labeled_base[corr_cols].corr(numeric_only=True)
feat_labels = [DISPLAY_NAME_MAP.get(c, c) for c in corr_matrix.columns]

fig, ax = plt.subplots(figsize=(9, 7))
im = ax.imshow(corr_matrix.values, aspect="auto")

ax.set_xticks(np.arange(len(corr_matrix.columns)))
ax.set_yticks(np.arange(len(corr_matrix.index)))
ax.set_xticklabels(feat_labels, rotation=45, ha="right")
ax.set_yticklabels(feat_labels)

for i in range(len(corr_matrix.index)):
    for j in range(len(corr_matrix.columns)):
        val = corr_matrix.iloc[i, j]
        if pd.notna(val):
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8)

fig.colorbar(im, ax=ax)
finalize_plot(fig, file_key="fig_4_6", show=True)

# Simpan dataset
if SAVE_OUTPUT:
    df_customer_period.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Customer_Period_All.xlsx", index=False)
    df_labeled_base.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Labeled_Base.xlsx", index=False)
    df_scoring_base.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Scoring_Base.xlsx", index=False)

print("=" * 70)
print("RINGKASAN BLOK 5")
print("=" * 70)
print(f"- Observasi berlabel : {format_int(len(df_labeled_base))}")
print(f"- Observasi scoring  : {format_int(len(df_scoring_base))}")
print(f"- Jumlah fitur       : {len(FEATURE_COLS)}")
print("=" * 70)


# =========================================================
# BLOK 6 - PENENTUAN LABEL CHURN
# =========================================================
print("=" * 70)
print("BLOK 6 - PENENTUAN LABEL CHURN")
print("=" * 70)

df_labeled = df_labeled_base.copy()
df_labeled["frequency_pred"] = pd.to_numeric(df_labeled["frequency_pred"], errors="coerce").fillna(0)
df_labeled["churn"] = (df_labeled["frequency_pred"] <= 0).astype(int)
df_labeled["churn_reason"] = np.where(df_labeled["churn"] == 1, "no_transaction", "active")

df_scoring = df_scoring_base.copy()

# ---------------------------------------------------------
# 6.1 GAMBAR 4.7 - DISTRIBUSI CHURN DAN NON-CHURN
# ---------------------------------------------------------
churn_dist = (
    df_labeled["churn"]
    .value_counts()
    .rename_axis("churn")
    .reset_index(name="jumlah")
)

churn_dist["kategori"] = churn_dist["churn"].map({
    1: "Churn",
    0: "Non-Churn",
})

churn_dist = churn_dist.sort_values("churn", ascending=False).reset_index(drop=True)

print_chart_title("Gambar 4.7 - Distribusi Churn dan Non-Churn")

fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(churn_dist["kategori"], churn_dist["jumlah"])
ax.set_xlabel("Kategori")
ax.set_ylabel("Jumlah Observasi")
ax.grid(axis="y", alpha=0.3)

add_value_labels_to_bars(ax, fmt="int")
finalize_plot(fig, file_key="fig_4_7", show=True)

# ---------------------------------------------------------
# 6.2 GAMBAR 4.8 - CHURN RATE PER SLICE
# ---------------------------------------------------------
slice_stats = (
    df_labeled
    .groupby("slice_number", as_index=False)
    .agg(
        obs_start=("obs_start", "min"),
        obs_end=("obs_end", "max"),
        jumlah=(COL_ID, "size"),
        jumlah_churn=("churn", "sum"),
        churn_rate=("churn", "mean"),
    )
)

slice_stats["churn_rate"] = slice_stats["churn_rate"] * 100

print_chart_title("Gambar 4.8 - Churn Rate per Slice")

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(slice_stats["slice_number"], slice_stats["churn_rate"], marker="o")
ax.set_xlabel("Slice")
ax.set_ylabel("Churn Rate (%)")
ax.set_xticks(slice_stats["slice_number"])
ax.grid(alpha=0.3)

for _, row in slice_stats.iterrows():
    ax.annotate(
        format_percent(row["churn_rate"]),
        (row["slice_number"], row["churn_rate"]),
        textcoords="offset points",
        xytext=(0, 6),
        ha="center",
        fontsize=9,
    )

finalize_plot(fig, file_key="fig_4_8", show=True)

# ---------------------------------------------------------
# 6.4 RINGKASAN LABEL CHURN
# ---------------------------------------------------------
n_labeled = len(df_labeled)
n_churn = int(df_labeled["churn"].sum())
n_non_churn = int(n_labeled - n_churn)
churn_rate_total = (n_churn / n_labeled * 100) if n_labeled > 0 else np.nan

if SAVE_OUTPUT:
    df_labeled.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Labeled_Final.xlsx", index=False)
    df_scoring.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Scoring_Base_Final.xlsx", index=False)
    slice_stats.to_excel(f"{OUTPUT_DATASET_DIR}/Audit_Churn_Rate_per_Slice.xlsx", index=False)

print("=" * 70)
print("RINGKASAN BLOK 6")
print("=" * 70)
print(f"- Total observasi berlabel : {format_int(n_labeled)}")
print(f"- Jumlah churn             : {format_int(n_churn)} ({format_percent(churn_rate_total)})")
print(f"- Jumlah non-churn         : {format_int(n_non_churn)}")
print("=" * 70)


# =========================================================
# BLOK 7 - SPLITTING DATA TRAINING, VALIDATION, TESTING, DAN SCORING
# =========================================================
print("=" * 70)
print("BLOK 7 - SPLITTING DATA")
print("=" * 70)

labeled_slices = sorted(df_labeled["slice_number"].dropna().unique().tolist())

if len(labeled_slices) < 3:
    raise ValueError("Jumlah slice berlabel terlalu sedikit untuk pembagian train-validation-test.")

TEST_SLICE = max(labeled_slices)
TRAIN_VALID_SLICES = [s for s in labeled_slices if s < TEST_SLICE]

if len(TRAIN_VALID_SLICES) < MIN_TRAIN_END + 1:
    raise ValueError("Jumlah slice training-validation tidak cukup untuk walk-forward validation.")

scoring_slices = (
    sorted(df_scoring["slice_number"].dropna().unique().tolist())
    if len(df_scoring) > 0 else []
)

df_train_valid = (
    df_labeled[df_labeled["slice_number"].isin(TRAIN_VALID_SLICES)]
    .sort_values(["slice_number", COL_ID])
    .reset_index(drop=True)
)

df_test = (
    df_labeled[df_labeled["slice_number"] == TEST_SLICE]
    .sort_values(["slice_number", COL_ID])
    .reset_index(drop=True)
)

df_scoring_final = (
    df_scoring
    .sort_values(["slice_number", COL_ID])
    .reset_index(drop=True)
)

print(f"Slice training-validation : {TRAIN_VALID_SLICES}")
print(f"Slice testing             : {TEST_SLICE}")
print(f"Slice scoring             : {scoring_slices if scoring_slices else '-'}")

# ---------------------------------------------------------
# 7.1 TABEL 4.7 - SKEMA WALK-FORWARD VALIDATION
# ---------------------------------------------------------
walk_forward_rows = []

for valid_slice in TRAIN_VALID_SLICES:
    if valid_slice <= MIN_TRAIN_END:
        continue

    train_slices = [s for s in TRAIN_VALID_SLICES if s < valid_slice]

    if len(train_slices) < MIN_TRAIN_END:
        continue

    tv_mask = df_train_valid["slice_number"].isin(train_slices)
    vv_mask = df_train_valid["slice_number"] == valid_slice

    walk_forward_rows.append({
        "Fold": len(walk_forward_rows) + 1,
        "Slice Training": ", ".join([str(int(s)) for s in train_slices]),
        "Slice Validation": int(valid_slice),
        "Obs. Training": int(df_train_valid[tv_mask].shape[0]),
        "Obs. Validasi": int(df_train_valid[vv_mask].shape[0]),
        "Churn Rate Training": float(df_train_valid.loc[tv_mask, "churn"].mean() * 100),
        "Churn Rate Validation": float(df_train_valid.loc[vv_mask, "churn"].mean() * 100),
        "train_slices_raw": train_slices,
        "validation_slice_raw": valid_slice,
    })

table_4_7 = pd.DataFrame(walk_forward_rows)

if len(table_4_7) == 0:
    raise ValueError("Tabel walk-forward validation kosong. Periksa MIN_TRAIN_END atau konfigurasi window.")

print("\nTabel 4.7 - Skema Walk-Forward Validation")

d47 = table_4_7[
    [
        "Fold",
        "Slice Training",
        "Slice Validation",
        "Obs. Training",
        "Obs. Validasi",
        "Churn Rate Training",
        "Churn Rate Validation",
    ]
].copy()

for col in ["Fold", "Slice Validation", "Obs. Training", "Obs. Validasi"]:
    d47[col] = d47[col].apply(format_int)

d47["Churn Rate Training"] = d47["Churn Rate Training"].apply(format_percent)
d47["Churn Rate Validation"] = d47["Churn Rate Validation"].apply(format_percent)

display(d47)
save_table(df=d47, file_key="table_4_7")

# ---------------------------------------------------------
# 7.2 GAMBAR 4.9 - PERBANDINGAN CHURN RATE TRAINING-VALIDATION DAN TESTING
# ---------------------------------------------------------
tv_churn_rate = float(df_train_valid["churn"].mean() * 100)
test_churn_rate = float(df_test["churn"].mean() * 100)

plot_split_df = pd.DataFrame({
    "Data": ["Training-Validation", "Testing"],
    "Churn Rate": [tv_churn_rate, test_churn_rate],
})

print_chart_title("Gambar 4.9 - Perbandingan Churn Rate Training-Validation dan Testing")

fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(plot_split_df["Data"], plot_split_df["Churn Rate"])
ax.set_xlabel("Data")
ax.set_ylabel("Churn Rate (%)")
ax.grid(axis="y", alpha=0.3)

add_value_labels_to_bars(ax, fmt="percent")
finalize_plot(fig, file_key="fig_4_9", show=True)

# ---------------------------------------------------------
# 7.3 GAMBAR 4.10 - DIAGRAM WALK-FORWARD VALIDATION
# ---------------------------------------------------------
print_chart_title("Gambar 4.10 - Diagram Walk-Forward Validation")

fig, ax = plt.subplots(figsize=(10, 4))
y_positions = np.arange(len(table_4_7))[::-1]

for idx, (_, row) in enumerate(table_4_7.iterrows()):
    y = y_positions[idx]

    train_slices = row["train_slices_raw"]
    valid_slice = int(row["validation_slice_raw"])

    train_start = int(min(train_slices))
    train_end = int(max(train_slices))

    train_churn = float(
        df_train_valid.loc[
            df_train_valid["slice_number"].isin(train_slices),
            "churn",
        ].mean() * 100
    )

    valid_churn = float(
        df_train_valid.loc[
            df_train_valid["slice_number"] == valid_slice,
            "churn",
        ].mean() * 100
    )

    ax.barh(
        y=y,
        width=train_end - train_start + 1,
        left=train_start,
        height=0.35,
        label="Training" if idx == 0 else None,
    )

    ax.barh(
        y=y,
        width=1,
        left=valid_slice,
        height=0.35,
        label="Validation" if idx == 0 else None,
    )

    ax.text(
        x=train_start + (train_end - train_start + 1) / 2,
        y=y,
        s=f"{train_churn:.1f}%".replace(".", ","),
        va="center",
        ha="center",
        fontsize=9,
        color="white",
    )

    ax.text(
        x=valid_slice + 0.5,
        y=y,
        s=f"{valid_churn:.1f}%".replace(".", ","),
        va="center",
        ha="center",
        fontsize=9,
        color="white",
    )

ax.set_yticks(y_positions)
ax.set_yticklabels([f"Fold {int(f)}" for f in table_4_7["Fold"]])
ax.set_xlabel("Slice")
ax.set_ylabel("Fold")
ax.set_xticks(sorted(df_labeled["slice_number"].unique()))
ax.grid(axis="x", alpha=0.3)
ax.legend()

finalize_plot(fig, file_key="fig_4_10", show=True)

# ---------------------------------------------------------
# 7.4 SIAPKAN X, y UNTUK MODELING
# ---------------------------------------------------------
model_feature_cols = [col for col in FEATURE_COLS if col in df_labeled.columns]

if len(model_feature_cols) == 0:
    raise ValueError("Tidak ada fitur yang tersedia untuk modeling.")

X_train_valid = df_train_valid[model_feature_cols].copy()
y_train_valid = df_train_valid["churn"].astype(int).copy()

X_test = df_test[model_feature_cols].copy()
y_test = df_test["churn"].astype(int).copy()

# Data fold mentah untuk proses tuning/modeling pada blok berikutnya.
walk_forward_folds = []

for _, row in table_4_7.iterrows():
    walk_forward_folds.append({
        "fold": int(row["Fold"]),
        "train_slices": row["train_slices_raw"],
        "validation_slice": int(row["validation_slice_raw"]),
    })

# ---------------------------------------------------------
# 7.5 SIMPAN DATA SPLIT
# ---------------------------------------------------------
if SAVE_OUTPUT:
    df_train_valid.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Training_Validation.xlsx", index=False)
    df_test.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Testing.xlsx", index=False)
    df_scoring_final.to_excel(f"{OUTPUT_DATASET_DIR}/Dataset_Scoring_Final.xlsx", index=False)

# ---------------------------------------------------------
# 7.6 RINGKASAN BLOK 7
# ---------------------------------------------------------
print("=" * 70)
print("RINGKASAN BLOK 7")
print("=" * 70)
print(f"- Slice training-validation : {TRAIN_VALID_SLICES}")
print(f"- Slice testing             : {TEST_SLICE}")
print(f"- Slice scoring             : {scoring_slices if scoring_slices else '-'}")
print(f"- Observasi train-validation: {format_int(len(df_train_valid))}")
print(f"- Observasi testing         : {format_int(len(df_test))}")
print(f"- Observasi scoring         : {format_int(len(df_scoring_final))}")
print(f"- Churn rate train-valid    : {format_percent(tv_churn_rate)}")
print(f"- Churn rate testing        : {format_percent(test_churn_rate)}")
print(f"- Fitur model               : {model_feature_cols}")
print("=" * 70)


# =========================================================
# BLOK 8 - XGBOOST, TUNING, DAN TRAINING FINAL
# =========================================================
print("=" * 70)
print("BLOK 8 - XGBOOST, TUNING, DAN TRAINING FINAL")
print("=" * 70)

# ---------------------------------------------------------
# 8.0 PARAMETER DASAR MODELING
# ---------------------------------------------------------
n_pos = int((y_train_valid == 1).sum())
n_neg = int((y_train_valid == 0).sum())
scale_pos_weight_default = n_neg / n_pos if n_pos > 0 else 1.0

scale_pos_low = XGB_SEARCH_SPACE.get(
    "scale_pos_weight",
    (max(0.1, scale_pos_weight_default * 0.5), max(0.2, scale_pos_weight_default * 2.0))
)[0]

scale_pos_high = XGB_SEARCH_SPACE.get(
    "scale_pos_weight",
    (max(0.1, scale_pos_weight_default * 0.5), max(0.2, scale_pos_weight_default * 2.0))
)[1]

print(f"\n- Churn training-validation    : {format_int(n_pos)}")
print(f"- Non-Churn training-validation: {format_int(n_neg)}")
print(f"- scale_pos_weight awal        : {format_metric(scale_pos_weight_default)}")
print(f"- USE_OPTUNA_TUNING            : {USE_OPTUNA_TUNING}")

# ---------------------------------------------------------
# 8.1 TABEL 4.8 - SEARCH SPACE HYPERPARAMETER XGBOOST
# ---------------------------------------------------------
table_4_8 = pd.DataFrame({
    "Parameter": [
        "max_depth", "learning_rate", "subsample", "colsample_bytree",
        "min_child_weight", "gamma", "reg_alpha", "reg_lambda",
        "scale_pos_weight", "n_estimators", "early_stopping_rounds",
    ],
    "Ruang Pencarian / Nilai": [
        f"{XGB_SEARCH_SPACE['max_depth'][0]} - {XGB_SEARCH_SPACE['max_depth'][1]}",
        f"{XGB_SEARCH_SPACE['learning_rate'][0]} - {XGB_SEARCH_SPACE['learning_rate'][1]}",
        f"{XGB_SEARCH_SPACE['subsample'][0]} - {XGB_SEARCH_SPACE['subsample'][1]}",
        f"{XGB_SEARCH_SPACE['colsample_bytree'][0]} - {XGB_SEARCH_SPACE['colsample_bytree'][1]}",
        f"{XGB_SEARCH_SPACE['min_child_weight'][0]} - {XGB_SEARCH_SPACE['min_child_weight'][1]}",
        f"{XGB_SEARCH_SPACE['gamma'][0]} - {XGB_SEARCH_SPACE['gamma'][1]}",
        f"{XGB_SEARCH_SPACE['reg_alpha'][0]} - {XGB_SEARCH_SPACE['reg_alpha'][1]}",
        f"{XGB_SEARCH_SPACE['reg_lambda'][0]} - {XGB_SEARCH_SPACE['reg_lambda'][1]}",
        f"{scale_pos_low:.4f} - {scale_pos_high:.4f}",
        str(N_ESTIMATORS_CAP),
        str(EARLY_STOPPING_ROUNDS),
    ],
})

print("\nTabel 4.8 - Search Space Hyperparameter XGBoost")
display(table_4_8)
save_table(df=table_4_8, file_key="table_4_8")

# ---------------------------------------------------------
# 8.2 FUNGSI EVALUASI WALK-FORWARD
# ---------------------------------------------------------
def get_base_xgb_params(params: dict) -> dict:
    base = {
        "objective": "binary:logistic",
        "eval_metric": ["auc", "logloss"],
        "tree_method": "hist",
        "seed": RANDOM_SEED,
        "nthread": N_JOBS,
        "verbosity": 0,
    }
    base.update(params)
    return base

def get_best_iteration(model) -> int:
    if hasattr(model, "best_iteration") and model.best_iteration is not None:
        return int(model.best_iteration) + 1
    if hasattr(model, "best_ntree_limit") and model.best_ntree_limit is not None:
        return int(model.best_ntree_limit)
    return int(model.num_boosted_rounds())

def evaluate_params_walk_forward(params: dict, return_detail: bool = False):
    fold_rows = []
    best_iters = []
    xgb_params = get_base_xgb_params(params)

    for _, fold_row in table_4_7.iterrows():
        train_slices = fold_row["train_slices_raw"]
        valid_slice = int(fold_row["validation_slice_raw"])

        train_idx = df_train_valid["slice_number"].isin(train_slices)
        valid_idx = df_train_valid["slice_number"] == valid_slice

        X_tr = df_train_valid.loc[train_idx, model_feature_cols].copy()
        y_tr = df_train_valid.loc[train_idx, "churn"].astype(int).copy()
        X_val = df_train_valid.loc[valid_idx, model_feature_cols].copy()
        y_val = df_train_valid.loc[valid_idx, "churn"].astype(int).copy()

        dtrain = xgb.DMatrix(X_tr, label=y_tr, feature_names=model_feature_cols)
        dvalid = xgb.DMatrix(X_val, label=y_val, feature_names=model_feature_cols)

        model = xgb.train(
            params=xgb_params,
            dtrain=dtrain,
            num_boost_round=N_ESTIMATORS_CAP,
            evals=[(dtrain, "train"), (dvalid, "validation")],
            early_stopping_rounds=EARLY_STOPPING_ROUNDS,
            verbose_eval=False,
        )

        best_iter = get_best_iteration(model)
        y_val_proba = model.predict(dvalid, iteration_range=(0, best_iter))
        auc_val = safe_roc_auc(y_val, y_val_proba)
        if pd.isna(auc_val):
            raise ValueError(
                f"Slice validasi {valid_slice} hanya berisi satu kelas churn. "
                "Ubah konfigurasi window atau MIN_TRAIN_END."
            )

        best_iters.append(best_iter)
        fold_rows.append({
            "Fold": int(fold_row["Fold"]),
            "Slice Validation": valid_slice,
            "AUC Validasi": auc_val,
            "Best Iteration": best_iter,
        })

    detail_df = pd.DataFrame(fold_rows)
    mean_auc = float(detail_df["AUC Validasi"].mean())
    std_auc = float(detail_df["AUC Validasi"].std(ddof=0))
    best_n_estimators = int(np.median(best_iters)) if len(best_iters) > 0 else 1
    best_n_estimators = max(1, best_n_estimators)

    if return_detail:
        return mean_auc, std_auc, best_n_estimators, detail_df

    return mean_auc

def suggest_xgb_params(trial: optuna.Trial) -> dict:
    return {
        "max_depth": trial.suggest_int(
            "max_depth",
            int(XGB_SEARCH_SPACE["max_depth"][0]),
            int(XGB_SEARCH_SPACE["max_depth"][1]),
        ),
        "learning_rate": trial.suggest_float(
            "learning_rate",
            float(XGB_SEARCH_SPACE["learning_rate"][0]),
            float(XGB_SEARCH_SPACE["learning_rate"][1]),
            log=True,
        ),
        "subsample": trial.suggest_float(
            "subsample",
            float(XGB_SEARCH_SPACE["subsample"][0]),
            float(XGB_SEARCH_SPACE["subsample"][1]),
        ),
        "colsample_bytree": trial.suggest_float(
            "colsample_bytree",
            float(XGB_SEARCH_SPACE["colsample_bytree"][0]),
            float(XGB_SEARCH_SPACE["colsample_bytree"][1]),
        ),
        "min_child_weight": trial.suggest_float(
            "min_child_weight",
            float(XGB_SEARCH_SPACE["min_child_weight"][0]),
            float(XGB_SEARCH_SPACE["min_child_weight"][1]),
        ),
        "gamma": trial.suggest_float(
            "gamma",
            float(XGB_SEARCH_SPACE["gamma"][0]),
            float(XGB_SEARCH_SPACE["gamma"][1]),
        ),
        "reg_alpha": trial.suggest_float(
            "reg_alpha",
            float(XGB_SEARCH_SPACE["reg_alpha"][0]),
            float(XGB_SEARCH_SPACE["reg_alpha"][1]),
        ),
        "reg_lambda": trial.suggest_float(
            "reg_lambda",
            float(XGB_SEARCH_SPACE["reg_lambda"][0]),
            float(XGB_SEARCH_SPACE["reg_lambda"][1]),
        ),
        "scale_pos_weight": trial.suggest_float(
            "scale_pos_weight",
            float(scale_pos_low),
            float(scale_pos_high),
        ),
    }

# ---------------------------------------------------------
# 8.3 EVALUASI PARAMETER AWAL
# ---------------------------------------------------------
baseline_params = {
    "max_depth": 3,
    "learning_rate": 0.1,
    "subsample": 1.0,
    "colsample_bytree": 1.0,
    "min_child_weight": 1,
    "gamma": 0.0,
    "reg_alpha": 0.0,
    "reg_lambda": 1.0,
    "scale_pos_weight": scale_pos_weight_default,
}

baseline_auc, baseline_std, baseline_best_iter, baseline_detail = evaluate_params_walk_forward(
    params=baseline_params,
    return_detail=True,
)

print(f"\nEvaluasi parameter awal selesai.")
print(f"- Rata-rata AUC validasi awal: {format_metric(baseline_auc)}")

# ---------------------------------------------------------
# 8.4 OPTUNA TUNING ATAU PARAMETER DRAFT
# ---------------------------------------------------------
study = None
optuna_trials = pd.DataFrame()
trial_history = pd.DataFrame()

if USE_OPTUNA_TUNING:
    def objective(trial: optuna.Trial) -> float:
        return evaluate_params_walk_forward(
            params=suggest_xgb_params(trial),
            return_detail=False,
        )

    study = optuna.create_study(
        direction="maximize",
        sampler=TPESampler(seed=RANDOM_SEED),
        study_name="xgboost_churn_walk_forward",
    )

    print(f"\nMulai tuning Optuna ({N_OPTUNA_TRIALS} trial)...")
    study.optimize(
        objective,
        n_trials=N_OPTUNA_TRIALS,
        timeout=OPTUNA_TIMEOUT,
        show_progress_bar=True,
    )
    print("Tuning selesai.")

    best_params = study.best_params.copy()
    best_validation_auc = float(study.best_value)
    best_auc, best_std, best_n_estimators, best_detail = evaluate_params_walk_forward(
        params=best_params,
        return_detail=True,
    )

else:
    print("\nUSE_OPTUNA_TUNING = False.")
    print("Model memakai hyperparameter dari draft.")

    best_params = DRAFT_BEST_XGB_PARAMS.copy()
    best_n_estimators = int(DRAFT_BEST_N_ESTIMATORS)

    best_auc, best_std, _, best_detail = evaluate_params_walk_forward(
        params=best_params,
        return_detail=True,
    )
    best_validation_auc = best_auc

print(f"- Best validation AUC  : {format_metric(best_auc)}")
print(f"- Estimasi jumlah pohon: {format_int(best_n_estimators)}")

# ---------------------------------------------------------
# 8.5 TABEL 4.9 - BEST HYPERPARAMETER XGBOOST
# ---------------------------------------------------------
table_4_9 = pd.DataFrame({
    "Parameter": list(best_params.keys()) + ["n_estimators"],
    "Nilai": [
        round(float(v), 4) if isinstance(v, float) else v
        for v in best_params.values()
    ] + [best_n_estimators],
})

print("\nTabel 4.9 - Best Hyperparameter XGBoost")
display(table_4_9)
save_table(df=table_4_9, file_key="table_4_9")

# ---------------------------------------------------------
# 8.6 TABEL 4.10 - PERBANDINGAN PERFORMA SEBELUM DAN SESUDAH TUNING
# ---------------------------------------------------------
table_4_10 = pd.DataFrame({
    "Model": ["Parameter Awal", "Hasil Tuning Optuna" if USE_OPTUNA_TUNING else "Hyperparameter Draft"],
    "Rata-rata ROC-AUC Validasi": [baseline_auc, best_auc],
    "Std ROC-AUC Validasi": [baseline_std, best_std],
    "Estimasi Jumlah Pohon": [baseline_best_iter, best_n_estimators],
})

print("\nTabel 4.10 - Perbandingan Performa Sebelum dan Sesudah Tuning")
d410 = table_4_10.copy()
d410["Rata-rata ROC-AUC Validasi"] = d410["Rata-rata ROC-AUC Validasi"].apply(format_metric)
d410["Std ROC-AUC Validasi"] = d410["Std ROC-AUC Validasi"].apply(format_metric)
d410["Estimasi Jumlah Pohon"] = d410["Estimasi Jumlah Pohon"].apply(format_int)
display(d410)
save_table(df=table_4_10, file_key="table_4_10")

# ---------------------------------------------------------
# 8.7 GAMBAR 4.11 - OPTUNA OPTIMIZATION HISTORY
# ---------------------------------------------------------
if USE_OPTUNA_TUNING and study is not None:
    optuna_trials = study.trials_dataframe()
    trial_history = optuna_trials[optuna_trials["state"] == "COMPLETE"].copy()
    trial_history["best_so_far"] = trial_history["value"].cummax()

    print_chart_title("Gambar 4.11 - Optuna Optimization History")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        trial_history["number"],
        trial_history["value"],
        marker="o",
        linewidth=1,
        label="AUC per Trial",
    )
    ax.plot(
        trial_history["number"],
        trial_history["best_so_far"],
        linewidth=2,
        label="AUC Terbaik Sementara",
    )
    ax.set_xlabel("Trial")
    ax.set_ylabel("AUC Validasi")
    ax.grid(alpha=0.3)
    ax.legend()

    finalize_plot(fig, file_key="fig_4_11", show=True)

    if SAVE_OUTPUT:
        optuna_trials.to_excel(f"{OUTPUT_LOG_DIR}/Optuna_Trials_Detail.xlsx", index=False)

else:
    print("\nGambar 4.11 - Optuna Optimization History dilewati karena USE_OPTUNA_TUNING = False.")

# ---------------------------------------------------------
# 8.8 TRAINING MODEL FINAL
# ---------------------------------------------------------
final_params = get_base_xgb_params(best_params)

dtrain_valid_all = xgb.DMatrix(
    X_train_valid,
    label=y_train_valid,
    feature_names=model_feature_cols,
)

dtest = xgb.DMatrix(
    X_test,
    label=y_test,
    feature_names=model_feature_cols,
)

model_final = xgb.train(
    params=final_params,
    dtrain=dtrain_valid_all,
    num_boost_round=best_n_estimators,
    evals=[(dtrain_valid_all, "train_valid")],
    verbose_eval=False,
)

y_train_valid_proba = model_final.predict(dtrain_valid_all)
y_test_proba = model_final.predict(dtest)

train_valid_auc_final = safe_roc_auc(y_train_valid, y_train_valid_proba)
test_auc_preview = safe_roc_auc(y_test, y_test_proba)

df_train_valid_pred = df_train_valid.copy()
df_train_valid_pred[PRED_PROBA_COL] = y_train_valid_proba

df_test_pred = df_test.copy()
df_test_pred[PRED_PROBA_COL] = y_test_proba

print(f"\n- AUC training-validation: {format_metric(train_valid_auc_final)}")
print(f"- AUC testing preview    : {format_metric(test_auc_preview)}")

# ---------------------------------------------------------
# 8.9 GAMBAR 4.12 - XGBOOST TREE ITERASI AWAL, TENGAH, DAN AKHIR
# ---------------------------------------------------------
def shorten_tree_text(text: str) -> str:
    def repl(m):
        try:
            return f"{float(m.group(0)):.4f}"
        except (TypeError, ValueError):
            return m.group(0)

    return re.sub(r"-?\d+\.\d+", repl, text)

if GENERATE_TREE_PLOT:
    tree_specs = []

    if best_n_estimators <= 1:
        tree_specs = [{"idx": 0, "label": "Iterasi Awal"}]
    elif best_n_estimators == 2:
        tree_specs = [
            {"idx": 0, "label": "Iterasi Awal"},
            {"idx": 1, "label": "Iterasi Akhir"},
        ]
    else:
        tree_specs = [
            {"idx": 0, "label": "Iterasi Awal"},
            {"idx": max(1, best_n_estimators // 2), "label": "Iterasi Tengah"},
            {"idx": best_n_estimators - 1, "label": "Iterasi Akhir"},
        ]

    try:
        n_panels = len(tree_specs)

        fig, axes = plt.subplots(
            nrows=n_panels,
            ncols=1,
            figsize=(28, 6.5 * n_panels),
            constrained_layout=True,
        )

        if n_panels == 1:
            axes = [axes]

        for ax, spec in zip(axes, tree_specs):
            xgb.plot_tree(
                model_final,
                num_trees=spec["idx"],
                ax=ax,
                rankdir="LR",
            )

            ax.set_title(
                spec["label"],
                fontsize=18,
                pad=12,
                fontweight="bold",
            )

            for txt in ax.texts:
                txt.set_text(shorten_tree_text(txt.get_text()))
                txt.set_fontsize(16)

        print_chart_title("Gambar 4.12 - XGBoost Tree Iterasi Awal, Tengah, dan Akhir")
        finalize_plot(fig, file_key="fig_4_12", show=True)

    except Exception as e:
        print(f"Visualisasi tree XGBoost gagal: {e}")

else:
    print("\nGambar 4.12 dilewati. Atur GENERATE_TREE_PLOT=1 bila gambar tree diperlukan.")

# ---------------------------------------------------------
# 8.10 SIMPAN MODEL DAN LOG
# ---------------------------------------------------------
if SAVE_OUTPUT:
    model_final.save_model(f"{OUTPUT_DATASET_DIR}/model_xgboost_final.json")

    df_train_valid_pred.to_excel(
        f"{OUTPUT_DATASET_DIR}/Dataset_Training_Validation_Prediksi.xlsx",
        index=False,
    )

    df_test_pred.to_excel(
        f"{OUTPUT_DATASET_DIR}/Dataset_Testing_Prediksi.xlsx",
        index=False,
    )

    baseline_detail.to_excel(
        f"{OUTPUT_LOG_DIR}/Walk_Forward_Baseline_Detail.xlsx",
        index=False,
    )

    best_detail.to_excel(
        f"{OUTPUT_LOG_DIR}/Walk_Forward_Best_Detail.xlsx",
        index=False,
    )

    with open(f"{OUTPUT_LOG_DIR}/Best_Params_XGBoost.json", "w") as f:
        json.dump({
            "use_optuna_tuning": USE_OPTUNA_TUNING,
            "best_params": best_params,
            "best_validation_auc": best_validation_auc,
            "best_n_estimators": best_n_estimators,
            "model_feature_cols": model_feature_cols,
        }, f, indent=4)

print("=" * 70)
print("RINGKASAN BLOK 8")
print("=" * 70)
print(f"- USE_OPTUNA_TUNING  : {USE_OPTUNA_TUNING}")
print(f"- AUC validasi awal  : {format_metric(baseline_auc)}")
print(f"- AUC validasi best  : {format_metric(best_auc)}")
print(f"- Jumlah pohon final : {format_int(best_n_estimators)}")
print(f"- AUC testing preview: {format_metric(test_auc_preview)}")
print("=" * 70)


# =========================================================
# BLOK 9 - EVALUASI MODEL PADA DATA TESTING
# =========================================================
print("=" * 70)
print("BLOK 9 - EVALUASI MODEL PADA DATA TESTING")
print("=" * 70)

# ---------------------------------------------------------
# 9.1 TABEL 4.11 - EVALUASI THRESHOLD PADA DATA TESTING
# ---------------------------------------------------------
try:
    average_precision_score
except NameError:
    from sklearn.metrics import average_precision_score

try:
    brier_score_loss
except NameError:
    from sklearn.metrics import brier_score_loss

threshold_grid  = np.linspace(0.01, 0.99, 99)
threshold_table = build_threshold_table(y_test.values, y_test_proba, threshold_grid)

selected_threshold = select_threshold(threshold_table, THRESHOLD_SELECTION_METHOD)

test_auc = safe_roc_auc(y_test.values, y_test_proba)
test_ap = (
    average_precision_score(y_test.values, y_test_proba)
    if len(np.unique(y_test)) > 1 else np.nan
)
test_brier = brier_score_loss(y_test.values, y_test_proba)

def get_threshold_row(method: str, label: str) -> dict:
    thr = select_threshold(threshold_table, method)
    metrics = calculate_binary_metrics(y_test.values, y_test_proba, thr)

    return {
        "Metode Threshold": label,
        **metrics,
        "roc_auc": test_auc,
        "pr_auc": test_ap,
        "brier_score": test_brier,
    }

table_4_11 = pd.DataFrame([
    get_threshold_row("balanced_accuracy", "Best Balanced Accuracy"),
    get_threshold_row("f1", "Best F1"),
    {
        "Metode Threshold": "Default 0,50",
        **calculate_binary_metrics(y_test.values, y_test_proba, 0.50),
        "roc_auc": test_auc,
        "pr_auc": test_ap,
        "brier_score": test_brier,
    },
])

print("\nTabel 4.11 - Evaluasi Threshold pada Data Testing")

d411 = table_4_11.copy()
metric_cols_float = [
    "threshold",
    "accuracy",
    "precision",
    "recall",
    "specificity",
    "f1_score",
    "balanced_accuracy",
    "youden_j",
    "roc_auc",
    "pr_auc",
    "brier_score",
]

for col in metric_cols_float:
    d411[col] = d411[col].apply(format_metric)

for col in ["tn", "fp", "fn", "tp"]:
    d411[col] = d411[col].apply(format_int)

display(d411)
save_table(df=table_4_11, file_key="table_4_11")

selected_metrics = calculate_binary_metrics(
    y_test.values,
    y_test_proba,
    selected_threshold,
)

print(f"\nThreshold terpilih ({THRESHOLD_SELECTION_METHOD}): {format_metric(selected_threshold)}")

# ---------------------------------------------------------
# 9.2 PREDIKSI LABEL FINAL
# ---------------------------------------------------------
df_test_eval = df_test_pred.copy()
df_test_eval["used_threshold"] = selected_threshold
df_test_eval[PRED_LABEL_COL] = (
    df_test_eval[PRED_PROBA_COL] >= selected_threshold
).astype(int)

tn, fp, fn, tp = confusion_matrix(
    y_test.values,
    df_test_eval[PRED_LABEL_COL].values,
    labels=[0, 1],
).ravel()

# ---------------------------------------------------------
# 9.3 GAMBAR 4.13 - ROC CURVE PADA DATA TESTING
# ---------------------------------------------------------
print_chart_title("Gambar 4.13 - ROC Curve pada Data Testing")

if len(np.unique(y_test)) > 1:
    fpr, tpr, _ = roc_curve(y_test.values, y_test_proba)
    roc_auc_val = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, label=f"AUC = {roc_auc_val:.4f}".replace(".", ","))
    ax.plot([0, 1], [0, 1], linestyle="--")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")

    finalize_plot(fig, file_key="fig_4_13", show=True)
else:
    print("ROC Curve tidak dibuat karena data testing hanya memiliki satu kelas.")

# ---------------------------------------------------------
# 9.4 GAMBAR 4.14 - CONFUSION MATRIX PADA THRESHOLD FINAL
# ---------------------------------------------------------
print_chart_title("Gambar 4.14 - Confusion Matrix pada Threshold Final")

cm = np.array([[tn, fp], [fn, tp]])

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm)

ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(["Prediksi Non-Churn", "Prediksi Churn"])
ax.set_yticklabels(["Aktual Non-Churn", "Aktual Churn"])
ax.set_xlabel("Prediksi")
ax.set_ylabel("Aktual")

for i in range(2):
    for j in range(2):
        ax.text(
            j,
            i,
            format_int(cm[i, j]),
            ha="center",
            va="center",
            fontsize=12,
        )

fig.colorbar(im, ax=ax)
finalize_plot(fig, file_key="fig_4_14", show=True)

# ---------------------------------------------------------
# 9.5 SIMPAN HASIL EVALUASI
# ---------------------------------------------------------
if SAVE_OUTPUT:
    df_test_eval.to_excel(
        f"{OUTPUT_DATASET_DIR}/Dataset_Testing_Evaluasi_Final.xlsx",
        index=False,
    )

    threshold_table.to_excel(
        f"{OUTPUT_LOG_DIR}/Threshold_Search_Data_Testing.xlsx",
        index=False,
    )

    pd.DataFrame([selected_metrics]).to_excel(
        f"{OUTPUT_LOG_DIR}/Selected_Threshold_Metrics.xlsx",
        index=False,
    )

# ---------------------------------------------------------
# 9.6 RINGKASAN BLOK 9
# ---------------------------------------------------------
print("=" * 70)
print("RINGKASAN BLOK 9")
print("=" * 70)
print(f"- ROC-AUC testing      : {format_metric(test_auc)}")
print(f"- Threshold final      : {format_metric(selected_threshold)}")
print(f"- Accuracy             : {format_metric(selected_metrics['accuracy'])}")
print(f"- Precision            : {format_metric(selected_metrics['precision'])}")
print(f"- Recall               : {format_metric(selected_metrics['recall'])}")
print(f"- F1-score             : {format_metric(selected_metrics['f1_score'])}")
print(f"- TN / FP / FN / TP    : {format_int(tn)} / {format_int(fp)} / {format_int(fn)} / {format_int(tp)}")
print("=" * 70)


# =========================================================
# BLOK 10 - ANALISIS INTERPRETABILITAS MENGGUNAKAN SHAP
# =========================================================
print("=" * 70)
print("BLOK 10 - ANALISIS INTERPRETABILITAS MENGGUNAKAN SHAP")
print("=" * 70)

# ---------------------------------------------------------
# 10.1 HITUNG NILAI SHAP
# ---------------------------------------------------------
explainer = shap.TreeExplainer(model_final)

shap_values_raw = explainer.shap_values(X_test[model_feature_cols])

if isinstance(shap_values_raw, list):
    shap_values = shap_values_raw[1]
else:
    shap_values = shap_values_raw

shap_values = np.asarray(shap_values)

if shap_values.ndim != 2:
    raise ValueError(f"Format SHAP tidak sesuai. Dimensi: {shap_values.shape}")

expected_value_raw = explainer.expected_value
expected_value = float(np.asarray(expected_value_raw).ravel()[-1]) \
    if isinstance(expected_value_raw, (list, np.ndarray)) else float(expected_value_raw)

print(f"Dimensi SHAP   : {shap_values.shape}")
print(f"Expected value : {format_metric(expected_value)}")

# ---------------------------------------------------------
# 10.2 TABEL 4.12 - MEAN ABSOLUTE FITUR
# ---------------------------------------------------------
mean_abs_shap = np.abs(shap_values).mean(axis=0)
mean_shap     = shap_values.mean(axis=0)

table_4_12 = pd.DataFrame({
    "Peringkat":      np.arange(1, len(model_feature_cols) + 1),
    "Fitur":          model_feature_cols,
    "Deskripsi":      [FEATURE_DESCRIPTION_MAP.get(c, "-") for c in model_feature_cols],
    "Mean Abs. SHAP": mean_abs_shap,
    "Mean SHAP":      mean_shap,
})

table_4_12 = table_4_12.sort_values("Mean Abs. SHAP", ascending=False).reset_index(drop=True)
table_4_12["Peringkat"] = np.arange(1, len(table_4_12) + 1)

print("\nTabel 4.12 - Mean Absolute Fitur")

d412 = table_4_12.copy()
d412["Mean Abs. SHAP"] = d412["Mean Abs. SHAP"].apply(format_decimal)
d412["Mean SHAP"]      = d412["Mean SHAP"].apply(format_decimal)

display(d412)
save_table(df=table_4_12, file_key="table_4_12")

if GENERATE_SHAP_PLOTS:
    # ---------------------------------------------------------
    # 10.3 GAMBAR 4.15 - SHAP IMPORTANCE PLOT
    # ---------------------------------------------------------
    print_chart_title("Gambar 4.15 - SHAP Importance Plot")

    plot_importance = table_4_12.head(15).sort_values("Mean Abs. SHAP", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(plot_importance["Fitur"], plot_importance["Mean Abs. SHAP"])
    ax.set_xlabel("Mean Absolute SHAP Value")
    ax.set_ylabel("Fitur")
    ax.grid(axis="x", alpha=0.3)

    add_value_labels_to_horizontal_bars(ax, fmt="decimal")
    finalize_plot(fig, file_key="fig_4_15", show=True)

else:
    print("\nGambar 4.15 dilewati. Atur GENERATE_SHAP_PLOTS=1 bila gambar SHAP diperlukan.")

if GENERATE_SHAP_PLOTS:
    # ---------------------------------------------------------
    # 10.4 GAMBAR 4.16 - SHAP SUMMARY PLOT
    # ---------------------------------------------------------
    print_chart_title("Gambar 4.16 - SHAP Summary Plot")

    plt.figure(figsize=(10, 6))

    shap.summary_plot(
        shap_values,
        X_test[model_feature_cols],
        feature_names=[DISPLAY_NAME_MAP.get(c, c) for c in model_feature_cols],
        show=False,
        max_display=min(15, len(model_feature_cols)),
    )

    fig = plt.gcf()

    if SAVE_OUTPUT:
        fig.savefig(
            f"{OUTPUT_FIG_DIR}/{FIG_FILE_MAP.get('fig_4_16', 'Gambar_4_16_SHAP_Summary_Plot')}.png",
            dpi=200,
            bbox_inches="tight",
        )

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(fig)

else:
    print("\nGambar 4.16 dilewati. Atur GENERATE_SHAP_PLOTS=1 bila gambar SHAP diperlukan.")

# ---------------------------------------------------------
# 10.5 PILIH OBSERVASI UNTUK INTERPRETASI LOKAL
# ---------------------------------------------------------
df_local_cand = df_test_eval.copy()
df_local_cand["_row_idx"] = np.arange(len(df_local_cand))

predicted_positive = df_local_cand[df_local_cand[PRED_LABEL_COL] == 1].copy()

local_row = (
    predicted_positive.sort_values(PRED_PROBA_COL, ascending=False).iloc[0]
    if len(predicted_positive) > 0
    else df_local_cand.sort_values(PRED_PROBA_COL, ascending=False).iloc[0]
)

local_idx = int(local_row["_row_idx"])
local_customer_id = local_row[COL_ID]
local_score = float(local_row[PRED_PROBA_COL])
local_actual = int(local_row["churn"])
local_pred = int(local_row[PRED_LABEL_COL])

local_shap_values = shap_values[local_idx, :]
local_feat_values = X_test.iloc[local_idx][model_feature_cols]

print(
    f"\nObservasi lokal: ID={local_customer_id} | "
    f"skor={format_metric(local_score)} | "
    f"aktual={CHURN_LABEL_MAP.get(local_actual)} | "
    f"prediksi={CHURN_LABEL_MAP.get(local_pred)}"
)

if GENERATE_SHAP_PLOTS:
    # ---------------------------------------------------------
    # 10.6 GAMBAR 4.17 - SHAP LOCAL WATERFALL PLOT
    # ---------------------------------------------------------
    print_chart_title("Gambar 4.17 - SHAP Local Waterfall Plot")

    try:
        shap_explanation = shap.Explanation(
            values=local_shap_values,
            base_values=expected_value,
            data=local_feat_values.values,
            feature_names=[DISPLAY_NAME_MAP.get(c, c) for c in model_feature_cols],
        )

        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(
            shap_explanation,
            max_display=min(10, len(model_feature_cols)),
            show=False,
        )

        fig = plt.gcf()

        if SAVE_OUTPUT:
            fig.savefig(
                f"{OUTPUT_FIG_DIR}/{FIG_FILE_MAP.get('fig_4_17', 'Gambar_4_17_SHAP_Local_Waterfall_Plot')}.png",
                dpi=200,
                bbox_inches="tight",
            )

        if SHOW_PLOTS:
            plt.show()
        else:
            plt.close(fig)

    except Exception as e:
        print(f"Waterfall plot gagal, gunakan alternatif. Error: {e}")

        local_driver_df = pd.DataFrame({
            "Fitur": model_feature_cols,
            "SHAP Value": local_shap_values,
        }).sort_values("SHAP Value", ascending=True)

        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(local_driver_df["Fitur"], local_driver_df["SHAP Value"])
        ax.set_xlabel("SHAP Value")
        ax.set_ylabel("Fitur")
        ax.grid(axis="x", alpha=0.3)

        finalize_plot(fig, file_key="fig_4_17", show=True)

else:
    print("\nGambar 4.17 dilewati. Atur GENERATE_SHAP_PLOTS=1 bila gambar SHAP diperlukan.")

if GENERATE_SHAP_PLOTS:
    # ---------------------------------------------------------
    # 10.7 GAMBAR 4.18 - SHAP LOCAL FORCE PLOT
    # ---------------------------------------------------------
    print_chart_title("Gambar 4.18 - SHAP Local Force Plot")

    try:
        plt.figure(figsize=(10, 3))

        shap.force_plot(
            expected_value,
            local_shap_values,
            local_feat_values,
            feature_names=[DISPLAY_NAME_MAP.get(c, c) for c in model_feature_cols],
            matplotlib=True,
            show=False,
        )

        fig = plt.gcf()

        if SAVE_OUTPUT:
            fig.savefig(
                f"{OUTPUT_FIG_DIR}/{FIG_FILE_MAP.get('fig_4_18', 'Gambar_4_18_SHAP_Local_Force_Plot')}.png",
                dpi=200,
                bbox_inches="tight",
            )

        if SHOW_PLOTS:
            plt.show()
        else:
            plt.close(fig)

    except Exception as e:
        print(f"Force plot gagal, gunakan alternatif. Error: {e}")

        local_driver_df2 = pd.DataFrame({
            "Fitur": model_feature_cols,
            "SHAP Value": local_shap_values,
        }).sort_values("SHAP Value", ascending=True)

        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(local_driver_df2["Fitur"], local_driver_df2["SHAP Value"])
        ax.set_xlabel("SHAP Value")
        ax.set_ylabel("Fitur")
        ax.grid(axis="x", alpha=0.3)

        finalize_plot(fig, file_key="fig_4_18", show=True)

else:
    print("\nGambar 4.18 dilewati. Atur GENERATE_SHAP_PLOTS=1 bila gambar SHAP diperlukan.")

# ---------------------------------------------------------
# 10.8 SIMPAN HASIL SHAP
# ---------------------------------------------------------
df_test_shap_detail = df_test_eval.copy()

for i, feat in enumerate(model_feature_cols):
    df_test_shap_detail[f"shap_{feat}"] = shap_values[:, i]

if SAVE_OUTPUT:
    df_test_shap_detail.to_excel(
        f"{OUTPUT_DATASET_DIR}/Dataset_Testing_SHAP_Detail.xlsx",
        index=False,
    )

    table_4_12.to_excel(
        f"{OUTPUT_TABLE_DIR}/{TABLE_FILE_MAP.get('table_4_12', 'Tabel_4_12_Mean_Absolute_Fitur')}.xlsx",
        index=False,
    )

top_features_text = ", ".join(table_4_12.head(5)["Fitur"].tolist())

print("=" * 70)
print("RINGKASAN BLOK 10")
print("=" * 70)
print(f"- Fitur paling berpengaruh: {top_features_text}")
print(f"- Contoh lokal ID customer: {local_customer_id}")
print("=" * 70)


# =========================================================
# BLOK 11 - SCORING CUSTOMER AKTIF
# =========================================================
print("=" * 70)
print("BLOK 11 - SCORING CUSTOMER AKTIF")
print("=" * 70)

if len(df_scoring_final) == 0:
    raise ValueError("Data scoring kosong.")

# ---------------------------------------------------------
# 11.0 FALLBACK SEGMENTASI RISIKO
# ---------------------------------------------------------
if "assign_risk_segment" not in globals():
    def assign_risk_segment(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out = out.sort_values(PRED_PROBA_COL, ascending=False).reset_index(drop=True)

        n_scoring = len(out)
        high_n_abs = int(np.ceil(n_scoring * HIGH_RISK_TOP_PCT))
        medium_n_abs = int(np.ceil(n_scoring * MEDIUM_RISK_NEXT_PCT))

        out["risk_rank"] = np.arange(1, n_scoring + 1)
        out["risk_segment"] = "Risiko Rendah"

        if high_n_abs > 0:
            out.loc[0:high_n_abs - 1, "risk_segment"] = "Risiko Tinggi"

        if medium_n_abs > 0:
            out.loc[high_n_abs:high_n_abs + medium_n_abs - 1, "risk_segment"] = "Risiko Sedang"

        return out

if "RISK_SEGMENT_SHORT_MAP" not in globals():
    RISK_SEGMENT_SHORT_MAP = {
        "Risiko Tinggi": "Tinggi",
        "Risiko Sedang": "Sedang",
        "Risiko Rendah": "Rendah",
    }

# ---------------------------------------------------------
# 11.1 PREDIKSI SKOR CHURN
# ---------------------------------------------------------
X_scoring_aligned = df_scoring_final[model_feature_cols].copy()

dscoring = xgb.DMatrix(
    X_scoring_aligned,
    feature_names=model_feature_cols,
)

scoring_proba = model_final.predict(dscoring)

df_scoring_pred = df_scoring_final.copy()
df_scoring_pred["_scoring_row_id"] = np.arange(len(df_scoring_pred))
df_scoring_pred[PRED_PROBA_COL] = scoring_proba
df_scoring_pred["used_threshold"] = selected_threshold
df_scoring_pred[PRED_LABEL_COL] = (
    df_scoring_pred[PRED_PROBA_COL] >= selected_threshold
).astype(int)

df_scoring_ranked = assign_risk_segment(df=df_scoring_pred)

# ---------------------------------------------------------
# 11.2 DRIVER SHAP UNTUK DATA SCORING
# ---------------------------------------------------------
shap_scoring_raw = explainer.shap_values(X_scoring_aligned[model_feature_cols])

shap_scoring_values = np.asarray(
    shap_scoring_raw[1] if isinstance(shap_scoring_raw, list)
    else shap_scoring_raw
)

if shap_scoring_values.ndim != 2:
    raise ValueError(f"Format SHAP scoring tidak sesuai. Dimensi: {shap_scoring_values.shape}")

driver_rows = []

for row_idx in range(len(df_scoring_ranked)):
    orig_idx = int(df_scoring_ranked.iloc[row_idx]["_scoring_row_id"])
    row_shap = shap_scoring_values[orig_idx, :]
    abs_order = np.argsort(np.abs(row_shap))[::-1]

    d = {
        "_scoring_row_id": orig_idx,
    }

    for rank_idx in range(min(3, len(model_feature_cols))):
        feat_idx = abs_order[rank_idx]
        feat = model_feature_cols[feat_idx]

        d[f"driver_{rank_idx + 1}_feature"] = feat
        d[f"driver_{rank_idx + 1}_description"] = FEATURE_DESCRIPTION_MAP.get(feat, "-")
        d[f"driver_{rank_idx + 1}_value"] = X_scoring_aligned.iloc[orig_idx][feat]
        d[f"driver_{rank_idx + 1}_shap"] = round(float(row_shap[feat_idx]), 4)
        d[f"driver_{rank_idx + 1}_direction"] = (
            "Menaikkan skor churn"
            if row_shap[feat_idx] > 0
            else "Menurunkan skor churn"
        )

    driver_rows.append(d)

df_scoring_driver = pd.DataFrame(driver_rows)

driver_merge_cols = ["_scoring_row_id"] + [
    c for c in df_scoring_driver.columns
    if c.startswith("driver_")
]

df_scoring_ranked = df_scoring_ranked.merge(
    df_scoring_driver[driver_merge_cols],
    on="_scoring_row_id",
    how="left",
)

# ---------------------------------------------------------
# 11.3 TABEL 4.13 - RINGKASAN HASIL SCORING
# ---------------------------------------------------------
score_mean = float(df_scoring_ranked[PRED_PROBA_COL].mean())
score_median = float(df_scoring_ranked[PRED_PROBA_COL].median())
score_min = float(df_scoring_ranked[PRED_PROBA_COL].min())
score_max = float(df_scoring_ranked[PRED_PROBA_COL].max())

n_pred_churn = int(df_scoring_ranked[PRED_LABEL_COL].sum())
n_pred_non_churn = int(len(df_scoring_ranked) - n_pred_churn)

table_4_13 = pd.DataFrame({
    "Metrik": [
        "Jumlah Observasi Scoring",
        "Jumlah Customer Unik",
        "Rata-rata Skor Churn",
        "Median Skor Churn",
        "Skor Minimum",
        "Skor Maksimum",
        "Prediksi Churn (berdasarkan threshold)",
        "Prediksi Non-Churn (berdasarkan threshold)",
        "Threshold Klasifikasi",
    ],
    "Nilai": [
        len(df_scoring_ranked),
        df_scoring_ranked[COL_ID].nunique(),
        round(score_mean, 4),
        round(score_median, 4),
        round(score_min, 4),
        round(score_max, 4),
        n_pred_churn,
        n_pred_non_churn,
        round(float(selected_threshold), 4),
    ],
})

print("\nTabel 4.13 - Ringkasan Hasil Scoring")
display(table_4_13)
save_table(df=table_4_13, file_key="table_4_13")

# ---------------------------------------------------------
# 11.4 TABEL 4.14 - SEGMENTASI RISIKO CUSTOMER BERDASARKAN SKOR CHURN
# ---------------------------------------------------------
segment_order_map = {
    "Risiko Tinggi": 1,
    "Risiko Sedang": 2,
    "Risiko Rendah": 3,
}

table_4_14 = (
    df_scoring_ranked
    .groupby("risk_segment", as_index=False)
    .agg(
        jumlah_observasi=(COL_ID, "size"),
        jumlah_customer=(COL_ID, "nunique"),
        rata_rata_skor=(PRED_PROBA_COL, "mean"),
        median_skor=(PRED_PROBA_COL, "median"),
        skor_min=(PRED_PROBA_COL, "min"),
        skor_max=(PRED_PROBA_COL, "max"),
    )
)

table_4_14["persentase_observasi"] = (
    table_4_14["jumlah_observasi"]
    / table_4_14["jumlah_observasi"].sum()
    * 100
)

table_4_14["_order"] = table_4_14["risk_segment"].map(segment_order_map)

table_4_14 = (
    table_4_14
    .sort_values("_order")
    .drop(columns="_order")
    .reset_index(drop=True)
)

table_4_14 = table_4_14.rename(columns={
    "risk_segment": "Segmen Risiko",
    "jumlah_observasi": "Jumlah Observasi",
    "jumlah_customer": "Jumlah Customer",
    "rata_rata_skor": "Rata-rata Skor",
    "median_skor": "Median Skor",
    "skor_min": "Skor Min",
    "skor_max": "Skor Maks",
    "persentase_observasi": "Persentase (%)",
})

print("\nTabel 4.14 - Segmentasi Risiko Customer Berdasarkan Skor Churn")

d414 = table_4_14.copy()

for col in ["Jumlah Observasi", "Jumlah Customer"]:
    d414[col] = d414[col].apply(format_int)

for col in ["Rata-rata Skor", "Median Skor", "Skor Min", "Skor Maks"]:
    d414[col] = d414[col].apply(format_metric)

d414["Persentase (%)"] = d414["Persentase (%)"].apply(format_percent)

display(d414)
save_table(df=table_4_14, file_key="table_4_14")

# ---------------------------------------------------------
# 11.5 TABEL 4.15 - CONTOH CUSTOMER PADA SEGMEN RISIKO churn TINGGI
# ---------------------------------------------------------
high_risk_df = (
    df_scoring_ranked[df_scoring_ranked["risk_segment"] == "Risiko Tinggi"]
    .sort_values(PRED_PROBA_COL, ascending=False)
    .copy()
)

table_4_15 = pd.DataFrame({
    "ID Customer": high_risk_df[COL_ID].head(7).values,
    "Skor Churn": high_risk_df[PRED_PROBA_COL].head(7).values,
    "Peringkat Risiko": high_risk_df["risk_rank"].head(7).values,
    "Segmen Risiko": (
        high_risk_df["risk_segment"]
        .head(7)
        .map(RISK_SEGMENT_SHORT_MAP)
        .fillna(high_risk_df["risk_segment"].head(7))
        .values
    ),
    "Driver 1": high_risk_df["driver_1_feature"].head(7).values,
    "Driver 2": high_risk_df["driver_2_feature"].head(7).values,
    "Driver 3": high_risk_df["driver_3_feature"].head(7).values,
})

print("\nTabel 4.15 - Contoh Customer pada Segmen Risiko churn Tinggi")

d415 = table_4_15.copy()
d415["Skor Churn"] = d415["Skor Churn"].apply(format_metric)
d415["Peringkat Risiko"] = d415["Peringkat Risiko"].apply(format_int)

display(d415)
save_table(df=table_4_15, file_key="table_4_15")

# ---------------------------------------------------------
# 11.6 GAMBAR 4.19 - HISTOGRAM SKOR CHURN PADA DATA SCORING
# ---------------------------------------------------------
print_chart_title("Gambar 4.19 - Histogram Skor Churn pada Data Scoring")

fig, ax = plt.subplots(figsize=(8, 5))

ax.hist(df_scoring_ranked[PRED_PROBA_COL], bins=20)
ax.axvline(
    selected_threshold,
    linestyle="--",
    label=f"Threshold ({format_metric(selected_threshold)})",
)

ax.set_xlabel("Skor Churn")
ax.set_ylabel("Jumlah Observasi")
ax.grid(axis="y", alpha=0.3)
ax.legend()

finalize_plot(fig, file_key="fig_4_19", show=True)

# ---------------------------------------------------------
# 11.7 GAMBAR 4.20 - JUMLAH CUSTOMER PER SEGMEN RISIKO
# ---------------------------------------------------------
print_chart_title("Gambar 4.20 - Jumlah Customer per Segmen Risiko")

fig, ax = plt.subplots(figsize=(7, 5))

ax.bar(table_4_14["Segmen Risiko"], table_4_14["Jumlah Customer"])
ax.set_xlabel("Segmen Risiko")
ax.set_ylabel("Jumlah Customer")
ax.grid(axis="y", alpha=0.3)

add_value_labels_to_bars(ax, fmt="int")
finalize_plot(fig, file_key="fig_4_20", show=True)

# ---------------------------------------------------------
# 11.8 SIMPAN HASIL SCORING
# ---------------------------------------------------------
df_scoring_export = df_scoring_ranked.drop(
    columns=["_scoring_row_id"],
    errors="ignore",
)

if SAVE_OUTPUT:
    df_scoring_export.to_excel(
        f"{OUTPUT_SCORING_DIR}/Scoring_Customer_Aktif_Lengkap.xlsx",
        index=False,
    )

    df_scoring_export.to_csv(
        f"{OUTPUT_SCORING_DIR}/Scoring_Customer_Aktif_Lengkap.csv",
        index=False,
        encoding="utf-8-sig",
    )

    table_4_15.to_excel(
        f"{OUTPUT_SCORING_DIR}/Contoh_Customer_Risiko_Tinggi.xlsx",
        index=False,
    )

# ---------------------------------------------------------
# 11.9 RINGKASAN BLOK 11
# ---------------------------------------------------------
n_high = int((df_scoring_ranked["risk_segment"] == "Risiko Tinggi").sum())
n_medium = int((df_scoring_ranked["risk_segment"] == "Risiko Sedang").sum())
n_low = int((df_scoring_ranked["risk_segment"] == "Risiko Rendah").sum())

print("=" * 70)
print("RINGKASAN BLOK 11")
print("=" * 70)
print(f"- Observasi scoring    : {format_int(len(df_scoring_ranked))}")
print(f"- Rata-rata skor churn : {format_metric(score_mean)}")
print(f"- Median skor churn    : {format_metric(score_median)}")
print(f"- Threshold            : {format_metric(selected_threshold)}")
print(f"- Prediksi Churn       : {format_int(n_pred_churn)}")
print(f"- Prediksi Non-Churn   : {format_int(n_pred_non_churn)}")
print(f"- Risiko Tinggi        : {format_int(n_high)}")
print(f"- Risiko Sedang        : {format_int(n_medium)}")
print(f"- Risiko Rendah        : {format_int(n_low)}")
print("=" * 70)

