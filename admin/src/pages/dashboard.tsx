import { useGetDashboardStats } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatNumber } from "@/lib/format";
import { Users, ShoppingCart, DollarSign, Activity, Wallet, TrendingUp } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
  const { data: stats, isLoading } = useGetDashboardStats();

  if (isLoading || !stats) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <Skeleton className="h-4 w-[100px]" />
                <Skeleton className="h-4 w-4 rounded-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-[120px]" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const cards = [
    {
      title: "Today's Profit",
      value: formatCurrency(stats.todayProfit),
      icon: TrendingUp,
      highlight: true
    },
    {
      title: "Today's Orders",
      value: formatNumber(stats.todayOrders),
      icon: Activity,
      highlight: true
    },
    {
      title: "Total Profit",
      value: formatCurrency(stats.totalProfit),
      icon: DollarSign,
    },
    {
      title: "Total Orders",
      value: formatNumber(stats.totalOrders),
      icon: ShoppingCart,
    },
    {
      title: "Total Users",
      value: formatNumber(stats.totalUsers),
      icon: Users,
    },
    {
      title: "Total User Balance",
      value: formatCurrency(stats.totalUserBalance),
      icon: Wallet,
    },
    {
      title: "Supplier Balance",
      value: formatCurrency(stats.supplierBalance),
      icon: Server,
    },
    {
      title: "Pending Payments",
      value: formatNumber(stats.pendingPayments),
      icon: CreditCard,
    }
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, i) => (
          <Card key={i} className={card.highlight ? "border-primary/50 shadow-sm bg-primary/5" : ""}>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <card.icon className={`h-4 w-4 ${card.highlight ? 'text-primary' : 'text-muted-foreground'}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono">{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { Server, CreditCard } from "lucide-react";