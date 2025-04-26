import ApiService from '@/services/api.service';

export class ApiVotingRepository {
  async list(projectId: string | number) {
    console.log('aqui no repository voting list()'); // log antes de criar a URL
    const url = `/projects/${projectId}/votingsessions`;
    console.log('URL construída:', url);
    const response = await ApiService.get(url);
    return response.data;
  }

  async create(projectId: string | number, voteEndDate: string, questions: string[]) {
    console.log('Repository: Entrou no método create para projectId:', projectId);
    const url = `/projects/${projectId}/votingsessions`;  // Certifique-se de terminar com uma barra
    console.log('Repository: URL construída (create):', url);
    try {
      const response = await ApiService.post(url, {
        vote_end_date: voteEndDate,
        questions, // usando shorthand
        finish: true,
      });
      console.log('Repository: Resposta do ApiService:', response);
      return response.data;
    } catch (error) {
      console.error('Repository: Erro no ApiService.post:', error);
      throw error;
    }
  }
}