/**
 * TypeScript interfaces for OEM ID Update feature
 */

export interface OemUpdateHeaders {
  dealerid: string;
  'tekion-api-token': string;
  tenantname: string;
  userid: string;
  accept?: string;
  'accept-language'?: string;
  applicationid?: string;
  clientid?: string;
  'content-type'?: string;
  locale?: string;
  origin?: string;
  'original-tenantid'?: string;
  'original-userid'?: string;
  productids?: string;
  program?: string;
  roleid?: string;
  subapplicationid?: string;
  'tek-siteid'?: string;
  'user-agent'?: string;
  [key: string]: string | undefined;
}

export interface OemUpdateRow {
  email: string;
  oemId: string;
  status?: 'pending' | 'success' | 'failed';
  error?: string;
  scenario?: 'CREATED' | 'EXISTING' | 'NEW';
  oldOemId?: string;
}

export interface OemTemplate {
  dealerId: string;
  oem: string;
  make: string;
  makeOverrideDisabled: boolean;
}

export interface BatchProgress {
  total: number;
  processed: number;
  success: number;
  failed: number;
  created: number;
  existing: number;
  logs: string[];
}

export interface TekionUser {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  oemMappings?: OemMapping[];
}

export interface OemMapping {
  dealerId: string;
  complexListId?: string;
  oemDetails: OemDetail[];
}

export interface OemDetail {
  oem: string;
  oemId: string | null;
  makeOverrideDisabled: boolean;
  complexListId?: string;
  makeOverrides?: MakeOverride[];
}

export interface MakeOverride {
  make: string;
  oemId: string | null;
  complexListId?: string;
}

export interface ParsedCsvData {
  headers: string[];
  rows: any[];
  emailColumn: string | null;
  oemIdColumn: string | null;
}
