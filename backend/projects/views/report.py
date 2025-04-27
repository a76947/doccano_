from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from django.utils.dateparse import parse_datetime

from projects.models import Project
from labels.models import Span, Category, TextLabel


class AnnotationReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        project_type = project.project_type

        user_id = request.query_params.get('user')
        label_text = request.query_params.get('label')
        search_text = request.query_params.get('text')
        start = request.query_params.get('start')

        result = []

        if project_type == 'SequenceLabeling':
            query = Q(example__project=project)
            if user_id:
                query &= Q(user_id=user_id)
            if start:
                start_dt = parse_datetime(start)
                if start_dt:
                    query &= Q(updated_at__gte=start_dt)

            annotations = Span.objects.filter(query)
            if label_text:
                annotations = annotations.filter(label__text=label_text)
            if search_text:
                annotations = annotations.filter(example__text__icontains=search_text)

            for ann in annotations:
                result.append({
                    'text': ann.example.text,
                    'label': ann.label.text,
                    'user': ann.user.username,
                    'updated_at': ann.updated_at,
                })

        elif project_type == 'DocumentClassification':
            query = Q(example__project=project)
            if user_id:
                query &= Q(user_id=user_id)
            if start:
                start_dt = parse_datetime(start)
                if start_dt:
                    query &= Q(updated_at__gte=start_dt)

            annotations = Category.objects.filter(query)
            if label_text:
                annotations = annotations.filter(label__text=label_text)
            if search_text:
                annotations = annotations.filter(example__text__icontains=search_text)

            for ann in annotations:
                result.append({
                    'text': ann.example.text,
                    'label': ann.label.text,
                    'user': ann.user.username,
                    'updated_at': ann.updated_at,
                })

        elif project_type == 'Seq2seq':
            query = Q(example__project=project)
            if user_id:
                query &= Q(user_id=user_id)
            if start:
                start_dt = parse_datetime(start)
                if start_dt:
                    query &= Q(updated_at__gte=start_dt)

            annotations = TextLabel.objects.filter(query)
            if search_text:
                annotations = annotations.filter(example__text__icontains=search_text)

            for ann in annotations:
                result.append({
                    'text': ann.example.text,
                    'label': ann.text,
                    'user': ann.user.username,
                    'updated_at': ann.updated_at,
                })

        else:
            return Response({"detail": f"Tipo de projeto '{project_type}' não suportado."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)
