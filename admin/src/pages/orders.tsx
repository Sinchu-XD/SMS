import { useState } from "react";
import { useGetOrders, getGetOrdersQueryKey } from "@workspace/api-client-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate } from "@/lib/format";
import { Skeleton } from "@/components/ui/skeleton";

export default function Orders() {
  const [filter, setFilter] = useState<"today"|"week"|"month"|"all">("today");
  const { data: ordersPage, isLoading } = useGetOrders({ filter, limit: 100 });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'waiting': return 'secondary';
      case 'received': return 'outline';
      case 'cancelled': 
      case 'timeout': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Orders</h1>
        <Select value={filter} onValueChange={(v: any) => setFilter(v)}>
          <SelectTrigger className="w-[180px] bg-card">
            <SelectValue placeholder="Filter period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="today">Today</SelectItem>
            <SelectItem value="week">This Week</SelectItem>
            <SelectItem value="month">This Month</SelectItem>
            <SelectItem value="all">All Time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Service / Country</TableHead>
              <TableHead>Phone / Code</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Profit</TableHead>
              <TableHead className="text-center">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={7} className="text-center h-24"><Skeleton className="w-full h-8" /></TableCell></TableRow>
            ) : ordersPage?.items.map((o) => (
              <TableRow key={o.id}>
                <TableCell className="text-xs text-muted-foreground">{formatDate(o.createdAt)}</TableCell>
                <TableCell>
                  <div className="font-medium">{o.userName || o.userId}</div>
                  <div className="text-xs text-muted-foreground font-mono">{o.userId}</div>
                </TableCell>
                <TableCell>
                  <div className="font-medium">{o.service}</div>
                  <div className="text-xs text-muted-foreground">{o.country}</div>
                </TableCell>
                <TableCell className="font-mono text-sm">
                  <div>{o.phoneNumber || '-'}</div>
                  {o.smsCode && <div className="text-primary font-bold">{o.smsCode}</div>}
                </TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(o.price)}</TableCell>
                <TableCell className="text-right font-mono text-emerald-600 dark:text-emerald-400">
                  {o.profit ? formatCurrency(o.profit) : '-'}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant={getStatusColor(o.status)} className="capitalize">{o.status}</Badge>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && ordersPage?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center h-24 text-muted-foreground">
                  No orders found for this period.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
