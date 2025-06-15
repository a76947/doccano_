import logging
from typing import List

from django.shortcuts import get_object_or_404

from examples.assignment.strategies import StrategyName, create_assignment_strategy
from examples.models import Assignment, Example
from projects.models import Member, Project

logger = logging.getLogger(__name__)

def bulk_assign(project_id: int, strategy_name: StrategyName, member_ids: List[int], weights: List[int]) -> None:
    logger.info(f"bulk_assign: project_id={project_id}, strategy_name={strategy_name}, member_ids={member_ids}, weights={weights}")
    project = get_object_or_404(Project, pk=project_id)
    members = Member.objects.filter(project=project, pk__in=member_ids)
    logger.info(f"bulk_assign: Retrieved members: {[m.user.username for m in members]}")
    if len(members) != len(member_ids):
        raise ValueError("Invalid member ids")
    # Sort members by member_ids
    members = sorted(members, key=lambda m: member_ids.index(m.id))
    index_to_user = {i: member.user for i, member in enumerate(members)}

    # Delete existing assignments for the examples that are about to be reassigned.
    # This prevents duplicate assignments if the same examples are assigned again.
    assigned_examples_to_delete = Example.objects.filter(project=project, assignments__isnull=False)
    if assigned_examples_to_delete.exists():
        Assignment.objects.filter(example__in=assigned_examples_to_delete).delete()
        logger.info(f"bulk_assign: Deleted existing assignments for {assigned_examples_to_delete.count()} examples.")

    unassigned_examples = Example.objects.filter(project=project)
    logger.info(f"bulk_assign: Unassigned examples (after deletion): {unassigned_examples.count()}")
    index_to_example = {i: example for i, example in enumerate(unassigned_examples)}
    dataset_size = unassigned_examples.count()

    strategy = create_assignment_strategy(strategy_name, dataset_size, weights)
    assignments = strategy.assign()
    assignments = [
        Assignment(
            project=project,
            example=index_to_example[assignment.example],
            assignee=index_to_user[assignment.user],
        )
        for assignment in assignments
    ]
    logger.info(f"bulk_assign: Prepared {len(assignments)} assignments for creation.")
    Assignment.objects.bulk_create(assignments)
    logger.info("bulk_assign: Assignments created successfully.")
