import ApiService from '@/services/api.service'

export class ApiRulesRepository {
    async list(projectId: string | number) {
        const url = `/projects/${projectId}/rules/tosubmit`
        const response = await ApiService.get(url)
        return response.data
    }

    async listSubmittesRules(projectId: string | number) {
        const url = `/projects/${projectId}/rules/submited`
        const response = await ApiService.get(url)
        return response.data
    }

    async submit(url: string, question: string) {
        const response = await ApiService.post(url, { question })
        return response.data
    }

    async delete(url: string, questionId: string | number) {
        const response = await ApiService.delete(url, { data: { id: questionId } });
        return response.data;
    }

    async edit(url: string, question: string) {
        const response = await ApiService.put(url, { question });
        return response.data;
    }
}