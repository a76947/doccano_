from django.urls import path

from .views import (
    DatasetCatalog, 
    DatasetExportAPI, 
    AnnotationHistoryAPI, 
    AnnotationHistoryTableDataAPI,
    DiscrepancyHistoryAPI,
    DiscrepancyHistoryTableDataAPI,
    PerspectiveHistoryAPI,
    PerspectiveHistoryTableDataAPI,
    AnnotationHistoryPDFAPI,
)

urlpatterns = [
    path(route="projects/<int:project_id>/download-format", view=DatasetCatalog.as_view(), name="download-format"),
    path(route="projects/<int:project_id>/download", view=DatasetExportAPI.as_view(), name="download-dataset"),
    path(route="projects/<int:project_id>/annotation-history", view=AnnotationHistoryAPI.as_view(), name="annotation-history"),
    path(route="projects/<int:project_id>/annotation-history-data", view=AnnotationHistoryTableDataAPI.as_view(), name="annotation-history-data"),
    path(route="projects/<int:project_id>/discrepancy-history", view=DiscrepancyHistoryAPI.as_view(), name="discrepancy-history"),
    path(route="projects/<int:project_id>/discrepancy-history-data", view=DiscrepancyHistoryTableDataAPI.as_view(), name="discrepancy-history-data"),
    path(route="projects/<int:project_id>/perspective-history", view=PerspectiveHistoryAPI.as_view(), name="perspective-history"),
    path(route="projects/<int:project_id>/perspective-history-data", view=PerspectiveHistoryTableDataAPI.as_view(), name="perspective-history-data"),
    path(route="projects/<int:project_id>/annotation-history-pdf", view=AnnotationHistoryPDFAPI.as_view(), name="annotation-history-pdf"),
]
