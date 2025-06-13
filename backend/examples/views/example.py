from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import os
import logging

from examples.filters import ExampleFilter
from examples.models import Example
from examples.serializers import ExampleSerializer
from projects.models import Member, Project
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly

logger = logging.getLogger(__name__)


class ExampleList(generics.ListCreateAPIView):
    serializer_class = ExampleSerializer
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ("created_at", "updated_at", "score")
    search_fields = ("text", "filename")
    model = Example
    filterset_class = ExampleFilter

    @property
    def project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_id"])

    def get_queryset(self):
        member = get_object_or_404(Member, project=self.project, user=self.request.user)
        if member.is_admin():
            return self.model.objects.filter(project=self.project)

        queryset = self.model.objects.filter(project=self.project, assignments__assignee=self.request.user)
        if self.project.random_order:
            queryset = queryset.order_by("assignments__id")
        return queryset

    def perform_create(self, serializer):
        serializer.save(project=self.project)

    def delete(self, request, *args, **kwargs):
        queryset = self.project.examples
        delete_ids = request.data["ids"]
        if delete_ids:
            queryset.filter(pk__in=delete_ids).delete()
        else:
            queryset.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExampleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Example.objects.all()
    serializer_class = ExampleSerializer
    lookup_url_kwarg = "example_id"
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]


class DatasetNamesAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin] # Or appropriate permissions

    def get(self, request, *args, **kwargs):
        project_id = kwargs["project_id"]
        project = get_object_or_404(Project, pk=project_id)
        
        dataset_names = []
        for example in Example.objects.filter(project=project):
            logger.info(f"Processing example ID: {example.id}")
            logger.info(f"  example.filename.name: {example.filename.name if example.filename else 'N/A'}")
            logger.info(f"  example.upload_name: {example.upload_name if example.upload_name else 'N/A'}")
            if example.upload_name:
                dataset_names.append(example.upload_name)
            elif example.filename:
                dataset_names.append(os.path.basename(example.filename.name))
        
        # Get unique dataset names
        unique_dataset_names = sorted(list(set(dataset_names)))

        return Response({"datasetNames": unique_dataset_names}, status=status.HTTP_200_OK)
