import { Link, useLocation } from "wouter";
import { 
  LayoutDashboard, 
  Server, 
  Users, 
  ShoppingCart, 
  CreditCard, 
  LineChart, 
  Settings, 
  Radio
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Services", href: "/services", icon: Server },
  { name: "Users", href: "/users", icon: Users },
  { name: "Orders", href: "/orders", icon: ShoppingCart },
  { name: "Payments", href: "/payments", icon: CreditCard },
  { name: "Profit", href: "/profit", icon: LineChart },
  { name: "Broadcast", href: "/broadcast", icon: Radio },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      <div className="w-full md:w-64 border-r bg-sidebar flex-shrink-0">
        <div className="h-16 flex items-center px-6 border-b">
          <span className="font-bold text-lg tracking-tight">SMS Terminal</span>
        </div>
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <main className="flex-1 p-6 md:p-8 overflow-y-auto min-h-[100dvh]">
        {children}
      </main>
    </div>
  );
}
