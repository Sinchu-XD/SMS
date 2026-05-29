import { useState } from "react";
import { useGetProfitStats, GetProfitStatsPeriod } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatCurrency, formatNumber } from "@/lib/format";
import { Skeleton } from "@/components/ui/skeleton";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function Profit() {
  const [period, setPeriod] = useState<GetProfitStatsPeriod>("week");
  const { data: stats, isLoading } = useGetProfitStats({ period });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Profit Analytics</h1>
        <Select value={period} onValueChange={(v: any) => setPeriod(v)}>
          <SelectTrigger className="w-[180px] bg-card">
            <SelectValue placeholder="Period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="today">Today</SelectItem>
            <SelectItem value="week">This Week</SelectItem>
            <SelectItem value="month">This Month</SelectItem>
            <SelectItem value="all">All Time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Profit</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-[120px]" /> : <div className="text-2xl font-bold font-mono">{formatCurrency(stats?.totalProfit || 0)}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Orders</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-[120px]" /> : <div className="text-2xl font-bold font-mono">{formatNumber(stats?.totalOrders || 0)}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Profit / Order</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-[120px]" /> : <div className="text-2xl font-bold font-mono">{formatCurrency(stats?.avgProfitPerOrder || 0)}</div>}
          </CardContent>
        </Card>
      </div>

      <Card className="pt-6">
        <CardContent>
          <div className="h-[400px] w-full">
            {isLoading ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats?.breakdown || []} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                  <XAxis 
                    dataKey="date" 
                    stroke="currentColor" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false} 
                    opacity={0.5} 
                  />
                  <YAxis 
                    stroke="currentColor" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false} 
                    tickFormatter={(value) => `$${value}`} 
                    opacity={0.5} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }}
                    labelStyle={{ color: 'hsl(var(--muted-foreground))', marginBottom: '4px' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="profit" 
                    stroke="hsl(var(--primary))" 
                    strokeWidth={2} 
                    dot={false}
                    activeDot={{ r: 6, fill: 'hsl(var(--primary))' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
