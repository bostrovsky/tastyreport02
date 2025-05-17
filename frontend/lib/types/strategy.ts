export interface Strategy {
  id: string
  name: string
  description: string
  type: StrategyType
  status: StrategyStatus
  createdAt: string
  updatedAt: string
  userId: string
}

export type StrategyType =
  | "IRON_CONDOR"
  | "BUTTERFLY"
  | "STRADDLE"
  | "STRANGLE"
  | "CUSTOM"

export type StrategyStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "ARCHIVED"

export interface CreateStrategyInput {
  name: string
  description: string
  type: StrategyType
}

export interface UpdateStrategyInput extends Partial<CreateStrategyInput> {
  status?: StrategyStatus
}
