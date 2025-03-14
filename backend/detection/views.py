import requests
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Image
from .serializers import ImageSerializer

API_URL = settings.METADATA_API_URL


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by("id")
    serializer_class = ImageSerializer
    pagination_class = PageNumberPagination
    # Добавляем поддержку поиска
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['metadata']  # Фильтрация по точному значению
    search_fields = ['metadata']  # Поиск по частичному совпадению

    def perform_create(self, serializer):
        """При создании изображения получаем метаданные и записываем их в модель."""
        instance = serializer.save()  # Сохраняем изображение

        try:
            # Отправляем изображение
            with open(instance.image.path, "rb") as img_file:
                files = {"image": img_file}
                response = requests.post(API_URL, files=files)

            # Обновляем метаданные
            if response.status_code == 200:
                metadata = response.json().get("metadata", "No metadata received")
                instance.metadata = metadata
                instance.save()

        except RequestException as e:
            return Response(
                {"error": f"API недоступно: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
