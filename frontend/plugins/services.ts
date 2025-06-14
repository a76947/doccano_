import { Plugin } from '@nuxt/types'
import { repositories } from './repositories'
import { ExampleApplicationService } from '@/services/application/example/exampleApplicationService'
import { LabelApplicationService } from '@/services/application/label/labelApplicationService'
import { OptionApplicationService } from '@/services/application/option/optionApplicationService'
import { ProjectApplicationService } from '@/services/application/project/projectApplicationService'
import { TagApplicationService } from '@/services/application/tag/tagApplicationService'
import { BoundingBoxApplicationService } from '@/services/application/tasks/boundingBox/boundingBoxApplicationService'
import { SegmentationApplicationService } from '@/services/application/tasks/segmentation/segmentationApplicationService'
import { SequenceLabelingApplicationService } from '@/services/application/tasks/sequenceLabeling/sequenceLabelingApplicationService'
import { UserApplicationService } from '~/services/application/user/userAplicationService'
import { ApiPerspectiveRepository } from '@/repositories/perspective/apiPerspectiveRepository'
import { PerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

// Update with perspective property

import { AnnotationApplicationService } from '@/services/application/annotation/annotationApplicationService'
import { DiscrepacieApplicationService } from '@/services/application/descrepancys/discrepanciesApplicationService'
import { RulesApplicationService } from '~/services/application/rules/rulesApplicationService'
import { VotingApplicationService } from '~/services/application/votationrules/votingApplicationService'
import { AnswerRuleApplicationService } from '~/services/application/ruleanswer/rulesAnswerApplicationService'
import { RuleDiscussionApplicationService } from '~/services/application/ruleDiscussion/ruleDiscussionApplicationService'

export interface Services {
  categoryType: LabelApplicationService
  spanType: LabelApplicationService
  relationType: LabelApplicationService
  project: ProjectApplicationService
  user: UserApplicationService
  example: ExampleApplicationService
  sequenceLabeling: SequenceLabelingApplicationService
  option: OptionApplicationService
  tag: TagApplicationService
  bbox: BoundingBoxApplicationService
  segmentation: SegmentationApplicationService

  perspective: PerspectiveApplicationService 
  discrepancy: DiscrepacieApplicationService

  annotation: AnnotationApplicationService
  rules: RulesApplicationService
  voting : VotingApplicationService
  answer: AnswerRuleApplicationService
  ruleDiscussion: RuleDiscussionApplicationService


}

declare module 'vue/types/vue' {
  interface Vue {
    readonly $services: Services
  }
}

repositories.perspective = new ApiPerspectiveRepository()

const plugin: Plugin = (_, inject) => {
  const services: Services = {
    categoryType: new LabelApplicationService(repositories.categoryType),
    spanType: new LabelApplicationService(repositories.spanType),
    relationType: new LabelApplicationService(repositories.relationType),
    project: new ProjectApplicationService(repositories.project),
    example: new ExampleApplicationService(repositories.example),
    sequenceLabeling: new SequenceLabelingApplicationService(
      repositories.span,
      repositories.relation
    ),
    option: new OptionApplicationService(repositories.option),
    tag: new TagApplicationService(repositories.tag),
    bbox: new BoundingBoxApplicationService(repositories.boundingBox),
    segmentation: new SegmentationApplicationService(repositories.segmentation),
    user: new UserApplicationService(repositories.user),
    rules: new RulesApplicationService(repositories.rules),
    voting: new VotingApplicationService(repositories.voting),
    answer: new AnswerRuleApplicationService(repositories.answer),
    ruleDiscussion: new RuleDiscussionApplicationService(repositories.ruleDiscussion),

    perspective: new PerspectiveApplicationService(repositories.perspective), // Add this line
    discrepancy: new DiscrepacieApplicationService(repositories.discrepancy), // Add this line
    annotation: new AnnotationApplicationService(repositories.annotation)
  }
  inject('services', services)
}

export default plugin
