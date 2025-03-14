from django.db import models

class Image(models.Model):
    image = models.ImageField(upload_to='images/')  # Файл изображения
    upload_date = models.DateTimeField(auto_now_add=True)  # Автоматическая дата загрузки
    metadata = models.TextField(blank=True, null=True)  # Опциональные метаданные

    def __str__(self):
        return f"Image {self.id} uploaded on {self.upload_date}"
