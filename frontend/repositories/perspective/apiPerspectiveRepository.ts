import axios from 'axios'

export function useApiPerspectiveRepository() {
  const create = async (projectId: number, data: any) => {
    // 🔁 ALTERAR perspective → perspectives
    await axios.post(`/v1/projects/${projectId}/perspectives/`, data)
  }

  const list = async (projectId: number) => {
    const res = await axios.get(`/v1/projects/${projectId}/perspectives/`)
    return res.data
  }

  return { create, list }
}
