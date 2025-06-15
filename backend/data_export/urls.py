from django.urls import path

from .views import DatasetCatalog, DatasetExportAPI, AnnotationHistoryAPI, AnnotationHistoryTableDataAPI

urlpatterns = [
    path(route="projects/<int:project_id>/download-format", view=DatasetCatalog.as_view(), name="download-format"),
    path(route="projects/<int:project_id>/download", view=DatasetExportAPI.as_view(), name="download-dataset"),
    path(route="projects/<int:project_id>/annotation-history", view=AnnotationHistoryAPI.as_view(), name="annotation-history"),
    path(route="projects/<int:project_id>/annotation-history-data", view=AnnotationHistoryTableDataAPI.as_view(), name="annotation-history-data"),
]
