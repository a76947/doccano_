export class CommentItem {
  constructor(
    readonly id: number,
    readonly user: number,
    readonly username: string,
    readonly example: number,
    readonly text: string,
    readonly createdAt: string,
    readonly label: number | null
  ) {}

  by(userId: number) {
    return this.user === userId
  }
}
