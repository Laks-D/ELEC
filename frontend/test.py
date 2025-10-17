import pytesseract

# Set the path to the tesseract executable if needed
pytesseract.pytesseract.tesseract_cmd = r"D:\tesseract\tesseract.exe"  # Update this path if necessary

print(pytesseract.get_tesseract_version())
