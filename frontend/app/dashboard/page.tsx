"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/providers/AuthProvider";
import { getStrategies, Strategy } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { user, isLoading, signOut, session } = useAuth();
  const router = useRouter();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  useEffect(() => {
    const fetchStrategies = async () => {
      if (session?.access_token) {
        setLoadingStrategies(true);
        setError(null);
        try {
          const data = await getStrategies(session.access_token);
          setStrategies(data);
        } catch (err: any) {
          setError(err.message || "Failed to load strategies");
        } finally {
          setLoadingStrategies(false);
        }
      }
    };
    fetchStrategies();
  }, [session?.access_token]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return null; // Redirecting
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full">
      <h1 className="text-2xl font-bold mb-4">Welcome, {user.email}!</h1>
      <Button onClick={async () => { await signOut(); router.push("/login"); }}>
        Sign Out
      </Button>
      <div className="mt-8 w-full max-w-2xl">
        <h2 className="text-xl font-semibold mb-2">Your Strategies</h2>
        {loadingStrategies && <div>Loading strategies...</div>}
        {error && <div className="text-red-500">{error}</div>}
        <ul className="divide-y divide-border">
          {strategies.map((strategy) => (
            <li key={strategy.id} className="py-2">
              <div className="font-medium">{strategy.name}</div>
              <div className="text-sm text-muted-foreground">{strategy.description}</div>
              {strategy.is_default && (
                <span className="text-xs text-blue-500 ml-2">Default</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
