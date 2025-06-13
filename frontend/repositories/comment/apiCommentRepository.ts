import { CommentItem } from '@/domain/models/comment/comment'
import { Page } from '@/domain/models/page'
import ApiService from '@/services/api.service'

export type SearchOption = { [key: string]: string | (string | null)[] }

function toModel(item: { [key: string]: any }): CommentItem {
  return new CommentItem(
    item.id,
    item.user,
    item.username,
    item.example,
    item.text,
    item.created_at,
    item.label || null
  )
}

function toPayload(item: CommentItem): { [key: string]: any } {
  return {
    id: item.id,
    user: item.user,
    text: item.text,
    label: item.label
  }
}

export class APICommentRepository {
  constructor(private readonly request = ApiService) {}

  async listAll(
    projectId: string,
    { limit = '10', offset = '0', q = '', sortBy = '', sortDesc = '' }: SearchOption
  ): Promise<Page<CommentItem>> {
    const ordering = sortDesc === 'true' ? `-${sortBy}` : `${sortBy}`
    const url = `/projects/${projectId}/comments?q=${q}&limit=${limit}&offset=${offset}&ordering=${ordering}`
    const response = await this.request.get(url)
    return new Page(
      response.data.count,
      response.data.next,
      response.data.previous,
      response.data.results.map((item: { [key: string]: any }) => toModel(item))
    )
  }

  async list(projectId: string, exampleId: number, labelId?: number): Promise<CommentItem[]> {
    const base = `/projects/${projectId}/comments?example=${exampleId}&limit=100`
    let url = base
    if (labelId) url += `&label=${labelId}`
    const response = await this.request.get(url)
    return response.data.results.map((item: { [key: string]: any }) => toModel(item))
  }

  async create(
    projectId: string,
    exampleId: number,
    text: string,
    labelId?: number
  ): Promise<CommentItem> {
    const url = `/projects/${projectId}/comments?example=${exampleId}`
    const payload: any = { text }
    if (labelId) payload.label = labelId
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }

  async update(projectId: string, comment: CommentItem): Promise<CommentItem> {
    const url = `/projects/${projectId}/comments/${comment.id}`
    const payload = toPayload(comment)
    const response = await this.request.put(url, payload)
    return toModel(response.data)
  }

  async delete(projectId: string, comment: CommentItem): Promise<void> {
    const url = `/projects/${projectId}/comments/${comment.id}`
    await this.request.delete(url)
  }

  async deleteBulk(projectId: string, comments: CommentItem[]): Promise<void> {
    const url = `/projects/${projectId}/comments`
    const ids = comments.map((comment) => comment.id)
    await this.request.delete(url, { ids })
  }
}
