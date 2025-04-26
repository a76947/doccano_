import { ApiAnswerRepository } from '@/repositories/answerule/answerRuleRepository';

export class AnswerRuleApplicationService {
    constructor(private readonly repository: ApiAnswerRepository) {}

    async list(projectId: string | number, answerSessionId: string | number) {
        console.log('Entrou no service.list com projectId:', projectId);
        return await this.repository.list(projectId, answerSessionId);
    }

    async createAnswerSession(
        projectId: string | number,
        responses: string[],
        votingSessionId: string | number,
      ) {
        console.log('Answer Service: Creating answer session with responses:', responses, 'votingSessionId:', votingSessionId, 'projectId:', projectId);
        return await this.repository.createAnswerSession(
            projectId, responses, votingSessionId);
      }

}