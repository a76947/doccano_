from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers
from django.db import IntegrityError
from .models import Perspective

from .models import (
    BoundingBoxProject,
    ImageCaptioningProject,
    ImageClassificationProject,
    IntentDetectionAndSlotFillingProject,
    Member,
    Project,
    SegmentationProject,
    Seq2seqProject,
    SequenceLabelingProject,
    Speech2textProject,
    Tag,
    TextClassificationProject,
    Perspective,
    PerspectiveAnswer,
    PerspectiveGroup,
)


class MemberSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    rolename = serializers.SerializerMethodField()

    @classmethod
    def get_username(cls, instance):
        user = instance.user
        return user.username if user else None

    @classmethod
    def get_rolename(cls, instance):
        role = instance.role
        return role.name if role else None

    class Meta:
        model = Member
        fields = ("id", "user", "role", "username", "rolename")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "project",
            "text",
        )
        read_only_fields = ("id", "project")


class ProjectSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    author = serializers.SerializerMethodField()

    @classmethod
    def get_author(cls, instance):
        if instance.created_by:
            return instance.created_by.username
        return ""

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "guideline",
            "project_type",
            "created_at",
            "updated_at",
            "random_order",
            "author",
            "collaborative_annotation",
            "single_class_classification",
            "allow_member_to_create_label_type",
            "is_text_project",
            "tags",
        ]
        read_only_fields = (
            "created_at",
            "updated_at",
            "author",
            "is_text_project",
        )

    def create(self, validated_data):
        tags = TagSerializer(data=validated_data.pop("tags", []), many=True)
        project = self.Meta.model.objects.create(**validated_data)
        tags.is_valid()
        tags.save(project=project)
        return project

    def update(self, instance, validated_data):
        # Don't update tags. Please use TagAPI.
        validated_data.pop("tags", None)
        return super().update(instance, validated_data)


class TextClassificationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = TextClassificationProject


class SequenceLabelingProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = SequenceLabelingProject
        fields = ProjectSerializer.Meta.fields + ["allow_overlapping", "grapheme_mode", "use_relation"]


class Seq2seqProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = Seq2seqProject


class IntentDetectionAndSlotFillingProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = IntentDetectionAndSlotFillingProject


class Speech2textProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = Speech2textProject


class ImageClassificationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = ImageClassificationProject


class BoundingBoxProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = BoundingBoxProject


class SegmentationProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = SegmentationProject


class ImageCaptioningProjectSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        model = ImageCaptioningProject


class ProjectPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        Project: ProjectSerializer,
        **{cls.Meta.model: cls for cls in ProjectSerializer.__subclasses__()},
    }

        
class PerspectiveSerializer(serializers.ModelSerializer):
    options = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    class Meta:
        model = Perspective
        fields = ['id', 'name', 'question', 'data_type', 'options', 'group', 'project']
        read_only_fields = ['id']

    def validate(self, attrs):
        group = attrs.get('group') or getattr(self.instance, 'group', None)
        question = attrs.get('question')
        if group and question:
            exists = Perspective.objects.filter(group=group, question=question)
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise serializers.ValidationError({
                    'question': 'Já existe uma pergunta com este texto neste grupo.'
                })
        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError({
                'question': 'Já existe uma pergunta com este texto neste grupo.'
            })
        

class PerspectiveGroupSerializer(serializers.ModelSerializer):
    questions = PerspectiveSerializer(many=True, read_only=True)
    
    class Meta:
        model = PerspectiveGroup
        fields = ['id', 'name', 'description', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']

class PerspectiveAnswerSerializer(serializers.ModelSerializer):
    created_by_username = serializers.SerializerMethodField()
    # If there's no created_at field, you can add a method field to return current time
    created_at = serializers.SerializerMethodField(required=False)
    
    class Meta:
        model = PerspectiveAnswer
        fields = [
            'id', 'perspective', 'project', 'example', 'answer', 
            'created_by', 'created_by_username', 'created_at'
        ]
    
    def get_created_by_username(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return None
    
    def get_created_at(self, obj):
        # If your model has a different timestamp field, use that
        if hasattr(obj, 'created_date'):
            return obj.created_date
        if hasattr(obj, 'timestamp'):
            return obj.timestamp
        # Otherwise return current time
        from django.utils import timezone
        return timezone.now()
