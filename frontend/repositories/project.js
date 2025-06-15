import { BaseRepository } from './base'

export class ProjectRepository extends BaseRepository {
  constructor() {
    super('projects')
  }

  // ... existing code ...

  async fetchReport(projectId, params = {}) {
    const response = await this.http.get(`${this.resource}/${projectId}/report/`, { params })
    return response
  }
} 