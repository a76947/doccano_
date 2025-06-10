from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, views
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from examples.models import Example
from django.db.models import Count
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from projects.models import Project
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly
from projects.serializers import ProjectPolymorphicSerializer


class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectPolymorphicSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ["name", "created_at", "created_by", "project_type"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [
                IsAuthenticated,
            ]
        else:
            self.permission_classes = [IsAuthenticated & IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        return Project.objects.filter(role_mappings__user=self.request.user)

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        project.add_admin()

    def delete(self, request, *args, **kwargs):
        delete_ids = request.data["ids"]
        projects = Project.objects.filter(
            role_mappings__user=self.request.user,
            role_mappings__role__name=settings.ROLE_PROJECT_ADMIN,
            pk__in=delete_ids,
        )
        # Todo: I want to use bulk delete.
        # But it causes the constraint error.
        # See https://github.com/django-polymorphic/django-polymorphic/issues/229
        for project in projects:
            project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectPolymorphicSerializer
    lookup_url_kwarg = "project_id"
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]


class CloneProject(views.APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        cloned_project = project.clone()
        serializer = ProjectPolymorphicSerializer(cloned_project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class DiscrepancyAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        # Valor fixo de discrepância
        discrepancy_threshold = 70
        examples = Example.objects.filter(project_id=project_id)

        if not examples.exists():
            raise NotFound("No examples found for this project.")

        discrepancies = []
        for example in examples:
            labels = example.categories.values('label', 'label__text').annotate(count=Count('label'))
            total_labels = sum(label['count'] for label in labels)

            if total_labels > 0:
                percentages = {label['label__text']: (label['count'] / total_labels) * 100 for label in labels}
                max_percentage = max(percentages.values())

                # Sempre incluir o exemplo, mas marcar se é uma discrepância
                discrepancies.append({
                    "id": example.id,
                    "text": example.text,
                    "percentages": percentages,
                    "is_discrepancy": max_percentage < discrepancy_threshold,
                    "max_percentage": max_percentage
                })

        return Response({
            "discrepancies": discrepancies
        })