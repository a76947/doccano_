import abc

from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from examples.models import Example, ExampleState
from label_types.models import CategoryType, LabelType, RelationType, SpanType
from labels.models import Category, Label, Relation, Span
from projects.models import Member, Project
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly


class ProgressAPI(APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    def get(self, request, *args, **kwargs):
        examples = Example.objects.filter(project=self.kwargs["project_id"]).values("id")
        total = examples.count()
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        if project.collaborative_annotation:
            complete = ExampleState.objects.count_done(examples)
        else:
            complete = ExampleState.objects.count_done(examples, user=self.request.user)
        data = {"total": total, "remaining": total - complete, "complete": complete}
        return Response(data=data, status=status.HTTP_200_OK)


class MemberProgressAPI(APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    def get(self, request, *args, **kwargs):
        examples = Example.objects.filter(project=self.kwargs["project_id"]).values("id")
        members = Member.objects.filter(project=self.kwargs["project_id"])
        data = ExampleState.objects.measure_member_progress(examples, members)
        return Response(data=data, status=status.HTTP_200_OK)


class LabelDistribution(abc.ABC, APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    model = Label
    label_type = LabelType

    def get(self, request, *args, **kwargs):
        labels = self.label_type.objects.filter(project=self.kwargs["project_id"])
        examples = Example.objects.filter(project=self.kwargs["project_id"]).values("id")
        members = Member.objects.filter(project=self.kwargs["project_id"])
        data = self.model.objects.calc_label_distribution(examples, members, labels)
        return Response(data=data, status=status.HTTP_200_OK)


class CategoryTypeDistribution(LabelDistribution):
    model = Category
    label_type = CategoryType


class SpanTypeDistribution(LabelDistribution):
    model = Span
    label_type = SpanType


class RelationTypeDistribution(LabelDistribution):
    model = Relation
    label_type = RelationType


class DatasetStatisticsAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, project_id):
        # Log all incoming parameters
        print(f"===== DATASET STATISTICS REQUEST =====")
        print(f"Request parameters: {request.query_params}")
        
        # Get request parameters with defaults
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        status_filter = request.query_params.get('status')
        annotation_filter = request.query_params.get('annotation_type')
        ordering = request.query_params.get('ordering', '-updated_at')  # Default sort by updated_at desc
        
        # Get label filter parameters - THIS IS NEW
        label_type = request.query_params.get('label_type')
        label_id = request.query_params.get('label_id')
        
        # Get assignee filter parameter - THIS IS NEW
        assignee = request.query_params.get('assignee') or request.query_params.get('username')
        
        # Field name mapping from frontend to database
        field_mapping = {
            'updatedAt': 'updated_at',
            'id': 'id',
            'text': 'text',  # Add text as a sortable field
            'status': None,  # Special handling for status
            'categoryCount': None,  # Special handling for counts
            'spanCount': None,
            'relationCount': None
        }
        
        # Basic query
        query = Example.objects.filter(project_id=project_id)
        
        # Get the total count before applying filters
        total = query.count()
        
        # Apply filters if provided
        filtered_query = query
        if status_filter:
            if status_filter == 'annotated':
                filtered_query = filtered_query.filter(states__isnull=False).distinct()
            elif status_filter == 'pending':
                filtered_query = filtered_query.filter(states__isnull=True)
        
        if annotation_filter:
            if annotation_filter == 'hasCategories':
                filtered_query = filtered_query.filter(categories__isnull=False).distinct()
            elif annotation_filter == 'hasSpans':
                filtered_query = filtered_query.filter(spans__isnull=False).distinct()
            elif annotation_filter == 'hasRelations':
                filtered_query = filtered_query.filter(relations__isnull=False).distinct()
            elif annotation_filter == 'noAnnotations':
                filtered_query = filtered_query.filter(
                    categories__isnull=True, 
                    spans__isnull=True,
                    relations__isnull=True
                )
        
        # Label type and ID filtering
        if label_type and label_id:
            try:
                # Remove any ':' prefix if it exists
                if ':' in label_id:
                    label_id = label_id.split(':')[1]
                
                # Convert to integer for database query
                label_id = int(label_id)
                
                print(f"Filtering by label: {label_type}, id={label_id}")
                
                if label_type == 'category':
                    filtered_query = filtered_query.filter(categories__label=label_id).distinct()
                elif label_type == 'span':
                    filtered_query = filtered_query.filter(spans__label=label_id).distinct()
                elif label_type == 'relation':
                    filtered_query = filtered_query.filter(relations__type=label_id).distinct()
            except (ValueError, TypeError) as e:
                print(f"Error filtering by label: {e}")
                # Don't apply filter if we can't parse the ID
        
        # Assignee filtering
        if assignee:
            try:
                print(f"Filtering by assignee: {assignee}")
                
                # Try Option 1: Use assignments relationship instead of states
                try:
                    filtered_query = filtered_query.filter(assignments__assignee__username=assignee).distinct()
                    print(f"Filtering by assignments__assignee__username succeeded")
                except Exception as e1:
                    print(f"Filtering by assignments failed: {e1}")
                    
                    # Try Option 2: Use a different field name for user in states
                    try:
                        filtered_query = filtered_query.filter(states__annotator__username=assignee).distinct()
                        print(f"Filtering by states__annotator__username succeeded")
                    except Exception as e2:
                        print(f"Filtering by annotator failed: {e2}")
                        
                        # Try Option 3: Use the assignment model directly with a subquery
                        try:
                            from django.db.models import Exists, OuterRef
                            from django.contrib.auth.models import User
                            
                            user = User.objects.filter(username=assignee).first()
                            if user:
                                from examples.models import Assignment
                                assignment_subquery = Assignment.objects.filter(
                                    example=OuterRef('pk'),
                                    assignee=user
                                )
                                filtered_query = filtered_query.filter(Exists(assignment_subquery)).distinct()
                                print(f"Filtering by assignment subquery succeeded")
                        except Exception as e3:
                            print(f"All assignee filtering approaches failed. Last error: {e3}")
                            
            except Exception as e:
                print(f"Error in assignee filtering: {e}")
        
        # Fix the Unknown sort field issue
        if ordering:
            original_ordering = ordering
            sort_field = ordering.lstrip('-')
            sort_direction = '-' if ordering.startswith('-') else ''
            
            print(f"Sort request: original={original_ordering}, field={sort_field}, direction={sort_direction}")
            
            # Special handling for status field which maps to states__isnull
            if sort_field == 'status':
                print("Applying status sort")
                if sort_direction == '-':
                    filtered_query = filtered_query.annotate(
                        has_states=Count('states')
                    ).order_by('-has_states')
                else:
                    filtered_query = filtered_query.annotate(
                        has_states=Count('states')
                    ).order_by('has_states')
            # Special handling for annotation count fields
            elif sort_field == 'categoryCount':
                print("Applying category count sort")
                filtered_query = filtered_query.annotate(
                    cat_count=Count('categories')
                ).order_by(f'{sort_direction}cat_count')
            elif sort_field == 'spanCount':
                print("Applying span count sort")
                filtered_query = filtered_query.annotate(
                    span_count=Count('spans')
                ).order_by(f'{sort_direction}span_count')
            elif sort_field == 'relationCount':
                print("Applying relation count sort")
                filtered_query = filtered_query.annotate(
                    rel_count=Count('relations')
                ).order_by(f'{sort_direction}rel_count')
            # Standard field sorting
            elif sort_field in field_mapping:
                db_field = field_mapping[sort_field]
                if db_field is not None:
                    print(f"Applying standard sort on {db_field}")
                    filtered_query = filtered_query.order_by(f'{sort_direction}{db_field}')
                else:
                    print(f"Field {sort_field} mapped to None, defaulting to updated_at")
                    filtered_query = filtered_query.order_by('-updated_at')
            else:
                print(f"Unknown sort field: {sort_field}, defaulting to updated_at")
                filtered_query = filtered_query.order_by('-updated_at')
        
        # Count annotated examples
        annotated_count = Example.objects.filter(
            project_id=project_id,
            states__isnull=False
        ).distinct().count()
        
        # Get filtered count
        filtered_total = filtered_query.count()
        
        # Apply pagination
        start = (page - 1) * page_size
        end = page * page_size
        # Use the already ordered query for pagination
        paginated_query = filtered_query[start:end]

        # Print final query for debugging
        print(f"Final filtered count: {filtered_total} out of {total} total")
        
        # Format the entries
        entries = []
        for example in paginated_query:
            entries.append({
                'id': example.id,
                'text': example.text[:100] + '...' if len(example.text) > 100 else example.text,
                'annotated': example.states.exists(),
                'categoryCount': example.categories.count(),
                'spanCount': example.spans.count(),
                'relationCount': example.relations.count(),
                'updatedAt': example.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        data = {
            'total': total,  # Total in database
            'filtered': filtered_total,  # Count after filters
            'annotated': annotated_count,
            'unannotated': total - annotated_count,
            'entries': entries,
            'page': page,
            'pageSize': page_size,
            'totalPages': (filtered_total + page_size - 1) // page_size  # Ceiling division
        }

        return Response(data)
