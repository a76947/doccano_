import ApiService from '@/services/api.service'

export interface LabelStat { version: number; labels: string[]; votes: number[] }

export class ApiStatsRepository {
  async labelVotes(projectId: string|number, params: any = {}): Promise<LabelStat[]> {
    const { data } = await ApiService.get(`/projects/${projectId}/stats/label-votes`, { params })
    return data
  }

  async datasets(projectId: string|number) {
    const { data } = await ApiService.get(`/projects/${projectId}/datasets`)
    return data
  }
} 