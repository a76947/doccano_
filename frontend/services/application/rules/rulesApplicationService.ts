import { ApiRulesRepository } from '@/repositories/rules/apiRulesRepository'

export class RulesApplicationService {
    constructor(private readonly repository: ApiRulesRepository) {}

    async listRulesToSubmit(projectId: string | number) {
        return await this.repository.list(projectId)
    }
    
    async listRulesSubmited(projectId: string | number) {
        return await this.repository.listSubmittesRules(projectId)
    }

    async createRule(projectId: string | number, question: string) {
        console.log('aqui no service rules', question)
        const url = `/projects/${projectId}/rules/tosubmit`
        const response = await this.repository.submit(url, question)
        return response.data
    }

    async deleteRule(projectId: string | number, questionId: string | number) {
        console.log('aqui no service rules para delete', questionId);
        const url = `/projects/${projectId}/rules/tosubmit/${questionId}/`;
        const response = await this.repository.delete(url, questionId);
        return response;
    }
}