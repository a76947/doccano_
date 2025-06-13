from rest_framework import serializers

from .models import Assignment, Comment, Example, ExampleState


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comment
        fields = (
            "id",
            "user",
            "username",
            "example",
            "label",        # campo exposto
            "text",
            "created_at",
        )
        read_only_fields = ("user", "example", "username")


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Assignment
        fields = ("id", "assignee", "example", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ExampleSerializer(serializers.ModelSerializer):
    annotation_approver = serializers.SerializerMethodField()
    is_confirmed        = serializers.SerializerMethodField()
    assignments         = serializers.SerializerMethodField()

    @staticmethod
    def get_annotation_approver(instance):
        return instance.annotations_approved_by.username \
            if instance.annotations_approved_by else None

    def get_is_confirmed(self, instance):
        user = self.context.get("request").user
        states = (
            instance.states.all()
            if instance.project.collaborative_annotation
            else instance.states.filter(confirmed_by_id=user.id)
        )
        return states.exists()

    def get_assignments(self, instance):
        return [
            {
                "id": a.id,
                "assignee": a.assignee.username,
                "assignee_id": a.assignee.id,
            }
            for a in instance.assignments.all()
        ]

    class Meta:
        model  = Example
        fields = [
            "id",
            "filename",
            "meta",
            "annotation_approver",
            "comment_count",
            "text",
            "is_confirmed",
            "upload_name",
            "score",
            "assignments",
        ]
        read_only_fields = (
            "filename",
            "is_confirmed",
            "upload_name",
            "assignments",
        )


class ExampleStateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ExampleState
        fields = ("id", "example", "confirmed_by", "confirmed_at")
        read_only_fields = ("id", "example", "confirmed_by", "confirmed_at")
