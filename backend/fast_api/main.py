from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import io
from googletrans import Translator

app = FastAPI()

# Load model and processor once during startup
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Создаём объект переводчика
translator = Translator()


async def generate_description(image_data):
    try:
        # Convert uploaded file to PIL Image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Process and generate caption
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        return description
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


async def translate_text(text, dest_lang="ru"):
    try:
        translation = translator.translate(text, dest=dest_lang)
        return translation.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@app.post("/upload/")
async def upload_image(image: UploadFile = File(...)):
    image_data = await image.read()

    # Получаем описание изображения
    description = await generate_description(image_data)

    # Переводим описание на русский
    translated_description = await translate_text(description, "ru")
    print(translated_description)

    return JSONResponse(content={"metadata": translated_description})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
