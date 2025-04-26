import ApiService from '@/services/api.service';

export class ApiAnswerRepository {
  async list(projectId: string | number, answerSessionId: string | number) {
    console.log('aqui no repository voting list()'); // log antes de criar a URL
    const url = `/projects/${projectId}/votingsessions/${answerSessionId}/answers`; // Adicione o sufixo correto
    console.log('URL construída:', url);
    const response = await ApiService.get(url);
    return response.data;
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
}