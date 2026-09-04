import sqlite3
from pathlib import Path
import pandas as pd


# =========================================================
# 1. XÁC ĐỊNH THƯ MỤC DỮ LIỆU
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

EXTRACT_DIR = BASE_DIR / "data" / "extracted"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATABASE_DIR = BASE_DIR / "data" / "database"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. TÌM THƯ MỤC DỮ LIỆU MỚI NHẤT
# =========================================================

def get_latest_extracted_dir():

    subdirs = [
        d for d in EXTRACT_DIR.iterdir()
        if d.is_dir()
    ]

    if not subdirs:
        raise FileNotFoundError(
            "Không tìm thấy thư mục dữ liệu trong "
            "data/extracted. Hãy chạy data_crawler.py trước."
        )

    latest_dir = max(
        subdirs,
        key=lambda x: x.name
    )

    print(
        f"1. Phát hiện dữ liệu mới nhất tại: {latest_dir}"
    )

    return latest_dir


# =========================================================
# 3. ĐỌC VÀ HỢP NHẤT DỮ LIỆU 3 SÀN
# =========================================================

def clean_and_merge_data():

    data_dir = get_latest_extracted_dir()

    search_patterns = {
        "HOSE": "*HSX*.csv",
        "HNX": "*HNX*.csv",
        "UPCOM": "*UPCOM*.csv"
    }

    dfs = []

    print(
        "\n2. Đang đọc và hợp nhất dữ liệu 3 sàn..."
    )

    for exchange, pattern in search_patterns.items():

        files = list(
            data_dir.glob(pattern)
        )

        if not files:
            print(
                f"   ! Không tìm thấy file {exchange}"
            )
            continue

        for filepath in files:

            print(
                f"   -> Đang đọc {exchange}: "
                f"{filepath.name}"
            )

            df = pd.read_csv(
                filepath,
                encoding="utf-8-sig"
            )

            # Xóa khoảng trắng thừa ở tên cột
            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            # Chuẩn hóa tên cột
            column_mapping = {
                "<Ticker>": "Ticker",
                "<DTYYYYMMDD>": "Date",
                "<Open>": "Open",
                "<High>": "High",
                "<Low>": "Low",
                "<Close>": "Close",
                "<Volume>": "Volume"
            }

            df = df.rename(
                columns=column_mapping
            )

            # Kiểm tra các cột bắt buộc
            required_columns = [
                "Ticker",
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]

            missing_columns = [
                col
                for col in required_columns
                if col not in df.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"{filepath.name} thiếu cột: "
                    f"{missing_columns}"
                )

            # Thêm tên sàn
            df["Exchange"] = exchange

            dfs.append(df)

    if not dfs:
        raise FileNotFoundError(
            "Không tìm thấy file CSV dữ liệu thô!"
        )

    # Hợp nhất 3 sàn
    full_df = pd.concat(
        dfs,
        ignore_index=True
    )

    print(
        f"   => Tổng dữ liệu thô: "
        f"{len(full_df):,} dòng"
    )


    # =====================================================
    # 4. LÀM SẠCH DỮ LIỆU
    # =====================================================

    print(
        "\n3. Đang thực hiện làm sạch dữ liệu..."
    )


    # -----------------------------------------------------
    # 4.1. Chuẩn hóa ngày
    # -----------------------------------------------------

    full_df["Date"] = pd.to_datetime(
        full_df["Date"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )


    # -----------------------------------------------------
    # 4.2. Chuyển dữ liệu giá và khối lượng sang số
    # -----------------------------------------------------

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    for column in numeric_columns:

        full_df[column] = pd.to_numeric(
            full_df[column],
            errors="coerce"
        )


    # -----------------------------------------------------
    # 4.3. Xóa dữ liệu bị thiếu
    # -----------------------------------------------------

    before = len(full_df)

    full_df = full_df.dropna(
        subset=[
            "Ticker",
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]
    )

    print(
        f"   -> Loại dữ liệu thiếu: "
        f"{before - len(full_df):,} dòng"
    )


    # -----------------------------------------------------
    # 4.4. Xóa dữ liệu trùng
    # -----------------------------------------------------

    before = len(full_df)

    full_df = full_df.drop_duplicates(
        subset=[
            "Ticker",
            "Exchange",
            "Date"
        ]
    )

    print(
        f"   -> Loại dữ liệu trùng: "
        f"{before - len(full_df):,} dòng"
    )


    # -----------------------------------------------------
    # 4.5. Kiểm tra dữ liệu giá
    # -----------------------------------------------------

    before = len(full_df)

    valid_condition = (
        (full_df["Open"] > 0) &
        (full_df["High"] > 0) &
        (full_df["Low"] > 0) &
        (full_df["Close"] > 0) &
        (full_df["Volume"] >= 0) &
        (full_df["High"] >= full_df["Open"]) &
        (full_df["High"] >= full_df["Close"]) &
        (full_df["High"] >= full_df["Low"]) &
        (full_df["Low"] <= full_df["Open"]) &
        (full_df["Low"] <= full_df["Close"])
    )

    full_df = full_df[
        valid_condition
    ].copy()

    print(
        f"   -> Loại dữ liệu giá không hợp lệ: "
        f"{before - len(full_df):,} dòng"
    )


    # -----------------------------------------------------
    # 4.6. Sắp xếp dữ liệu
    # -----------------------------------------------------

    full_df = full_df.sort_values(
        by=[
            "Exchange",
            "Ticker",
            "Date"
        ]
    ).reset_index(drop=True)


    # -----------------------------------------------------
    # 4.7. Đưa thứ tự cột về chuẩn
    # -----------------------------------------------------

    columns = [
        "Ticker",
        "Exchange",
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    full_df = full_df[columns]


    print(
        f"\n   => HOÀN TẤT LÀM SẠCH: "
        f"{len(full_df):,} dòng dữ liệu!"
    )

    return full_df


# =========================================================
# 5. LƯU DỮ LIỆU
# =========================================================

def save_to_database(df):

    print(
        "\n4. Đang lưu dữ liệu..."
    )


    # =====================================================
    # A. LƯU CSV
    # =====================================================

    csv_path = (
        PROCESSED_DIR /
        "cleaned_stock_data.csv"
    )

    df_to_save = df.copy()

    df_to_save["Date"] = (
        df_to_save["Date"]
        .dt.strftime("%Y-%m-%d")
    )

    df_to_save.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"   ✓ Đã xuất CSV: {csv_path}"
    )


    # =====================================================
    # B. LƯU SQLITE
    # =====================================================

    db_path = (
        DATABASE_DIR /
        "stock_database.db"
    )

    conn = sqlite3.connect(
        db_path
    )

    df_to_save.to_sql(
        "stock_prices",
        conn,
        if_exists="replace",
        index=False
    )

    conn.close()

    print(
        f"   ✓ Đã lưu SQLite: {db_path}"
    )
    print(
        "     Bảng: stock_prices"
    )


    # =====================================================
    # C. LƯU PARQUET
    # =====================================================

    parquet_path = (
        PROCESSED_DIR /
        "cleaned_stock_data.parquet"
    )

    try:

        df.to_parquet(
            parquet_path,
            index=False
        )

        print(
            f"   ✓ Đã xuất Parquet: "
            f"{parquet_path}"
        )

    except ImportError:

        print(
            "   ! Chưa cài thư viện Parquet."
        )
        print(
            "   ! Có thể bỏ qua Parquet, "
            "CSV và SQLite vẫn được lưu."
        )


# =========================================================
# 6. MAIN
# =========================================================

if __name__ == "__main__":

    try:

        print("\n" + "=" * 60)
        print(
            "TV2 - DATA PROCESSING & DATABASE"
        )
        print("=" * 60)

        df_clean = clean_and_merge_data()

        save_to_database(
            df_clean
        )

        print("\n" + "=" * 60)
        print(
            "✅ TV2 HOÀN THÀNH NHIỆM VỤ 2!"
        )
        print(
            "Dữ liệu đã được làm sạch, "
            "chuẩn hóa và lưu vào CSDL."
        )
        print("=" * 60)

    except Exception as e:

        print(
            f"\n❌ LỖI: {e}"
        )