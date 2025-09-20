import random
import string
import tkinter as tk
import time
import os
import io
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import pytesseract
from datetime import datetime
import threading

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# -----------------------------
# Google Drive Setup
# -----------------------------
SERVICE_ACCOUNT_FILE = "pmc-storage-cf6ac4dc51db.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=creds)

# -----------------------------
# Generate device code
# -----------------------------
def generate_device_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# -----------------------------
# Parent folder (shared)
# -----------------------------
PARENT_FOLDER_ID = "1imrbLP1qe-ZegYBCntQsZ9D4uFE0J7Il"

# -----------------------------
# Create folder on Drive
# -----------------------------
def create_drive_folder(folder_name):
    results = drive_service.files().list(
        q=f"name='{folder_name}' and '{PARENT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    items = results.get("files", [])
    if items:
        return items[0]['id']
    else:
        folder = drive_service.files().create(
            body={'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents':[PARENT_FOLDER_ID]},
            fields='id'
        ).execute()
        return folder['id']

# -----------------------------
# Delete folder from Drive
# -----------------------------
def delete_drive_folder(folder_id):
    try:
        drive_service.files().delete(fileId=folder_id).execute()
    except Exception as e:
        print(f"Error deleting folder {folder_id}: {e}")

# -----------------------------
# Download file from Drive
# -----------------------------
def download_file(file_id, local_path):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()

# -----------------------------
# Parse date to DD MMM YYYY
# -----------------------------
def format_date(yy=None, mm=None, dd=None, from_text=None):
    try:
        if from_text:
            # พยายาม parse จากข้อความ OCR เช่น "25 NOV 2025"
            dt = datetime.strptime(from_text.strip(), '%d %b %Y')
        else:
            year = 2000 + int(yy) if int(yy) < 50 else 1900 + int(yy)
            dt = datetime(year, int(mm), int(dd))
        return dt.strftime('%d %b %Y')
    except:
        return ''

# -----------------------------
# OCR Passport Parsing
# -----------------------------
def read_passport_data(image_path):
    # OCR ทั้งภาพ
    text_full = pytesseract.image_to_string(Image.open(image_path))
    lines = [line.strip() for line in text_full.split('\n') if line.strip()]
    mrz_lines = [line.replace(' ','') for line in lines if len(line.replace(' ','').strip())>=30]
    
    if len(mrz_lines)<2:
        print("Error: MRZ not found")
        return None
    
    mrz1, mrz2 = mrz_lines[-2], mrz_lines[-1]

    try:
        data = {}
        # MRZ fields
        data['type'] = mrz1[0]
        data['countryCode'] = mrz1[2:5]
        names = mrz1[5:].split('<<')
        data['surName'] = names[0].replace('<',' ').strip()
        data['titleName'] = names[1].replace('<',' ').strip() if len(names)>1 else ''
        data['passportNo'] = mrz2[0:9].replace('<','')
        data['nationality'] = mrz2[10:13]
        dob_yy = mrz2[13:15]
        dob_mm = mrz2[15:17]
        dob_dd = mrz2[17:19]
        data['dateOfBirth'] = format_date(dob_yy,dob_mm,dob_dd)
        data['sex'] = mrz2[20]
        exp_yy = mrz2[21:23]
        exp_mm = mrz2[23:25]
        exp_dd = mrz2[25:27]
        data['dateOfExpiry'] = format_date(exp_yy,exp_mm,exp_dd)

        # OCR text fields
        # Place of Birth
        # pob_match = re.search(r'Place of Birth[:\s]+([A-Z\s]+)', text_full, re.I)
        # data['placeOfBirth'] = pob_match.group(1).strip() if pob_match else ''
        # # Height
        # height_match = re.search(r'Height[:\s]+(\d+)', text_full, re.I)
        # data['height'] = height_match.group(1).strip() if height_match else ''
        # # Date of Issue
        # doi_match = re.search(r'Date of Issue[:\s]+(\d{2}\s+[A-Z]{3}\s+\d{4})', text_full, re.I)
        # data['dateOfIssue'] = doi_match.group(1).strip() if doi_match else ''

        # ตรวจสอบ field ว่าง
        missing = [k for k,v in data.items() if not v]
        if missing:
            print("Error: Missing fields:", missing)
            return None

        return data
    except Exception as e:
        print("Error parsing passport:", e)
        return None

# -----------------------------
# Monitor folder loop
# -----------------------------
def monitor_folder(folder_id):
    while True:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false",
            fields="files(id,name)"
        ).execute()
        files = results.get('files',[])
        
        if not files:
            print("No file found. Waiting 5 seconds...")
            time.sleep(5)
            continue

        for f in files:
            local_file = f"temp_{f['name']}"
            download_file(f['id'], local_file)
            print(f"Downloaded file: {local_file}")

            data = read_passport_data(local_file)

            # ลบไฟล์ใน Drive + local
            # drive_service.files().delete(fileId=f['id']).execute()
            os.remove(local_file)
            print(f"Deleted file: {f['name']}")

            if data:
                print("Passport data object:", data)
            else:
                print("Data incomplete. Skipping to next file.")
        
        time.sleep(5)

# -----------------------------
# Run
# -----------------------------
device_code = generate_device_code()
folder_id = create_drive_folder(device_code)

# -----------------------------
# UI
# -----------------------------
root = tk.Tk()
root.title("Device Code Generator")
label = tk.Label(root, text=f"Device Code: {device_code}", font=("Arial",18))
label.pack(padx=20,pady=20)

def on_close():
    delete_drive_folder(folder_id)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# เรียก loop monitor ใน background
threading.Thread(target=monitor_folder,args=(folder_id,),daemon=True).start()

root.mainloop()
