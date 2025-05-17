"use client"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Strategy, StrategyType, CreateStrategyInput, UpdateStrategyInput } from "@/lib/types/strategy"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"

const strategyFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().min(1, "Description is required"),
  type: z.enum(["IRON_CONDOR", "BUTTERFLY", "STRADDLE", "STRANGLE", "CUSTOM"] as const),
})

type StrategyFormValues = z.infer<typeof strategyFormSchema>

interface StrategyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  strategy?: Strategy
  onSubmit: (data: CreateStrategyInput | UpdateStrategyInput) => Promise<void>
}

export function StrategyDialog({
  open,
  onOpenChange,
  strategy,
  onSubmit,
}: StrategyDialogProps) {
  const form = useForm<StrategyFormValues>({
    resolver: zodResolver(strategyFormSchema),
    defaultValues: {
      name: strategy?.name ?? "",
      description: strategy?.description ?? "",
      type: strategy?.type ?? "IRON_CONDOR",
    },
  })

  const handleSubmit = async (data: StrategyFormValues) => {
    await onSubmit(data)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{strategy ? "Edit Strategy" : "New Strategy"}</DialogTitle>
          <DialogDescription>
            {strategy
              ? "Make changes to your strategy here."
              : "Create a new strategy to get started."}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Strategy name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Strategy description"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a strategy type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="IRON_CONDOR">Iron Condor</SelectItem>
                      <SelectItem value="BUTTERFLY">Butterfly</SelectItem>
                      <SelectItem value="STRADDLE">Straddle</SelectItem>
                      <SelectItem value="STRANGLE">Strangle</SelectItem>
                      <SelectItem value="CUSTOM">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="submit">
                {strategy ? "Save changes" : "Create strategy"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
