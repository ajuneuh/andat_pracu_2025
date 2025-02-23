import os
import sys
import cv2
import numpy as np
import requests
from datetime import datetime, timedelta, timezone

def download_image(url, save_path):
    try:
        print(f"Mulai mengunduh: {url}")  # Debug tambahan
        for attempt in range(3):  # Coba maksimal 3 kali
            response = requests.get(url, stream=True, timeout=10)
            print(f"Percobaan {attempt+1}: Status kode {response.status_code}")  # Debug tambahan
            if response.status_code == 200:
                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Berhasil mengunduh: {save_path}")
                return True
        print(f"Gagal mengunduh {url} setelah 3 percobaan")
        return False
    except requests.RequestException as e:
        print(f"Error saat mengunduh {save_path}: {e}")
        return False

def analyze_rainfall(image_path, pixel_coord):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    b, g, r, a = image[pixel_coord[1], pixel_coord[0]]  # OpenCV uses BGR
    color = (r, g, b)
    
    rainfall_levels = {
        (0, 0, 0): "0.0-0.5mm",
        (0, 255, 255): "0.5-1mm",
        (0, 230, 255): "1.0-1.5mm",
        (0, 206, 255): "1.5-2mm",
        (0, 181, 255): "2.0-2.5mm",
        (0, 156, 255): "2.5-3.5mm",
        (0, 131, 255): "3.5-4mm",
        (0, 107, 255): "4.0-4.5mm",
        (0, 82, 255): "4.5-5mm",
        (0, 57, 255): "5.0-7.5mm",
        (0, 46, 235): "7.5-10mm",
        (0, 39, 207): "10.0-15mm",
        (0, 32, 180): "15.0-20mm",
        (0, 26, 153): "20.0-25mm",
        (0, 19, 126): "25.0-30mm",
        (0, 12, 99): "30.0-40mm",
        (0, 5, 71): "40.0mm--"
    }
    
    return rainfall_levels.get(color, "0.0-0.5mm")

def draw_rectangle(image_path, top_left, bottom_right, save_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 255, 255), 2)
    cv2.imwrite(save_path, image)

def download_wrf_images(output_folder):
    base_url = "http://nimbus.meteo.itb.ac.id/weather/model/wrf_new/cy00/d02/rainuv10/"
    filename_template = "wrf-00-rainuv10-{datetime}.png"
    
    execution_date = datetime.now(timezone.utc)
    start_dt = execution_date + timedelta(days=1, hours=7)  # D+1 07:00 UTC
    end_dt = execution_date + timedelta(days=2, hours=7)    # D+2 07:00 UTC
    
    save_dir = os.path.join(output_folder, execution_date.strftime("%Y-%m-%d"))
    os.makedirs(save_dir, exist_ok=True)
    
    current_dt = start_dt
    while current_dt <= end_dt:
        if current_dt.hour % 3 == 1 or current_dt.hour % 3 == 4 or current_dt.hour % 3 == 7:
            datetime_str = current_dt.strftime("%Y%m%d_%H")
            filename = filename_template.format(datetime=datetime_str)
            file_url = base_url + filename
            file_full_path = os.path.join(save_dir, filename)
            
            if download_image(file_url, file_full_path):
                pixel_coord = (332, 246)
                rainfall = analyze_rainfall(file_full_path, pixel_coord)
                
                top_left = (327, 242)
                bottom_right = (335, 250)
                
                new_filename = filename.replace(".png", f"--{rainfall}.png")
                save_path = os.path.join(save_dir, new_filename)
                draw_rectangle(file_full_path, top_left, bottom_right, save_path)
                print(f"Gambar disimpan sebagai {save_path}")
        
        current_dt += timedelta(hours=3)

if __name__ == "__main__":
    # Ambil argumen folder dari GitHub Actions, atau default ke YYYY-MM-DD hari ini
    if len(sys.argv) > 1:
        folder_name = sys.argv[1]
    else:
        folder_name = datetime.utcnow().strftime("%Y-%m-%d")

    download_wrf_images(folder_name)
