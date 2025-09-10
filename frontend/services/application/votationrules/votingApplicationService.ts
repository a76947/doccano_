import { ApiVotingRepository } from '~/repositories/votation/votingRepository'

export class VotingApplicationService {
    constructor(private readonly repository: ApiVotingRepository) {}

    async list(projectId: string | number) {
        return await this.repository.list(projectId)
    }

    async createVotingSession(projectId: string | number, 
        voteEndDate: string, questions: string[]) {
        console.log("Service: Creating voting session with date:", 
            voteEndDate, "and questions:", questions);
        return await this.repository.create(projectId, voteEndDate, questions);
    }

    async updateSessionFinish(projectId: string | number, votingSessionId: string | number) {
        const url = `/projects/${projectId}/votingsessions/${votingSessionId}/`;
        const response = await this.repository.updateSessionFinish(url);
        return response;
    }

}