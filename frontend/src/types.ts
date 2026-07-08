export type Role = "customer" | "dispatcher" | "technician" | "manager" | "anonymous";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  name: string;
  role: Role;
  departments: number[];
  is_available: boolean | null;
}

export interface Department {
  id: number;
  name: string;
  code: string;
  slug: string;
  description: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  department: number;
}

export interface Property {
  id: number;
  label: string;
  property_type: string;
  address_line: string;
  community: string;
  city: string;
  emirate: string;
  unit_number: string;
  access_notes: string;
  is_active: boolean;
}

export interface MiniUser {
  id: number;
  username: string;
  name: string;
}

export interface RequestItem {
  id: number;
  reference: string;
  title: string;
  status: string;
  status_display: string;
  priority: string;
  priority_display: string;
  department: Department;
  category_name: string | null;
  location_label: string | null;
  community: string | null;
  requester: MiniUser;
  assignee: MiniUser | null;
  sla_due_at: string | null;
  sla_breached: boolean;
  is_open: boolean;
  created_at: string;
  updated_at: string;
}

export interface RequestEvent {
  id: number;
  verb: string;
  verb_display: string;
  actor: string | null;
  from_value: string;
  to_value: string;
  created_at: string;
}

export interface WorkLog {
  id: number;
  author_name: string;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export interface RequestDetail extends RequestItem {
  description: string;
  preferred_visit_at: string | null;
  received_at: string | null;
  assigned_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  closed_at: string | null;
  events: RequestEvent[];
  worklogs: WorkLog[];
}

export interface Technician {
  id: number;
  username: string;
  name: string;
  title: string;
}

export interface AppNotification {
  id: number;
  text: string;
  is_read: boolean;
  created_at: string;
  request: number | null;
  request_reference: string | null;
}

export interface Metrics {
  total: number;
  open: number;
  unassigned: number;
  sla_breached: number;
  by_status: { status: string; count: number }[];
  by_priority: { priority: string; count: number }[];
  by_department: { department: string; count: number }[];
  technician_workload: { technician: string; open: number }[];
  volume_14d: { date: string; count: number }[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
