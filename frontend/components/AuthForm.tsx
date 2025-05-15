"use client"

import { useState, FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AuthFormProps {
  mode: "login" | "register";
  onSubmit: (email: string, password: string) => Promise<void>;
  isLoading: boolean;
  error?: string | null;
}

export function AuthForm({ mode, onSubmit, isLoading, error }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await onSubmit(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-sm mx-auto">
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          disabled={isLoading}
        />
      </div>
      <div>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          disabled={isLoading}
        />
      </div>
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? "Loading..." : mode === "login" ? "Sign In" : "Register"}
      </Button>
    </form>
  );
}
