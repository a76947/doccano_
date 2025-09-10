from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, F
from django.utils import timezone
from ..models import Project
from examples.models import Example
from collections import defaultdict
from labels.models import Category, Span, TextLabel, Relation
from rest_framework.renderers import JSONRenderer
import json

class ReportAnnotationsView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request, project_id):
        """
        Get a filtered report of annotations for a specific project
        """
        try:
            project = Project.objects.get(id=project_id)
            
            # Get filter parameters
            datasets = request.GET.getlist('datasets[]') or request.GET.getlist('datasets')
            agreement_filter = request.GET.get('agreement', 'all')
            perspective_answers_json = request.GET.get('perspective_answers')
            perspective_filters = {}

            print(f"DEBUG: Raw perspective_answers_json received: {perspective_answers_json}")

            if perspective_answers_json:
                try:
                    perspective_filters = json.loads(perspective_answers_json)
                    print(f"DEBUG: Parsed perspective_filters: {perspective_filters}")
                except json.JSONDecodeError:
                    print(f"ERROR: Could not decode perspective_answers JSON: {perspective_answers_json}")
                    # You might want to return an error response here or handle it gracefully

            print(f"DEBUG: Received datasets parameter: {datasets}")
            
            # --- Start New Debug: List all upload_names in the project ---
            all_project_examples = Example.objects.filter(project=project)
            all_upload_names = [f"'{e.upload_name}' (ID: {e.id})" for e in all_project_examples]
            print(f"DEBUG: All upload_names in project {project_id}: {all_upload_names}")
            # --- End New Debug ---

            # Base query for examples
            examples_query = Example.objects.filter(project=project)
            print(f"DEBUG: Examples query count BEFORE dataset filter: {examples_query.count()}")
            
            # Apply dataset filter if specified
            if datasets and 'all' not in datasets:
                print(f"DEBUG: Filtering by datasets: {datasets}")
                examples_query = examples_query.filter(upload_name__in=datasets)
            
            print(f"DEBUG: Examples query count AFTER dataset filter: {examples_query.count()}")
            print(f"DEBUG: Generated SQL Query (after dataset filter): {examples_query.query}")

            # Apply perspective filters
            if perspective_filters:
                print(f"DEBUG: Applying perspective filters: {perspective_filters}")
                initial_example_count = examples_query.count()
                print(f"DEBUG: Examples count before perspective filter: {initial_example_count}")
                
                combined_q_filters = Q()
                has_any_perspective_filter = False

                for question_id_str, selected_value in perspective_filters.items():
                    # If the selected_value is an empty list, skip this filter as it implies no specific selection.
                    if isinstance(selected_value, list) and len(selected_value) == 0:
                        print(f"DEBUG: Skipping filter for Q{question_id_str} as selected value list is empty.")
                        continue

                    has_any_perspective_filter = True
                    question_id = int(question_id_str)
                    
                    question_q = Q(perspective_answers__perspective__id=question_id)

                    if isinstance(selected_value, list):
                        # For list of values (e.g., multi-select string/int options)
                        # Use F expressions for list/array containment if supported by your DB/Django version for JSONField
                        # For TextField, __in works with a list of strings
                        answer_values_str = [str(v) for v in selected_value]
                        answer_q = Q(perspective_answers__answer__in=answer_values_str)
                        print(f"DEBUG: Building filter for Q{question_id_str} (list): {answer_values_str}")
                    elif isinstance(selected_value, bool):
                        str_value = 'Yes' if selected_value else 'No'
                        answer_q = Q(perspective_answers__answer=str_value)
                        print(f"DEBUG: Building filter for Q{question_id_str} (bool): {str_value}")
                    else:
                        # For single string/int value, ensure comparison is explicitly against the string literal
                        str_value = str(selected_value)
                        from django.db.models import Value
                        answer_q = Q(perspective_answers__answer=Value(str_value))
                        print(f"DEBUG: Building filter for Q{question_id_str} (single): {str_value}")
                    
                    current_filter_q = question_q & answer_q
                    combined_q_filters &= current_filter_q
                
                if has_any_perspective_filter:
                    # Filter by the combined conditions and ensure distinct examples
                    examples_query = examples_query.filter(combined_q_filters).distinct()
                    print(f"DEBUG: Examples count AFTER perspective filter: {examples_query.count()}")
                    print(f"DEBUG: Generated SQL Query (after perspective filter): {examples_query.query}")

            # Get all examples with their annotations
            examples = examples_query.prefetch_related(
                'categories',
                'spans',
                'texts',
                'relations',
                'perspective_answers' # Also prefetch perspective answers to ensure they are available if needed later
            )

            # Group by dataset and collect statistics
            dataset_stats = defaultdict(lambda: {
                'name': '',
                'total_documents': 0,
                'annotated_documents': 0,
                'annotations': {
                    'categories': defaultdict(lambda: {
                        'count': 0,
                        'users': set(),
                        'agreement': {
                            'total': 0,
                            'agreed': 0,
                            'disagreed': 0
                        }
                    }),
                    'spans': defaultdict(lambda: {
                        'count': 0,
                        'users': set(),
                        'agreement': {
                            'total': 0,
                            'agreed': 0,
                            'disagreed': 0
                        }
                    }),
                    'relations': defaultdict(lambda: {
                        'count': 0,
                        'users': set(),
                        'agreement': {
                            'total': 0,
                            'agreed': 0,
                            'disagreed': 0
                        }
                    })
                }
            })

            for example in examples:
                # Use upload_name as dataset_name, fallback to 'Arquivo sem nome' if empty
                dataset_name = example.upload_name if example.upload_name else f'Arquivo sem nome (ID: {example.id})'
                print(f"DEBUG: Processing example {example.id} with upload_name: '{example.upload_name}'")

                dataset = dataset_stats[dataset_name]
                
                if not dataset['name']:
                    dataset['name'] = dataset_name
                
                dataset['total_documents'] += 1
                
                print(f"DEBUG: Example {example.id} - Current agreement_filter: {agreement_filter}")

                # Process categories
                categories = example.categories.all()
                print(f"DEBUG: Example {example.id} - Categories count: {categories.count()}")
                if categories.exists():
                    is_agreed_category = False # Default value
                    if categories.count() == 1:
                        is_agreed_category = True
                    elif categories.count() > 1:
                        first_category = categories.first()
                        if first_category and first_category.label:
                            first_label = first_category.label
                            if all(c.label == first_label for c in categories if c.label):
                                is_agreed_category = True
                    print(f"DEBUG: Example {example.id} - is_agreed_category: {is_agreed_category}")

                    include_annotations_for_example_category = False
                    print(f"DEBUG: Example {example.id} - agreement_filter (category): {agreement_filter}")
                    if agreement_filter == 'all':
                        include_annotations_for_example_category = True
                    elif agreement_filter == 'agreed' and is_agreed_category:
                        include_annotations_for_example_category = True
                    elif agreement_filter == 'disagreed' and not is_agreed_category:
                        include_annotations_for_example_category = True
                    print(f"DEBUG: Example {example.id} - include_annotations_for_example_category: {include_annotations_for_example_category}")

                    if include_annotations_for_example_category:
                        dataset['annotated_documents'] += 1
                        for category in categories:
                            if category.label:
                                label_text = category.label.text
                                stats = dataset['annotations']['categories'][label_text]
                                stats['count'] += 1
                                stats['users'].add(category.user.id)
                                
                                stats['agreement']['total'] += 1
                                if is_agreed_category:
                                    stats['agreement']['agreed'] += 1
                                else:
                                    stats['agreement']['disagreed'] += 1
                
                # Process spans
                spans = example.spans.all()
                print(f"DEBUG: Example {example.id} - Spans count: {spans.count()}")
                if spans.exists():
                    is_agreed_span = False # Default value
                    if spans.count() == 1:
                        is_agreed_span = True
                    elif spans.count() > 1:
                        first_span = spans.first()
                        if first_span and first_span.label:
                            if all(s.label == first_span.label and s.start_offset == first_span.start_offset and s.end_offset == first_span.end_offset for s in spans if s.label):
                                 is_agreed_span = True
                    print(f"DEBUG: Example {example.id} - is_agreed_span: {is_agreed_span}")

                    include_annotations_for_example_span = False
                    print(f"DEBUG: Example {example.id} - agreement_filter (span): {agreement_filter}")
                    if agreement_filter == 'all':
                        include_annotations_for_example_span = True
                    elif agreement_filter == 'agreed' and is_agreed_span:
                        include_annotations_for_example_span = True
                    elif agreement_filter == 'disagreed' and not is_agreed_span:
                        include_annotations_for_example_span = True
                    print(f"DEBUG: Example {example.id} - include_annotations_for_example_span: {include_annotations_for_example_span}")

                    if include_annotations_for_example_span:
                        dataset['annotated_documents'] += 1
                        for span in spans:
                            if span.label:
                                label_text = span.label.text
                                stats = dataset['annotations']['spans'][label_text]
                                stats['count'] += 1
                                stats['users'].add(span.user.id)
                                
                                stats['agreement']['total'] += 1
                                if is_agreed_span:
                                    stats['agreement']['agreed'] += 1
                                else:
                                    stats['agreement']['disagreed'] += 1
                
                # Process relations
                relations = example.relations.all()
                print(f"DEBUG: Example {example.id} - Relations count: {relations.count()}")
                if relations.exists():
                    is_agreed_relation = False # Default value
                    if relations.count() == 1:
                        is_agreed_relation = True
                    elif relations.count() > 1:
                        first_relation = relations.first()
                        if first_relation and first_relation.type:
                            if not all(r.type == first_relation.type and r.from_id == first_relation.from_id and r.to_id == first_relation.to_id for r in relations if r.type):
                                is_agreed_relation = False
                    print(f"DEBUG: Example {example.id} - is_agreed_relation: {is_agreed_relation}")

                    include_annotations_for_example_relation = False
                    print(f"DEBUG: Example {example.id} - agreement_filter (relation): {agreement_filter}")
                    if agreement_filter == 'all':
                        include_annotations_for_example_relation = True
                    elif agreement_filter == 'agreed' and is_agreed_relation:
                        include_annotations_for_example_relation = True
                    elif agreement_filter == 'disagreed' and not is_agreed_relation:
                        include_annotations_for_example_relation = True
                    print(f"DEBUG: Example {example.id} - include_annotations_for_example_relation: {include_annotations_for_example_relation}")

                    if include_annotations_for_example_relation:
                        dataset['annotated_documents'] += 1
                        for relation in relations:
                            if relation.type:
                                label_text = relation.type.text
                                stats = dataset['annotations']['relations'][label_text]
                                stats['count'] += 1
                                stats['users'].add(relation.user.id)
                                
                                stats['agreement']['total'] += 1
                                if is_agreed_relation:
                                    stats['agreement']['agreed'] += 1
                                else:
                                    stats['agreement']['disagreed'] += 1

            # Format response
            report_data = []
            for dataset_name, stats in dataset_stats.items():
                # Add dataset summary
                report_data.append({
                    'type': 'dataset_summary',
                    'dataset': dataset_name,
                    'total_documents': stats['total_documents'],
                    'annotated_documents': stats['annotated_documents'],
                    'annotation_percentage': round(
                        (stats['annotated_documents'] / stats['total_documents'] * 100)
                        if stats['total_documents'] > 0 else 0,
                        2
                    )
                })
                
                # Add category annotations
                for label_name, label_stats in stats['annotations']['categories'].items():
                    total = label_stats['agreement']['total']
                    agreed = label_stats['agreement']['agreed']
                    agreement_percentage = (agreed / total * 100) if total > 0 else 0
                    
                    report_data.append({
                        'type': 'category',
                        'dataset': dataset_name,
                        'label': label_name,
                        'count': label_stats['count'],
                        'unique_users': len(label_stats['users']),
                        'agreement': {
                            'percentage': round(agreement_percentage, 2),
                            'total': total,
                            'agreed': agreed,
                            'disagreed': label_stats['agreement']['disagreed']
                        }
                    })
                
                # Add span annotations
                for label_name, label_stats in stats['annotations']['spans'].items():
                    total = label_stats['agreement']['total']
                    agreed = label_stats['agreement']['agreed']
                    agreement_percentage = (agreed / total * 100) if total > 0 else 0
                    
                    report_data.append({
                        'type': 'span',
                        'dataset': dataset_name,
                        'label': label_name,
                        'count': label_stats['count'],
                        'unique_users': len(label_stats['users']),
                        'agreement': {
                            'percentage': round(agreement_percentage, 2),
                            'total': total,
                            'agreed': agreed,
                            'disagreed': label_stats['agreement']['disagreed']
                        }
                    })
                
                # Add relation annotations
                for label_name, label_stats in stats['annotations']['relations'].items():
                    total = label_stats['agreement']['total']
                    agreed = label_stats['agreement']['agreed']
                    agreement_percentage = (agreed / total * 100) if total > 0 else 0
                    
                    report_data.append({
                        'type': 'relation',
                        'dataset': dataset_name,
                        'label': label_name,
                        'count': label_stats['count'],
                        'unique_users': len(label_stats['users']),
                        'agreement': {
                            'percentage': round(agreement_percentage, 2),
                            'total': total,
                            'agreed': agreed,
                            'disagreed': label_stats['agreement']['disagreed']
                        }
                    })

            # Get list of available datasets for the filter directly from aggregated stats
            available_datasets_from_stats = sorted(list(dataset_stats.keys()))
            
            # Ensure 'all' is the first option if it's not explicitly in stats keys
            available_datasets = []
            if 'all' not in available_datasets_from_stats:
                available_datasets.append('all')
            available_datasets.extend(available_datasets_from_stats)

            print(f"DEBUG: Final available_datasets for response (from stats keys): {available_datasets}")
            print(f"DEBUG: Final report_data items: {report_data}")

            return Response({
                'report_data': report_data,
                'available_datasets': available_datasets
            }, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 