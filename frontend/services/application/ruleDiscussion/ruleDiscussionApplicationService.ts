import {
  ApiRuleDiscussionRepository,
} from '~/repositories/ruleDiscussion/apiRuleDiscussionRepository'

export class RuleDiscussionApplicationService {
  constructor(private readonly repository: ApiRuleDiscussionRepository) {}

  async list(projectId: string | number, sessionId: string | number, questionIndex: number) {
    return await this.repository.list(projectId, sessionId, questionIndex)
  }

  async create(
    projectId: string | number,
    sessionId: string | number,
    questionIndex: number,
    message: string,
  ) {
    return await this.repository.create(
      projectId,
      sessionId,
      questionIndex,
      message,
    )
  }
} 