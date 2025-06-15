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
from django.http import HttpResponse

from examples.models import Example, ExampleState
from label_types.models import CategoryType, LabelType, RelationType, SpanType
from labels.models import Category, Label, Relation, Span
from projects.models import Member, Project
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly

logger = logging.getLogger(__name__)

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

        # Apply perspective filters
        if perspective_filters:
            print(f"DEBUG: Applying perspective filters: {perspective_filters}")
            initial_example_count = filtered_query.count()
            print(f"DEBUG: Examples count before perspective filter: {initial_example_count}")
            
            combined_q_filters = Q()
            has_any_perspective_filter = False

            for question_id, value in perspective_filters.items():
                # If the selected_value is an empty list, skip this filter as it implies no specific selection.
                if isinstance(value, list) and len(value) == 0:
                    print(f"DEBUG: Skipping filter for Q{question_id} as selected value list is empty.")
                    continue

                has_any_perspective_filter = True
                
                if isinstance(value, list):
                    # For list of values (e.g., multi-select string/int options)
                    answer_values_str = [str(v) for v in value]
                    answer_q = Q(perspective_answers__answer__in=answer_values_str)
                    print(f"DEBUG: Building filter for Q{question_id} (list): {answer_values_str}")
                elif isinstance(value, bool):
                    str_value = 'Yes' if value else 'No'
                    answer_q = Q(perspective_answers__answer=str_value)
                    print(f"DEBUG: Building filter for Q{question_id} (bool): {str_value}")
                else:
                    # For single string/int value
                    str_value = str(value)
                    from django.db.models import Value
                    answer_q = Q(perspective_answers__answer=Value(str_value))
                    print(f"DEBUG: Building filter for Q{question_id} (single): {str_value}")
                
                current_filter_q = Q(perspective_answers__perspective__id=question_id) & answer_q
                combined_q_filters &= current_filter_q
            
            if has_any_perspective_filter:
                # Filter by the combined conditions and ensure distinct examples
                filtered_query = filtered_query.filter(combined_q_filters).distinct()
                print(f"DEBUG: Examples count AFTER perspective filter: {filtered_query.count()}")
                print(f"DEBUG: Generated SQL Query (after perspective filter): {filtered_query.query}")
        
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


class DatasetReportAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

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
                    status=status.HTTP_404_NOT_FOUND,
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
                        status=status.HTTP_400_BAD_REQUEST,
                        content_type='application/json'
                    )

            # Build base query
            try:
                base_query = Example.objects.filter(project=project)
                print(f"DIRECT PRINT: Base query count: {base_query.count()}")
            except Exception as e:
                print(f"DIRECT PRINT: Error building base query: {str(e)}")
                return Response(
                    {'error': f'Error building base query: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            # Apply perspective filters if any
            if perspective_filters:
                try:
                    for question_id, value in perspective_filters.items():
                        if not value:  # Skip empty values
                            continue
                            
                        # Convert value to list if it's not already
                        values = value if isinstance(value, list) else [value]
                        
                        if not values:  # Skip empty lists
                            continue
                            
                        print(f"DIRECT PRINT: Applying filter for question {question_id} with values {values}")
                        
                        # Build the filter condition
                        filter_condition = Q()
                        for val in values:
                            filter_condition |= Q(
                                perspective_answers__perspective__id=question_id,
                                perspective_answers__answer=val
                            )
                        
                        # Apply the filter
                        base_query = base_query.filter(filter_condition).distinct()
                        print(f"DIRECT PRINT: Query count after filter: {base_query.count()}")
                except Exception as e:
                    print(f"DIRECT PRINT: Error applying perspective filters: {str(e)}")
                    return Response(
                        {'error': f'Error applying perspective filters: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST,
                        content_type='application/json'
                    )

            # Calculate statistics
            try:
                total_docs = base_query.count()
                annotated_docs = base_query.filter(states__isnull=False).distinct().count()
                unannotated_docs = total_docs - annotated_docs
                
                print(f"DIRECT PRINT: Total docs: {total_docs}")
                print(f"DIRECT PRINT: Annotated docs: {annotated_docs}")
                print(f"DIRECT PRINT: Unannotated docs: {unannotated_docs}")
            except Exception as e:
                print(f"DIRECT PRINT: Error calculating statistics: {str(e)}")
                return Response(
                    {'error': f'Error calculating statistics: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )

            # Generate PDF
            try:
                # Create a BytesIO buffer to store the PDF
                buffer = BytesIO()
                
                # Create the PDF document
                doc = SimpleDocTemplate(buffer, pagesize=letter)
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
                
                # Add statistics section
                elements.append(Paragraph("Statistics", styles['Heading2']))
                stats_data = [
                    ["Total Documents", str(total_docs)],
                    ["Annotated Documents", str(annotated_docs)],
                    ["Unannotated Documents", str(unannotated_docs)]
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
                
                # Add sample entries section
                elements.append(Paragraph("Sample Entries", styles['Heading2']))
                sample_entries = base_query.order_by('id')[:10]  # Get first 10 entries
                entry_data = [["ID", "Text", "Status"]]
                for entry in sample_entries:
                    status = "Annotated" if entry.states.exists() else "Pending"
                    entry_data.append([str(entry.id), entry.text[:100] + "...", status])
                entry_table = Table(entry_data, colWidths=[50, 400, 100])
                entry_table.setStyle(TableStyle([
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
                elements.append(entry_table)
                
                # Build the PDF
                doc.build(elements)
                
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
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content_type='application/json'
                )
                
        except Exception as e:
            print(f"DIRECT PRINT: Unexpected error: {str(e)}")
            import traceback
            print(f"DIRECT PRINT: Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )
