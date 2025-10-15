from backend.ocr_parser import preprocess_image
import os

input_path = "data/sample1.png"
output_path = "data/sample1_preprocessed.png"

if not os.path.exists(input_path):
    print(f"Error: Input file not found: {input_path}")
else:
    try:
        img = preprocess_image(input_path)
        img.save(output_path)
        print(f"Saved preprocessed image to {output_path}")
    except Exception as e:
        print(f"Error during preprocessing: {e}")
