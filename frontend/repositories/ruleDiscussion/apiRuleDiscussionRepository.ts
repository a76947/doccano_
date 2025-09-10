import ApiService from '@/services/api.service'

export class ApiRuleDiscussionRepository {
  async list(
    projectId: string | number,
    sessionId: string | number,
    questionIndex: number,
  ) {
    const url = `/projects/${projectId}/rules/messages`
    const response = await ApiService.get(url, {
      params: {
        session_id: sessionId,
        question_index: questionIndex,
      },
    })
    return response.data
  }

  async create(
    projectId: string | number,
    sessionId: string | number,
    questionIndex: number,
    message: string,
  ) {
    const url = `/projects/${projectId}/rules/messages`
    const response = await ApiService.post(url, {
      session_id: sessionId,
      question_index: questionIndex,
      message,
    })
    return response.data
  }
} 