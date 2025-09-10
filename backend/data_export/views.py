import csv
import os
from celery.result import AsyncResult
from django.http import FileResponse, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import logging
import json
from django.conf import settings
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime

from .celery_tasks import export_dataset, export_annotation_history, export_discrepancy_history, export_perspective_history, export_annotation_history_pdf
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
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, *args, **kwargs):
        try:
            project_id = self.kwargs["project_id"]
            dataset_name = request.query_params.get('dataset_name')
            annotation_status = request.query_params.get('annotation_status', 'All')

            # Get the data from the CSV file
            task_id = request.GET.get("taskId")
            if not task_id:
                return Response(
                    {"error": "Task ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = AsyncResult(task_id)
            if not task.ready():
                return Response({"status": "Not ready"})

            if not task.successful():
                return Response(
                    {"error": str(task.result)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            filepath = task.result
            if not os.path.exists(filepath):
                return Response(
                    {"error": "Report file not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Read the CSV data
            data = []
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)

            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Add title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            elements.append(Paragraph(f"Example Texts Report", title_style))

            # Add report info
            info_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            if dataset_name:
                info_text += f"\nDataset: {dataset_name}"
            
            info_paragraph = Paragraph(info_text, styles['Normal'])
            elements.append(info_paragraph)
            elements.append(Spacer(1, 20))

            # Add example texts
            for i, row in enumerate(data, 1):
                example_text = row.get('example_text', '')
                if example_text:
                    # Add example number
                    elements.append(Paragraph(f"Example {i}", styles['Heading2']))
                    # Add the text
                    text_paragraph = Paragraph(example_text, styles['Normal'])
                    elements.append(text_paragraph)
                    elements.append(Spacer(1, 20))

            # Build PDF
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()

            # Clean up the CSV file
            try:
                os.remove(filepath)
                os.rmdir(os.path.dirname(filepath))
            except Exception as e:
                logger.warning(f"Could not remove temporary file {filepath}: {e}")

            # Create the response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="example-texts.pdf"'
            response.write(pdf)
            
            return response

        except Exception as e:
            logger.error(f"Error in AnnotationHistoryAPI: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        dataset_name = request.data.pop("datasetName", None)
        annotation_status = request.data.pop("annotationStatus", "All")
        task = export_annotation_history.delay(
            project_id=project_id,
            dataset_name=dataset_name,
            annotation_status=annotation_status
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
                    # Check if file exists before trying to read it
                    if not os.path.exists(filepath):
                        logger.error(f"CSV file not found: {filepath}")
                        return Response(
                            {"status": "Error", "message": "Report file not found."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    with open(filepath, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        logger.info(f"CSV Reader Fieldnames: {reader.fieldnames}")
                        for row_num, row in enumerate(reader):
                            logger.info(f"CSV Row {row_num}: {row}")
                            if 'perspectives' in row and row['perspectives']:
                                try:
                                    row['perspectives'] = json.loads(row['perspectives'])
                                except json.JSONDecodeError:
                                    logger.warning(f"Could not parse perspectives JSON for row {row_num}: {row['perspectives']}")
                                    row['perspectives'] = [] # Default to empty list on error
                            else:
                                row['perspectives'] = [] # Ensure it's an empty list if not present or empty
                            data.append(row)
                    
                    # Only remove the file after successfully reading it
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(f"Could not remove temporary file {filepath}: {e}")
                    
                    return Response(data, status=status.HTTP_200_OK)
                except Exception as e:
                    # Log the error and return a 500 response if file processing fails
                    logger.error(f"Error processing CSV file {filepath}: {e}", exc_info=True)
                    return Response(
                        {"status": "Error", "message": "Failed to process report file."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Task failed, return the exception/traceback
                logger.error(f"Celery task {task_id} failed: {task.result}", exc_info=True)
                return Response(
                    {"status": "Error", "message": str(task.result)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response({"status": "Not ready"})


class DiscrepancyHistoryAPI(APIView):
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
        dataset_name = request.data.pop("datasetName", None)
        task = export_discrepancy_history.delay(
            project_id=project_id, dataset_name=dataset_name
        )
        return Response({"task_id": task.task_id})


class DiscrepancyHistoryTableDataAPI(APIView):
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
                            # Parse JSON fields
                            if 'percentages' in row:
                                try:
                                    row['percentages'] = json.loads(row['percentages'])
                                except json.JSONDecodeError:
                                    row['percentages'] = {}
                            
                            if 'perspective_answers' in row:
                                try:
                                    row['perspective_answers'] = json.loads(row['perspective_answers'])
                                except json.JSONDecodeError:
                                    row['perspective_answers'] = []
                            
                            # Convert boolean string to actual boolean
                            if 'is_discrepancy' in row:
                                row['is_discrepancy'] = row['is_discrepancy'].lower() == 'true'
                            
                            # Convert numeric strings to actual numbers
                            if 'max_percentage' in row:
                                row['max_percentage'] = float(row['max_percentage'])
                            if 'diff_count' in row:
                                row['diff_count'] = int(row['diff_count'])
                            
                            data.append(row)
                    os.remove(filepath)
                    return Response(data, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Error processing CSV file {filepath}: {e}", exc_info=True)
                    return Response({"status": "Error", "message": "Failed to process report file."},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(f"Celery task {task_id} failed: {task.result}", exc_info=True)
                return Response({"status": "Error", "message": str(task.result)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status": "Not ready"})


class PerspectiveHistoryAPI(APIView):
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
        dataset_name = request.data.pop("datasetName", None)
        task = export_perspective_history.delay(
            project_id=project_id, dataset_name=dataset_name
        )
        return Response({"task_id": task.task_id})


class PerspectiveHistoryTableDataAPI(APIView):
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
                    # Check if file exists before trying to read it
                    if not os.path.exists(filepath):
                        logger.error(f"CSV file not found: {filepath}")
                        return Response(
                            {"status": "Error", "message": "Report file not found."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    with open(filepath, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            data.append(row)
                    
                    # Only remove the file after successfully reading it
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(f"Could not remove temporary file {filepath}: {e}")
                    
                    return Response(data, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Error processing CSV file {filepath}: {e}", exc_info=True)
                    return Response(
                        {"status": "Error", "message": "Failed to process report file."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                logger.error(f"Celery task {task_id} failed: {task.result}", exc_info=True)
                return Response(
                    {"status": "Error", "message": str(task.result)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response({"status": "Not ready"})


class AnnotationHistoryPDFAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            dataset_name = request.query_params.get('dataset_name')
            annotation_status = request.query_params.get('annotation_status', 'All')
            
            # Trigger the PDF export task
            task = export_annotation_history_pdf.delay(project_id, dataset_name, annotation_status)
            
            return Response({
                'task_id': task.id,
                'status': 'processing'
            })
        except Exception as e:
            logger.error(f"Error in AnnotationHistoryPDFAPI: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, project_id):
        try:
            task_id = request.data.get('task_id')
            if not task_id:
                return Response(
                    {'error': 'Task ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check task status
            task = export_annotation_history_pdf.AsyncResult(task_id)
            
            if task.ready():
                if task.successful():
                    filepath = task.result
                    if os.path.exists(filepath):
                        response = FileResponse(
                            open(filepath, 'rb'),
                            content_type='application/pdf'
                        )
                        response['Content-Disposition'] = f'attachment; filename="annotation_history.pdf"'
                        
                        # Delete the file after sending
                        try:
                            os.remove(filepath)
                            os.rmdir(os.path.dirname(filepath))
                        except Exception as e:
                            logger.error(f"Error cleaning up PDF file: {e}")
                            
                        return response
                    else:
                        return Response(
                            {'error': 'PDF file not found'},
                            status=status.HTTP_404_NOT_FOUND
                        )
                else:
                    return Response(
                        {'error': str(task.result)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response({
                    'status': 'processing',
                    'task_id': task_id
                })
                
        except Exception as e:
            logger.error(f"Error in AnnotationHistoryPDFAPI: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
