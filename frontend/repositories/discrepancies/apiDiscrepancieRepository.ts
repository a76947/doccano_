import ApiService from '@/services/api.service'


export class ApiDiscrepancieRepository {


    async list(projectId: string | number, params?: { threshold?: number }) {
        const url = `/projects/${projectId}/discrepacies`
        const response = await ApiService.get(url, { params })
        return response.data
    }
}