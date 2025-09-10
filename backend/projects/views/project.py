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
from collections import defaultdict
import os
from django.db.models import Q

from projects.models import Project, PerspectiveAnswer

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
        project = serializer.save(created_by=self.request.user, project_version=1)
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status = instance.status
        new_status = request.data.get('status', old_status)

        # Handle version changes based on status changes
        if new_status != old_status:
            if new_status == "open" and old_status == "closed":
                instance.project_version += 1
            elif new_status == "closed" and old_status == "open":
                # Ensure version doesn't go below 1
                instance.project_version = max(1, instance.project_version - 1)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


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
        try:
            project = get_object_or_404(Project, id=project_id)
            discrepancy_threshold = 70
            examples = Example.objects.filter(project_id=project_id)

            if not examples.exists():
                raise NotFound("No examples found for this project.")

            # Get filter parameters from URL
            filter_perspective = request.query_params.get('perspective')
            filter_answer = request.query_params.get('answer')
            dataset_name = request.query_params.get('dataset_name')

            # Apply dataset filter if specified
            if dataset_name:
                examples = examples.filter(
                    Q(filename__icontains=dataset_name) |
                    Q(upload_name__icontains=dataset_name)
                )

            discrepancies = []
            for example in examples:
                # Get annotations with user information
                labels = example.categories.values(
                    'label', 
                    'label__text', 
                    'user'
                ).annotate(count=Count('label'))
                
                total_labels = sum(label['count'] for label in labels)
                if total_labels == 0:
                    continue

                # Get users who annotated this example
                all_annotators = set(label['user'] for label in labels if label['user'])
                
                # If there's a filter, filter annotators who gave the specific answer
                if filter_perspective and filter_answer:
                    perspective_answers = {}
                    matching_annotators = set()
                    
                    for annotator_id in all_annotators:
                        user_responses = PerspectiveAnswer.objects.filter(
                            project_id=project_id,
                            created_by_id=annotator_id
                        ).select_related('perspective', 'perspective__group')
                        
                        has_matching_answer = False
                        
                        for response in user_responses:
                            group_id = str(response.perspective.group.id)
                            question_id = str(response.perspective.id)
                            
                            if group_id not in perspective_answers:
                                perspective_answers[group_id] = {}
                            if question_id not in perspective_answers[group_id]:
                                perspective_answers[group_id][question_id] = {}
                            
                            perspective_answers[group_id][question_id][str(annotator_id)] = response.answer
                            
                            if (question_id == filter_perspective and 
                                response.answer == filter_answer):
                                has_matching_answer = True
                        
                        if has_matching_answer:
                            matching_annotators.add(annotator_id)
                    
                    if not matching_annotators:
                        continue
                        
                    labels = [label for label in labels if label['user'] in matching_annotators]
                    
                    aggregated = defaultdict(int)
                    for label in labels:
                        aggregated[label['label__text']] += label['count']

                    total_labels = sum(aggregated.values())
                    if total_labels == 0:
                        continue

                    percentages = {k: (v / total_labels) * 100 for k, v in aggregated.items()}
                    max_percentage = max(percentages.values())
                    annotators = matching_annotators
                else:
                    aggregated = defaultdict(int)
                    for label in labels:
                        aggregated[label['label__text']] += label['count']

                    total_labels = sum(aggregated.values())
                    if total_labels == 0:
                        continue

                    percentages = {k: (v / total_labels) * 100 for k, v in aggregated.items()}
                    max_percentage = max(percentages.values())
                    annotators = all_annotators
                    
                    perspective_answers = {}
                    for annotator_id in annotators:
                        user_responses = PerspectiveAnswer.objects.filter(
                            project_id=project_id,
                            created_by_id=annotator_id
                        ).select_related('perspective', 'perspective__group')
                        
                        for response in user_responses:
                            group_id = str(response.perspective.group.id)
                            question_id = str(response.perspective.id)
                            
                            if group_id not in perspective_answers:
                                perspective_answers[group_id] = {}
                            if question_id not in perspective_answers[group_id]:
                                perspective_answers[group_id][question_id] = {}
                            
                            perspective_answers[group_id][question_id][str(annotator_id)] = response.answer

                # Get current dataset name
                current_dataset_name = "N/A"
                if example.filename and example.filename.name:
                    current_dataset_name = os.path.basename(example.filename.name)
                elif example.upload_name:
                    current_dataset_name = example.upload_name

                discrepancy = {
                    "id": example.id,
                    "text": example.text,
                    "datasetName": current_dataset_name,
                    "percentages": percentages,
                    "is_discrepancy": max_percentage < discrepancy_threshold,
                    "max_percentage": max_percentage,
                    "perspective_answers": perspective_answers,
                    "annotators": list(annotators),
                    "numberOfAnnotations": total_labels,
                    "date": example.created_at.strftime("%Y-%m-%d %H:%M:%S") if example.created_at else "N/A"
                }
                
                discrepancies.append(discrepancy)

            return Response({"discrepancies": discrepancies})
            
        except Exception as e:
            print(f"Error in DiscrepancyAnalysisView: {str(e)}")
            return Response(
                {"detail": "An error occurred while processing your request."},
                status=500
            )

