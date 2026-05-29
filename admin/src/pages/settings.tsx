import { useEffect } from "react";
import { useGetSettings, useUpdateSettings, getGetSettingsQueryKey } from "@workspace/api-client-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { useQueryClient } from "@tanstack/react-query";

const formSchema = z.object({
  usdRate: z.coerce.number().min(0.1, "Must be greater than 0"),
  maintenance: z.boolean(),
  welcomeMessage: z.string().min(1, "Welcome message is required"),
  upiId: z.string().optional(),
  upiQrUrl: z.string().optional(),
  supportUsername: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function Settings() {
  const { data: settings, isLoading } = useGetSettings();
  const updateSettings = useUpdateSettings();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      usdRate: 85,
      maintenance: false,
      welcomeMessage: "",
      upiId: "",
      upiQrUrl: "",
      supportUsername: "",
    }
  });

  useEffect(() => {
    if (settings) {
      form.reset(settings);
    }
  }, [settings, form]);

  const onSubmit = (data: FormValues) => {
    updateSettings.mutate({ data }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetSettingsQueryKey() });
        toast({ title: "Settings saved successfully" });
      },
      onError: () => {
        toast({ title: "Failed to save settings", variant: "destructive" });
      }
    });
  };

  if (isLoading) return null;

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">General Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="maintenance"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Maintenance Mode</FormLabel>
                      <FormDescription>
                        Disable bot access for all users except admins.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="usdRate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>USD to INR Rate</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormDescription>Used for converting balance and pricing.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="supportUsername"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Support Username</FormLabel>
                    <FormControl>
                      <Input placeholder="@support" {...field} />
                    </FormControl>
                    <FormDescription>Telegram username for the support contact.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Messages & Bot Copy</CardTitle>
            </CardHeader>
            <CardContent>
              <FormField
                control={form.control}
                name="welcomeMessage"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Welcome Message</FormLabel>
                    <FormControl>
                      <Textarea rows={4} {...field} />
                    </FormControl>
                    <FormDescription>Sent to users when they start the bot.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Payment Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="upiId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>UPI ID</FormLabel>
                    <FormControl>
                      <Input placeholder="name@bank" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="upiQrUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>UPI QR Image URL</FormLabel>
                    <FormControl>
                      <Input placeholder="https://..." {...field} />
                    </FormControl>
                    <FormDescription>Optional URL for a QR code image to display for deposits.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Button type="submit" disabled={updateSettings.isPending}>
            {updateSettings.isPending ? "Saving..." : "Save Settings"}
          </Button>
        </form>
      </Form>
    </div>
  );
}
