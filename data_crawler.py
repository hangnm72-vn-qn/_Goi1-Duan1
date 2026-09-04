import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
# Thư mục lưu dữ liệu
RAW_DIR = Path("data/raw")
EXTRACT_DIR = Path("data/extracted")

# Tự động tạo thư mục nếu chưa có
RAW_DIR.mkdir(parents=True, exist_ok=True)
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

print("Data crawler initialized!")

# DETECT FILE DỮ LIỆU MỚI NHẤT TỪ CAFEF

CAFЕF_URL = "https://cafef.vn/du-lieu/du-lieu-download.chn"

def detect_latest_file():
    print("\nĐang tìm file dữ liệu mới nhất trên CafeF...")

    response = requests.get(
        CAFЕF_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    candidates = []

    # Tìm tất cả các link trên trang CafeF
    for link in soup.find_all("a", href=True):

        href = link["href"]
        text = link.get_text(" ", strip=True)

        # Chỉ lấy link có chữ "Upto 3 sàn"
        if "Upto 3 sàn" not in text:
            continue

        # Chỉ lấy file ZIP
        if not href.lower().endswith(".zip"):
            continue

        # Bỏ dữ liệu chưa điều chỉnh
        if ".Raw." in href:
            continue

        # Tìm ngày trong đường dẫn
        match = re.search(
            r"(\d{8})",
            href
        )

        if match:

            date_str = match.group(1)

            candidates.append({
                "date": date_str,
                "url": urljoin(CAFЕF_URL, href)
            })

    # Không tìm thấy file
    if not candidates:
        raise RuntimeError(
            "Không tìm thấy file Upto 3 sàn trên CafeF."
        )

    # Chọn file có ngày mới nhất
    latest = max(
        candidates,
        key=lambda x: x["date"]
    )

    print("✓ Đã phát hiện file mới nhất")
    print("  Ngày:", latest["date"])
    print("  URL :", latest["url"])
         
    return latest["date"], latest["url"]

print("TEST DETECT")

detect_latest_file()

# DOWNLOAD FILE

def download_file(date_str, url):
    print("\nĐang tải file dữ liệu...")

    filename = url.split("/")[-1]
    output_path = RAW_DIR / filename

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        stream=True,
        timeout=60
    )

    response.raise_for_status()

    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    print("✓ Tải file thành công")
    print("  File:", output_path)

    return output_path

# EXTRACT FILE

def extract_file(zip_path, date_str):
    print("\nĐang giải nén file...")

    extract_path = EXTRACT_DIR / date_str
    extract_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    print("✓ Giải nén thành công")
    print("  Thư mục:", extract_path)

    return extract_path

# VALIDATE FILES

def validate_files(extract_path):
    print("\nĐang kiểm tra dữ liệu...")

    expected_files = [
        "CafeF.HSX.Upto03.09.2026.csv",
        "CafeF.HNX.Upto03.09.2026.csv",
        "CafeF.UPCOM.Upto03.09.2026.csv"
    ]

    for filename in expected_files:
        file_path = extract_path / filename

        if file_path.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ Thiếu: {filename}")
            raise FileNotFoundError(
                f"Không tìm thấy file: {filename}"
            )

    print("\n✓ VALIDATE THÀNH CÔNG — Đủ dữ liệu 3 sàn!")

    return True


# MAIN

def main():
    ...
    date_str, url = detect_latest_file()
    zip_path = download_file(date_str, url)
    extract_path = extract_file(zip_path, date_str)
    validate_files(extract_path)

    print("\n✓ DATA CRAWLER HOÀN TẤT!")


if __name__ == "__main__":
    main()