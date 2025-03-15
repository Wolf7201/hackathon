import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from detection.models import Image

FASTAPI_URL = "http://127.0.0.1:8001/upload/"  # URL FastAPI сервиса


class Command(BaseCommand):
    help = "Обрабатывает изображения из папки dataset/ и добавляет их в базу данных"

    def handle(self, *args, **kwargs):
        dataset_path = os.path.join(settings.BASE_DIR, "dataset")  # Папка с датасетом

        if not os.path.exists(dataset_path):
            self.stdout.write(self.style.ERROR(f"Папка {dataset_path} не найдена!"))
            return

        images = [f for f in os.listdir(dataset_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not images:
            self.stdout.write(self.style.WARNING("В папке dataset/ нет изображений"))
            return

        for img_name in images:
            img_path = os.path.join(dataset_path, img_name)
            self.stdout.write(f"📷 Обрабатываю: {img_name}")

            with open(img_path, "rb") as img_file:
                files = {"image": img_file}
                try:
                    response = requests.post(FASTAPI_URL, files=files)
                    if response.status_code == 200:
                        data = response.json()

                        # Создаём запись в БД
                        Image.objects.create(
                            image=f"dataset/{img_name}",  # Сохраняем относительный путь
                            description=data.get("description", ""),
                            detected_objects=data.get("detected_objects", ""),
                            text=data.get("text", "")
                        )

                        self.stdout.write(self.style.SUCCESS(f"✅ Добавлено в БД: {img_name}"))
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Ошибка FastAPI ({response.status_code}): {response.text}"))
                except requests.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"❌ Ошибка запроса: {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 Обработка завершена!"))
