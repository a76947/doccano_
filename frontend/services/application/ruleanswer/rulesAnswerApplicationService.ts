import { ApiAnswerRepository } from '@/repositories/answerule/answerRuleRepository';

export class AnswerRuleApplicationService {
    private repository: ApiAnswerRepository;
    constructor() {
        this.repository = new ApiAnswerRepository();
    }

    async listUserAnswers(projectId: string | number, votingSessionId: string | number) {
        return await this.repository.listUserAnswers(projectId, votingSessionId);
    }

    async list(projectId: string | number, answerSessionId: string | number) {
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