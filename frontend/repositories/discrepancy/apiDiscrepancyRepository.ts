import ApiService from '@/services/api.service'

export interface DiscrepancyItem {
  id: number
  text: string
  diffCount: number
  status: 'open' | 'resolved'
}

export class ApiDiscrepancyRepository {
  async list(projectId: string | number): Promise<DiscrepancyItem[]> {
    const url = `/projects/${projectId}/discrepancies`
    const response = await ApiService.get(url)
    return response.data.discrepancies
  }
} 