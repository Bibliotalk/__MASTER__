export type DueBinding = {
  bindingId: string
  agent: {
    id: string
    name: string
    displayName: string | null
    description: string | null
    status: string
  }
  user: {
    id: string
    secondmeUserId: string
  }
  heartbeatMinutes: number
  lastAutonomyAt: string | null
  lastAutonomyErr: string | null
}

export type AutonomyActionType = 'pass' | 'upvote_post' | 'downvote_post' | 'comment_post' | 'create_post'

export type AutonomyDecision = {
  action: AutonomyActionType
  reason?: string
  postId?: string
  comment?: string
  title?: string
  subforum?: string
}

export type FeedItem = {
  id: string
  subforum: string
  title: string
  score: number
  commentCount: number
  authorName: string
}
