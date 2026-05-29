import { useGetBroadcastLogs } from "@workspace/api-client-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate, formatNumber } from "@/lib/format";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function Broadcast() {
  const { data: logsPage, isLoading } = useGetBroadcastLogs({ limit: 50 });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Broadcast History</h1>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[180px]">Date</TableHead>
              <TableHead>Message Preview</TableHead>
              <TableHead className="text-right">Sent</TableHead>
              <TableHead className="text-right">Failed</TableHead>
              <TableHead className="text-center">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={5} className="text-center h-24"><Skeleton className="w-full h-8" /></TableCell></TableRow>
            ) : logsPage?.items.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="text-xs text-muted-foreground">{formatDate(log.createdAt)}</TableCell>
                <TableCell className="max-w-md truncate font-medium text-sm">
                  {log.textPreview}
                </TableCell>
                <TableCell className="text-right font-mono text-emerald-600 dark:text-emerald-400">
                  {formatNumber(log.sent)}
                </TableCell>
                <TableCell className="text-right font-mono text-red-600 dark:text-red-400">
                  {formatNumber(log.failed)}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant={log.failed > log.sent ? "destructive" : "secondary"}>
                    Completed
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && logsPage?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-24 text-muted-foreground">
                  No broadcast logs found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
