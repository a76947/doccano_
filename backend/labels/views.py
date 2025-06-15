from functools import partial
from typing import Type

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CanEditLabel
from .serializers import (
    BoundingBoxSerializer,
    CategorySerializer,
    RelationSerializer,
    SegmentationSerializer,
    SpanSerializer,
    TextLabelSerializer,
)
from labels.models import (
    BoundingBox,
    Category,
    Label,
    Relation,
    Segmentation,
    Span,
    TextLabel,
)
from projects.models import Project
from projects.permissions import IsProjectMember


class BaseListAPI(generics.ListCreateAPIView):
    label_class: Type[Label]
    pagination_class = None
    permission_classes = [IsAuthenticated & IsProjectMember]
    swagger_schema = None

    @property
    def project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_id"])

    def get_queryset(self):
        queryset = self.label_class.objects.filter(example=self.kwargs["example_id"])
        # Se tiver ?all=1 e o utilizador for admin do projecto, devolve todas as anotações
        show_all = self.request.query_params.get("all") in ["1", "true", "True"]

        if not self.project.collaborative_annotation and not (show_all and self.request.user.is_staff):
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def create(self, request, *args, **kwargs):
        request.data["example"] = self.kwargs["example_id"]
        try:
            response = super().create(request, args, kwargs)
        except ValidationError as err:
            response = Response({"detail": err.messages}, status=status.HTTP_400_BAD_REQUEST)
        return response

    def perform_create(self, serializer):
        serializer.save(example_id=self.kwargs["example_id"], user=self.request.user)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = "annotation_id"
    swagger_schema = None

    @property
    def project(self):
        return get_object_or_404(Project, pk=self.kwargs["project_id"])

    def get_permissions(self):
        if self.project.collaborative_annotation:
            self.permission_classes = [IsAuthenticated & IsProjectMember]
        else:
            self.permission_classes = [IsAuthenticated & IsProjectMember & partial(CanEditLabel, self.queryset)]
        return super().get_permissions()


class CategoryListAPI(BaseListAPI):
    label_class = Category
    serializer_class = CategorySerializer

    def create(self, request, *args, **kwargs):
        if self.project.single_class_classification:
            self.get_queryset().delete()
        return super().create(request, args, kwargs)


class CategoryDetailAPI(BaseDetailAPI):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SpanListAPI(BaseListAPI):
    label_class = Span
    serializer_class = SpanSerializer


class SpanDetailAPI(BaseDetailAPI):
    queryset = Span.objects.all()
    serializer_class = SpanSerializer


class TextLabelListAPI(BaseListAPI):
    label_class = TextLabel
    serializer_class = TextLabelSerializer


class TextLabelDetailAPI(BaseDetailAPI):
    queryset = TextLabel.objects.all()
    serializer_class = TextLabelSerializer


class RelationList(BaseListAPI):
    label_class = Relation
    serializer_class = RelationSerializer


class RelationDetail(BaseDetailAPI):
    queryset = Relation.objects.all()
    serializer_class = RelationSerializer


class BoundingBoxListAPI(BaseListAPI):
    label_class = BoundingBox
    serializer_class = BoundingBoxSerializer


class BoundingBoxDetailAPI(BaseDetailAPI):
    queryset = BoundingBox.objects.all()
    serializer_class = BoundingBoxSerializer


class SegmentationListAPI(BaseListAPI):
    label_class = Segmentation
    serializer_class = SegmentationSerializer


class SegmentationDetailAPI(BaseDetailAPI):
    queryset = Segmentation.objects.all()
    serializer_class = SegmentationSerializer


class ProjectLabelsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        categories = Category.objects.filter(example__project=project)
        spans = Span.objects.filter(example__project=project)
        text_labels = TextLabel.objects.filter(example__project=project)
        relations = Relation.objects.filter(example__project=project)
        bounding_boxes = BoundingBox.objects.filter(example__project=project)
        segmentations = Segmentation.objects.filter(example__project=project)

        labels = {
            "categories": [
                {"label": category.label.text, "user": category.user.username}
                for category in categories
            ],
            "spans": [
                {"label": span.label.text, "user": span.user.username}
                for span in spans
            ],
            "text_labels": [
                {"label": text_label.text, "user": text_label.user.username}
                for text_label in text_labels
            ],
            "relations": [
                {"label": relation.type.text, "user": relation.user.username}
                for relation in relations
            ],
            "bounding_boxes": [
                {"label": bbox.label.text, "user": bbox.user.username}
                for bbox in bounding_boxes
            ],
            "segmentations": [
                {"label": segmentation.label.text, "user": segmentation.user.username}
                for segmentation in segmentations
            ],
        }

        return Response(labels)
