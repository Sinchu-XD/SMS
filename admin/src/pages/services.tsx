import { useState } from "react";
import { useGetServices, useUpdateService, useDeleteService, useCreateService, getGetServicesQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate } from "@/lib/format";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

export default function Services() {
  const { data: servicesPage, isLoading } = useGetServices();
  const updateService = useUpdateService();
  const deleteService = useDeleteService();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const handleToggle = (id: string, enabled: boolean) => {
    updateService.mutate({ id, data: { enabled } }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetServicesQueryKey() });
        toast({ title: "Service updated", description: `Service is now ${enabled ? 'enabled' : 'disabled'}` });
      }
    });
  };

  const handleDelete = (id: string) => {
    if (!confirm("Delete this service?")) return;
    deleteService.mutate({ id }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetServicesQueryKey() });
        toast({ title: "Service deleted" });
      }
    });
  };

  if (isLoading || !servicesPage) {
    return <div className="space-y-4"><Skeleton className="h-10 w-[200px]" /><Skeleton className="h-[400px] w-full" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Services</h1>
        <Button>Add Service</Button>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code / Name</TableHead>
              <TableHead>Country</TableHead>
              <TableHead className="text-right">Cost</TableHead>
              <TableHead className="text-right">Sell (USD)</TableHead>
              <TableHead className="text-right">Sell (INR)</TableHead>
              <TableHead className="text-center">Avail.</TableHead>
              <TableHead className="text-center">Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {servicesPage.items.map((srv) => (
              <TableRow key={srv.id}>
                <TableCell>
                  <div className="font-medium">{srv.serviceName}</div>
                  <div className="text-xs text-muted-foreground font-mono">{srv.serviceCode}</div>
                </TableCell>
                <TableCell>{srv.countryName}</TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(srv.supplierPrice)}</TableCell>
                <TableCell className="text-right font-mono">{formatCurrency(srv.sellPriceUsd)}</TableCell>
                <TableCell className="text-right font-mono">₹{srv.sellPriceInr}</TableCell>
                <TableCell className="text-center font-mono">
                  <Badge variant={srv.availability > 0 ? "secondary" : "outline"}>{srv.availability}</Badge>
                </TableCell>
                <TableCell className="text-center">
                  <Switch 
                    checked={srv.enabled} 
                    onCheckedChange={(c) => handleToggle(srv.id, c)} 
                  />
                </TableCell>
                <TableCell className="text-right space-x-2">
                  <Button variant="destructive" size="sm" onClick={() => handleDelete(srv.id)}>Delete</Button>
                </TableCell>
              </TableRow>
            ))}
            {servicesPage.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center h-24 text-muted-foreground">
                  No services found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
