import ApiService from '@/services/api.service'


export class ApiDiscrepancieRepository {
    async list(projectId: string | number) {
        console.log('no Repository das discrepancias')
        const url = `/projects/${projectId}/discrepacies`
        const response = await ApiService.get(url)
        return response.data
    }
}