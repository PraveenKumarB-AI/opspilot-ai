# Unitization of completed work orders

## What unitization does
Unitization moves the costs of a completed work order into individual asset records so they can be depreciated. Until a work order is unitized, its costs stay in construction work in progress.

## Running unitization
Open Work Orders, filter by status "Completed, not unitized", select the work orders, and click Unitize. LedgerGrid matches cost lines to asset records using the retirement unit on each line.

## Unitization errors
The most common error is "no matching retirement unit". Add the retirement unit to the cost line, or allocate the cost manually from the Allocation tab, then unitize again.
