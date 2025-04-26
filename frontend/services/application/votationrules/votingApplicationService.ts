import { ApiVotingRepository } from '~/repositories/votation/votingRepository'

export class VotingApplicationService {
    constructor(private readonly repository: ApiVotingRepository) {}

    async list(projectId: string | number) {
        console.log('Entrou no service.list com projectId:', projectId);
        return await this.repository.list(projectId)
    }

    async createVotingSession(projectId: string | number, 
        voteEndDate: string, questions: string[]) {
        console.log("Service: Creating voting session with date:", 
            voteEndDate, "and questions:", questions);
        return await this.repository.create(projectId, voteEndDate, questions);
      }

}