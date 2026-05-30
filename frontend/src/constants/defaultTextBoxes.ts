/**
 * ✅ FIX 2.3: Shared DEFAULT_TEXT_BOXES constant
 * 
 * Prevents duplication between App.tsx and useScreenshotEngineForShell.ts
 * Single source of truth for default text box configuration.
 * 
 * Contains all 50 URLs across 3 categories:
 * - PARTS (17 URLs)
 * - SERVICE (16 URLs)
 * - ACCOUNTING (17 URLs)
 */

export interface TextBox {
  id: string;
  sessionName: string;
  urls: string;
  batchTimeout: number;
  batchTimeoutUnit: string;
  selected: boolean;
}

/**
 * DEFAULT TEXT BOXES: PARTS, SERVICE, ACCOUNTING
 * These persist even if localStorage is cleared.
 */
export const DEFAULT_TEXT_BOXES: TextBox[] = [
  {
    id: "textbox-1",
    sessionName: "PARTS",
    urls: `https://preprodapp.tekioncloud.com/parts/void-reasons
https://preprodapp.tekioncloud.com/parts/priority-codes
https://preprodapp.tekioncloud.com/parts/return-reasons
https://preprodapp.tekioncloud.com/parts/core-management-setup/reasons-setup
https://preprodapp.tekioncloud.com/parts/adjustment-reason
https://preprodapp.tekioncloud.com/parts/price-codes/list
https://preprodapp.tekioncloud.com/parts/price-breaks
https://preprodapp.tekioncloud.com/parts/customized-price
https://preprodapp.tekioncloud.com/parts/default-part-pricing
https://preprodapp.tekioncloud.com/parts/manufacturer
https://preprodapp.tekioncloud.com/parts/warehouse-management
https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/general
https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/customerNotifications
https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/dealerDetails#general-details
https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/dealerDetails#media-upload
https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/dealerDetails#oem-details
https://preprodapp.tekioncloud.com/parts/parts-settings/pdf-configuration`,
    batchTimeout: 900,
    batchTimeoutUnit: "seconds",
    selected: true,
  },
  {
    id: "textbox-2",
    sessionName: "SERVICE",
    urls: `https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/consumer-scheduling
https://preprodapp.tekioncloud.com/ro/opcode
https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/transportation
https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/shops
https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/serviceAdvisors
https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/general
https://preprodapp.tekioncloud.com/accounting/setupFields
https://preprodapp.tekioncloud.com/ro/labor-pricing
https://preprodapp.tekioncloud.com/service/settings/ro-settings
https://preprodapp.tekioncloud.com/core/cashiering-settings
https://preprodapp.tekioncloud.com/core/fees
https://preprodapp.tekioncloud.com/core/coupons
https://preprodapp.tekioncloud.com/ro/pdf-settings
https://preprodapp.tekioncloud.com/service/settings/checkin-setup/settings
https://preprodapp.tekioncloud.com/ro/mpvi-settings/FORMS
https://preprodapp.tekioncloud.com/ro/dispatch-settings`,
    batchTimeout: 900,
    batchTimeoutUnit: "seconds",
    selected: true,
  },
  {
    id: "textbox-3",
    sessionName: "ACCOUNTING",
    urls: `https://preprodapp.tekioncloud.com/accounting/accountPayable
https://preprodapp.tekioncloud.com/accounting/accountReceivable/setup
https://preprodapp.tekioncloud.com/accounting/journalMapping/list
https://preprodapp.tekioncloud.com/vi/visettings
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=NEW_VEHICLE
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=USED_VEHICLE
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=FNI_PRODUCT
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=RECEIVABLES
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=PAYABLES
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=SERVICE
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=PARTS_N_ACCESSORIES
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=FO_OTHERS
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=PAYMENT_METHODS_VAR_OPS
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=PAYMENT_METHODS_FIXED_OPS
https://preprodapp.tekioncloud.com/accounting/glaccountmapping/list?module=TEKION_PAY
https://preprodapp.tekioncloud.com/accounting/accountSettings
https://preprodapp.tekioncloud.com/accounting/autoPostingSettings`,
    batchTimeout: 900,
    batchTimeoutUnit: "seconds",
    selected: true,
  },
];
