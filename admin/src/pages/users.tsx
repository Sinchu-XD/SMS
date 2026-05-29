import { useState } from "react";
import { useGetUsers, useToggleUserBan, getGetUsersQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatNumber, formatDate } from "@/lib/format";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { Search } from "lucide-react";

export default function Users() {
  const [search, setSearch] = useState("");
  const { data: usersPage, isLoading } = useGetUsers({ search, limit: 50 });
  const toggleBan = useToggleUserBan();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const handleBanToggle = (userId: number, banned: boolean) => {
    toggleBan.mutate({ userId: userId.toString(), data: { banned } }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetUsersQueryKey() });
        toast({ title: banned ? "User banned" : "User unbanned" });
      }
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Users</h1>
      </div>

      <div className="flex items-center gap-2 max-w-sm">
        <Search className="w-4 h-4 text-muted-foreground" />
        <Input 
          placeholder="Search users..." 
          value={search} 
          onChange={(e) => setSearch(e.target.value)} 
          className="bg-card"
        />
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User ID</TableHead>
              <TableHead>Name / Username</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="text-right">Total Spent</TableHead>
              <TableHead className="text-right">Orders</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="text-center">Banned</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={8} className="text-center h-24"><Skeleton className="w-full h-8" /></TableCell></TableRow>
            ) : usersPage?.items.map((u) => (
              <TableRow key={u.userId} className={u.banned ? "opacity-50" : ""}>
                <TableCell className="font-mono text-xs">{u.userId}</TableCell>
                <TableCell>
                  <div className="font-medium">{u.name}</div>
                  {u.username && <div className="text-xs text-muted-foreground">@{u.username}</div>}
                </TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(u.balance)}</TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(u.spent)}</TableCell>
                <TableCell className="text-right font-mono">{formatNumber(u.orders)}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDate(u.joined)}</TableCell>
                <TableCell className="text-center">
                  <Switch 
                    checked={u.banned} 
                    onCheckedChange={(c) => handleBanToggle(u.userId, c)} 
                  />
                </TableCell>
                <TableCell className="text-right space-x-2">
                  <Button variant="outline" size="sm">Adjust Balance</Button>
                </TableCell>
              </TableRow>
            ))}
            {!isLoading && usersPage?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center h-24 text-muted-foreground">
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
