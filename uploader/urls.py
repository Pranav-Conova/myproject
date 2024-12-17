from django.urls import path
from .views import upload_file, presentation_stream

urlpatterns = [
    path('', upload_file, name='upload_file'),
    path('presentation/<int:file_id>/<int:sasi>/', presentation_stream, name='presentation_stream'),
]
