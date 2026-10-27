# Depreciation run failures

## Common causes
A depreciation run fails most often because an asset has no depreciation method assigned, the accounting period is already closed, or an in-service date falls after the run period. The run log under Reports > Run History lists the first asset that failed.

## How to fix a failed run
Open Run History, select the failed run, and download the error log. Assign a method to any asset flagged "method missing", or reopen the period if your role allows it. Then start the run again from Depreciation > Run. Runs are safe to repeat; they replace results for the same period.

## When to contact support
If the run fails again with the same error after you correct the assets, open a ticket with the run ID and the error log attached.
