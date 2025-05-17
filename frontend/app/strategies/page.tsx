"use client"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Plus, MoreVertical, Pencil, Trash } from "lucide-react"
import { useState } from "react"
import { StrategyDialog } from "@/components/strategies/strategy-dialog"
import { Strategy, CreateStrategyInput, UpdateStrategyInput } from "@/lib/types/strategy"
import { createStrategy, deleteStrategy, getStrategies, updateStrategy } from "@/lib/api/strategies"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

export default function StrategiesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | undefined>()
  const queryClient = useQueryClient()

  const { data: strategies = [], isLoading } = useQuery({
    queryKey: ["strategies"],
    queryFn: getStrategies,
  })

  const createMutation = useMutation({
    mutationFn: createStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] })
      toast.success("Strategy created successfully")
    },
    onError: () => {
      toast.error("Failed to create strategy")
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateStrategyInput }) =>
      updateStrategy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] })
      toast.success("Strategy updated successfully")
    },
    onError: () => {
      toast.error("Failed to update strategy")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] })
      toast.success("Strategy deleted successfully")
    },
    onError: () => {
      toast.error("Failed to delete strategy")
    },
  })

  const handleCreate = async (data: CreateStrategyInput) => {
    await createMutation.mutateAsync(data)
  }

  const handleUpdate = async (data: UpdateStrategyInput) => {
    if (selectedStrategy) {
      await updateMutation.mutateAsync({ id: selectedStrategy.id, data })
    }
  }

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this strategy?")) {
      await deleteMutation.mutateAsync(id)
    }
  }

  const handleEdit = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setIsDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Strategies</h1>
        <Button onClick={() => {
          setSelectedStrategy(undefined)
          setIsDialogOpen(true)
        }}>
          <Plus className="mr-2 h-4 w-4" />
          New Strategy
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center">Loading...</div>
      ) : strategies.length === 0 ? (
        <div className="rounded-lg border p-4">
          <p className="text-muted-foreground">
            No strategies found. Create your first strategy to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strategy) => (
            <Card key={strategy.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{strategy.name}</CardTitle>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEdit(strategy)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleDelete(strategy.id)}
                      >
                        <Trash className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <CardDescription>{strategy.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="font-medium">{strategy.type}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Status:</span>
                  <span className="font-medium">{strategy.status}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <StrategyDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        strategy={selectedStrategy}
        onSubmit={selectedStrategy ? handleUpdate : handleCreate}
      />
    </div>
  )
}
