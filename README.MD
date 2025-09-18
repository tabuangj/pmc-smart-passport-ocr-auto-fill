# README.md

## PMC-Smart Passport OCR

โปรแกรมนี้ช่วยอ่านข้อมูลจากรูปภาพพาสปอร์ตด้วย OCR และแสดงผลลัพธ์ในรูปแบบ JSON โดยใช้ PySide6 สำหรับ GUI และ PassportEye + Tesseract สำหรับการอ่าน MRZ

---

### 1. เตรียมเครื่องมือ

#### 1.1 ติดตั้ง Python 3.10+  
ดาวน์โหลดจาก [python.org](https://www.python.org/downloads/)

#### 1.2 ติดตั้ง Tesseract OCR  
ดาวน์โหลดและติดตั้ง [Tesseract OCR for Windows](https://github.com/tesseract-ocr/tesseract/wiki)

> **สำคัญ:** ติดตั้งไว้ที่ `C:\Program Files\Tesseract-OCR\tesseract.exe`  
> (หากติดตั้งที่อื่น ให้แก้ไขบรรทัด `pytesseract.pytesseract.tesseract_cmd` ใน [`ocr_passport.py`](ocr_passport.py))

---

### 2. สร้าง Virtual Environment

```sh
python -m venv .venv