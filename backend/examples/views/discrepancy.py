from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from examples.models import Example
from projects.models import Project


class DiscrepancyAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        # Threshold (percentage) below which we consider there is a discrepancy
        discrepancy_threshold = 70  # e.g. 70 %

        project = get_object_or_404(Project, id=project_id)

        examples = Example.objects.filter(project_id=project_id)
        if not examples.exists():
            raise NotFound("No examples found for this project.")

        # perspective_<id>=val1,val2 query params
        perspective_filters = {}
        for key, value in request.query_params.items():
            if key.startswith("perspective_"):
                q_id = key.replace("perspective_", "")
                perspective_filters[q_id] = value.split(",") if "," in value else [value]

        discrepancies = []
        for example in examples:
            # count labels for this example (categories)
            label_agg = example.categories.values("label", "label__text").annotate(cnt=Count("label"))
            total = sum(obj["cnt"] for obj in label_agg)
            if total == 0:
                continue

            percentages = {obj["label__text"]: (obj["cnt"] / total) * 100 for obj in label_agg}
            max_percent = max(percentages.values())

            # Perspective answers filtering (optional)
            perspective_answers = {}
            if perspective_filters:
                answers = example.project.perspective_answers.all() if hasattr(example.project, "perspective_answers") else []
                for ans in answers:
                    perspective_answers[str(ans.perspective.id)] = ans.answer

            matches_filters = True
            if perspective_filters:
                for q_id, allowed in perspective_filters.items():
                    if q_id not in perspective_answers or perspective_answers[q_id] not in allowed:
                        matches_filters = False
                        break

            if not matches_filters:
                continue

            discrepancies.append(
                {
                    "id": example.id,
                    "text": example.text,
                    "percentages": percentages,
                    "is_discrepancy": max_percent < discrepancy_threshold,
                    "max_percentage": max_percent,
                    "diff_count": len(percentages),
                }
            )

        return Response({"discrepancies": discrepancies}) 