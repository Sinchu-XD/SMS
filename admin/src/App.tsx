import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { Layout } from "@/components/layout";

import Dashboard from "@/pages/dashboard";
import Services from "@/pages/services";
import Users from "@/pages/users";
import Orders from "@/pages/orders";
import Payments from "@/pages/payments";
import Profit from "@/pages/profit";
import Settings from "@/pages/settings";
import Broadcast from "@/pages/broadcast";

const queryClient = new QueryClient();

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/services" component={Services} />
        <Route path="/users" component={Users} />
        <Route path="/orders" component={Orders} />
        <Route path="/payments" component={Payments} />
        <Route path="/profit" component={Profit} />
        <Route path="/settings" component={Settings} />
        <Route path="/broadcast" component={Broadcast} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
