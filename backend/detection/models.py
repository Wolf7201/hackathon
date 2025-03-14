from django.db import models

class Image(models.Model):
    image = models.ImageField(upload_to='images/')  # Файл изображения
    upload_date = models.DateTimeField(auto_now_add=True)  # Автоматическая дата загрузки
    description = models.TextField(blank=True, null=True)  # Описание изображения
    detected_objects = models.TextField(blank=True, null=True)  # Обнаруженные объекты
    text = models.TextField(blank=True, null=True)  # Переведённый текст

    def __str__(self):
        return f"Image {self.id} uploaded on {self.upload_date}"