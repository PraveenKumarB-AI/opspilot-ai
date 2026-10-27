# ERP integration and sync errors

## How the sync works
LedgerGrid exchanges journal entries and asset additions with your ERP through the Integration Hub. Syncs run every hour by default.

## Sync errors
Open Integration Hub > Sync Log to see failed records. The most common causes are a closed period in the ERP, an inactive account code, or a missing cost center mapping. Fix the mapping under Integration Hub > Mappings and click Retry.

## Changing the sync schedule
Administrators can change the sync frequency under Integration Hub > Settings. The shortest supported interval is 15 minutes.
