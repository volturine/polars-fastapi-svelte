payload:
{
"analysis_id": "fbb90c69-b85d-439f-b305-32e309bab063",
"datasource_id": "73e8397f-39fc-482a-bc2f-cba7efcf6ec4",
"pipeline_steps": [
{
"id": "a0f0c795-f99c-43c2-ad63-c31830f56c2d",
"type": "chart",
"config": {
"chart_type": "bar",
"x_column": "city",
"y_column": "total_spent",
"bins": 10,
"aggregation": "sum",
"group_column": null
},
"depends_on": [],
"is_applied": true
},
{
"id": "08fdcea4-f69b-41dd-b1d1-0722f91ebc85",
"type": "filter",
"config": {
"conditions": [
{
"column": "first_name",
"operator": "contains",
"value": "c",
"value_type": "string"
}
],
"logic": "AND"
},
"depends_on": [],
"is_applied": true
},
{
"id": "4b8d0074-ba26-4255-bbaa-5585fbf61574",
"type": "view",
"config": {
"rowLimit": 100
},
"depends_on": [
"08fdcea4-f69b-41dd-b1d1-0722f91ebc85"
],
"is_applied": true
},
{
"id": "0481dc4e-3735-4aef-8378-a5e4a169450b",
"type": "filter",
"config": {
"conditions": [
{
"column": "first_name",
"operator": "=",
"value": "Alice",
"value_type": "string"
}
],
"logic": "AND"
},
"depends_on": [
"4b8d0074-ba26-4255-bbaa-5585fbf61574"
],
"is_applied": true
},
{
"id": "b25d6267-3cec-42f6-9ba7-bc60b207e473",
"type": "notification",
"config": {
"method": "telegram",
"recipient": "6421740079",
"subscriber_ids": [
"6421740079"
],
"bot_token": "",
"input_columns": [
"customer_id"
],
"output_column": "notification_status",
"message_template": "{{customer_id}} hi.",
"subject_template": "Notification",
"batch_size": 10,
"timeout_seconds": 20
},
"depends_on": [
"0481dc4e-3735-4aef-8378-a5e4a169450b"
],
"is_applied": true
},
{
"id": "972a09fe-f3f0-44cb-9b77-7429fc955e8c",
"type": "select",
"config": {
"columns": [
"first_name",
"last_name",
"customer_id"
]
},
"depends_on": [
"b25d6267-3cec-42f6-9ba7-bc60b207e473"
],
"is_applied": true
},
{
"id": "819c95be-42a5-49c5-96c8-071da2aab1ba",
"type": "view",
"config": {
"rowLimit": 100
},
"depends_on": [
"972a09fe-f3f0-44cb-9b77-7429fc955e8c"
],
"is_applied": true
}
],
"target_step_id": "819c95be-42a5-49c5-96c8-071da2aab1ba",
"format": "parquet",
"filename": "source_1",
"destination": "datasource",
"datasource_type": "iceberg",
"iceberg_options": {
"table_name": "test_export",
"namespace": "exports"
},
"duckdb_options": null,
"datasource_config": {
"output": {
"datasource_type": "iceberg",
"format": "parquet",
"filename": "source_1",
"iceberg": {
"namespace": "exports",
"table_name": "test_export"
},
"notification": {
"method": "telegram",
"excluded_recipients": [],
"body_template": "Analysis: {{analysis_name}}\nStatus: {{status}}\nDuration: {{duration_ms}}ms\nRows: {{row_count}}"
}
}
}
}

step timings:
chart: 0.05659600719809532ms
filter: 0.5548089975491166ms
view: 0.008407019777223468ms
filter_2: 0.12290998711250722ms
notification: 119.10186198656447ms
select: 0.05338099435903132ms
view_2: 0.010035000741481781ms

query plan:
SELECT [col("first_name"), col("last_name"), col("customer_id")]
DF ["customer_id", "first_name", "last_name", "email", ...]; PROJECT \*/12 COLUMNS
