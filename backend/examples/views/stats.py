from datetime import datetime

from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from projects.permissions import IsProjectMember
from labels.models import Category
from label_types.models import CategoryType


class LabelVoteHistoryView(APIView):
    """Return cumulative vote counts per label after each annotation ("versões").

    Query-parameters
    ----------------
    before : ISO-8601 datetime (opcional)
        Considere apenas anotações criadas até esta data.
    version : int (opcional)
        Snapshot até à N-ésima anotação.
    progress : int 0-100 (opcional)
        Snapshot correspondente a X % do total de anotações.
        Ignorado se "version" for fornecido.
    """

    permission_classes = [IsAuthenticated & IsProjectMember]

    def get(self, request, project_id: int):
        qs = Category.objects.filter(example__project_id=project_id).order_by("created_at", "id")

        before_param = request.query_params.get("before")
        if before_param:
            try:
                before_dt = datetime.fromisoformat(before_param)
            except ValueError:
                return Response({"detail": "Invalid 'before' param"}, status=400)
            qs = qs.filter(created_at__lte=before_dt)

        total_annotations = qs.count()
        if total_annotations == 0:
            return Response([])

        # Map id -> text for faster lookup
        label_text_map = {
            obj.id: obj.text for obj in CategoryType.objects.filter(project_id=project_id)
        }

        # Apply version / progress filters (deterministic slice)
        version_param = request.query_params.get("version")
        progress_param = request.query_params.get("progress")
        if version_param is not None:
            try:
                version_n = int(version_param)
                if version_n < 1:
                    raise ValueError
            except ValueError:
                return Response({"detail": "version must be positive integer"}, status=400)
            qs = qs[:version_n]
        elif progress_param is not None:
            try:
                prog = int(progress_param)
                if not 0 <= prog <= 100:
                    raise ValueError
            except ValueError:
                return Response({"detail": "progress must be integer 0-100"}, status=400)
            slice_len = max(1, int(total_annotations * prog / 100))
            qs = qs[:slice_len]

        # Build cumulative counts
        cumulative = {}
        results = []
        version_counter = 0
        add_all_versions = version_param is None and progress_param is None

        for cat in qs:
            version_counter += 1
            cumulative[cat.label_id] = cumulative.get(cat.label_id, 0) + 1

            if add_all_versions:
                results.append(self._snapshot_obj(version_counter, cumulative, label_text_map))

        if not add_all_versions:
            results.append(self._snapshot_obj(version_counter, cumulative, label_text_map))

        return Response(results)

    @staticmethod
    def _snapshot_obj(version: int, cum_dict: dict, label_map: dict):
        labels = []
        votes = []
        for lid, cnt in cum_dict.items():
            labels.append(label_map.get(lid, str(lid)))
            votes.append(cnt)
        return {"version": version, "labels": labels, "votes": votes} 