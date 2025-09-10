import { ApiDiscrepancieRepository } from '@/repositories/discrepancies/apiDiscrepancieRepository'

export class DiscrepacieApplicationService {
    constructor(private readonly repository: ApiDiscrepancieRepository) {}

    async listDiscrepancie(projectId: string | number) {
        return await this.repository.list(projectId)
      }
}