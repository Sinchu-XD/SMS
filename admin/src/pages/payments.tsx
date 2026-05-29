import { useState } from "react";
import { useGetPayments, useApprovePayment, useRejectPayment, getGetPaymentsQueryKey, GetPaymentsStatus } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatCurrency, formatDate } from "@/lib/format";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Check, X } from "lucide-react";

export default function Payments() {
  const [status, setStatus] = useState<GetPaymentsStatus>("pending");
  const { data: paymentsPage, isLoading } = useGetPayments({ status, limit: 50 });
  const approvePayment = useApprovePayment();
  const rejectPayment = useRejectPayment();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const handleApprove = (id: string) => {
    approvePayment.mutate({ id }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetPaymentsQueryKey() });
        toast({ title: "Payment approved" });
      }
    });
  };

  const handleReject = (id: string) => {
    rejectPayment.mutate({ id }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetPaymentsQueryKey() });
        toast({ title: "Payment rejected" });
      }
    });
  };

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'approved': return 'default';
      case 'pending': return 'secondary';
      case 'rejected': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Payments</h1>
        <Select value={status} onValueChange={(v: any) => setStatus(v)}>
          <SelectTrigger className="w-[180px] bg-card">
            <SelectValue placeholder="Filter status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="all">All</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Proof / Ref</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={7} className="text-center h-24"><Skeleton className="w-full h-8" /></TableCell></TableRow>
            ) : paymentsPage?.items.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="text-xs text-muted-foreground">{formatDate(p.createdAt)}</TableCell>
                <TableCell>
                  <div className="font-medium">{p.userName || p.userId}</div>
                  <div className="text-xs text-muted-foreground font-mono">{p.userId}</div>
                </TableCell>
                <TableCell className="uppercase font-medium text-xs">{p.method}</TableCell>
                <TableCell className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">
                  {formatCurrency(p.amount)}
                </TableCell>
                <TableCell className="font-mono text-xs">{p.proofText || '-'}</TableCell>
                <TableCell className="text-center">
                  <Badge variant={getStatusColor(p.status)} className="capitalize">{p.status}</Badge>
                </TableCell>
                <TableCell className="text-right space-x-2">
                  {p.status === 'pending' && (
                    <>
                      <Button size="sm" variant="outline" className="text-emerald-600 border-emerald-600 hover:bg-emerald-50" onClick={() => handleApprove(p.id)}>
                        <Check className="w-4 h-4 mr-1" /> Approve
                      </Button>
                      <Button size="sm" variant="outline" className="text-red-600 border-red-600 hover:bg-red-50" onClick={() => handleReject(p.id)}>
                        <X className="w-4 h-4 mr-1" /> Reject
                      </Button>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && paymentsPage?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center h-24 text-muted-foreground">
                  No payments found for this status.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
