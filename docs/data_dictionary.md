# Data Dictionary

All sources are synthetic monthly Parquet snapshots. Ingested DuckDB tables also receive `source_month` lineage.

## `provider_master`

One row per provider: `provider_id`, `provider_name`, `provider_type`, `specialty`, `segment`, `provider_zip`, `provider_state`, `region`, `territory`, `sales_rep_id`, `activation_date`, `status`, `employee_band`, `annual_volume_band`.

## `sales_rep_master`

One row per sales representative: `sales_rep_id`, `sales_rep_name`, `region`, `territory`, `manager_name`, `hire_date`, `status`.

## `applications`

One row per digital application: `application_id`, `application_date`, `application_month`, `customer_zip`, `customer_state`, `requested_amount`, `approval_flag`, `approved_amount`, `decline_flag`, `conversion_flag`, `digital_source`. It intentionally has no authoritative provider or rep identifiers and contains no customer PII.

## `application_assignment_events`

One row per assignment event: `assignment_event_id`, `application_id`, `assignment_date`, `assigned_provider_id`, `assignment_method`, `assignment_confidence`, `assignment_status`, `assigned_by`. Status is `assigned`, `manual_review`, or `unallocated`.

## `provider_location_reference`

One row per provider location: `provider_id`, `provider_zip`, `provider_state`, `specialty`, `sales_rep_id`, `territory`, `region`, `active_flag`.

## `financed_sales`

One row per financed transaction: `transaction_id`, `application_id`, `transaction_date`, `financed_amount`, `product_type`. Attribution is derived through the application assignment relationship.

## `provider_activity`

One row per provider and month: `month`, `provider_id`, `active_flag`, `applications_count`, `training_completed_flag`, `rep_contact_count`, `days_since_last_transaction`.

## `sales_goals`

One row per rep and month: `month`, `sales_rep_id`, `sales_goal`, `application_goal`, `activation_goal`.

## `pipeline`

One row per synthetic opportunity snapshot: `opportunity_id`, `month`, `provider_id`, `sales_rep_id`, `stage`, `estimated_volume`, `probability`, `expected_close_date`, `initiative_type`.
