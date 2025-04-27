import ApiService from '@/services/api.service'

export const getAnnotationReport = async (
  projectId: number,
  filters: {
    user?: number;
    label?: string;
    text?: string;
    start?: string;
  } = {}
) => {
  const response = await ApiService.get(`/v1/projects/${projectId}/report`, {
    params: filters,
  })
  return response.data
}
