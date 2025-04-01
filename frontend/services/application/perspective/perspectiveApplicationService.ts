import { ApiPerspectiveRepository } from '@/repositories/perspective/apiPerspectiveRepository'

// Class-based implementation (for the Vue 2 app services system)
export class PerspectiveApplicationService {
  constructor(private readonly repository: ApiPerspectiveRepository) {}

  async createPerspective(projectId: string | number, data: any) {
    return await this.repository.create(projectId, data)
  }

  async listPerspective(projectId: string | number) {
    return await this.repository.list(projectId)
  }

  async createPerspectiveGroup(projectId: string | number, data: any) {
    return await this.repository.createGroup(projectId, data)
  }

  async listPerspectiveGroups(projectId: string | number) {
    return await this.repository.listGroups(projectId)
  }

  async createPerspectiveAnswer(projectId: string | number, data: any) {
    return await this.repository.createAnswer(projectId, data)
  }

  async listPerspectiveAnswers(projectId: string | number) {
    return await this.repository.listAnswers(projectId)
  }

  async deletePerspective(projectId: string | number, questionId: string | number) {
    return await this.repository.delete(projectId, questionId)
  }
}

// Function-based implementation (for Vue 3 composition API)
export function usePerspectiveApplicationService() {
  const repository = new ApiPerspectiveRepository()
  
  return {
    createPerspective: (projectId: string | number, data: any) => 
      repository.create(projectId, data),
    
    listPerspective: (projectId: string | number) => 
      repository.list(projectId),
    
    createPerspectiveGroup: (projectId: string | number, data: any) => 
      repository.createGroup(projectId, data),
    
    listPerspectiveGroups: (projectId: string | number) => 
      repository.listGroups(projectId),

    createPerspectiveAnswer: (projectId: string | number, data: any) => 
      repository.createAnswer(projectId, data),
    
    listPerspectiveAnswers: (projectId: string | number) => 
      repository.listAnswers(projectId),

    deletePerspective: (projectId: string | number, questionId: string | number) => 
      repository.delete(projectId, questionId)
  }
}
