import { APIAnnotationRepository, AnnotationItem } from '@/repositories/annotation/apiAnnotationRepository'

export class AnnotationApplicationService {
  constructor(private readonly repository: APIAnnotationRepository) {}

  async getUserAnnotations(
    projectId: string | number, 
    documentId: string | number,
    userId: string | number
  ): Promise<AnnotationItem[]> {
    return await this.repository.getUserAnnotations(projectId, documentId, userId);
  }

  async getComparisonData(
    projectId: string | number,
    documentId: string | number,
    user1Id: string | number,
    user2Id: string | number
  ): Promise<{user1: AnnotationItem[], user2: AnnotationItem[]}> {
    return await this.repository.getComparisonData(projectId, documentId, user1Id, user2Id);
  }
}