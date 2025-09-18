# ocr_passport.py — Robust MRZ extractor (PassportEye + Tesseract on Windows)
# Debug mode: เก็บ ROI / rotation ที่ลอง OCR ไว้ตรวจสอบ
# deps: pip install passporteye opencv-python pytesseract

import os, re, tempfile, shutil
from pathlib import Path
import cv2
import pytesseract
from passporteye import read_mrz

# ---------- CONFIG: Path Tesseract (Windows) ----------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- Helpers ----------
def _fmt_date_yyMMdd(s: str | None) -> str | None:
    if not s or len(s) < 6 or not s.isdigit():
        return None
    yy, mm, dd = int(s[:2]), int(s[2:4]), int(s[4:6])
    year = 2000 + yy if yy < 80 else 1900 + yy
    return f"{year:04d}-{mm:02d}-{dd:02d}"

def _clean_surname(s: str | None) -> str | None:
    if not s: return None
    t = s.replace("<", " ").upper()
    t = re.sub(r'[^A-Z ]+', '', t)
    return re.sub(r'\s{2,}', ' ', t).strip() or None

def _clean_given_from_mrz(s: str | None) -> str | None:
    if not s: return None
    t = s.upper().replace('<', ' ')
    t = re.sub(r'[^A-Z ]+', '', t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'\b[KXVYE]{2,}\b', ' ', t)
    t = re.sub(r'(?:\s*(?:NK|KE|K|E))+$', '', t)
    parts = t.split()
    return " ".join(parts[:2]) if parts else None

def _post_clean_name(s: str | None) -> str | None:
    if not s: return None
    t = re.sub(r'[^A-Z ]', '', s.upper()).strip()
    return re.sub(r'\s{2,}', ' ', t) or None

# ---------- Core reader ----------
def _read_with_passporteye(image_bgr, dbgdir=None, tag="full"):
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    cv2.imwrite(tmp.name, image_bgr)
    try:
        mrz = read_mrz(tmp.name, save_roi=False, extra_cmdline_params="--oem 1 --psm 6")
        if mrz is None:
            if dbgdir: cv2.imwrite(str(Path(dbgdir) / f"fail_{tag}.jpg"), image_bgr)
            return None
        d = mrz.to_dict()
        raw1 = d.get("mrz1") or getattr(mrz, "mrz_line1", "") or ""
        raw2 = d.get("mrz2") or getattr(mrz, "mrz_line2", "") or ""
        raw_mrz = (raw1 + ("\n" if raw1 or raw2 else "") + raw2)

        if dbgdir:
            cv2.imwrite(str(Path(dbgdir) / f"ok_{tag}.jpg"), image_bgr)
            with open(Path(dbgdir) / f"raw_{tag}.txt", "w", encoding="utf-8") as f:
                f.write(raw_mrz)

        return {
            "surname": _post_clean_name(_clean_surname(d.get("surname"))),
            "given_names": _post_clean_name(_clean_given_from_mrz(d.get("names"))),
            "passport_number": (d.get("number") or "").upper() or None,
            "nationality": (d.get("nationality") or "").upper() or None,
            "birth_date": _fmt_date_yyMMdd(d.get("date_of_birth")),
            "sex": (d.get("sex") or "").upper() or None,
            "expiry_date": _fmt_date_yyMMdd(d.get("date_of_expiry")),
            "issuer": (d.get("country") or "").upper() or None,
            "optional": d.get("optional_data") or None,
            "raw_mrz": raw_mrz,
        }
    finally:
        try: os.remove(tmp.name)
        except: pass

# ---------- Public API ----------
def extract_mrz(image_path: str, debug=False) -> dict:
    img = cv2.imread(str(Path(image_path)))
    if img is None:
        return {"error": f"Cannot read image: {image_path}"}

    dbgdir = None
    if debug:
        dbgdir = tempfile.mkdtemp(prefix="mrz_dbg_")
        print(f"[DEBUG] saving debug outputs to {dbgdir}")

    rotations = [
        ("r0", lambda x: x),
        ("r90", lambda x: cv2.rotate(x, cv2.ROTATE_90_CLOCKWISE)),
        ("r180", lambda x: cv2.rotate(x, cv2.ROTATE_180)),
        ("r270", lambda x: cv2.rotate(x, cv2.ROTATE_90_COUNTERCLOCKWISE)),
    ]

    for tag, rot in rotations:
        r = _read_with_passporteye(rot(img), dbgdir=dbgdir, tag=f"full_{tag}")
        if r: return r

    H, W = img.shape[:2]
    crops = [
        ("left",  img[:, :int(W*0.28)]),
        ("right", img[:, int(W*0.72):]),
        ("bot1",  img[int(H*0.62):, :]),
        ("bot2",  img[int(H*0.70):, :]),
    ]
    for cname, roi in crops:
        for tag, rot in rotations:
            r = _read_with_passporteye(rot(roi), dbgdir=dbgdir, tag=f"{cname}_{tag}")
            if r: return r

    return {"error": "MRZ not detected"}

# ---------- CLI ----------
if __name__ == "__main__":
    TEST_IMG = r"C:\Users\tabua\OneDrive\Pictures\73448 - Copy.jpg"
    print(extract_mrz(TEST_IMG, debug=True))

