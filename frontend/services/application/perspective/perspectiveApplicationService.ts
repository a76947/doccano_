import { useApiPerspectiveRepository } from '@/repositories/perspective/apiPerspectiveRepository'

export function usePerspectiveApplicationService() {
  const repo = useApiPerspectiveRepository()

  const createPerspective = async (projectId: number, data: any) => {
    await repo.create(projectId, data)
  }

  const listPerspective = async (projectId: number) => {
    return await repo.list(projectId)
  }

  return { createPerspective, listPerspective }
}
