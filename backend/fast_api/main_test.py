from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import BlipProcessor, BlipForConditionalGeneration, MarianMTModel, MarianTokenizer
from ultralytics import YOLO
from PIL import Image
from io import BytesIO

app = FastAPI()

# Загрузка моделей и процессоров
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
translation_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
translation_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-ru")
yolo_model = YOLO("yolov8n.pt")

def translate_text(text: str) -> str:
    tokens = translation_tokenizer(text, return_tensors="pt", padding=True)
    out = translation_model.generate(**tokens)
    return translation_tokenizer.decode(out[0], skip_special_tokens=True)

@app.post("/upload/")
async def process_image(image: UploadFile = File(...)):
    try:
        img = Image.open(BytesIO(await image.read())).convert("RGB")

        # Генерация описания
        inputs = blip_processor(img, return_tensors="pt")
        caption = blip_processor.decode(blip_model.generate(**inputs)[0], skip_special_tokens=True)
        translated_caption = translate_text(caption)

        # Обнаружение объектов
        results = yolo_model(img)
        names = []
        for res in results:
            for box in res.boxes:
                names.append(yolo_model.names[int(box.cls)])
        detected_objects = translate_text(", ".join(sorted(set(names))))

        return JSONResponse({
            "description": translated_caption,
            "detected_objects": detected_objects,
            "text": "Тут будет распознанный текст"
        })
    except Exception as e:
        raise HTTPException(500, f"Ошибка обработки изображения: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
