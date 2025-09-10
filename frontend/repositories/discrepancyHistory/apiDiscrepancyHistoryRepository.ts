import ApiService from '@/services/api.service'

export class APIDiscrepancyHistoryRepository {
  constructor(private readonly request = ApiService) {}

  async prepare(projectId: string, datasetName: string | null): Promise<string> {
    const url = `/projects/${projectId}/discrepancy-history`
    const data = {
      datasetName
    }
    const response = await this.request.post(url, data)
    return response.data.task_id
  }

  async fetch(projectId: string, taskId: string): Promise<any[]> {
    const url = `/projects/${projectId}/discrepancy-history-data?taskId=${taskId}`
    const response = await this.request.get(url)
    return response.data
  }

  async downloadFile(projectId: string, taskId: string): Promise<void> {
    const url = `/projects/${projectId}/discrepancy-history?taskId=${taskId}`
    const config = {
      responseType: 'blob'
    }
    const response = await this.request.get(url, config)
    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', `discrepancy_history_${projectId}_${taskId}.zip`)
    document.body.appendChild(link)
    link.click()
  }
} 