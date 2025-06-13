import csv
import os
from celery.result import AsyncResult
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

from .celery_tasks import export_dataset, export_annotation_history
from .pipeline.catalog import Options
from projects.models import Project
from projects.permissions import IsProjectAdmin

logger = logging.getLogger(__name__)


class DatasetCatalog(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, *args, **kwargs):
        project_id = kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        use_relation = getattr(project, "use_relation", False)
        options = Options.filter_by_task(project.project_type, use_relation)
        return Response(data=options, status=status.HTTP_200_OK)


class DatasetExportAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, *args, **kwargs):
        task_id = request.GET["taskId"]
        task = AsyncResult(task_id)
        ready = task.ready()
        if ready:
            filename = task.result
            return FileResponse(open(filename, mode="rb"), as_attachment=True)
        return Response({"status": "Not ready"})

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        file_format = request.data.pop("format")
        export_approved = request.data.pop("exportApproved", False)
        task = export_dataset.delay(
            project_id=project_id, file_format=file_format, confirmed_only=export_approved, **request.data
        )
        return Response({"task_id": task.task_id})


class AnnotationHistoryAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin] # Or appropriate permissions

    def get(self, request, *args, **kwargs):
        task_id = request.GET["taskId"]
        task = AsyncResult(task_id)
        ready = task.ready()
        if ready:
            filename = task.result
            return FileResponse(open(filename, mode="rb"), as_attachment=True)
        return Response({"status": "Not ready"})

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        dataset_name = request.data.pop("datasetName", None)
        # Add any other parameters needed for your report
        task = export_annotation_history.delay(
            project_id=project_id, dataset_name=dataset_name, **request.data
        )
        return Response({"task_id": task.task_id})


class AnnotationHistoryTableDataAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, *args, **kwargs):
        task_id = request.GET["taskId"]
        task = AsyncResult(task_id)
        ready = task.ready()
        
        if ready:
            if task.successful():
                filepath = task.result
                data = []
                try:
                    with open(filepath, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            data.append(row)
                    os.remove(filepath)
                    return Response(data, status=status.HTTP_200_OK)
                except Exception as e:
                    # Log the error and return a 500 response if file processing fails
                    logger.error(f"Error processing CSV file {filepath}: {e}", exc_info=True)
                    return Response({"status": "Error", "message": "Failed to process report file."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Task failed, return the exception/traceback
                logger.error(f"Celery task {task_id} failed: {task.result}", exc_info=True)
                return Response({"status": "Error", "message": str(task.result)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status": "Not ready"})
