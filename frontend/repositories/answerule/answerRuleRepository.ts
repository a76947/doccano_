import ApiService from '@/services/api.service';

export class ApiAnswerRepository {
  async list(projectId: string | number, answerSessionId: string | number) {
    const url = `/projects/${projectId}/votingsessions/${answerSessionId}/answers`;
    console.log('URL construída:', url);
    try {
      const response = await ApiService.get(url);
      console.log('Resposta do GET:', response.data);
      return response.data;
    } catch (error) {
      console.error('Erro no GET:', error);
      throw error;
    }
  }

  async createAnswerSession(
    projectId: string | number,
    responses: string[],
    votingSessionId: string | number,
  ) {
    const url = `/projects/${projectId}/votingsessions/${votingSessionId}/answers`;
    // Envia apenas o campo answer (lista de strings);
    // o backend extrai o usuário via request.user
    return await ApiService.post(url, { answer: responses });
  }

  async updateSessionFinish(url: string) {
    console.log('aqui no repository voting updateSessionFinish() com URL:', url);
    const response = await ApiService.put(url, { finish: true });
    return response;
  }

  async listUserAnswers(projectId: string | number, votingSessionId: string | number) {
    const url = `/projects/${projectId}/votingsessions/${votingSessionId}/user-answers`;
    console.log('URL construída para user answers:', url);
    try {
      const response = await ApiService.get(url);
      console.log('Resposta do GET (user answers):', response.data);
      return response.data;
    } catch (error) {
      console.error('Erro no GET de user answers:', error);
      throw error;
    }
  }
}