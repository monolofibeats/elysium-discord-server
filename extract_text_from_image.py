from PIL import Image
import pytesseract

def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang="eng+deu+spa")
    return text
