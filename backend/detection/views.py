import requests
import piexif
from PIL import Image, PngImagePlugin
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from requests.exceptions import RequestException
from rest_framework import status, viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Image as ImageModel
from .serializers import ImageSerializer

API_URL = settings.METADATA_API_URL


class ImageViewSet(viewsets.ModelViewSet):
    queryset = ImageModel.objects.all().order_by("id")
    serializer_class = ImageSerializer
    pagination_class = PageNumberPagination

    # Добавляем поддержку поиска
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['description']
    search_fields = ['description']

    def perform_create(self, serializer):
        """При создании изображения получаем метаданные, записываем их в модель и обновляем EXIF изображения."""
        instance = serializer.save()  # Сохраняем изображение в БД

        try:
            # Отправляем изображение на API нейронки
            with open(instance.image.path, "rb") as img_file:
                files = {"image": img_file}
                response = requests.post(API_URL, files=files)

            if response.status_code == 200:
                data = response.json()

                # Записываем полученные метаданные в БД
                instance.description = data.get("description", "No description received")
                instance.detected_objects = data.get("detected_objects", "No objects detected")
                instance.text = data.get("text", "No translated text")
                instance.save()

                # Записываем метаданные в EXIF изображения
                write_metadata(
                    instance.image.path,
                    instance.description,
                    instance.detected_objects,
                    instance.text
                )

        except RequestException as e:
            return Response(
                {"error": f"API недоступно: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


def write_metadata(image_path, description, list_of_objects, text):
    """Записывает метаданные в EXIF изображения."""
    img = Image.open(image_path)
    img_format = img.format

    if isinstance(list_of_objects, str):
        list_of_objects = [list_of_objects]  # Приводим к списку, если строка

    combined_metadata = (
        f"description: {description}\n"
        f"objects: {', '.join(list_of_objects)}\n"
        f"text: {text if text else 'No text detected'}"
    )

    try:
        if img_format in ['JPEG', 'TIFF']:
            exif_dict = piexif.load(img.info.get('exif', b''))
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = combined_metadata.encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes, format=img_format)

        elif img_format == 'PNG':
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text('ImageDescription', combined_metadata)
            img.save(image_path, pnginfo=pnginfo, format=img_format)

        else:
            img.info['ImageDescription'] = combined_metadata
            img.save(image_path, format=img_format)

    finally:
        img.close()
