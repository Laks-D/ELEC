
import re, os, sys
from PIL import Image
import pytesseract
import cv2
import numpy as np

# If tesseract isn't found via PATH on Windows, uncomment & set path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image_cv(image_path, scale_up=True):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    if scale_up:
        h,w = gray.shape
        scale = 1.5 if max(h,w) < 1200 else 1.0
        gray = cv2.resize(gray, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.medianBlur(gray, 3)
    th = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,31,15)
    return Image.fromarray(th)

def get_best_langs():
    """Return best Tesseract lang string: prefer eng+tam if tam available."""
    try:
        langs = pytesseract.get_tesseract_version()  # quick check only
    except:
        langs = None
    # try to list installed langs
    try:
        installed = pytesseract.get_languages(config='')  # returns list
    except Exception:
        # fallback attempt to run CLI
        try:
            out = os.popen('tesseract --list-langs').read()
            installed = [l.strip() for l in out.splitlines() if l.strip() and not l.lower().startswith('list')]
        except:
            installed = []
    if 'tam' in installed and 'eng' in installed:
        return 'eng+tam'
    if 'eng' in installed:
        return 'eng'
    return 'eng'  # forced fallback

def ocr_with_confidence(pil_img, lang='eng'):
    """Return full raw_text and token-level list (word, conf)."""
    config = "--oem 3 --psm 6"
    # uses image_to_data for token confidences
    try:
        data = pytesseract.image_to_data(pil_img, lang=lang, config=config, output_type=pytesseract.Output.DICT)
        words = []
        raw_text = []
        for i, w in enumerate(data.get('text', [])):
            if w and w.strip():
                conf = data.get('conf', [])[i]
                words.append({'word': w.strip(), 'conf': int(conf) if conf and conf != '-1' else None})
                raw_text.append(w.strip())