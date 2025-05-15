"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/providers/AuthProvider";

export default function RegisterPage() {
  const { signUp, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleRegister = async (email: string, password: string) => {
    const { error } = await signUp(email, password);
    if (error) {
      setError(error);
    } else {
      setError(null);
      router.push("/dashboard");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Register</h1>
      <AuthForm mode="register" onSubmit={handleRegister} isLoading={isLoading} error={error} />
    </div>
  );
}
