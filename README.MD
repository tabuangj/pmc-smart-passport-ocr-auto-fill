# pmc-automation: Passport MRZ Extractor

โปรเจกต์นี้ใช้ Python ในการอ่านและแยกข้อมูล MRZ จากภาพถ่ายหนังสือเดินทาง (Passport) ด้วย PassportEye และ Tesseract OCR

## Features

- รองรับไฟล์ภาพ .jpg, .png ฯลฯ
- ตรวจจับ MRZ อัตโนมัติ (ลองหลายมุม/หลายตำแหน่ง)
- มีโหมด Debug สำหรับตรวจสอบผลลัพธ์ OCR

## Requirements

- Windows OS
- Python 3.10 ขึ้นไป
- Tesseract OCR (Windows)
- pip

## Installation

### 1. ติดตั้ง Python

ดาวน์โหลดและติดตั้ง [Python](https://www.python.org/downloads/windows/)

### 2. ติดตั้ง Tesseract OCR

ดาวน์โหลดและติดตั้ง [Tesseract OCR for Windows](https://github.com/tesseract-ocr/tesseract/wiki)

> **สำคัญ:** จำ path ที่ติดตั้ง เช่น `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 3. Clone Repository

```sh
git clone https://github.com/yourusername/pmc-automation.git
cd pmc-automation
```

### 4. ติดตั้ง Dependencies

```sh
pip install passporteye opencv-python pytesseract
```

## Usage

### 1. เตรียมไฟล์ภาพ Passport

เช่น `C:\Users\yourname\Pictures\passport.jpg`

### 2. Run Script

```sh
python ocr_passport.py
```

หรือระบุไฟล์ภาพเองในโค้ด (แก้ไขบรรทัด `TEST_IMG`)

```python
TEST_IMG = r"C:\Users\yourname\Pictures\passport.jpg"
```

### 3. ดูผลลัพธ์

ผลลัพธ์จะเป็นข้อมูล MRZ ในรูปแบบ dictionary และหากเปิด debug mode จะมีไฟล์ debug output ในโฟลเดอร์ชั่วคราว

## Example Output

```python
{
    "surname": "DOE",
    "given_names": "JOHN",
    "passport_number": "A1234567",
    "nationality": "THA",
    "birth_date": "1990-01-01",
    "sex": "M",
    "expiry_date": "2030-01-01",
    "issuer": "THA",
    "optional": None,
    "raw_mrz": "P<THADOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<A1234567THA900101M3001017<<<<<<<<<<<<<<04"
}
```

## Debug Mode

หากต้องการดูไฟล์ debug (ROI, rotation, raw MRZ):

```python
extract_mrz(TEST_IMG, debug=True)
```

จะมีโฟลเดอร์ debug สร้างขึ้นและแสดง path ใน console

## Troubleshooting

- หากอ่านภาพไม่ได้ ตรวจสอบ path ภาพและสิทธิ์การเข้าถึง
- หาก Tesseract ไม่ทำงาน ตรวจสอบ path ในบรรทัดนี้ของโค้ด:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```

## License

MIT License

---