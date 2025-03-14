from io import BytesIO

import cv2
import numpy as np
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from spellchecker import SpellChecker
from transformers import BlipProcessor, BlipForConditionalGeneration, MarianMTModel, MarianTokenizer
from ultralytics import YOLO

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"
app = FastAPI()

# Загрузка моделей и процессоров
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
translation_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
translation_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
yolo_model = YOLO("yolov8n.pt")


# Функция для исправления орфографии
def correct_spelling(text, lang=None):
    if not text or lang is None:
        ru_chars = sum(1 for c in text if 'а' <= c.lower() <= 'я' or c.lower() == 'ё')
        en_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')

        if ru_chars > en_chars:
            lang = 'ru'
        else:
            lang = 'en'

    try:
        spell = SpellChecker(language=lang)

        words = text.split()
        corrected_words = []

        for word in words:
            leading_punct = ""
            trailing_punct = ""

            while word and not word[0].isalnum():
                leading_punct += word[0]
                word = word[1:]

            while word and not word[-1].isalnum():
                trailing_punct = word[-1] + trailing_punct
                word = word[:-1]

            if not word or any(c.isdigit() for c in word):
                corrected_words.append(leading_punct + word + trailing_punct)
                continue

            if not spell.known([word]):
                correction = spell.correction(word)
                if correction:
                    word = correction

            corrected_words.append(leading_punct + word + trailing_punct)

        return ' '.join(corrected_words)
    except Exception as e:
        print(f"Ошибка при исправлении орфографии: {e}")
        return text


# Функция для распознавания текста
def demo_handwritten_recognition(image: Image.Image):
    image_cv = np.array(image)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

    config = "--psm 6 --oem 3 -l rus+eng"
    text_gray = pytesseract.image_to_string(gray, config=config)

    if text_gray:
        corrected = correct_spelling(text_gray)
        return corrected
    return text_gray


def translate_text(text: str) -> str:
    tokens = translation_tokenizer(text, return_tensors="pt", padding=True)
    out = translation_model.generate(**tokens)
    return translation_tokenizer.decode(out[0], skip_special_tokens=True)


@app.post("/upload/")
async def process_image(image: UploadFile = File(...)):
    img = Image.open(BytesIO(await image.read())).convert("RGB")
    inputs = blip_processor(img, return_tensors="pt")
    caption = blip_processor.decode(blip_model.generate(**inputs)[0], skip_special_tokens=True)
    translated_caption = translate_text(caption)
    results = yolo_model(img)
    names = []
    for res in results:
        for box in res.boxes:
            names.append(yolo_model.names[int(box.cls)])
    detected_objects = translate_text(", ".join(sorted(set(names))))
    # Обработка текста на изображении
    text = demo_handwritten_recognition(img)
    return JSONResponse({
        "description": translated_caption,
        "detected_objects": detected_objects,
        "text": text
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
