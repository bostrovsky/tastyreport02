"use client"

import { Header } from "./header"
import { Sidebar } from "./sidebar"

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="relative min-h-screen">
      <Header />
      <div className="flex">
        <div className="hidden w-64 shrink-0 md:block">
          <Sidebar className="fixed h-[calc(100vh-3.5rem)] w-64 border-r" />
        </div>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
