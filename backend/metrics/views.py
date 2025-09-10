import abc
import json
import io
import logging
from datetime import datetime
from io import BytesIO

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.textlabels import Label as ChartLabel
from django.http import HttpResponse
from django.contrib.auth.models import User

from examples.models import Example, ExampleState
from label_types.models import CategoryType, LabelType, RelationType, SpanType
from labels.models import Category, Label, Relation, Span
from projects.models import Member, Project, PerspectiveAnswer
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly

logger = logging.getLogger(__name__)

# Define HTTP status codes at module level to ensure availability
HTTP_200_OK = status.HTTP_200_OK
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR

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
        
        # --- NEW DEBUGGING STEP: Print all perspective answers ---
        from projects.models import PerspectiveAnswer # Ensure imported
        all_perspective_answers = PerspectiveAnswer.objects.filter(project_id=project_id).select_related('created_by', 'perspective')
        print("DEBUG: All Perspective Answers in Project:")
        if all_perspective_answers.exists():
            for pa in all_perspective_answers:
                print(f"DEBUG:    User: {pa.created_by.username} (ID: {pa.created_by.id}), Question: {pa.perspective.id} - {pa.perspective.question}, Answer: {pa.answer}")
        else:
            print("DEBUG:    No perspective answers found in this project.")
        print("----------------------------------------------------")
        # --- END NEW DEBUGGING STEP ---
        
        # Get request parameters with defaults
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        status_filter = request.query_params.get('status')
        annotation_filter = request.query_params.get('annotation_type')
        ordering = request.query_params.get('ordering', '-updated_at')  # Default sort by updated_at desc
        
        # Get label filter parameters
        label_type = request.query_params.get('label_type')
        label_id = request.query_params.get('label_id')
        
        # Get assignee filter parameter
        assignee = request.query_params.get('assignee') or request.query_params.get('username')

        # Get perspective filters
        perspective_filters = request.query_params.get('perspective_filters')
        if perspective_filters:
            try:
                perspective_filters = json.loads(perspective_filters)
            except json.JSONDecodeError:
                print("Error decoding perspective filters JSON")
                perspective_filters = None
        
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
        
        # Initialize matching_users_ids. If no perspective filters are applied, this will remain None.
        # If filters are applied, it will contain the IDs of users who match all filters.
        matching_users_ids = None

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

        # Apply perspective filters based on annotator's answers
        if perspective_filters:
            print(f"DEBUG: Applying annotator-perspective filters: {perspective_filters}")

            # 2. Get the IDs of users who match ALL combined perspective filters
            from django.db.models import Subquery, OuterRef, Count
            from projects.models import PerspectiveAnswer # Ensure this is imported at the top
            from projects.models import Member # Ensure this is imported at the top for all_project_annotators_ids
            from django.contrib.auth.models import User # Import User model for direct querying

            # Start with all users who are members of this project.
            # We use distinct() to avoid duplicate users if they have multiple role mappings.
            users_matching_filters_queryset = User.objects.filter(role_mappings__project_id=project_id).distinct()

            num_active_perspective_filters = 0

            for question_id, selected_values in perspective_filters.items():
                if not selected_values: # Skip if no values selected for this question
                    continue

                num_active_perspective_filters += 1
                
                # Build a Q object for the specific question and its allowed answers
                # Corrected the reverse relation to 'perspectiveanswer' (singular, lowercase model name)
                single_question_answer_condition = Q(
                    perspectiveanswer__perspective__id=question_id
                )
                values_q = Q()
                values_to_check = selected_values if isinstance(selected_values, list) else [selected_values]
                for val in values_to_check:
                    if isinstance(val, bool):
                        val_str = 'Yes' if val else 'No'
                    else:
                        val_str = str(val)
                    values_q |= Q(perspectiveanswer__answer=val_str)
                
                # Combine question ID and answer values
                single_question_answer_condition &= values_q

                # Chain the filters. Each filter call adds an INNER JOIN, implementing the AND logic.
                # We apply distinct after each filter to manage potential duplicates from joins.
                users_matching_filters_queryset = users_matching_filters_queryset.filter(single_question_answer_condition).distinct()

            # Final step: If there were active filters, matching_users_ids will be built from the filtered queryset
            if num_active_perspective_filters > 0:
                matching_users_ids = list(users_matching_filters_queryset.values_list('id', flat=True))
            else:
                # If no filters were provided or no active filters, no users match by default for this logic
                matching_users_ids = []

            print(f"DEBUG: FINAL Matching user IDs (New Logic - Chained Filters and Corrected Relation): {matching_users_ids}")

            if not matching_users_ids:
                # If no users match all perspective filters, we don't filter documents at all
                # (they will all be passed, but their individual charts might be empty)
                print("DEBUG: No users match all perspective filters. Document list will NOT be filtered by perspective at this stage.")
                # Keep filtered_query as is, effectively no document-level filtering by perspective
            else:
                # Filter documents to only include those annotated by at least one matching user
                has_matching_annotator = Q(
                    Q(categories__user__id__in=matching_users_ids) |
                    Q(spans__user__id__in=matching_users_ids) |
                    Q(relations__user__id__in=matching_users_ids)
                )
                filtered_query = filtered_query.filter(has_matching_annotator).distinct()
                print(f"DEBUG: Documents filtered to those with annotations by matching users. Count: {filtered_query.count()}")

            print(f"DEBUG: Examples count AFTER annotator-perspective filter: {filtered_query.count()}")
            # Only print SQL query if the queryset is not empty
            if filtered_query.exists():
                print(f"DEBUG: Generated SQL Query (after annotator-perspective filter): {filtered_query.query}")
            else:
                print(f"DEBUG: Queryset is empty, skipping SQL query generation.")

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
            # Get label counts for this example, filtered by matching_users_ids if available
            category_counts = {}
            # Check if matching_users_ids is set (i.e., perspective filter is active and found matching users)
            if matching_users_ids is not None: 
                # Filter categories by users who match the perspective filters
                categories_for_example = example.categories.filter(user__id__in=matching_users_ids)
            else:
                # If no perspective filter, consider all categories for the example
                categories_for_example = example.categories.all()

            for category in categories_for_example:
                label_text = category.label.text
                category_counts[label_text] = category_counts.get(label_text, 0) + 1

            entries.append({
                'id': example.id,
                'text': example.text[:100] + '...' if len(example.text) > 100 else example.text,
                'annotated': example.states.exists(),
                'categoryCount': categories_for_example.count(), # Update count based on filtered categories
                'spanCount': example.spans.count(),
                'relationCount': example.relations.count(),
                'updatedAt': example.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'labelDistribution': category_counts  # Add the label distribution
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


class DatasetReportAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def create_bar_chart(self, data, title, width=400, height=200):
        """Create a bar chart using reportlab's drawing capabilities."""
        drawing = Drawing(width, height)
        
        # Create the bar chart
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = height - 100
        bc.width = width - 100
        bc.data = [list(data.values())]
        bc.categoryAxis.categoryNames = list(data.keys())
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 20
        
        # Customize the appearance
        bc.bars[0].fillColor = colors.Color(0.8, 0.9, 1)  # Light blue
        bc.bars[0].strokeColor = colors.black
        
        # Customize axes
        bc.categoryAxis.labels.fontName = 'Helvetica'
        bc.categoryAxis.labels.fontSize = 8
        bc.categoryAxis.labels.angle = 45
        bc.categoryAxis.labels.dy = -10
        
        bc.valueAxis.labels.fontName = 'Helvetica'
        bc.valueAxis.labels.fontSize = 8
        
        # Add title
        title_label = ChartLabel()
        title_label.setText(title)
        title_label.fontName = 'Helvetica-Bold'
        title_label.fontSize = 14
        title_label.x = width/2
        title_label.y = height - 20
        title_label.textAnchor = 'middle'
        
        # Add percentage labels
        for i, value in enumerate(data.values()):
            label = ChartLabel()
            label.setText(f"{value:.1f}%")
            label.fontName = 'Helvetica'
            label.fontSize = 10
            label.x = bc.x + (i * (bc.width / len(data))) + (bc.width / len(data) / 2)
            label.y = bc.y + bc.height + 5
            label.textAnchor = 'middle'
            drawing.add(label)
        
        drawing.add(bc)
        drawing.add(title_label)
        
        return drawing

    def create_document_chart(self, data, width=150, height=120):
        """Create a smaller bar chart for individual documents."""
        drawing = Drawing(width, height)
        
        # Create the bar chart
        bc = VerticalBarChart()
        bc.x = 20
        bc.y = 20
        bc.height = height - 60  # Increased space for labels
        bc.width = width - 40
        bc.data = [list(data.values())]
        bc.categoryAxis.categoryNames = list(data.keys())
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 20
        
        # Customize the appearance
        bc.bars[0].fillColor = colors.Color(0.8, 0.9, 1)  # Light blue
        bc.bars[0].strokeColor = colors.black
        
        # Show and customize category axis labels
        bc.categoryAxis.labels.fontName = 'Helvetica'
        bc.categoryAxis.labels.fontSize = 8
        bc.categoryAxis.labels.angle = 45
        bc.categoryAxis.labels.dy = -5
        bc.categoryAxis.labels.dx = 0
        
        # Hide value axis labels
        bc.valueAxis.labels.fontSize = 0
        
        # Add percentage labels
        for i, value in enumerate(data.values()):
            label = ChartLabel()
            label.setText(f"{value:.1f}%")
            label.fontName = 'Helvetica'
            label.fontSize = 8
            label.x = bc.x + (i * (bc.width / len(data))) + (bc.width / len(data) / 2)
            label.y = bc.y + bc.height + 5
            label.textAnchor = 'middle'
            drawing.add(label)
        
        drawing.add(bc)
        return drawing

    def get(self, request, project_id):
        print(f"DIRECT PRINT: Accept header: {request.headers.get('Accept', '')}")
        print(f"DIRECT PRINT: Received PDF generation request for project {project_id}")
        print(f"DIRECT PRINT: User: {request.user.username}")
        print(f"DIRECT PRINT: Request params: {request.GET}")

        try:
            # Get project info
            try:
                project = get_object_or_404(Project, pk=project_id)
                print(f"DIRECT PRINT: Project name: {project.name}")
            except Exception as e:
                print(f"DIRECT PRINT: Error getting project: {str(e)}")
                return Response(
                    {'error': f'Error getting project: {str(e)}'},
                    status=HTTP_404_NOT_FOUND,
                    content_type='application/json'
                )

            # Get perspective filters if any
            perspective_filters = request.GET.get('perspective_filters')
            if perspective_filters:
                try:
                    perspective_filters = json.loads(perspective_filters)
                    print(f"DIRECT PRINT: Perspective filters: {perspective_filters}")
                except json.JSONDecodeError as e:
                    print(f"DIRECT PRINT: Error decoding perspective filters: {str(e)}")
                    return Response(
                        {'error': 'Invalid perspective filters format'},
                        status=HTTP_400_BAD_REQUEST,
                        content_type='application/json'
                    )

            # Build base query for examples, considering perspective filters if applied
            try:
                base_query = Example.objects.filter(project=project)
                print(f"DIRECT PRINT: Base query count before perspective filter: {base_query.count()}")

                matching_users_ids = None # Initialize

                if perspective_filters:
                    # Logic to find matching users based on perspective filters (similar to DatasetStatisticsAPI)
                    users_matching_filters_queryset = User.objects.filter(role_mappings__project=project).distinct()

                    num_active_perspective_filters = 0

                    for question_id, selected_values in perspective_filters.items():
                        if not selected_values: 
                            continue

                        num_active_perspective_filters += 1
                        
                        single_question_answer_condition = Q(
                            perspectiveanswer__perspective__id=question_id
                        )
                        values_q = Q()
                        values_to_check = selected_values if isinstance(selected_values, list) else [selected_values]
                        for val in values_to_check:
                            if isinstance(val, bool):
                                val_str = 'Yes' if val else 'No'
                            else:
                                val_str = str(val)
                            values_q |= Q(perspectiveanswer__answer=val_str)
                        
                        single_question_answer_condition &= values_q

                        users_matching_filters_queryset = users_matching_filters_queryset.filter(single_question_answer_condition).distinct()
                    
                    if num_active_perspective_filters > 0:
                        matching_users_ids = list(users_matching_filters_queryset.values_list('id', flat=True))
                    else:
                        matching_users_ids = []

                    if matching_users_ids:
                        has_matching_annotator = Q(
                            Q(categories__user__id__in=matching_users_ids) |
                            Q(spans__user__id__in=matching_users_ids) |
                            Q(relations__user__id__in=matching_users_ids)
                        )
                        base_query = base_query.filter(has_matching_annotator).distinct()

            except Exception as e:
                print(f"DIRECT PRINT: Error building base query or applying perspective filters: {str(e)}")
                import traceback
                print(f"DIRECT PRINT: Traceback: {traceback.format_exc()}")
                return Response(
                    {'error': f'Error building query for report: {str(e)}'},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            # Calculate statistics
            try:
                total_docs = base_query.count()
                annotated_docs = base_query.filter(states__isnull=False).distinct().count()
                unannotated_docs = total_docs - annotated_docs
                
                # Calculate percentages
                annotated_percentage = (annotated_docs / total_docs * 100) if total_docs > 0 else 0
                unannotated_percentage = (unannotated_docs / total_docs * 100) if total_docs > 0 else 0
                
            except Exception as e:
                print(f"DIRECT PRINT: Error calculating statistics: {str(e)}")
                return Response(
                    {'error': f'Error calculating statistics: {str(e)}'},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            # Generate PDF
            try:
                # Create a BytesIO buffer to store the PDF
                buffer = BytesIO()
                
                # Create the PDF document
                pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []
                
                # Add title
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30
                )
                elements.append(Paragraph(f"Dataset Report - {project.name}", title_style))
                
                # Add statistics section with percentages
                elements.append(Paragraph("Statistics", styles['Heading2']))
                stats_data = [
                    ["Total Documents", f"{total_docs}"],
                    ["Annotated Documents", f"{annotated_docs} ({annotated_percentage:.1f}%)"],
                    ["Unannotated Documents", f"{unannotated_docs} ({unannotated_percentage:.1f}%)"]
                ]
                stats_table = Table(stats_data, colWidths=[200, 100])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(stats_table)
                elements.append(Spacer(1, 20))

                # Add perspective filters section if any
                if perspective_filters:
                    elements.append(Paragraph("Applied Perspective Filters", styles['Heading2']))
                    filter_data = [["Question ID", "Value"]]
                    for question_id, value in perspective_filters.items():
                        if value:  # Only add non-empty values
                            values = value if isinstance(value, list) else [value]
                            for val in values:
                                filter_data.append([str(question_id), str(val)])
                    filter_table = Table(filter_data, colWidths=[200, 100])
                    filter_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(filter_table)
                    elements.append(Spacer(1, 20))

                # Add Label Distribution Sections with percentages and charts
                # Category Distribution
                category_distribution_data = {}
                if CategoryType.objects.filter(project=project).exists():
                    categories_query = Category.objects.filter(example__in=base_query)
                    if matching_users_ids is not None:
                        categories_query = categories_query.filter(user__id__in=matching_users_ids)
                    
                    category_counts = categories_query.values('label__text').annotate(count=Count('label__text')).order_by('label__text')
                    total_categories = sum(item['count'] for item in category_counts)
                    
                    for item in category_counts:
                        percentage = (item['count'] / total_categories * 100) if total_categories > 0 else 0
                        category_distribution_data[item['label__text']] = percentage

                if category_distribution_data:
                    elements.append(Paragraph("Category Distribution", styles['Heading2']))
                    # Add bar chart
                    chart = self.create_bar_chart(category_distribution_data, "Category Distribution")
                    elements.append(chart)
                    elements.append(Spacer(1, 20))

                # Span Distribution
                span_distribution_data = {}
                if SpanType.objects.filter(project=project).exists():
                    spans_query = Span.objects.filter(example__in=base_query)
                    if matching_users_ids is not None:
                        spans_query = spans_query.filter(user__id__in=matching_users_ids)
                    
                    span_counts = spans_query.values('label__text').annotate(count=Count('label__text')).order_by('label__text')
                    total_spans = sum(item['count'] for item in span_counts)
                    
                    for item in span_counts:
                        percentage = (item['count'] / total_spans * 100) if total_spans > 0 else 0
                        span_distribution_data[item['label__text']] = percentage

                if span_distribution_data:
                    elements.append(Paragraph("Span Distribution", styles['Heading2']))
                    # Add bar chart
                    chart = self.create_bar_chart(span_distribution_data, "Span Distribution")
                    elements.append(chart)
                    elements.append(Spacer(1, 20))

                # Relation Distribution
                relation_distribution_data = {}
                if RelationType.objects.filter(project=project).exists():
                    relations_query = Relation.objects.filter(example__in=base_query)
                    if matching_users_ids is not None:
                        relations_query = relations_query.filter(user__id__in=matching_users_ids)
                    
                    relation_counts = relations_query.values('type__text').annotate(count=Count('type__text')).order_by('type__text')
                    total_relations = sum(item['count'] for item in relation_counts)
                    
                    for item in relation_counts:
                        percentage = (item['count'] / total_relations * 100) if total_relations > 0 else 0
                        relation_distribution_data[item['type__text']] = percentage

                if relation_distribution_data:
                    elements.append(Paragraph("Relation Distribution", styles['Heading2']))
                    # Add bar chart
                    chart = self.create_bar_chart(relation_distribution_data, "Relation Distribution")
                    elements.append(chart)
                    elements.append(Spacer(1, 20))

                # Add Document-wise Label Distribution
                elements.append(Paragraph("Document-wise Label Distribution", styles['Heading2']))
                elements.append(Spacer(1, 20))

                # Get all documents
                documents = base_query.order_by('id')
                
                for example in documents:
                    # Create a table for each document
                    doc_data = [
                        [Paragraph(f"Document ID: {example.id}", styles['Heading3']), ""],
                        [Paragraph(example.text[:100] + "..." if len(example.text) > 100 else example.text, styles['Normal']), ""]
                    ]
                    
                    # Get document's category distribution
                    doc_categories = Category.objects.filter(example=example)
                    if matching_users_ids is not None:
                        doc_categories = doc_categories.filter(user__id__in=matching_users_ids)
                    
                    category_counts = doc_categories.values('label__text').annotate(count=Count('label__text'))
                    total_cats = sum(item['count'] for item in category_counts)
                    
                    if total_cats > 0:
                        category_dist = {}
                        for item in category_counts:
                            percentage = (item['count'] / total_cats * 100)
                            category_dist[item['label__text']] = percentage
                        
                        # Create chart for this document
                        chart = self.create_document_chart(category_dist)
                        doc_data.append(["", chart])
                    
                    doc_table = Table(doc_data, colWidths=[300, 150])
                    doc_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                    ]))
                    elements.append(doc_table)
                    elements.append(Spacer(1, 20))

                # Build the PDF
                pdf_doc.build(elements)
                
                # Get the value of the BytesIO buffer
                pdf = buffer.getvalue()
                buffer.close()
                
                # Create the response
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="dataset-report-{project_id}.pdf"'
                response.write(pdf)
                
                return response
                
            except Exception as e:
                print(f"DIRECT PRINT: Error generating PDF: {str(e)}")
                import traceback
                print(f"DIRECT PRINT: Traceback: {traceback.format_exc()}")
                return Response(
                    {'error': f'Error generating PDF: {str(e)}'},
                    status=HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )
                
        except Exception as e:
            print(f"DIRECT PRINT: Unexpected error: {str(e)}")
            import traceback
            print(f"DIRECT PRINT: Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )
