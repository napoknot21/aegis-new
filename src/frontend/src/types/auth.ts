export interface AccessibleOrganisation {
  id_org: number;
  id_user: number;
  org_code: string;
  org_name: string;
  email: string;
  display_name: string;
  office_ids: number[];
  office_codes: string[];
  office_names: string[];
  primary_office_id: number | null;
  primary_office_code: string | null;
  primary_office_name: string | null;
  role_codes: string[];
  accessible_fund_ids: number[];
  is_admin: boolean;
}

export interface CurrentSession {
  auth_enabled: boolean;
  authenticated: boolean;
  oid: string | null;
  tenant_id: string | null;
  email: string | null;
  preferred_username: string | null;
  display_name: string | null;
  default_org_id: number | null;
  orgs: AccessibleOrganisation[];
}
