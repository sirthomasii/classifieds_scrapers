export interface Publication {
  id: number;
  title: string;
  identifier: string;
  category: string;
  name: string;
  uid: string;
  level: string;
  status: string;
  is_visible: boolean;
  is_default: boolean;
  created_on: string | null;
  modified_on: string | null;
  affected_on: string | null;
  first_published_on: string | null;
  published_on: string | null;
}