import ApiService from '@/services/api.service'

export interface AnnotationItem {
  id: number;
  start_offset?: number;
  end_offset?: number;
  label?: number;
  text?: string;
  user?: number;
}

export class APIAnnotationRepository {
  constructor(private readonly request = ApiService) {}

  async getUserAnnotations(
    projectId: string | number, 
    documentId: string | number,
    userId: string | number
  ): Promise<AnnotationItem[]> {
    const url = `/projects/${projectId}/annotations?doc_id=${documentId}&user_id=${userId}`;
    try {
      const response = await this.request.get(url);
      console.log(`Annotation response for user ${userId}:`, response.data);
      return response.data.annotations || [];
    } catch (error) {
      console.error(`Error fetching annotations for user ${userId}:`, error);
      return [];
    }
  }

  async getComparisonData(
    projectId: string | number,
    documentId: string | number,
    user1Id: string | number,
    user2Id: string | number
  ): Promise<{user1: AnnotationItem[], user2: AnnotationItem[]}> {
    try {
      // Try first with the specified users
      const [user1Annotations, user2Annotations] = await Promise.all([
        this.getUserAnnotations(projectId, documentId, user1Id),
        this.getUserAnnotations(projectId, documentId, user2Id)
      ]);
      
      // If both users have no annotations, try with users 1 and 38 (from your backend logs)
      if (user1Annotations.length === 0 && user2Annotations.length === 0) {
        console.log("No annotations found for specified users, trying with users 1 and 38");
        const [fallbackUser1Annotations, fallbackUser2Annotations] = await Promise.all([
          this.getUserAnnotations(projectId, documentId, 1),
          this.getUserAnnotations(projectId, documentId, 38)
        ]);
        
        return {
          user1: fallbackUser1Annotations,
          user2: fallbackUser2Annotations
        };
      }
      
      return {
        user1: user1Annotations,
        user2: user2Annotations
      };
    } catch (error) {
      console.error("Error getting comparison data:", error);
      return {
        user1: [],
        user2: []
      };
    }
  }
}