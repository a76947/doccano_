import os
import shutil
import uuid
import csv
import json
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Exists, OuterRef, Count

from .pipeline.dataset import Dataset
from .pipeline.factories import (
    create_comment,
    create_formatter,
    create_labels,
    create_writer,
)
from .pipeline.services import ExportApplicationService
from data_export.models import ExportedExample
from projects.models import Member, Project
from examples.models import Example, ExampleState
from labels.models import Category, Span, TextLabel, BoundingBox, Segmentation, Relation

logger = get_task_logger(__name__)


def create_collaborative_dataset(project: Project, dirpath: str, confirmed_only: bool, formatters, writer):
    is_text_project = project.is_text_project
    if confirmed_only:
        examples = ExportedExample.objects.confirmed(project)
    else:
        examples = ExportedExample.objects.filter(project=project)
    labels = create_labels(project, examples)
    comments = create_comment(examples)
    dataset = Dataset(examples, labels, comments, is_text_project)

    service = ExportApplicationService(dataset, formatters, writer)

    filepath = os.path.join(dirpath, f"all.{writer.extension}")
    service.export(filepath)


def create_individual_dataset(project: Project, dirpath: str, confirmed_only: bool, formatters, writer):
    is_text_project = project.is_text_project
    members = Member.objects.filter(project=project)
    for member in members:
        if confirmed_only:
            examples = ExportedExample.objects.confirmed(project, user=member.user)
        else:
            examples = ExportedExample.objects.filter(project=project)
        labels = create_labels(project, examples, member.user)
        comments = create_comment(examples, member.user)
        dataset = Dataset(examples, labels, comments, is_text_project)

        service = ExportApplicationService(dataset, formatters, writer)

        filepath = os.path.join(dirpath, f"{member.username}.{writer.extension}")
        service.export(filepath)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def export_dataset(project_id, file_format: str, confirmed_only=False):
    project = get_object_or_404(Project, pk=project_id)
    dirpath = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
    os.makedirs(dirpath, exist_ok=True)
    formatters = create_formatter(project, file_format)
    writer = create_writer(file_format)
    if project.collaborative_annotation:
        create_collaborative_dataset(project, dirpath, confirmed_only, formatters, writer)
    else:
        create_individual_dataset(project, dirpath, confirmed_only, formatters, writer)
    zip_file = shutil.make_archive(dirpath, "zip", dirpath)
    shutil.rmtree(dirpath)
    return zip_file


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def export_annotation_history(project_id, dataset_name=None, annotation_status='All'):
    project = get_object_or_404(Project, pk=project_id)
    dirpath = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
    os.makedirs(dirpath, exist_ok=True)
    
    filepath = os.path.join(dirpath, "annotation_history.csv")
    logger.info(f"Creating annotation history file at: {filepath}")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['annotator', 'datasetName', 'label', 'date', 'example_text', 'numberOfAnnotations', 'perspectives']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            logger.info(f"Starting export_annotation_history for project {project_id}")
            logger.info(f"Selected dataset_name: {dataset_name}, annotation_status: {annotation_status}")

            examples_queryset = Example.objects.filter(project=project).prefetch_related(
                'assignments',
                'perspective_answers',
                'perspective_answers__perspective',
                'perspective_answers__created_by'
            )
            logger.debug(f"Initial examples_queryset count: {examples_queryset.count()}")

            if dataset_name:
                examples_queryset = examples_queryset.filter(
                    Q(filename__icontains=dataset_name) |
                    Q(upload_name__icontains=dataset_name)
                )
            logger.info(f"Total examples found: {examples_queryset.count()}")

            ANNOTATION_MODELS = {
                "DocumentClassification": Category,
                "SequenceLabeling": Span,
                "Seq2seq": TextLabel,
                "Speech2text": TextLabel,
                "ImageClassification": Category,
                "BoundingBox": BoundingBox,
                "Segmentation": Segmentation,
                "RelationExtraction": Relation,
            }
            AnnotationModel = ANNOTATION_MODELS.get(project.project_type)
            logger.info(f"Project type: {project.project_type}, Annotation Model: {AnnotationModel.__name__ if AnnotationModel else 'None'}")

            if annotation_status == 'Finished':
                examples_queryset = examples_queryset.filter(states__isnull=False).distinct()
            elif annotation_status == 'Not started':
                if AnnotationModel:
                    examples_queryset = examples_queryset.exclude(
                        Exists(AnnotationModel.objects.filter(example=OuterRef('pk')))
                    )
                else:
                    pass
            elif annotation_status == 'In progress':
                if AnnotationModel:
                    has_annotations = AnnotationModel.objects.filter(example=OuterRef('pk'))
                    examples_queryset = examples_queryset.filter(Exists(has_annotations))
                    examples_queryset = examples_queryset.filter(states__isnull=True)
                else:
                    examples_queryset = Example.objects.none()
            
            logger.info(f"Examples after status filter: {examples_queryset.count()}")

            for example in examples_queryset:
                try:
                    annotations = []
                    annotation_count = 0
                    if AnnotationModel:
                        annotations_for_example = AnnotationModel.objects.filter(example=example)
                        annotations.extend(annotations_for_example)
                        annotation_count = annotations_for_example.count()

                    logger.debug(f"Example {example.id} (Text: {example.text[:30]}...): Annotation Model: {AnnotationModel.__name__ if AnnotationModel else 'None'}, Annotations found: {annotations_for_example.count()}")

                    current_dataset_name = "N/A"
                    if example.filename and example.filename.name:
                        current_dataset_name = os.path.basename(example.filename.name)
                    elif example.upload_name:
                        current_dataset_name = example.upload_name
                    
                    logger.debug(f"Example {example.id} (Text: {example.text[:30]}...): Annotation count = {annotation_count}")
                    logger.info(f"Processing example ID: {example.id}, filename: {example.filename.name if example.filename else 'N/A'}, upload_name: {example.upload_name if example.upload_name else 'N/A'}")
                    logger.info(f"Example text: {example.text[:50]}...")

                    if not annotations:
                        # Get perspective answers for this example
                        perspective_answers = example.perspective_answers.all()
                        perspectives_data = []
                        for pa in perspective_answers:
                            perspectives_data.append({
                                'question': pa.perspective.question,
                                'answer': pa.answer,
                                'answered_by': pa.created_by.username if pa.created_by else 'N/A',
                                'answer_date': pa.created_at.strftime("%Y-%m-%d %H:%M:%S") if pa.created_at else 'N/A'
                            })

                        row = {
                            'annotator': 'N/A',
                            'datasetName': current_dataset_name,
                            'label': 'N/A',
                            'date': 'N/A',
                            'example_text': example.text if example.text else "",
                            'numberOfAnnotations': annotation_count,
                            'perspectives': json.dumps(perspectives_data)
                        }
                        logger.info(f"Writing row (no annotations): {row}")
                        logger.debug(f"Perspectives data for no annotations: {row.get('perspectives', 'N/A')}")
                        writer.writerow(row)
                    else:
                        for annotation in annotations:
                            label_text = "N/A"
                            if hasattr(annotation, 'label') and annotation.label:
                                label_text = annotation.label.text
                            elif hasattr(annotation, 'text'):
                                label_text = annotation.text
                            elif hasattr(annotation, 'points'):
                                label_text = annotation.label.text
                            elif hasattr(annotation, 'x'):
                                label_text = annotation.label.text
                            elif isinstance(annotation, Relation):
                                label_text = f"From:{annotation.from_id.id} To:{annotation.to_id.id} Type:{annotation.type.text}"
                            
                            logger.info(f"Annotation type: {type(annotation).__name__}, Label text: {label_text}")

                            # Get perspective answers for this example
                            perspective_answers = example.perspective_answers.all()
                            perspectives_data = []
                            for pa in perspective_answers:
                                perspectives_data.append({
                                    'question': pa.perspective.question,
                                    'answer': pa.answer,
                                    'answered_by': pa.created_by.username if pa.created_by else 'N/A',
                                    'answer_date': pa.created_at.strftime("%Y-%m-%d %H:%M:%S") if pa.created_at else 'N/A'
                                })

                            row = {
                                'annotator': annotation.user.username,
                                'datasetName': current_dataset_name,
                                'label': label_text,
                                'date': annotation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                                'example_text': example.text if example.text else "",
                                'numberOfAnnotations': annotation_count,
                                'perspectives': json.dumps(perspectives_data)
                            }
                            logger.info(f"Writing row (with annotation): {row}")
                            logger.debug(f"Perspectives data with annotation: {row.get('perspectives', 'N/A')}")
                            writer.writerow(row)
                except Exception as e:
                    logger.error(f"Error processing example {example.id}: {e}", exc_info=True)
                    continue

        # Verify the file was created and has content
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.info(f"Successfully created annotation history file at: {filepath}")
            return filepath
        else:
            logger.error(f"Failed to create annotation history file at: {filepath}")
            raise Exception("Failed to create annotation history file")

    except Exception as e:
        logger.error(f"Error in export_annotation_history: {e}", exc_info=True)
        # Clean up the directory if there was an error
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
        raise


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def export_discrepancy_history(project_id, dataset_name=None):
    project = get_object_or_404(Project, pk=project_id)
    dirpath = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
    os.makedirs(dirpath, exist_ok=True)
    
    filepath = os.path.join(dirpath, "discrepancy_history.csv")
    discrepancy_threshold = 70  # 70% threshold for discrepancies

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['example_id', 'datasetName', 'text', 'percentages', 'is_discrepancy', 'max_percentage', 'diff_count', 'perspective_answers']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        logger.info(f"Starting export_discrepancy_history for project {project_id}")
        logger.info(f"Selected dataset_name: {dataset_name}")

        # Use the same prefetch_related pattern as annotation history
        examples_queryset = Example.objects.filter(project=project).prefetch_related(
            'categories',
            'categories__label',
            'perspective_answers',
            'perspective_answers__perspective',
            'perspective_answers__created_by'
        )

        if dataset_name:
            examples_queryset = examples_queryset.filter(
                Q(filename__icontains=dataset_name) |
                Q(upload_name__icontains=dataset_name)
            )

        logger.info(f"Total examples found: {examples_queryset.count()}")

        for example in examples_queryset:
            try:
                # Count labels for this example (categories)
                label_agg = example.categories.values("label", "label__text").annotate(cnt=Count("label"))
                total = sum(obj["cnt"] for obj in label_agg)
                
                if total == 0:
                    continue

                percentages = {obj["label__text"]: (obj["cnt"] / total) * 100 for obj in label_agg}
                max_percent = max(percentages.values())

                # Get perspective answers for this example
                perspective_answers = example.perspective_answers.all()
                perspectives_data = []
                for pa in perspective_answers:
                    perspectives_data.append({
                        'question': pa.perspective.question,
                        'answer': pa.answer,
                        'answered_by': pa.created_by.username if pa.created_by else 'N/A',
                        'answer_date': pa.created_at.strftime("%Y-%m-%d %H:%M:%S") if pa.created_at else 'N/A'
                    })

                current_dataset_name = "N/A"
                if example.filename and example.filename.name:
                    current_dataset_name = os.path.basename(example.filename.name)
                elif example.upload_name:
                    current_dataset_name = example.upload_name

                row = {
                    'example_id': example.id,
                    'datasetName': current_dataset_name,
                    'text': example.text if example.text else "",
                    'percentages': json.dumps(percentages),
                    'is_discrepancy': max_percent < discrepancy_threshold,
                    'max_percentage': max_percent,
                    'diff_count': len(percentages),
                    'perspective_answers': json.dumps(perspectives_data)
                }
                
                logger.info(f"Writing row for example {example.id}: {row}")
                writer.writerow(row)
                
            except Exception as e:
                logger.error(f"Error processing example {example.id}: {e}", exc_info=True)
    
    logger.info(f"Finished export_discrepancy_history. Filepath: {filepath}")
    return filepath


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def export_perspective_history(project_id, dataset_name=None):
    project = get_object_or_404(Project, pk=project_id)
    dirpath = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
    os.makedirs(dirpath, exist_ok=True)
    
    filepath = os.path.join(dirpath, "perspective_history.csv")
    logger.info(f"Creating perspective history file at: {filepath}")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['question', 'answer', 'answered_by', 'answer_date', 'datasetName', 'example_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            logger.info(f"Starting export_perspective_history for project {project_id}")
            logger.info(f"Selected dataset_name: {dataset_name}")

            examples_queryset = Example.objects.filter(project=project).prefetch_related(
                'perspective_answers',
                'perspective_answers__perspective',
                'perspective_answers__created_by'
            )
            logger.debug(f"Initial examples_queryset count: {examples_queryset.count()}")

            if dataset_name:
                examples_queryset = examples_queryset.filter(
                    Q(filename__icontains=dataset_name) |
                    Q(upload_name__icontains=dataset_name)
                )
            logger.info(f"Total examples found: {examples_queryset.count()}")

            for example in examples_queryset:
                try:
                    current_dataset_name = "N/A"
                    if example.filename and example.filename.name:
                        current_dataset_name = os.path.basename(example.filename.name)
                    elif example.upload_name:
                        current_dataset_name = example.upload_name

                    # Get perspective answers for this example
                    perspective_answers = example.perspective_answers.all()
                    for pa in perspective_answers:
                        row = {
                            'question': pa.perspective.question,
                            'answer': pa.answer,
                            'answered_by': pa.created_by.username if pa.created_by else 'N/A',
                            'answer_date': pa.created_at.strftime("%Y-%m-%d %H:%M:%S") if pa.created_at else 'N/A',
                            'datasetName': current_dataset_name,
                            'example_text': example.text if example.text else ""
                        }
                        logger.info(f"Writing perspective answer row: {row}")
                        writer.writerow(row)

                except Exception as e:
                    logger.error(f"Error processing example {example.id}: {e}", exc_info=True)
                    continue

        # Verify the file was created and has content
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.info(f"Successfully created perspective history file at: {filepath}")
            return filepath
        else:
            logger.error(f"Failed to create perspective history file at: {filepath}")
            raise Exception("Failed to create perspective history file")

    except Exception as e:
        logger.error(f"Error in export_perspective_history: {e}", exc_info=True)
        # Clean up the directory if there was an error
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
        raise


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def export_annotation_history_pdf(project_id, dataset_name=None, annotation_status='All'):
    project = get_object_or_404(Project, pk=project_id)
    dirpath = os.path.join(settings.MEDIA_ROOT, str(uuid.uuid4()))
    os.makedirs(dirpath, exist_ok=True)
    
    filepath = os.path.join(dirpath, "annotation_history.pdf")
    logger.info(f"Creating annotation history PDF at: {filepath}")

    try:
        # Create the PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        normal_style = styles['Normal']

        # Create content
        content = []
        
        # Add title
        title = Paragraph(f"Annotation History Report - {project.name}", title_style)
        content.append(title)
        content.append(Spacer(1, 12))

        # Add report info
        info_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if dataset_name:
            info_text += f"\nDataset: {dataset_name}"
        info_text += f"\nAnnotation Status: {annotation_status}"
        
        info_paragraph = Paragraph(info_text, normal_style)
        content.append(info_paragraph)
        content.append(Spacer(1, 20))

        # Get the data
        examples_queryset = Example.objects.filter(project=project).prefetch_related(
            'assignments',
            'perspective_answers',
            'perspective_answers__perspective',
            'perspective_answers__created_by'
        )

        if dataset_name:
            examples_queryset = examples_queryset.filter(
                Q(filename__icontains=dataset_name) |
                Q(upload_name__icontains=dataset_name)
            )

        ANNOTATION_MODELS = {
            "DocumentClassification": Category,
            "SequenceLabeling": Span,
            "Seq2seq": TextLabel,
            "Speech2text": TextLabel,
            "ImageClassification": Category,
            "BoundingBox": BoundingBox,
            "Segmentation": Segmentation,
            "RelationExtraction": Relation,
        }
        AnnotationModel = ANNOTATION_MODELS.get(project.project_type)

        if annotation_status == 'Finished':
            examples_queryset = examples_queryset.filter(states__isnull=False).distinct()
        elif annotation_status == 'Not started':
            if AnnotationModel:
                examples_queryset = examples_queryset.exclude(
                    Exists(AnnotationModel.objects.filter(example=OuterRef('pk')))
                )
        elif annotation_status == 'In progress':
            if AnnotationModel:
                has_annotations = AnnotationModel.objects.filter(example=OuterRef('pk'))
                examples_queryset = examples_queryset.filter(Exists(has_annotations))
                examples_queryset = examples_queryset.filter(states__isnull=True)

        # Create table data
        table_data = [['Annotator', 'Dataset', 'Label', 'Date', 'Example Text', 'Annotations', 'Perspectives']]
        
        for example in examples_queryset:
            try:
                annotations = []
                annotation_count = 0
                if AnnotationModel:
                    annotations_for_example = AnnotationModel.objects.filter(example=example)
                    annotations.extend(annotations_for_example)
                    annotation_count = annotations_for_example.count()

                current_dataset_name = "N/A"
                if example.filename and example.filename.name:
                    current_dataset_name = os.path.basename(example.filename.name)
                elif example.upload_name:
                    current_dataset_name = example.upload_name

                if not annotations:
                    perspective_answers = example.perspective_answers.all()
                    perspectives_text = "\n".join([
                        f"Q: {pa.perspective.question}\nA: {pa.answer}\nBy: {pa.created_by.username if pa.created_by else 'N/A'}"
                        for pa in perspective_answers
                    ]) if perspective_answers else "N/A"

                    row = [
                        'N/A',
                        current_dataset_name,
                        'N/A',
                        'N/A',
                        example.text[:100] + "..." if len(example.text) > 100 else example.text,
                        str(annotation_count),
                        perspectives_text
                    ]
                    table_data.append(row)
                else:
                    for annotation in annotations:
                        label_text = "N/A"
                        if hasattr(annotation, 'label') and annotation.label:
                            label_text = annotation.label.text
                        elif hasattr(annotation, 'text'):
                            label_text = annotation.text
                        elif hasattr(annotation, 'points'):
                            label_text = annotation.label.text
                        elif hasattr(annotation, 'x'):
                            label_text = annotation.label.text
                        elif isinstance(annotation, Relation):
                            label_text = f"From:{annotation.from_id.id} To:{annotation.to_id.id} Type:{annotation.type.text}"

                        perspective_answers = example.perspective_answers.all()
                        perspectives_text = "\n".join([
                            f"Q: {pa.perspective.question}\nA: {pa.answer}\nBy: {pa.created_by.username if pa.created_by else 'N/A'}"
                            for pa in perspective_answers
                        ]) if perspective_answers else "N/A"

                        row = [
                            annotation.user.username,
                            current_dataset_name,
                            label_text,
                            annotation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                            example.text[:100] + "..." if len(example.text) > 100 else example.text,
                            str(annotation_count),
                            perspectives_text
                        ]
                        table_data.append(row)

            except Exception as e:
                logger.error(f"Error processing example {example.id}: {e}", exc_info=True)
                continue

        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        content.append(table)
        
        # Build PDF
        doc.build(content)

        # Verify the file was created and has content
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            logger.info(f"Successfully created annotation history PDF at: {filepath}")
            return filepath
        else:
            logger.error(f"Failed to create annotation history PDF at: {filepath}")
            raise Exception("Failed to create annotation history PDF")

    except Exception as e:
        logger.error(f"Error in export_annotation_history_pdf: {e}", exc_info=True)
        # Clean up the directory if there was an error
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
        raise
