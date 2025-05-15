// frontend/lib/api.ts

export interface Strategy {
    id: string;
    name: string;
    description?: string;
    is_default: boolean;
    // Add other fields as needed
  }

  export async function getStrategies(token: string): Promise<Strategy[]> {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/strategies/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error("Failed to fetch strategies");
    }
    return res.json();
  }
