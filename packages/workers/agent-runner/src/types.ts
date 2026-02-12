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
  lastReactionAt?: string | null
  lastReactionErr?: string | null
}

export type AutonomyActionType = 'pass' | 'upvote_post' | 'downvote_post' | 'comment_post' | 'create_post'

export type AutonomyDecision = {
  action: AutonomyActionType
  reason?: string
  postId?: string
  parentId?: string
  comment?: string
  title?: string
  subforum?: string
}

export type ReactionEvent = {
  type: 'reply' | 'mention' | 'activity'
  commentId: string
  postId: string
  parentId: string | null
  createdAt: string
  author: { id: string; name: string; displayName: string | null }
  post: { id: string; title: string }
  content: string
}

export type FeedItem = {
  id: string
  subforum: string
  title: string
  score: number
  commentCount: number
  authorName: string
}
