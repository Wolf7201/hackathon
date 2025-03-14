from django.contrib import admin
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Image
import csv
from django.http import HttpResponse


class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "thumbnail", "upload_date", "short_metadata")  # Что показывать в списке
    list_filter = ("upload_date",)  # Фильтр по дате
    search_fields = ("metadata",)  # Поиск по метаданным
    readonly_fields = ("upload_date", "image_preview")  # Только для просмотра
    actions = ["export_as_csv"]  # Добавляем экспорт в CSV

    def thumbnail(self, obj):
        """Превью изображений в списке."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="border-radius:5px;" />')
        return "No Image"

    thumbnail.short_description = "Preview"

    def short_metadata(self, obj):
        """Обрезаем метаданные до 50 символов для удобного отображения."""
        return obj.metadata[:50] + "..." if obj.metadata else "No Metadata"

    short_metadata.short_description = "Metadata"

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
        writer.writerow(["ID", "Upload Date", "Metadata"])
        for obj in queryset:
            writer.writerow([obj.id, obj.upload_date, obj.metadata])
        return response

    export_as_csv.short_description = "Export selected to CSV"


admin.site.register(Image, ImageAdmin)

