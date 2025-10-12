# backend/ocr_parser.py  (REPLACE existing)
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
        return " ".join(raw_text), words
    except Exception as e:
        # fallback to simple string
        try:
            txt = pytesseract.image_to_string(pil_img, lang=lang, config=config)
            return txt, []
        except Exception as e2:
            raise e

def _clean(s): return " ".join(s.split())

def extract_first_after(text, keywords, max_chars=80):
    for kw in keywords:
        pattern = re.escape(kw) + r".{0,%d}?([0-9]{1,10}[,\d]*)" % max_chars
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace(',', '')
    return None

def parse_bill_image(image_path, lang_hint=None):
    pil = preprocess_image_cv(image_path)
    # pick language string intelligently
    lang = lang_hint if lang_hint else get_best_langs()
    # try with lang; if fails and 'tam' attempted, fallback to 'eng'
    try:
        raw_text, tokens = ocr_with_confidence(pil, lang=lang)
    except Exception as e:
        # fallback to english
        raw_text, tokens = ocr_with_confidence(pil, lang='eng')

    text = _clean(raw_text)

    # extract common fields with robust fallbacks
    # consumer number patterns (TNEB consumer numbers often 11 digits)
    consumer = None
    m = re.search(r'(consumer(?:\s*no| no| number|\.no|:)?)[\s:]*([0-9]{6,14})', text, flags=re.IGNORECASE)
    if m:
        consumer = m.group(2)
    else:
        m2 = re.search(r'\b([0-9]{8,14})\b', text)
        if m2:
            consumer = m2.group(1)

    prev_read = extract_first_after(text, ['previous reading','previous','prev read','prev'])
    cur_read = extract_first_after(text, ['present reading','present','current reading','cur read','present read'])
    units = extract_first_after(text, ['units consumed','units','units billed','kwh','units this period','consumption'])
    if (not units) and prev_read and cur_read:
        try:
            units = str(int(cur_read) - int(prev_read))
        except:
            units = units
    amount = extract_first_after(text, ['total amount','amount to be paid','net amount','amount','total payable','total'])
    # final parsed dict
    parsed = {
        "raw_text": raw_text,
        "tokens": tokens[:200],   # first 200 tokens for debug
        "consumer_no": consumer,
        "prev_read": prev_read,
        "cur_read": cur_read,
        "units": units,
        "amount": amount,
        "lang_used": lang
    }
    return parsed

# quick CLI test if run directly
if __name__ == "__main__":
    import sys, json
    p = parse_bill_image(sys.argv[1] if len(sys.argv)>1 else "data/sample1.png")
    print(json.dumps(p, indent=2, ensure_ascii=False))
