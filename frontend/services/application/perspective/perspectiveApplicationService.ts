import { ApiPerspectiveRepository } from '@/repositories/perspective/apiPerspectiveRepository'

// Class-based implementation (para Vue 2 "services")
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

  // NOVO método para atualizar (PUT) uma perspetiva
  async updatePerspective(projectId: string | number, questionId: string | number, data: any) {
    return await this.repository.update(projectId, questionId, data)
  }
}

// Function-based implementation (para Vue 3 Composition API)
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
      repository.delete(projectId, questionId),

    // NOVO método para atualizar (PUT) uma perspetiva
    updatePerspective: (projectId: string | number, questionId: string | number, data: any) =>
      repository.update(projectId, questionId, data)
  }
}
