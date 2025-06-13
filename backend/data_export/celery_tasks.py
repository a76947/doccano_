import os
import shutil
import uuid
import csv

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Exists, OuterRef

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

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['annotator', 'datasetName', 'label', 'date', 'example_text', 'numberOfAnnotations']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        logger.info(f"Starting export_annotation_history for project {project_id}")
        logger.info(f"Selected dataset_name: {dataset_name}, annotation_status: {annotation_status}")

        examples_queryset = Example.objects.filter(project=project).prefetch_related('assignments')
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
                    row = {
                        'annotator': 'N/A',
                        'datasetName': current_dataset_name,
                        'label': 'N/A',
                        'date': 'N/A',
                        'example_text': example.text if example.text else "",
                        'numberOfAnnotations': annotation_count
                    }
                    logger.info(f"Writing row (no annotations): {row}")
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

                        row = {
                            'annotator': annotation.user.username,
                            'datasetName': current_dataset_name,
                            'label': label_text,
                            'date': annotation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                            'example_text': example.text if example.text else "",
                            'numberOfAnnotations': annotation_count
                        }
                        logger.info(f"Writing row (with annotation): {row}")
                        writer.writerow(row)
            except Exception as e:
                logger.error(f"Error processing example {example.id}: {e}", exc_info=True)
    
    logger.info(f"Finished export_annotation_history. Filepath: {filepath}")
    return filepath
