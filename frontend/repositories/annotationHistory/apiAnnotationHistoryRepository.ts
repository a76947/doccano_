import ApiService from '@/services/api.service'

export class APIAnnotationHistoryRepository {
  constructor(private readonly request = ApiService) {}

  async prepare(projectId: string, datasetName: string | null, annotationStatus: string = 'All'): Promise<string> {
    const url = `/projects/${projectId}/annotation-history`
    const data = {
      datasetName,
      annotation_status: annotationStatus
    }
    const response = await this.request.post(url, data)
    return response.data.task_id
  }

  async fetch(projectId: string, taskId: string): Promise<any[]> {
    const url = `/projects/${projectId}/annotation-history-data?taskId=${taskId}`
    const response = await this.request.get(url)
    return response.data
  }

  async downloadFile(projectId: string, taskId: string): Promise<void> {
    const url = `/projects/${projectId}/annotation-history?taskId=${taskId}`
    const config = {
      responseType: 'blob'
    }
    const response = await this.request.get(url, config)
    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', `annotation_history_${projectId}_${taskId}.zip`)
    document.body.appendChild(link)
    link.click()
  }
} 