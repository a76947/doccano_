import ApiService from '@/services/api.service'

export class ApiPerspectiveRepository {
  async create(projectId: string | number, payload: any) {
    const url = `/projects/${projectId}/perspectives/`
    const response = await ApiService.post(url, payload)
    return response.data
  }

  async list(projectId: string | number) {
    const url = `/projects/${projectId}/perspectives/`
    const response = await ApiService.get(url)
    return response.data
  }

  async createGroup(projectId: string | number, payload: any) {
    console.log('aqui no repository', payload)
    const url = `/projects/${projectId}/perspective-groups/`
    const response = await ApiService.post(url, payload)
    return response.data
  }

  async listGroups(projectId: string | number) {
    const url = `/projects/${projectId}/perspective-groups/`
    const response = await ApiService.get(url)
    return response.data
  }

  async createAnswer(projectId: string | number, payload: any) {
    const url = `/projects/${projectId}/perspective-answers/`
    const response = await ApiService.post(url, payload)
    return response.data
  }

  async listAnswers(projectId: string | number) {
    const url = `/projects/${projectId}/perspective-answers/`
    const response = await ApiService.get(url)
    return response.data
  }

  async listAnswersByQuestion(projectId: string | number, questionId: string | number) {
    const url = `/projects/${projectId}/perspective-answers/?perspective=${questionId}`
    const response = await ApiService.get(url)
    return response.data
  }

  async delete(projectId: string | number, questionId: string | number) {
    const url = `/projects/${projectId}/perspectives/${questionId}/`
    const response = await ApiService.delete(url)
    return response.data
  }

  async update(projectId: string | number, questionId: string | number, payload: any) {
    const url = `/projects/${projectId}/perspectives/${questionId}/`
    const response = await ApiService.put(url, payload)
    return response.data
  }

  async deleteGroup(projectId: string | number, groupId: string | number) {
    const url = `/projects/${projectId}/perspective-groups/${groupId}/`
    const response = await ApiService.delete(url)
    return response.data
  }
}