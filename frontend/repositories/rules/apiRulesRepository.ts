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
        console.log('url', url)
        const response = await ApiService.post(url, { question })
        return response.data
    }

    async delete(url: string, questionId: string | number) {
        console.log('aqui no repository', url);
        const response = await ApiService.delete(url, { data: { id: questionId } });
        console.log('aqui no repository response', response);
        return response.data;
    }
}