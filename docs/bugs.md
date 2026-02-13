original taskfile:

1. graphical nodes
1. all the basic plots
1. all the basic graphs
1. add notification node
   1. notification configs should be configurable all in one in the nodes
      1. smtp
      2. telegram
1. AI API support node ollama/openai
   1. custom API endpoints
   2. configurable to wire localhosted or prod endpoints
1. add suport to directly ingest another analysis/id/ tab as source
   1. each analysis/id tab should have last node pose two functions export as datasource and second is point to the output lazyframe in the engine
   2. withing same analysis/id/ one should be able to use any tab as an input
   3. only withing the same analysis/id because we want to directly use the lazyframe
   4. when in different analysis we are still dependend to use Datasource witch can be only updated manualy from the analysis or by schedule
   5. basicaly this add same behaviour as python files.. each analysis id is a python file with transformation
      1. within same python file for optimal performance we use direct lazy frame
      2. between python files we are dependent on what was build and when it was build and if we want fresh data we need to schedule back to back builds
1. add healthecks (send notification)
   1. lives in datasources config panel
   2. on successfull full builds
   3. column rules
   4. row count
1. data lineage tab
   1. used for visualisation of datasources
   2. datsource lineage (if one is derived from another bacause it was generated with analysis)
   3. graphical UI with dragable nodes of all datasrouces and their relations.
   4. used for scheduling.
      1. cron schedules with DAGs for sequential builds of dependent datasets
      2. should use the backed analysis to build the datasets with correct logic
1. preview of running build
   1. since some builds might take longer would be nice to see the execution time and such in graphical way..
   2. spark has special ui for stages and such not sure what does polars have either way visualisating schedules and their builds is nice to have as we see what is building for how long and what will be built after
1. builds UI improvements
   1. as mentioned before some more graphics and relations
   2. better filters
1. column stats in datasources
1. when clicking on column we should trigger a column stats compute..
1. it should come from the bottom
1. have all the related stats for column of type.
1. think polars has some exact thing that will do it automaticaly
1. this should be displayed in pretty manner
1. the indexeddb popup
   1. should have truncated rows to fixed size
   2. expand on click
   3. have a copy button
1. we need an analysis version history
   1. with ui for selecting the version we want
   2. should be saved in backend with unlimited retentions
   3. each hit of save button should append a new analysis version that will be backed.
   4. the mode selet button in analysis
      1. will have a third button, that is rollback
      2. it will show a full big popup in the middle of the screen with the past version to choose from
   5. reverting to version is just another append to the version history

---

found bugs and further specificaitons for allignemnt

# main point dont stop until you have tested these with python tests for all backend.. and verified frontend does make equvalient calls and all datatypes are correct

1. when i create a new tab it should not be a datasource imidietly.. only when i save it
2. analysis tab that uses another tab as input was not updated after i updated the tab
3. healthchecks tab should show how many healthcheks are active
   1. their status past few exports
4. lets add a global configuration for the notification base settings
   1. these can be used as default in the notification node
   2. should be a small button in line where we have engines/cache/theme/settings
   3. it will have the base smtp and telegram settings i can configure/test
   4. it can have the configuration on whether to hide/unhide indexdb cache button
   5. it should be a popup in the middle of the screen
5. where are the prety graphs?? only thing i see when i add graphs is some string saying what should be actualy visualized
   1. what i ment as leafs they act exactly like inline dataset previews they dont modify the DAG can be wherever..
   2. react to data. and
   3. visualize. it approprietly..
   4. maybe use some visualisation library for the diferent graphs standard one best for svelte that we could use even when hosting with fastapi..
   5. they can be wherever in thed dag
6. opening lineage tab triggers infinite effects loop
   1. effect_update_depth_exceeded @ chunk-65GEI2FJ.js?v=b0d4693a:321
      infinite_loop_guard @ chunk-65GEI2FJ.js?v=b0d4693a:2522
      flush_effects @ chunk-65GEI2FJ.js?v=b0d4693a:2496
      flush @ chunk-65GEI2FJ.js?v=b0d4693a:2301
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:2422
      run_all @ chunk-65GEI2FJ.js?v=b0d4693a:43
      run_micro_tasks @ chunk-65GEI2FJ.js?v=b0d4693a:669
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:675
      chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush_effects @ chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush @ chunk-65GEI2FJ.js?v=b0d4693a:2301
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:2422
      run_all @ chunk-65GEI2FJ.js?v=b0d4693a:43
      run_micro_tasks @ chunk-65GEI2FJ.js?v=b0d4693a:669
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:675
      chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush_effects @ chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush @ chunk-65GEI2FJ.js?v=b0d4693a:2301
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:2422
      run_all @ chunk-65GEI2FJ.js?v=b0d4693a:43
      run_micro_tasks @ chunk-65GEI2FJ.js?v=b0d4693a:669
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:675
      chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush_effects @ chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush @ chunk-65GEI2FJ.js?v=b0d4693a:2301
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:2422
      run_all @ chunk-65GEI2FJ.js?v=b0d4693a:43
      run_micro_tasks @ chunk-65GEI2FJ.js?v=b0d4693a:669
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:675
      chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush_effects @ chunk-65GEI2FJ.js?v=b0d4693a:2492
      flush @ chunk-65GEI2FJ.js?v=b0d4693a:2301
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:2422
      run_all @ chunk-65GEI2FJ.js?v=b0d4693a:43
      run_micro_tasks @ chunk-65GEI2FJ.js?v=b0d4693a:669
      (anonymous) @ chunk-65GEI2FJ.js?v=b0d4693a:675
      chunk-65GEI2FJ.js?v=b0d4693a:321 Uncaught

---

when i open datasource preview in datasources of datasource that is not in analysis

INFO: 127.0.0.1:42020 - "POST /api/v1/logs/client HTTP/1.1" 200 OK
2026-02-13 20:43:35,056 - modules.compute.manager - INFO - Spawning new engine for analysis **preview**45e135ce-0525-4316-8777-b0b963ebfb7b (5/10)
2026-02-13 20:43:35,057 - modules.compute.engine - INFO - Engine started for analysis **preview**45e135ce-0525-4316-8777-b0b963ebfb7b (threads: 2, memory: 8192 MB, chunk_size: auto)
2026-02-13 20:43:35,057 - modules.compute.manager - INFO - Engine spawned successfully for analysis **preview**45e135ce-0525-4316-8777-b0b963ebfb7b
2026-02-13 20:43:35,085 - core.error_handlers - ERROR - Failed to list engine runs: 1 validation error for EngineRunResponseSchema
progress
Input should be a valid number [type=float_type, input_value=None, input_type=NoneType]
For further information visit https://errors.pydantic.dev/2.12/v/float_type
Traceback (most recent call last):
File "/home/kripso/workspace/polars-fastapi-svelte/backend/core/error_handlers.py", line 113, in sync_wrapper
return func(\*args, \*\*kwargs)
File "/home/kripso/workspace/polars-fastapi-svelte/backend/modules/engine_runs/routes.py", line 23, in list_runs
return service.list_engine_runs(

```^
session=session,
^^^^^^^^^^^^^^^^
...<5 lines>...
offset=offset,
^^^^^^^^^^^^^^
)
^
File "/home/kripso/workspace/polars-fastapi-svelte/backend/modules/engine_runs/service.py", line 101, in list_engine_runs
response.append(EngineRunResponseSchema.model_validate(payload))
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
File "/home/kripso/workspace/polars-fastapi-svelte/backend/.venv/lib/python3.13/site-packages/pydantic/main.py", line 716, in model_validate
return cls.**pydantic_validator**.validate_python(
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
obj,
^^^^
...<5 lines>...
by_name=by_name,
^^^^^^^^^^^^^^^^
)
^
pydantic_core.\_pydantic_core.ValidationError: 1 validation error for EngineRunResponseSchema
progress
Input should be a valid number [type=float_type, input_value=None, input_type=NoneType]
For further information visit https://errors.pydantic.dev/2.12/v/float_type

---

filter errors on anything i try:
{
"analysis_id": "8b2c65fe-ac7d-4faa-97e6-2f66844429d4",
"datasource_id": "435fed8b-9c00-4666-87df-be2e2f4b6813",
"pipeline_steps": [
{
"id": "id-c9ff8f4574994819c4d2cce45",
"type": "sort",
"config": {
"columns": [
"action"
],
"descending": [
true
]
},
"depends_on": [],
"is_applied": true
},
{
"id": "da58b622-545b-4bbf-881c-39ca08957083",
"type": "filter",
"config": {
"conditions": [
{
"column": "page",
"operator": "=",
"value": "/datasources",
"value_type": "string"
}
],
"logic": "AND"
},
"depends_on": [
"id-c9ff8f4574994819c4d2cce45"
],
"is_applied": true
},
{
"id": "bbcc37d6-f558-451f-96c6-742302caa537",
"type": "view",
"config": {
"rowLimit": 15
},
"depends_on": [
"da58b622-545b-4bbf-881c-39ca08957083"
],
"is_applied": true
}
],
"target_step_id": "bbcc37d6-f558-451f-96c6-742302caa537",
"row_limit": 15,
"page": 1,
"resource_config": null,
"datasource_config": {
"time_travel_ui": {
"open": false,
"month": "2026-02",
"day": ""
}
}
}

Job c282e902-01fa-4279-bcef-1b65db15dab2: Failed with error: Step config is invalid. Please check the configuration fields.
2026-02-13 20:39:27,182 - core.error_handlers - ERROR - PipelineExecutionError: Preview failed: Step config is invalid. Please check the configuration fields.
Traceback (most recent call last):
File "/home/kripso/workspace/polars-fastapi-svelte/backend/core/error_handlers.py", line 113, in sync_wrapper
return func(\*args, \*\*kwargs)
File "/home/kripso/workspace/polars-fastapi-svelte/backend/modules/compute/routes.py", line 25, in preview_step
return service.preview_step(
~~~~~~~~~~~~~~~~~~~~^
session=session,
^^^^^^^^^^^^^^^^
...<8 lines>...
request_json=request.model_dump(mode='json'),
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
)
^
File "/home/kripso/workspace/polars-fastapi-svelte/backend/modules/compute/service.py", line 245, in preview_step
raise PipelineExecutionError(
...<2 lines>...
)
core.exceptions.PipelineExecutionError: Preview failed: Step config is invalid. Please check the configuration fields.
```
