import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { homePathFor, useAuth } from "./auth";
import { Layout } from "./shell";
import type { Role } from "./types";
import { Loading, ToastProvider } from "./ui";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RequestDetail from "./pages/RequestDetail";
import CustomerRequests from "./pages/customer/Requests";
import NewRequest from "./pages/customer/NewRequest";
import DispatchInbox from "./pages/dispatch/Inbox";
import DispatchBoard from "./pages/dispatch/Board";
import TechJobs from "./pages/tech/Jobs";
import ManageDashboard from "./pages/manage/Dashboard";

function AuthedLayout({ allow }: { allow: Role[] }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allow.includes(user.role)) return <Navigate to={homePathFor(user.role)} replace />;
  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  const home = user ? homePathFor(user.role) : null;

  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={home ? <Navigate to={home} replace /> : <Landing />} />
        <Route path="/login" element={home ? <Navigate to={home} replace /> : <Login />} />
        <Route path="/register" element={home ? <Navigate to={home} replace /> : <Register />} />

        <Route element={<AuthedLayout allow={["customer"]} />}>
          <Route path="/app" element={<CustomerRequests />} />
          <Route path="/app/new" element={<NewRequest />} />
        </Route>
        <Route element={<AuthedLayout allow={["dispatcher", "manager"]} />}>
          <Route path="/dispatch" element={<DispatchInbox />} />
          <Route path="/dispatch/board" element={<DispatchBoard />} />
        </Route>
        <Route element={<AuthedLayout allow={["technician", "manager"]} />}>
          <Route path="/jobs" element={<TechJobs />} />
        </Route>
        <Route element={<AuthedLayout allow={["manager"]} />}>
          <Route path="/manage" element={<ManageDashboard />} />
        </Route>
        <Route element={<AuthedLayout allow={["customer", "dispatcher", "technician", "manager"]} />}>
          <Route path="/requests/:reference" element={<RequestDetail />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  );
}
