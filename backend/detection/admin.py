from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Image
import csv
from django.http import HttpResponse


class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "thumbnail", "upload_date", "short_description", "short_detected_objects", "text")  # Что показывать в списке
    list_filter = ("upload_date",)  # Фильтр по дате
    search_fields = ("description", "detected_objects", "text")  # Поиск по описанию, объектам и тексту
    readonly_fields = ("upload_date", "image_preview")  # Только для просмотра
    actions = ["export_as_csv"]  # Добавляем экспорт в CSV

    def thumbnail(self, obj):
        """Превью изображений в списке."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="border-radius:5px;" />')
        return "No Image"

    thumbnail.short_description = "Preview"

    def short_description(self, obj):
        """Обрезаем описание до 50 символов."""
        return obj.description[:50] + "..." if obj.description else "No Description"

    short_description.short_description = "Description"

    def short_detected_objects(self, obj):
        """Обрезаем список объектов до 50 символов."""
        return obj.detected_objects[:50] + "..." if obj.detected_objects else "No Objects"

    short_detected_objects.short_description = "Detected Objects"

    def image_preview(self, obj):
        """Отображение полного изображения в детальном просмотре."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="300" style="border-radius:10px;"/>')
        return "No Image"

    image_preview.short_description = "Full Image Preview"

    def export_as_csv(self, request, queryset):
        """Экспорт выбранных изображений в CSV."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="images.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Upload Date", "Description", "Detected Objects", "Text"])
        for obj in queryset:
            writer.writerow([obj.id, obj.upload_date, obj.description, obj.detected_objects, obj.text])
        return response

    export_as_csv.short_description = "Export selected to CSV"


admin.site.register(Image, ImageAdmin)
