import { Strategy, CreateStrategyInput, UpdateStrategyInput } from "@/lib/types/strategy"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function getStrategies(): Promise<Strategy[]> {
  const response = await fetch(`${API_URL}/api/v1/strategies/`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to fetch strategies")
  }

  return response.json()
}

export async function getStrategy(id: string): Promise<Strategy> {
  const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to fetch strategy")
  }

  return response.json()
}

export async function createStrategy(data: CreateStrategyInput): Promise<Strategy> {
  const response = await fetch(`${API_URL}/api/v1/strategies/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error("Failed to create strategy")
  }

  return response.json()
}

export async function updateStrategy(id: string, data: UpdateStrategyInput): Promise<Strategy> {
  const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error("Failed to update strategy")
  }

  return response.json()
}

export async function deleteStrategy(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/strategies/${id}`, {
    method: "DELETE",
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to delete strategy")
  }
}
