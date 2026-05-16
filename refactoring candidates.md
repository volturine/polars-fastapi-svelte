data-forge • scripts/check_code_hygiene.py:
  49: def _iter_files(root: Path, suffixes: set[str]):
  58: def _check_frontend_sources(errors: list[str]) -> None:
  70: def _check_python_sources(errors: list[str]) -> None:

data-forge • scripts/check_dependency_hygiene.py:
  29: def _is_sorted(items: list[str]) -> bool:
  33: def _normalize_dependency_name(raw: str) -> str:

data-forge • scripts/check_env_contracts.py:
   49: def _collect_class_env_keys(path: Path, class_name: str) -> set[str]:
   81: def _parse_env_keys(path: Path) -> tuple[list[EnvKey], list[str]]:
  108: def _compose_vars(paths: tuple[Path, ...]) -> tuple[set[str], set[str]]:

data-forge • scripts/check_test_layout.py:
  12: def _iter_package_test_dirs() -> list[Path]:

data-forge • scripts/generate_ts_build_stream_types.py:
   43: def _json_schema_type_to_ts(schema: dict[str, Any], defs: dict[str, Any]) -> str:
  107: def _schema_to_ts_declaration(name: str, schema: dict[str, Any], defs: dict[str, Any]) -> str:
  127: def _emit_ref(
  152: def _collect_refs(schema: dict[str, Any]) -> list[str]:
  170: def _event_union_source() -> tuple[dict[str, Any], dict[str, Any]]:

data-forge • scripts/generate_ts_step_types.py:
   98: def _json_schema_type_to_ts(
  171: def _schema_to_ts_declaration(name: str, schema: dict[str, Any], defs: dict[str, Any]) -> str:
  200: def _collect_refs(schema: dict[str, Any]) -> list[str]:
  219: def _format_typescript(content: str) -> str:

data-forge • scripts/run_with_timeout.py:
  45:     def _handle(self, signum: int, _frame: object) -> None:

data-forge • scripts/scan_warnings.py:
  36: def _load_allowlist(path: Path, scope: str) -> list[re.Pattern[str]]:
  56: def _allowed(line: str, allowlist: list[re.Pattern[str]]) -> bool:
  60: def _scan(output: str, *, allowlist: list[re.Pattern[str]]) -> list[Match]:
  72: def _pipe_stream(stream: io.TextIOBase | None, target: io.TextIOBase, chunks: list[str]) -> None:
  81: def _parse_args() -> argparse.Namespace:
  91: def _scan_returncode(scope: str, returncode: int) -> list[Match]:

backend • main.py:
   59: def _register_api_worker(worker_id: str) -> None:
   60:     def _register(session: Session) -> None:
   73: def _heartbeat_api_worker(worker_id: str) -> None:
   74:     def _heartbeat(session: Session) -> None:
   80: def _stop_api_worker(worker_id: str) -> None:
   81:     def _stop(session: Session) -> None:
   98: def _resolve_uvicorn_workers() -> int:
  107: def _guard_runtime_workers(workers: int) -> int:
  115: def _resolve_uvicorn_limit_concurrency() -> int | None:
  121: def _mark_running_builds_orphaned_across_namespaces() -> int:
  135: async def _wait_until_stopped(stop_event: asyncio.Event, delay_seconds: float) -> bool:
  194:     def _check_bot_enabled(session: Session) -> tuple[bool, str]:

backend • backend_core/auth_config.py:
  19: def _get_env_file() -> str | None:
  72:     def _validate_default_user_password(cls, value: str) -> str:
  84:     def _validate_security_requirements(self) -> AuthSettings:


backend • backend_core/engine_live.py:
  61:     async def _discard_waiter(self, namespace: str, future: asyncio.Future[str]) -> None:

backend • backend_core/error_handlers.py:
   36: def _error_body(message: str, error_code: str | None = None, details: dict | None = None) -> dict[str, Any]:
   59: def _status_for(exc: AppError) -> int:
   63: def _log_app_error(exc: AppError, status: int) -> None:
   83: def _raise_http(exc: Exception, operation: str, value_error_status: int | None) -> Never:
  129: def _sanitize_validation_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:

backend • backend_core/settings_store.py:
  40: def _warn_bootstrap_secret_missing(name: str) -> None:
  44: def _read_secret(row: AppSettings, field: str) -> str:
  51: def _write_secret(row: AppSettings, field: str, value: str) -> None:
  55: def _resolve_updated_secret(row: AppSettings, field: str, value: str | None) -> str:
  63: def _masked_settings_response(row: AppSettings) -> SettingsResponse:

backend • backend_core/validation.py:
  8: def _parse_uuid(value: str) -> str:

backend • modules/analysis/routes.py:
  30: def _analysis_etag(analysis: schemas.AnalysisResponseSchema) -> str:
  34: def _analysis_version(analysis: schemas.AnalysisResponseSchema) -> str:
  38: def _validate_if_match(current_version: str, current_etag: str, if_match: str | None) -> None:

backend • modules/analysis/schemas.py:
   95: def _reject_pipeline_steps(data: Any) -> Any:
  101: def _reject_status(data: Any) -> Any:

backend • modules/analysis/service.py:
    53: def _to_response(analysis: Analysis, *, is_favorite: bool = False) -> AnalysisResponseSchema:
    69: def _favorite_ids(session: Session, user_id: str | None, analysis_ids: list[str]) -> set[str]:
    78: def _slugify(value: str) -> str:
    83: def _default_output_name(analysis_name: str, tab_name: str, index: int) -> str:
    87: def _build_output_config(analysis_name: str, tab_name: str, branch: str, index: int) -> dict[str, Any]:
   102: def _clone_step_config(config: dict[str, Any]) -> dict[str, Any]:
   106: def _build_template_steps(template: AnalysisTemplate) -> list[dict[str, Any]]:
   121: def _datasource_config_from_request(
   132: def _build_tabs_from_template(
   186: def _extract_json_object(content: str) -> dict[str, Any]:
   202: def _rewrite_import_payload(
   285: def _collect_missing_import_datasources(session: Session, pipeline: dict[str, Any]) -> list[str]:  # type: ignore[type-arg]
   322: def _resolved_generation_provider(
   414: def _validate_analysis_payload(
   994: def _ensure_no_cycle(session: Session, analysis_id: str, source_analysis_id: str) -> None:
  1028:     def _is_valid_source(src_id: str) -> bool:
  1201: def _slugify_output_name(name: str) -> str:
  1208: def _next_duplicate_tab_name(tabs: list[PipelineTab], source_name: str) -> str:

backend • modules/analysis/templates.py:
  36: def _template_file() -> Path:

backend • modules/analysis_versions/service.py:
  139: def _ensure_no_cycle(session: Session, analysis_id: str, source_analysis_id: str) -> None:

backend • modules/auth/dependencies.py:
  10: def _resolve_session_token(request: Request) -> str | None:

backend • modules/auth/models.py:
  18: def _utcnow() -> datetime:

backend • modules/auth/routes.py:
   71: def _evict_me_cache() -> None:
   92: def _set_session_cookie(response: Response, session_token: str, *, secure: bool) -> None:
  104: def _clear_session_cookie(response: Response) -> None:
  108: def _oauth_state_cookie_key(provider: str) -> str:
  112: def _set_oauth_state_cookie(response: Response, provider: str, state: str, *, secure: bool) -> None:
  124: def _validate_oauth_state(request: Request, response: Response, provider: str, state: str | None) -> None:
  136: def _build_user_public(session: Session, user: User) -> UserPublic:
  152: def _request_device_info(request: Request) -> str | None:
  159: def _request_ip_address(request: Request) -> str | None:
  292: def _resolve_me(session: Session, token: str | None) -> UserPublic:

backend • modules/auth/service.py:
   41: def _utcnow() -> datetime:
   45: def _naive_utc(value: datetime) -> datetime:
   63: def _clear_owned_resources(session: Session, user_id: str) -> None:
   81: def _clear_owned_resources_in_namespaces(user_id: str) -> None:
  133: def _send_smtp_message(host: str, port: int, smtp_user: str, password: str, msg: EmailMessage) -> None:
  137: def _normalize_default_user_email(email: str) -> str:
  144: def _normalize_default_user_name(name: str, email: str) -> str:
  151: def _get_password_provider(session: Session, user_id: str) -> AuthProvider | None:
  156: def _build_default_provider_metadata(password: str) -> dict[str, str]:

backend • modules/chat/openrouter.py:
  24: def _headers(api_key: str) -> dict[str, str]:
  32: def _mcp_tool_to_openai(tool: dict) -> dict:

backend • modules/chat/routes.py:
   80: def _infer_patch(tool_id: str, method: str, path: str, result: dict) -> dict | None:
  106: def _format_param_details(name: str, schema: dict, required: bool, location: str, description: str = "") -> str:
  124: def _format_fallback_param_details(schema: dict) -> list[str]:
  130: def _build_tool_system_message(tools: list[dict]) -> str:
  205: def _push_tool_error(
  234: def _try_parse_json(text: str) -> list[dict] | None:
  251: def _parse_text_tool_calls(content: str) -> tuple[str, list[dict]]:
  280: async def _run_agent_turn(
  687:         async def _heartbeat_loop() -> None:

backend • modules/chat/sessions.py:
   84:     def _trim_messages(self) -> None:
  147:     def _db(self) -> DbSession:

backend • modules/compute/executor_client.py:
  21: def _ensure_runtime_available(runtime_probe: RuntimeAvailabilityProbe) -> None:
  27: async def _submit_and_wait(

backend • modules/compute/routes.py:
   75: async def _wait_for_websocket_disconnect(websocket: WebSocket) -> None:
   89: def _override_manager(container) -> Any | None:
   99: def _override_compute_executor(container) -> Any | None:
  103: def _resolve_websocket_user(websocket: WebSocket) -> User | None:
  114:     def _lookup(session: Session) -> User | None:
  125: async def _emit_active_build_event(
  151: def _get_durable_build_detail(session: Session, build_id: str) -> schemas.ActiveBuildDetail | None:
  158: def _list_durable_active_builds(session: Session, namespace: str) -> list[schemas.ActiveBuildSummary]:
  172: def _build_snapshot_message(session: Session, build_id: str) -> schemas.BuildSnapshotMessage | None:
  182: def _build_list_snapshot_message(session: Session, namespace: str) -> schemas.BuildListSnapshotMessage:
  186: async def _replay_build_events(websocket: WebSocket, build_id: str, after_sequence: int) -> int | None:
  202: async def _wait_for_build_notification(websocket: WebSocket, build_id: str, last_sequence: int = 0) -> BuildNotification | None:
  215: async def _wait_for_namespace_build_update(websocket: WebSocket, namespace: str, last_seen: str | None) -> str | None:
  233: def _get_durable_build_detail_by_engine_run(session: Session, engine_run_id: str) -> schemas.ActiveBuildDetail | None:
  240: async def _require_websocket_user(websocket: WebSocket) -> User:
  247: def _utcnow() -> datetime:
  251: def _analysis_name(session: Session, analysis_id: str | None) -> str:
  260: def _build_analysis_name(pipeline: dict) -> str:
  273: def _build_triggered_by(user: User | None) -> str:
  279: async def _send_build_snapshot(websocket: WebSocket, build_id: str) -> None:
  292: async def _send_build_list_snapshot(websocket: WebSocket, namespace: str) -> None:
  303: def _get_latest_build_namespace_update(namespace: str) -> str | None:
  310: async def _send_engine_snapshot(websocket: WebSocket) -> None:
  326: async def _wait_for_engine_notification(websocket: WebSocket, namespace: str, last_seen: str | None) -> str | None:

backend • modules/datasource/preflight.py:
  63: async def _cleanup_expired() -> None:
  75: async def _delete_temp_file(path: Path, *, delete_file: bool) -> None:

backend • modules/datasource/routes.py:
   76: def _write_chunk(path: Path, chunk: bytes) -> None:
   81: async def _save_upload_file(file: UploadFile, file_path: Path, max_bytes: int) -> None:
   94: def _list_export_branches(metadata_path: str) -> list[str]:
  118: def _matches_magic_number(file_extension: str, upload: UploadFile) -> bool:
  795: async def _handle_column_stats(

backend • modules/datasource/schemas.py:
  229:     def _normalize_description(cls, value: str | None) -> str | None:
  276:     def _normalize_description(cls, value: str | None) -> str | None:

backend • modules/datasource/service.py:
   39: def _open_excel_workbook(file_path: Path, *, table_name: str | None) -> Any:
  258: def _resolve_excel_bounds(
  325: def _parse_cell_range(workbook, cell_range: str, default_sheet: str | None) -> _ExcelBounds:
  368: def _validate_excel_bounds(sheet, start_row: int, start_col: int, end_col: int, end_row: int) -> None:
  383: def _detect_end_col(sheet, start_row: int, start_col: int) -> int:
  401: def _detect_end_row(sheet, start_row: int, start_col: int, end_col: int) -> int:
  419: def _collect_preview_rows(
  438: def _log_build_update(
  448: def _log_build_create(
  459: def _build_datasource_result_json(
  488: def _get_column_metadata_map(session: Session, datasource_id: str) -> dict[str, str | None]:
  786: def _delete_file_path(file_path: str) -> None:
  812: def _iceberg_cleanup_root(metadata_path: str) -> Path | None:
  827: def _is_within(path: Path, root: Path) -> bool:
  833: def _delete_datasource_files(datasource: DataSource) -> None:

backend • modules/export/generators.py:
   58: def _identifier(value: str) -> str:
   67: def _safe_json(value: Any) -> str:
   71: def _safe_py(value: Any) -> str:
   84: def _sql_quote(value: str) -> str:
   89: def _sql_literal(value: Any) -> str:
  100: def _tab_dependencies(tab: PipelineTab) -> set[str]:
  180: def _datasource_path_constant(
  199: def _scan_expression(datasource: DataSource | None, path_const: str) -> tuple[str, str | None]:
  225: def _polars_filter_expr(condition: dict[str, Any]) -> str | None:
  262: def _sql_filter_expr(condition: dict[str, Any]) -> str | None:
  304: def _polars_group_agg_expr(aggregation: dict[str, Any]) -> str | None:
  319: def _sql_group_agg_expr(aggregation: dict[str, Any]) -> str | None:

backend • modules/healthcheck/service.py:
  114: def _ensure_unique_row_count(

backend • modules/locks/routes.py:
   26: async def _get_websocket_owner_id(websocket: WebSocket) -> str | None:
   34: def _status_payload(resource_type: str, resource_id: str, lock: schemas.LockStatusResponse | None) -> dict:
   42: async def _send_status(
   51: async def _send_error(websocket: WebSocket, error: str, status_code: int) -> None:
   61: async def _notify_watchers(resource_type: str, resource_id: str, lock: schemas.LockStatusResponse | None) -> None:
   77: async def _lookup_lock_status(resource_type: str, resource_id: str) -> tuple[schemas.LockStatusResponse | None, bool]:
   81: async def _heartbeat_lock(
  104: async def _acquire_lock(
  125: async def _release_lock(

backend • modules/locks/service.py:
  12: def _utcnow() -> datetime:
  16: def _as_utc(value: datetime) -> datetime:
  22: def _expires_at(now: datetime, ttl_seconds: int | None) -> datetime:
  27: def _status(lock: ResourceLock, now: datetime | None = None) -> LockStatusResponse:

backend • modules/locks/watchers.py:
  
backend • modules/mcp/decorators.py:
  16: def _iter_wrapped(fn: Callable) -> list[Callable]:
  31: def _build_meta(fn: Callable, confirm_required: bool | None) -> dict[str, Any]:

backend • modules/mcp/executor.py:
  21: def _interpolate_path(path: str, args: dict) -> tuple[str, dict]:

backend • modules/mcp/pending.py:
  
backend • modules/mcp/registry.py:
   26: def _requires_confirm(method: str, path: str) -> bool:
   30: def _route_openapi_operation(route: APIRoute, schema: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
   46: def _description(op: dict[str, Any], meta: dict[str, Any], method: str, path: str) -> str:
   53: def _confirm_required(method: str, path: str, meta: dict[str, Any]) -> bool:
   60: def _tag_list(route: APIRoute, op: dict[str, Any]) -> list[str]:
   68: def _openapi_to_json_schema(schema_ref: Any, components: dict) -> Any:
   97: def _output_schema(op: dict[str, Any], meta: dict[str, Any], components: dict) -> dict[str, Any] | None:
  136: def _build_tool(route_data: dict, components: dict) -> dict:
  232: def _marked_routes(app: FastAPI) -> list[dict[str, Any]]:

backend • modules/mcp/router.py:
   16: def _response_model_name(route: APIRoute) -> str | None:
   70: def _get_endpoint_meta(endpoint: Callable[..., Any]) -> dict[str, Any] | None:
  135:     def _route_decorator(
  
backend • modules/mcp/routes.py:
  20: def _request_tool_context(request: Request) -> dict[str, dict[str, str]]:
  36: def _resolve_tool(app: FastAPI, tool_id: str, args: dict) -> tuple[dict, bool, list[dict], dict]:

backend • modules/mcp/validation.py:
   60: def _check_schema_node(schema: Any, path: str, issues: list[str]) -> None:
  111: def _format_error_path(error: jsonschema.ValidationError) -> str:
  116: def _build_error_message(error: jsonschema.ValidationError) -> str:

backend • modules/runtime_overview/service.py:
   18: def _utcnow() -> datetime:
   22: def _as_utc(value: datetime) -> datetime:
   28: def _age_seconds(value: datetime, *, now: datetime | None = None) -> float:
  108: def _queue_namespace_summary(namespace: str) -> schemas.QueueNamespaceSummary:
  124: def _read_queue_namespace_summary(
  148: def _queue_totals(

backend • modules/scheduler/routes.py:
  31: def _response(schedule: Schedule, datasource: DataSource | None, analysis: Analysis | None) -> schemas.ScheduleResponse:
  57: def _enrich(session: Session, schedules: list[Schedule]) -> list[schemas.ScheduleResponse]:

backend • modules/settings/routes.py:
  38: def _apply_telegram_bot_runtime(enabled: bool, token: str, telegram_bot) -> None:  # type: ignore[no-untyped-def]

backend • modules/telegram/bot.py:
   73:     def _poll_loop(self) -> None:
  167:     def _wait_for_retry(self, seconds: float) -> bool:
  170:     def _do_get_updates(
  199:     def _clear_webhook(self, token: str) -> None:
  209:     def _get_offset(self, token: str) -> int:
  213:     def _set_offset(self, token: str, offset: int) -> None:
  217:     def _handle_update(self, update: dict) -> None:
  234:     def _handle_subscribe(self, chat_id: str, title: str) -> None:
  239:         def _add(session) -> None:  # type: ignore[no-untyped-def]
  250:     def _handle_unsubscribe(self, chat_id: str) -> None:
  255:         def _remove(session) -> None:  # type: ignore[no-untyped-def]
  269:     def _send_message(self, chat_id: str, text: str) -> None:

backend • modules/udf/service.py:
  21: def _validate_code(code: str) -> None:
  30: def _signature_key(signature: dict) -> str:

backend • tests/conftest.py:
   63: def _register_backend_sqlmodel_metadata() -> None:
  111: def _backend_settings_tables() -> list[Any]:
  134: def _reset_backend_settings_state(engine: Engine) -> None:

backend • tests/test_analysis_export_code.py:
  6: def _create_analysis_with_join(client, left_ds_id: str, right_ds_id: str) -> str:

backend • tests/test_analysis.py:
    15: def _schema_enum_values(schema: dict, field_name: str) -> list[str]:
  1251:     def _make_payload(self, datasource_id: str, steps: list[dict]) -> dict:

backend • tests/test_auth_config.py:
  10: def _set_isolated_auth_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:

backend • tests/test_auth.py:
    67: def _make_postgres_engine(prefix: str = "auth", *, schema_name: str | None = None):
    83: def _schema_enum_values(schema: dict, field_name: str) -> list[str]:
  
backend • tests/test_build_comparison_api.py:
  8: def _create_run(

backend • tests/test_chat.py:
  17: def _session_history(session_id: str) -> list[dict]:
  25: def _done_count(history: list[dict]) -> int:
  29: def _wait_for_history(session_id: str, predicate: Callable[[list[dict]], bool], *, timeout: float = 0.5) -> list[dict]:
  40: async def _wait_for_history_async(

backend • tests/test_engine_runs.py:
  14: def _create_payload(

backend • tests/test_healthcheck_routes.py:
   8: def _create_datasource(session, ds_id: str | None = None) -> DataSource:
  23: def _create_check(session, datasource_id: str, name: str = "Row Count Check") -> HealthCheck:
  40: def _create_result(session, healthcheck_id: str, passed: bool, message: str, minutes_ago: int = 0) -> HealthCheckResult:

backend • tests/test_lineage.py:
   7: def _create_analysis(analysis_id: str, name: str) -> Analysis:
  20: def _create_datasource(
  36: def _seed_rich_lineage_graph(test_db_session):
  89: def _get_lineage(client, **params):

backend • tests/test_mcp.py:
  638:     def _path_names(path: str) -> set[str]:

backend • tests/test_proxy.py:
  11: def _request(scope_overrides: dict[str, Any] | None = None) -> Request:

backend • tests/test_runtime_overview.py:
  120: def _set_running_job_owner(session, build_id: str, worker_id: str) -> None:

backend • tests/test_settings.py:
   15: def _make_postgres_engine(prefix: str = "settings"):
  219:         def _read(session: Session) -> AppSettings | None:
  237:         def _seed(session: Session) -> None:
  744:     def _make_engine(self):
  953:     def _make_engine(self):

backend • tests/test_step_registry.py:
  16: def _load_worker_module(name: str, path: Path):

backend • tests/test_step_schemas.py:
  13: def _enum_values(schema: dict, field_name: str) -> list[str] | None:

backend • tests/integration/faux_datasource_runtime.py:
  158:     def _source_options(self, source: dict[str, object]) -> dict[str, Any]:
  162:     def _stat_value(self, value: object) -> float | str | None:
  169:     def _get_datasource(self, session: Session, datasource_id: str) -> DataSource:
  177:     def _schema_for(self, datasource: DataSource):
  194:     def _response(self, datasource: DataSource):
  201:     def _read_dataframe(self, datasource: DataSource) -> pl.DataFrame:
  220:     def _clean_dir(self) -> Path:

backend • tests/integration/test_datasource_extended.py:
  639:     def _insert_datasource(self, session, *, is_hidden: bool, csv_file: Path) -> DataSource:

backend • tests/integration/test_docker_bootstrap.py:
   15: def _base_url() -> str:
   22: def _db_url() -> str:
   29: def _default_user_email() -> str:
   36: def _default_user_password() -> str:
   43: def _psql_value(sql: str) -> str:
   51: def _wait_for_build_detail(client: httpx.Client, build_id: str, *, timeout: float = 180) -> dict[str, object]:
   66: def _wait_for_runtime_workers() -> tuple[int, int]:
   77: def _api_worker_count() -> int:
   84: def _wait_for_api_workers(min_count: int) -> int:
   94: def _wait_for_scheduled_build(schedule_id: str) -> tuple[str, str]:
  138: def _upload_datasource(client: httpx.Client, name: str) -> str:
  148: def _login_default_user(client: httpx.Client) -> None:
  162: def _create_analysis(client: httpx.Client, name: str, datasource_id: str) -> dict[str, object]:
  209: def _start_build(client: httpx.Client, analysis: dict[str, object]) -> str:

backend • tests/integration/test_postgres_runtime_integration.py:
   31: def _clear_database_state() -> None:
   45: def _table_exists(connection: psycopg.Connection, schema: str, table: str) -> bool:
   53: def _query_value(connection: psycopg.Connection, sql: str, params: tuple[object, ...] = ()):
   61: def _make_csv(rows: int) -> str:
   67: def _runtime_env(*, data_dir: Path, database_url: str, port: int) -> dict[str, str]:
   91: def _init_runtime_db(env: dict[str, str]) -> None:
  106: def _upload_datasource(client, name: str, *, content: str = SAMPLE_CSV) -> str:
  116: def _create_analysis(
  170: def _start_build(client, analysis: dict[str, object]) -> str:
  195: def _wait_for_running_build(client, build_id: str, *, timeout: float = 180) -> dict[str, object]:
  209: def _slow_steps() -> list[dict[str, object]]:
  533:             def _api_worker_count() -> int:
  633:             def _api_worker_count() -> int:

scheduler • main.py:
   71: async def _run_once(*, worker_id: str) -> bool:
  120: def _claim_due_schedule_refs(session: Session, *, worker_id: str) -> list[tuple[str, str]]:
  133: def _runtime_namespaces() -> list[str]:
  137: def _register_worker(*, worker_id: str) -> None:
  138:     def _register(session):
  151: def _heartbeat_worker(*, worker_id: str) -> None:
  152:     def _heartbeat(session):
  158: def _stop_worker(worker_id: str) -> None:
  159:     def _stop(session):
  165: def _heartbeat_loop_sync(*, stop_signal: threading.Event, worker_id: str, heartbeat_seconds: float) -> None:
  182:     def _stop() -> None:

scheduler • scheduler_service.py:
   39: def _utcnow() -> datetime:
   43: def _naive_utc(value: datetime) -> datetime:
   47: def _mark_schedule_failure(
  191: def _build_analysis_request(session: Session, schedule: Schedule, analysis_id: str) -> tuple[compute_schemas.BuildRequest, str, str, str | None, str | None]:
  214: def _build_refresh_request(schedule: Schedule) -> compute_schemas.BuildRequest:
  240: def _enqueue_schedule_refresh_build(
  274: def _enqueue_schedule_analysis_build(
  316: def _resolve_schedule_target(session: Session, datasource_id: str) -> tuple[str, str | None, str | None]:
  337: def _build_schedule_response(
  373: def _is_reingestable_raw_datasource(datasource: DataSource) -> bool:
  386: def _enrich_schedule_response(session: Session, schedule: Schedule) -> ScheduleResponse:
  395: def _enrich_schedule_response_batch(
  598: def _is_triggered_by_datasource(
  624: def _is_triggered_by_schedule(

scheduler • tests/test_scheduler.py:
  41: def _load_runtime_scheduler():

shared • contracts/analysis/step_types.py:
  76:     def _definition_for(self, step_type: str) -> StepType | None:

shared • contracts/build_jobs/live.py:
   5:     async def _discard_waiter(self, future: asyncio.Future[int]) -> None:
  60:     def _resolve_waiter(future: asyncio.Future[int], version: int) -> None:

shared • contracts/build_runs/live.py:
   91:     async def _discard_waiter(
  105:     def _resolve_waiter(future: asyncio.Future[BuildNotification], notification: BuildNotification) -> None:

shared • contracts/compute_requests/live.py:
    5:     async def _discard_waiter(self, future: asyncio.Future[int]) -> None:
   60:     def _resolve_waiter(future: asyncio.Future[int], version: int) -> None:
   10:     async def _discard_waiter(self, request_id: str, future: asyncio.Future[int]) -> None:
  122:     def _resolve_waiter(future: asyncio.Future[int], version: int) -> None:

shared • contracts/locks/models.py:
  8: def _utcnow() -> datetime:

shared • contracts/runtime/ipc.py:
   23: def _psycopg_conninfo() -> str:
   38: def _postgres_connection_socket(connection: psycopg.Connection) -> int:
   51: async def _wait_for_postgres_socket(connection: psycopg.Connection, stop_event) -> bool:
   56:     def _mark_ready() -> None:
   73: async def _serve_postgres_notifications(connection: psycopg.Connection, stop_event, handler: Callable[[dict[str, object]], Awaitable[None]]) -> None:
   93: def _notify_payload(notify: Notify) -> str:
  124: def _send_api_message(payload: dict[str, object], *, listener: ListenerKind) -> None:
  129: def _get_notify_connection() -> psycopg.Connection:
  144: def _reset_notify_connection() -> None:
  153: def _send_postgres_message(payload: dict[str, object]) -> None:

shared • core/ai_clients.py:
   35: def _retry_request(method: str, url: str, *, headers: dict | None = None, payload: dict | None = None, retries: int = _MAX_RETRIES) -> httpx.Response:
   93:     def _headers(self) -> dict[str, str]:
  140:     def _headers(self) -> dict[str, str]:
  179:     def _headers(self) -> dict[str, str]:
  186:     def _extract_generated_text(payload: object) -> str:

shared • core/build_jobs_service.py:
  12: def _utcnow() -> datetime:

shared • core/build_runs_service.py:
   15: def _utcnow() -> datetime:
   19: def _copy_json_dict(value: dict[str, Any] | None) -> dict[str, object]:
  144: def _next_sequence(session: Session, build_id: str) -> int:
  150: def _apply_context(run: BuildRun, event: compute_schemas.BuildEvent) -> None:
  166: def _apply_terminal_status(run: BuildRun, event: compute_schemas.BuildEvent) -> bool:
  201: def _terminal_status_for_event(event: compute_schemas.BuildEvent) -> BuildRunStatus | None:
  211: def _terminal_update_values(event: compute_schemas.BuildEvent) -> dict[str, object] | None:
  254: def _cas_update_build_run(session: Session, *, run: BuildRun, values: dict[str, object], expected_status: BuildRunStatus) -> BuildRun | None:
  398: def _list_build_events(session: Session, build_id: str) -> list[BuildEvent]:

shared • core/compute_requests_service.py:
  12: def _utcnow() -> datetime:

shared • core/config.py:
   36: def _default_data_dir() -> Path:
   41: def _get_env_file() -> str | None:
   50: def _resolve_dir(value: Path | str) -> Path:
   57: def _resolve_file_parent(value: Path | str) -> Path:
  208:     def _ensure_dirs(cls, value: Path) -> Path:
  213:     def _validate_upload_chunk_size(cls, value: int) -> int:
  222:     def _validate_log_level(cls, value: str) -> str:
  230:     def _validate_database_url(cls, value: str, _info) -> str:
  241:     def _validate_timezone(cls, value: str) -> str:
  249:     def _validate_log_queue_overflow(cls, value: str) -> str:
  257:     def _validate_trusted_proxy_hops(cls, value: int) -> int:
  263:     def _validate_numeric_constraints(self) -> 'Settings':
  273:     def _validate_directories_writable(self) -> 'Settings':
  282:     def _validate_lock_intervals(self) -> 'Settings':
  288:     def _validate_runtime_mode(self) -> 'Settings':

shared • core/database.py:
   20: def _engine_kwargs() -> dict[str, object]:
   29: def _create_engine(url: str, *, connect_args: dict[str, object] | None = None) -> Engine:
   59: def _invalidate_settings_cache() -> None:
   86: def _set_postgres_search_path(raw_connection: object, namespace: str) -> None:
   97: def _apply_postgres_search_path(connection: Connection, namespace: str) -> None:
  103: def _create_public_engine() -> Engine:
  107:     def _set_public_search_path(dbapi_connection, _connection_record, _connection_proxy) -> None:
  127: def _get_tenant_engine() -> Engine:
  140:             def _set_namespace_search_path(dbapi_connection, _connection_record, _connection_proxy) -> None:
  184: def _shared_tables():
  194: def _tenant_tables():
  231: def _create_shared_tables_postgres() -> None:
  242: def _ensure_postgres_schema(connection: Connection, schema: str) -> None:
  246: def _init_postgres_namespace(namespace: str) -> None:
  252: def _seed_shared_state() -> None:
  255:     def _seed(session: Session) -> None:
  264: def _run_postgres_init_locked(func) -> None:
  277: def _namespace_init_key(namespace: str) -> tuple[str, str]:
  281: def _mark_namespace_initialized(namespace: str) -> None:
  291: def _init_namespace_db(namespace: str) -> None:
  301: def _init_namespace_db_unlocked(namespace: str) -> None:
  310: def _bootstrap_postgres() -> None:
  326:     def _init_postgres() -> None:

shared • core/docker_healthcheck.py:
  11: def _now() -> datetime:
  18:     def _read(session):

shared • core/engine_instances_service.py:
   11: def _utcnow() -> datetime:
   15: def _copy_json(value: dict[str, object] | None) -> dict[str, object] | None:
   19: def _apply_engine_status(row: EngineInstance, *, status: EngineStatusInfo, stamp: datetime) -> None:
  155: def _read_dt(value: str | None) -> datetime | None:

shared • core/engine_runs_service.py:
   66: def _step_label_for_timing_key(key: str) -> tuple[str, str]:
  151: def _copy_result_json(value: dict[str, Any] | None) -> dict[str, Any]:
  155: def _latest_completed_step_name(result_json: dict[str, Any]) -> str | None:
  217: def _serialize_run(run: EngineRun) -> EngineRunResponseSchema:
  463: def _safe_int(val: object) -> int | None:
  472: def _load_result_summary(result_json: dict[str, Any] | None) -> EngineRunResultSummary:
  486: def _compute_schema_diff(schema_a: dict[str, str], schema_b: dict[str, str]) -> list[ColumnDiff]:
  501: def _compute_timing_diff(timings_a: dict[str, float], timings_b: dict[str, float]) -> list[TimingDiff]:

shared • core/exceptions.py:
    
shared • core/export_formats.py:
  41: def _write_duckdb(df: pl.DataFrame, path: str) -> None:

shared • core/healthcheck_runner.py:
   15: def _build_expressions(checks: list[HealthCheck], schema_names: set[str]) -> tuple[list[pl.Expr], list[HealthCheck]]:
   95: def _evaluate_row_count(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
  118: def _evaluate_column_count(check: HealthCheck, schema_names: set[str]) -> tuple[bool, str, HealthcheckDetails]:
  138: def _evaluate_column_null(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
  149: def _evaluate_null_percentage(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
  160: def _evaluate_column_unique(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
  177: def _evaluate_column_range(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:
  198: def _evaluate_duplicate_percentage(check: HealthCheck, row: pl.DataFrame) -> tuple[bool, str, HealthcheckDetails]:

shared • core/iceberg_metadata.py:
  83: def _resolve_iceberg_data_root(*, namespace_name: str | None = None, data_root: str | Path | None = None) -> Path:
  89: def _latest_metadata_file(metadata_dir: Path) -> str:
  96: def _strip_file_scheme(metadata_path: str) -> str:

shared • core/logging.py:
   53: def _client_ip(request: Request) -> str | None:
   65: def _adapt_datetime(value: datetime) -> str:
   69: def _day_from_ts(ts: datetime | None) -> date:
   95:     def _init_db(self) -> None:
  227:     def _enqueue_rows(self, kind: str, rows: list[dict[str, Any]]) -> None:
  244:     def _enqueue_flush(self) -> None:
  251:     def _ensure_flush_timer(self) -> None:
  262:     def _cancel_flush_timer(self) -> None:
  269:     def _run(self) -> None:
  282:     def _buffer_rows(self, kind: str, rows: list[dict[str, Any]]) -> None:
  290:     def _insert_rows(self, kind: str, day: date, rows: list[dict[str, Any]]) -> None:
  305:     def _lock_for_insert(self):
  313:     def _insert_request_logs(self, conn: psycopg.Connection, rows: list[dict[str, Any]], day: date) -> None:
  344:     def _insert_app_logs(self, conn: psycopg.Connection, rows: list[dict[str, Any]], day: date) -> None:
  367:     def _insert_client_logs(self, conn: psycopg.Connection, rows: list[dict[str, Any]], day: date) -> None:
  453:     async def _capture_response(self, request: Request, response: Response, duration_ms: float, request_id: str, request_body: bytes | None) -> Response:
  491:     def _log_request(
  534:     def _coerce_body(self, content_type: str | None, body: bytes | None) -> str | None:
  540: def _should_redact_path(path: str) -> bool:
  544: def _redact_json_value(value: Any) -> Any:
  594: def _extract_log_extras(record: logging.LogRecord) -> str | None:

shared • core/migrations.py:
   17: def _alembic_config(*, scope: str, schema: str) -> Config:
   29: def _connect(database_url: str) -> psycopg.Connection:
   33: def _normalized_database_url(database_url: str) -> str:
   39: def _database_exists(database_url: str) -> bool:
   51: def _maintenance_database_url(database_url: str) -> str:
   77: def _has_version_table(schema: str) -> bool:
   90: def _current_revision(schema: str) -> str | None:
  105: def _schema_has_table(*, schema: str, table_name: str) -> bool:
  118: def _stamp_schema(*, scope: str, schema: str, revision: str) -> None:
  122: def _upgrade_schema(*, scope: str, schema: str, revision: str) -> None:

shared • core/runtime_workers_service.py:
  8: def _utcnow() -> datetime:

shared • core/secrets.py:
  18: def _read_key_material() -> str:
  26: def _require_key_material() -> str:
  34: def _derive_key_for_material(material: str) -> bytes:
  38: def _derive_key() -> bytes:
  46: def _decode_payload(payload: str) -> bytes:

shared • core/settings_projection.py:
  22: def _read_secret(row: AppSettings, field: str) -> str:
  29: def _active_settings_engine_id() -> int:
  35: def _load_resolved_snapshot(session: Session) -> dict[str, object]:
  79: def _get_resolved_snapshot() -> dict[str, object]:

shared • database/alembic/env.py:
  37: def _should_configure_logging() -> bool:
  66: def _runtime_scope() -> str:
  70: def _target_schema() -> str:
  74: def _table_names() -> set[str]:
  80: def _target_metadata():
  88: def _include_object(object_, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]

shared • database/alembic/versions/0001_runtime_public.py:
  22: def _scope() -> str:

shared • database/alembic/versions/0002_runtime_tenant.py:
  42: def _scope() -> str:

shared • tests/test_build_comparison.py:
  14: def _create_run(

shared • tests/test_build_runs.py:
  12: def _starter() -> dict[str, object]:
  16: def _create_run(test_db_session):

shared • tests/test_compute_schemas.py:
  92: def _pipeline_payload() -> dict:

shared • tests/test_core_config.py:
  11: def _set_isolated_settings_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, data_dir: Path | None = None) -> Path:

shared • tests/test_core_smtp.py:
  7: def _message() -> EmailMessage:

 • tests/harness/base_fixtures.py:
   30: def _settings():
shared   36: def _register_sqlmodel_metadata() -> None:
   76: def _settings_tables() -> list[Any]:
   86: def _reset_settings_state(engine: Engine) -> None:
  110: def _schema_engine(database_url: str, schema: str) -> Engine:

shared • tests/harness/postgres_harness.py:
   89: def _drain_stream(stream, chunks: list[str]) -> None:
  135:     def _join_threads(self) -> None:
  189:     def _wait_for_port_mapping(self, *, timeout: float = 30) -> int:
  
worker-manager • main.py:
   61: def _register_manager(worker_id: str) -> None:
   62:     def _register(session) -> None:
   75: def _heartbeat_manager(worker_id: str, active_jobs: int = 0) -> None:
   76:     def _heartbeat(session) -> None:
   82: def _stop_manager(worker_id: str) -> None:
   83:     def _stop(session) -> None:
  104: def _manager_heartbeat_loop(stop_signal: threading.Event, worker_id: str, *, heartbeat_seconds: float = 5.0) -> None:
  109: async def _watch_process_stop_signal(stop_signal: ProcessEvent, stop_event: asyncio.Event) -> None:
  114: def _worker_main(stop_signal: ProcessEvent, stopped_signal: ProcessEvent) -> None:
  115:     async def _run() -> None:
  172: def _spawn_worker_process() -> ManagedWorkerProcess:
  180: def _wait_for_child_stop(child: ManagedWorkerProcess, *, timeout_seconds: float, require_ack: bool) -> bool:
  200: def _stop_worker_process(child: ManagedWorkerProcess) -> None:
  218: def _reap_dead_children(children: dict[int, ManagedWorkerProcess]) -> None:
  225: def _next_idle_child_pid(children: dict[int, ManagedWorkerProcess]) -> int | None:
  321:     def _stop() -> None:

worker-manager • builds/build_execution.py:
   20: async def _emit_active_build_event(
   44: async def _run_active_build_task(
  105: async def _run_queued_build_job(*, manager: ProcessManager, build_id: str) -> None:

worker-manager • builds/build_live.py:
   30: def _utcnow() -> datetime:
   34: def _safe_float(value: object, default: float = 0.0) -> float:
   42: def _safe_int(value: object) -> int | None:
   52: def _safe_str(value: object) -> str | None:
   58: def _safe_datetime(value: object) -> datetime | None:
   72: def _sanitize_log_message(value: object) -> str:
   85: def _normalize_payload(payload: dict) -> dict:
   93: def _should_throttle(build: ActiveBuild, payload: dict) -> bool:
  107: def _consume_throttled(build: ActiveBuild, payload: dict) -> list[dict]:
  340:     async def _cancel_tasks(self, tasks: list[asyncio.Task[None]]) -> None:
  377:     def _schedule_task_cleanup(self, build_id: str, task: asyncio.Task[None]) -> None:
  383:     async def _drop_task(self, build_id: str, task: asyncio.Task[None]) -> None:
  640:     def _prune_finished_locked(self) -> None:

worker-manager • datasources/datasource_loading.py:
   25: def _csv_opts(opts: dict[str, Any] | None) -> dict[str, Any]:
   38: def _read_excel(path: str, opts: dict[str, Any]) -> pl.LazyFrame:
   52: def _merge_excel_opts(config: dict[str, Any], opts: dict[str, Any]) -> dict[str, Any]:
   67: def _normalize_headers(values: tuple[object | None, ...]) -> list[str]:
   81: def _has_bounds(config: dict[str, Any]) -> bool:
   87: def _read_excel_bounds(config: dict[str, Any]) -> pl.LazyFrame:
  125: def _assert_select_only(query: str) -> None:

worker-manager • datasources/datasource_schemas.py:
  229:     def _normalize_description(cls, value: str | None) -> str | None:
  276:     def _normalize_description(cls, value: str | None) -> str | None:

worker-manager • datasources/datasource_service.py:
   43: def _prepare_clean_target(clean_dir: Path, datasource_id: str, branch: str) -> Path:
   49: def _write_iceberg_table(lazy: pl.LazyFrame, table_path: Path, build_mode: str) -> Table:
   75: def _build_iceberg_config(
   95: def _sync_iceberg_schema(table: Table, new_schema: Any) -> None:
   99: def _set_snapshot_metadata(config: dict[str, object], snapshot: Any | None) -> None:
  108: def _schema_cache_payload(schema_info: SchemaInfo) -> dict[str, Any]:
  113: def _get_first_non_null_samples(lazy: pl.LazyFrame, max_rows: int = 1000) -> dict[str, str | None]:
  122: def _schema_from_analysis(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
  130: def _schema_from_database(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
  160: def _schema_from_file(datasource: DataSource, sheet_name: str | None) -> SchemaInfo:
  199: def _extract_schema(datasource: DataSource, sheet_name: str | None = None) -> SchemaInfo:
  222: def _build_datasource_result_json(
  251: def _log_build_create(
  262: def _log_build_update(
  272: def _persist_schema_cache(session: Session, datasource: DataSource) -> None:
  623: def _get_column_metadata_map(session: Session, datasource_id: str) -> dict[str, str | None]:
  630: def _attach_column_descriptions(session: Session, datasource_id: str, schema_info: SchemaInfo) -> SchemaInfo:
  663: def _build_snapshot_preview(lazy: pl.LazyFrame, schema: pl.Schema, row_limit: int) -> SnapshotPreview:
  673: def _supports_min_max(dtype: pl.DataType) -> bool:
  695: def _supports_unique(dtype: pl.DataType) -> bool:
  718: def _build_snapshot_stats(lazy: pl.LazyFrame, schema: pl.Schema) -> list[ColumnStats]:
  748: def _build_schema_diff(schema_a: pl.Schema, schema_b: pl.Schema) -> list[SchemaDiff]:
  824: def _compute_histogram(series: pl.Series, bins: int = 20) -> list[dict[str, object]]:

worker-manager • operations/ai.py:
  53:     def _parse_options(cls, v: str | dict[str, object] | None) -> dict[str, object] | None:
  57:     def _validate_input_columns(self) -> "AIParams":
  63: def _build_prompt(template: str, row: dict[str, object]) -> str:
  69:     def _replace(m: re.Match[str]) -> str:
  
worker-manager • operations/datasource.py:
   88:     def _load_file(self, config: DatasourceParams) -> pl.LazyFrame:
   91:     def _load_database(self, config: DatasourceParams) -> pl.LazyFrame:
   94:     def _load_duckdb(self, config: DatasourceParams) -> pl.LazyFrame:
   97:     def _load_iceberg(self, config: DatasourceParams) -> pl.LazyFrame:
  113:     def _load_analysis(self, config: DatasourceParams) -> pl.LazyFrame:
  132: def _get_analysis_stack() -> tuple[tuple[str, str | None], ...]:
  136: def _load_analysis_pipeline(pipeline: dict, analysis_id: str, tab_id: str | None) -> pl.LazyFrame:
  154: def _analysis_cache_key(pipeline: dict, tab_id: str | None) -> str:
  164: def _resolve_pipeline_datasource(pipeline: dict, datasource: dict) -> dict:
  188: def _step_source_payload(step_config: dict, source_id: str) -> dict | None:
  201: def _get_analysis_cache(key: str) -> pl.LazyFrame | None:
  206: def _store_analysis_cache(key: str, frame: pl.LazyFrame) -> None:
  218: def _resolve_analysis_tab(tabs: list[dict], analysis_tab_id: str | None) -> dict:
  229: def _resolve_tab_chain(tabs: list[dict], target_tab_id: str) -> list[dict]:
  272: def _build_tab_pipeline(
  328: def _build_analysis_from_pipeline(pipeline: dict, analysis_tab_id: str | None) -> pl.LazyFrame:
  350: def _collect_analysis_sources(
  
worker-manager • operations/filter.py:
  207:     def _build_expr(self, cond: FilterCondition, schema: pl.Schema) -> pl.Expr:
  258: def _is_date_only_value(value: Any) -> bool:
  264: def _normalize_datetime_col(expr: pl.Expr, dtype: pl.DataType) -> pl.Expr:

  
worker-manager • operations/join.py:
  37:     def _join_with_how(
  
  
worker-manager • operations/notification.py:
  37:     def _validate(self) -> "NotificationParams":
  45: def _build_message(template: str, row: dict[str, object]) -> str:
  48:     def _replace(m: re.Match[str]) -> str:
  
worker-manager • operations/pivot.py:
   29:     def _auto_on_columns(lf: pl.LazyFrame, pivot_column: str) -> list[str]:
   36:     def _pivot_with_aggregate(
  
worker-manager • operations/plot.py:
  272: def _agg_expr(col: str, agg: AggregationType) -> pl.Expr:
  294: def _apply_sort(df: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  307: def _apply_date_bucket(lf: pl.LazyFrame, column: str, p: ChartParams) -> pl.LazyFrame:
  341: def _group_sort_value_col(p: ChartParams) -> str | None:
  349: def _apply_group_sort(
  398: def _aggregate_bar(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  413: def _aggregate_line(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  428: def _aggregate_pie(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  464: def _build_histogram(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  520: def _build_scatter(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  528: def _build_boxplot(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  559: def _aggregate_heatgrid(lf: pl.LazyFrame, p: ChartParams) -> pl.LazyFrame:
  
worker-manager • operations/step_converter.py:
  398: def _identity_config(config: dict) -> dict:
  
worker-manager • runtime/compute_engine.py:
    53:     def _classify_engine_error(exc: Exception) -> tuple[str, dict[str, object]]:
    22:     def _create_queues(self) -> None:
   127:     def _ensure_queues(self) -> None:
   132:     def _reset_state(self) -> None:
   189:     def _send_command(self, command: PreviewCommand | ExportCommand | SchemaCommand | RowCountCommand) -> str:
   269:     def _wait_for_queue_message(self, queue: MPQueue | None, *, timeout: float | None) -> tuple[str, object | None]:
   379:     def _store_pending_result(self, result: EngineResult) -> None:
   389:     def _await_shutdown_ack(self, timeout: float = 5.0) -> bool:
   444:     def _close_queues(self) -> None:
   461:     def _run_compute(
   656:     def _build_pipeline(
   837:     def _merge_query_plans(plans: list[dict | None]) -> dict | None:
   860:     def _get_query_plans(lf: pl.LazyFrame) -> dict | None:
   873:     def _extract_plans(
   883:     def _resolve_chart_preview(
   923:     def _execute_preview(
   979:     def _execute_export(
  1032:     def _execute_schema(
  1072:     def _execute_row_count(
  1112:     def _apply_step(

worker-manager • runtime/compute_manager.py:
   20: def _default_engine_factory(analysis_id: str, resource_config: dict | None = None) -> ComputeEngine:
   49:     def _key(self, analysis_id: str, namespace: str | None = None) -> str:
   52:     def _split_key(self, key: str) -> tuple[str, str]:
  169:     def _configs_differ(self, old_config: dict, new_config: dict) -> bool:
  172:     def _normalize_config(self, config: dict | None) -> dict:
  213:     def _get_defaults(self) -> dict:
  303:     def _emit_snapshot(self) -> None:

worker-manager • runtime/compute_request_runtime.py:
   60:             def _claim(session: Session) -> ClaimedComputeRequest | None:
  113: async def _run_once(*, worker_id: str, manager: ProcessManager) -> bool:
  130: async def _execute_request(claimed: ClaimedComputeRequest, manager: ProcessManager) -> None:
  393: def _write_artifact(request_id: str, filename: str, content: bytes) -> Path:
  401: def _error_message(exc: Exception) -> str:
  407: def _error_payload(exc: Exception) -> dict[str, object]:

worker-manager • runtime/compute_service.py:
    72: def _secure_temp_path(suffix: str) -> str:
    78: def _ensure_download_size(path: str) -> int:
   179: def _utcnow() -> datetime:
   183: def _resource_summary(engine) -> dict[str, int | None]:
   195: def _datasource_name(session: Session, datasource_id: str | None) -> str | None:
   204: def _estimate_remaining(elapsed_ms: int, completed_steps: int, total_steps: int) -> int | None:
   212: def _event_model(payload: dict[str, object]) -> compute_schemas.BuildEvent:
   216: def _build_event(
   224: async def _emit_build_event(
   234: async def _emit_progress(
   309: def _resolve_build_status(
   336: def _raise_engine_failure(
   393: def _preflight_datasource_for_compute(
   434: def _build_subscriber_message(context: BuildContext) -> str:
   487: def _load_healthcheck_lazy(output_path: str, export_format: str) -> pl.LazyFrame | None:
   495: def _send_pipeline_notifications(
   538:             def _normalize_target(value: object) -> tuple[str, str] | None:
   572: def _sync_iceberg_schema(table: IcebergTable, new_schema: pa.Schema) -> bool:
   576: def _upsert_output_datasource(
   628: def _build_preview_result_metadata(
   656: def _build_export_result_metadata(
   674: def _build_engine_run_execution_entries(
   704: def _copy_json_dict(value: object) -> dict[str, object]:
   708: def _tab_name_from_pipeline(analysis_pipeline: dict, tab_id: str | None) -> str | None:
   726: def _normalize_query_plan_snapshots(
   769: def _step_type_from_execution_entry(entry: dict[str, object]) -> str:
   783: def _build_step_snapshots_from_execution_entries(
   818: def _result_entry(
   841: def _log_entry(
   861: def _load_engine_run_result_json(session: Session, run_id: str) -> dict[str, object]:
   869: def _read_cancel_metadata(run: EngineRun) -> tuple[str | None, str | None]:
   879: def _raise_if_engine_run_cancelled(session: Session, run_id: str) -> None:
   888: def _cancel_started_engine_run_if_build_cancelled(build: ActiveBuild, *, run_id: str) -> None:
   903: def _parse_cancelled_at(value: str | None) -> datetime | None:
   909: def _read_build_cancel_metadata(run) -> tuple[str | None, str | None]:
   915: def _raise_if_build_cancelled(session: Session, build_id: str) -> None:
   924: def _finalize_failed_engine_run(
   988: def _build_canonical_engine_run_result(
  1060: def _initial_live_run_result(
  1088: def _resolve_branch_value(config: dict) -> str:
  1095: def _set_snapshot_metadata(config: dict, snapshot_id: str | None, snapshot_timestamp_ms: int | None) -> dict:
  1107: def _ensure_request_branch(request_payload: dict, branch: str) -> dict:
  1119: def _get_additional_datasources(
  1163: def _hydrate_udfs(session: Session, steps: list[dict]) -> list[dict]:
  1192: def _pipeline_output_to_tab_id(pipeline: dict) -> dict[str, str]:
  1208: def _step_source_payload(step_config: dict, source_id: str) -> dict | None:
  1221: def _pipeline_datasource_payload(pipeline: dict, datasource_id: str) -> dict | None:
  1237: def _resolve_pipeline_datasource_config(
  1288: def _resolve_step_source_config(
  1319: def _resolve_pipeline_request(
  2476: def _resolve_upstream_tabs(tabs: list[dict], target_tab_id: str) -> set[str]:
  2508: def _build_execution_tabs(pipeline: dict) -> tuple[list[dict], str | None]:
  2526: def _resolve_live_output_metadata(output_config: dict, tab_name: str) -> tuple[str | None, str | None]:
  2542: def _count_total_build_steps(tabs: list[dict], selected_tab_id: str | None) -> int:
  2558: async def _stream_engine_events(
  2720: async def _stream_resource_events(
  2745: def _schedule_stream_tasks(
  2796: def _start_stream_tasks(
  2871: async def _stop_stream_task(task: asyncio.Task | None) -> None:

worker-manager • runtime/compute_utils.py:
   22: def _build_step_map(steps: list[dict]) -> dict[str, dict]:
  104: def _engine_result_to_dict(result: EngineResult) -> dict[str, Any]:

worker-manager • runtime/engine_notifications.py:
  19:     def _write(session) -> None:

worker-manager • runtime/worker_runtime.py:
   39: async def _wait_until_stopped(stop_event: asyncio.Event, delay_seconds: float) -> bool:
   50: async def _wait_for_build_job_signal(stop_event: asyncio.Event, wake_event: asyncio.Event) -> None:
  122: async def _run_once(
  139:         def _mark_failed(session):
  148:     def _finalize(session):
  176:             def _claim(session):
  198: def _reconcile_schedule_run(session, *, build_id: str) -> None:
  225: def _register_worker(*, worker_id: str, capacity: int) -> None:
  226:     def _register(session):
  239: def _heartbeat_worker(*, worker_id: str, active_jobs: int | None = None) -> None:
  240:     def _heartbeat(session):
  246: def _stop_worker(worker_id: str) -> None:
  247:     def _stop(session):
  253: def _release_worker_jobs(worker_id: str) -> None:
  258:             def _release(session):
  266: def _heartbeat_loop_sync(*, stop_signal: threading.Event, worker_id: str, heartbeat_seconds: float) -> None:

worker-manager • tests/test_compute_monitor.py:
  
worker-manager • tests/test_fixes.py:
   141: def _chart_frame() -> pl.LazyFrame:
   848:     def _make_csv_config(self) -> tuple[str, dict]:
   943:     def _run_udf(self, code: str):
  1024:     def _check(self, query: str):

worker-manager • tests/test_healthchecks.py:
  13: def _create_datasource(session, ds_id: str | None = None) -> DataSource:
  27: def _make_check(
  46: def _create_check(session, datasource_id: str, name: str = "Row Count Check") -> HealthCheck:
  54: def _create_result(session, healthcheck_id: str, passed: bool, message: str, minutes_ago: int = 0) -> HealthCheckResult:

worker-manager • tests/test_iceberg_build_modes.py:
   16:     def _make_table(self, iceberg_fields: list[NestedField]) -> tuple[MagicMock, MagicMock]:
  114:     def _make_pipeline(self, datasource: DataSource, output_ds_id: str, build_mode: str = "full") -> dict:
  139:     def _make_engine_mock(self) -> MagicMock:
  150:     def _make_manager_mock(self) -> MagicMock:
  157:     def _setup_mocks(self, table_exists: bool = True):

worker-manager • tests/test_operations.py:
  25: def _frame() -> pl.LazyFrame:

worker-manager • tests/test_performance_baseline.py:
  9: def _measure(func, *args, **kwargs):

worker-manager • tests/test_runtime_workers.py:
   24: def _load_runtime_process():
  


  179 results - 37 files

backend • main.py:
  356  
  357:     if full_path.startswith("api/") or full_path == "api":
  358          raise HTTPException(status_code=404, detail="Not Found")

  374  
  375: if __name__ == "__main__":
  376      import multiprocessing

backend • backend_core/runtime_notifications.py:
  11      kind = payload.get("kind")
  12:     if kind == "build":
  13          namespace = payload.get("namespace")

  24          return
  25:     if kind == "engine":
  26          namespace = payload.get("namespace")

  29          return
  30:     if kind == "compute_response":
  31          request_id = payload.get("request_id")

backend • modules/analysis/routes.py:
  41      normalized = if_match.strip()
  42:     if normalized == "*":
  43          return

backend • modules/analysis/service.py:
  146          steps = _build_template_steps(template)
  147:         if template.id == "join_and_enrich" and index > 0:
  148              steps = []
  149:         if template.id == "join_and_enrich" and index == 0 and len(datasources) > 1:
  150              for step in steps:
  151:                 if step["type"] == "join":
  152                      step["config"]["right_source"] = datasources[1].id

  171  
  172:     if template.id == "join_and_enrich" and len(tabs) > 1 and first_output_id and first_tab_id:
  173          for index, tab in enumerate(tabs[1:], start=1):

  324      requested = provider.strip().lower() if provider else ""
  325:     if requested == "openrouter":
  326          api_key = get_resolved_openrouter_key()

  329          return "openrouter", "", {"api_key": api_key}
  330:     if requested == "openai":
  331          resolved = get_resolved_openai_settings()

  342          )
  343:     if requested == "ollama":
  344          resolved = get_resolved_ollama_settings()

  349          )
  350:     if requested == "huggingface":
  351          resolved = get_resolved_huggingface_settings()

backend • modules/auth/routes.py:
  187      )
  188:     _set_session_cookie(response, created_session.id, secure=request_scheme(request) == "https")
  189      return _build_user_public(session, user)

  224      )
  225:     _set_session_cookie(response, created_session.id, secure=request_scheme(request) == "https")
  226      return _build_user_public(session, user)

  393          state=state,
  394:         secure=request_scheme(request) == "https",
  395      )

  449      )
  450:     _set_session_cookie(response, created_session.id, secure=request_scheme(request) == "https")
  451      return response

  469          state=state,
  470:         secure=request_scheme(request) == "https",
  471      )

  541      )
  542:     _set_session_cookie(response, created_session.id, secure=request_scheme(request) == "https")
  543      return response

backend • modules/chat/routes.py:
  338              registry = [t for t in registry if t["id"] in id_set]
  339:         safe_tools = [t for t in registry if t["safety"] == "safe"]
  340:         mutating_tools = [t for t in registry if t["safety"] == "mutating"]
  341          all_tools = safe_tools + mutating_tools

  351              if tool_system_msg and use_text_format:
  352:                 insert_idx = 1 if api_messages and api_messages[0].get("role") == "system" else 0
  353                  api_messages.insert(insert_idx, tool_system_msg)

  588          # Update system message in conversation history
  589:         if session.messages and session.messages[0].get("role") == "system":
  590              session.messages[0]["content"] = body.system_prompt

  736              raise HTTPException(status_code=400, detail="API key is required")
  737:         if provider == "openrouter":
  738              if not key:

backend • modules/chat/sessions.py:
   86              return
   87:         system = [m for m in self.messages if m.get("role") == "system"]
   88          non_system = [m for m in self.messages if m.get("role") != "system"]

  224                  for m in messages:
  225:                     if m.get("role") == "user":
  226                          preview = m.get("content", "")[:100]

backend • modules/compute/routes.py:
  84              raise
  85:         if message.get("type") == "websocket.disconnect":
  86              return

backend • modules/datasource/routes.py:
  120      upload.file.seek(0)
  121:     if file_extension == ".parquet":
  122          return header.startswith(b"PAR1")
  123:     if file_extension == ".xlsx":
  124          return header.startswith(b"PK")

  171      csv_options = None
  172:     if file_type == "csv":
  173          csv_options = schemas.CSVOptions(

  288  
  289:         file_csv_options = csv_options if file_type == "csv" else None
  290          try:

  608          )
  609:     if datasource.source_type == "duckdb":
  610          raise HTTPException(

  613          )
  614:     if datasource.source_type == "api":
  615          raise HTTPException(status_code=400, detail="API datasources are not supported")

backend • modules/datasource/schemas.py:
  215              return None
  216:         if value.strip() == "":
  217              return None

backend • modules/datasource/service_lineage.py:
  195              current = queue.popleft()
  196:             neighbors = reverse_adj.get(current, set()) if mode == "upstream" else forward_adj.get(current, set())
  197              for node_id in neighbors:

backend • modules/datasource/service.py:
  412              values = [c.value for c in cell]
  413:         if all(value is None or str(value).strip() == "" for value in values):
  414              return max(start_row, row_index - 2)

  622  
  623:         if datasource.source_type == "duckdb" and "read_only" in update.config and update.config.get("read_only") != datasource.config.get("read_only", True):
  624              raise DataSourceValidationError(

  658          )
  659:         is_excel_file = next_config.get("file_type") == "excel"
  660:         if datasource.source_type == "file" and is_excel_file and has_excel_bounds:
  661              file_path = next_config.get("file_path")

backend • modules/export/generators.py:
  105      for step in tab.steps:
  106:         if step.type == "join":
  107              right_source = step.config.get("right_source")

  109                  deps.add(right_source)
  110:         if step.type == "union_by_name":
  111              raw_sources = step.config.get("sources")

  207      file_type = str(config.get("file_type", "")).lower()
  208:     if source_type == "file":
  209:         if file_type == "csv":
  210              return f"pl.scan_csv({path_const})", None
  211:         if file_type == "parquet":
  212              return f"pl.scan_parquet({path_const})", None

  233  
  234:     if operator == "is_null":
  235          return f"{column_expr}.is_null()"
  236:     if operator == "is_not_null":
  237          return f"{column_expr}.is_not_null()"
  238  
  239:     if value_type == "column" and isinstance(compare_column, str) and compare_column:
  240          rhs = f"pl.col({json.dumps(compare_column)})"

  244      if operator in {"=", "==", "!=", ">", "<", ">=", "<="}:
  245:         actual = "==" if operator == "=" else operator
  246          return f"{column_expr} {actual} {rhs}"
  247:     if operator == "contains":
  248          return f"{column_expr}.str.contains({rhs}, literal=True)"
  249:     if operator == "not_contains":
  250          return f"~{column_expr}.str.contains({rhs}, literal=True)"
  251:     if operator == "starts_with":
  252          return f"{column_expr}.str.starts_with({rhs})"
  253:     if operator == "ends_with":
  254          return f"{column_expr}.str.ends_with({rhs})"
  255:     if operator == "in":
  256          return f"{column_expr}.is_in({rhs})"
  257:     if operator == "not_in":
  258          return f"~{column_expr}.is_in({rhs})"

  270  
  271:     if operator == "is_null":
  272          return f"{lhs} IS NULL"
  273:     if operator == "is_not_null":
  274          return f"{lhs} IS NOT NULL"
  275  
  276:     if value_type == "column" and isinstance(compare_column, str) and compare_column:
  277          rhs = _sql_quote(compare_column)

  286      if operator in _FILTER_BINARY_OPERATORS:
  287:         actual = "=" if operator == "==" else operator
  288          return f"{lhs} {actual} {rhs}"
  289:     if operator == "contains":
  290          return f"{lhs} LIKE ('%' || {rhs} || '%')"
  291:     if operator == "not_contains":
  292          return f"{lhs} NOT LIKE ('%' || {rhs} || '%')"
  293:     if operator == "starts_with":
  294          return f"{lhs} LIKE ({rhs} || '%')"
  295:     if operator == "ends_with":
  296          return f"{lhs} LIKE ('%' || {rhs})"
  297:     if operator == "in":
  298          return f"{lhs} IN {rhs}"
  299:     if operator == "not_in":
  300          return f"{lhs} NOT IN {rhs}"

  313      func = function.lower()
  314:     if func == "n_unique":
  315          return f"pl.col({json.dumps(column)}).n_unique().alias({json.dumps(alias_name)})"

  332      expr = _sql_quote(column)
  333:     if template == "COUNT_DISTINCT":
  334          rendered = f"COUNT(DISTINCT {expr})"

  410  
  411:             if step.type == "filter":
  412                  conditions = [condition.model_dump(mode="json", exclude_none=True) for condition in FilterConfig.model_validate(config).conditions]

  415                  if exprs:
  416:                     joiner = " & " if logic == "AND" else " | "
  417                      lines.append(f"{next_var} = {current_var}.filter({joiner.join(exprs)})")

  420                      warn(f"Filter step in tab '{tab.name}' has no valid conditions")
  421:             elif step.type == "select":
  422                  columns = config.get("columns")

  442                          lines.append(f"{next_var} = {next_var}.with_columns({cast_expr})")
  443:             elif step.type == "drop":
  444                  columns = config.get("columns")

  449                      lines.append(f"{next_var} = {current_var}")
  450:             elif step.type == "sort":
  451                  columns = config.get("columns")

  465                      lines.append(f"{next_var} = {current_var}")
  466:             elif step.type == "rename":
  467                  mapping = config.get("column_mapping")

  471                      lines.append(f"{next_var} = {current_var}")
  472:             elif step.type == "groupby":
  473                  group_by = config.get("group_by")

  489                      warn(f"GroupBy step in tab '{tab.name}' is missing group_by or aggregations")
  490:             elif step.type == "join":
  491                  right_source = config.get("right_source")

  503                          right_list = "[" + ", ".join(json.dumps(col) for col in right_cols) + "]"
  504:                         mapped_how = "full" if how == "outer" else how
  505                          lines.append(

  515                      warn(f"Join step in tab '{tab.name}' could not resolve right source '{right_source}'")
  516:             elif step.type == "expression":
  517                  expression = config.get("expression")

  525                      warn(f"Expression step in tab '{tab.name}' is missing expression or column_name")
  526:             elif step.type == "with_columns":
  527                  expressions = config.get("expressions")

  536                              continue
  537:                         if expr_type == "literal":
  538                              rendered.append(f"pl.lit({_safe_py(expression.get('value'))}).alias({json.dumps(name)})")
  539:                         elif expr_type == "column" and isinstance(expression.get("column"), str):
  540                              rendered.append(

  542                              )
  543:                         elif expr_type == "udf":
  544                              warn(

  552                      lines.append(f"{next_var} = {current_var}")
  553:             elif step.type == "pivot":
  554                  on_col = config.get("columns")

  568                      warn(f"Pivot step in tab '{tab.name}' is missing columns")
  569:             elif step.type == "unpivot":
  570                  id_vars = config.get("id_vars")

  584                      warn(f"Unpivot step in tab '{tab.name}' is missing value_vars")
  585:             elif step.type == "deduplicate":
  586                  subset = config.get("subset")

  592                      lines.append(f"{next_var} = {current_var}.unique(keep={json.dumps(keep)})")
  593:             elif step.type == "sample":
  594                  fraction = config.get("fraction", 0.5)

  599                      lines.append(f"{next_var} = {current_var}.sample(fraction={_safe_py(fraction)})")
  600:             elif step.type == "limit":
  601                  n = config.get("n", 100)
  602                  lines.append(f"{next_var} = {current_var}.limit({int(n) if isinstance(n, int) else 100})")
  603:             elif step.type == "view":
  604                  lines.append(f"{current_var}.show(limit=5)")

  701              source_from = source_tables.get(tab.id, "(SELECT NULL WHERE FALSE)")
  702:             if source_from == "(SELECT NULL WHERE FALSE)":
  703                  warn(f"Tab '{tab.name}' is missing datasource metadata for SQL export")

  713  
  714:             if step.type == "filter":
  715                  conditions = [condition.model_dump(mode="json", exclude_none=True) for condition in FilterConfig.model_validate(config).conditions]

  718                  if exprs:
  719:                     joiner = " AND " if logic == "AND" else " OR "
  720                      body = f"SELECT * FROM {current_cte} WHERE " + joiner.join(exprs)

  722                      warn(f"Filter step in tab '{tab.name}' has no valid SQL conditions")
  723:             elif step.type == "select":
  724                  columns = config.get("columns")

  740                      warn(f"Select step in tab '{tab.name}' has no columns and was treated as pass-through")
  741:             elif step.type == "sort":
  742                  columns = config.get("columns")

  756                          body = f"SELECT * FROM {current_cte} ORDER BY " + ", ".join(clauses)
  757:             elif step.type == "groupby":
  758                  group_by = config.get("group_by")

  768                      warn(f"GroupBy step in tab '{tab.name}' is missing group_by or aggregations")
  769:             elif step.type == "join":
  770                  right_source = config.get("right_source")

  774                  right_cte = tab_final_cte.get(str(right_source)) if isinstance(right_source, str) else None
  775:                 if how == "cross" and right_cte:
  776                      body = f"SELECT l.*, r.* FROM {current_cte} AS l CROSS JOIN {right_cte} AS r"

  802                      warn(f"Join step in tab '{tab.name}' could not resolve right source '{right_source}'")
  803:             elif step.type == "expression":
  804                  expression = config.get("expression")

  809                      warn(f"Expression step in tab '{tab.name}' is missing expression or column_name")
  810:             elif step.type == "limit":
  811                  n = config.get("n", 100)

  813                  body = f"SELECT * FROM {current_cte} LIMIT {n_value}"
  814:             elif step.type == "deduplicate":
  815                  subset = config.get("subset")
  816                  keep = str(config.get("keep", "first"))
  817:                 if isinstance(subset, list) and subset and keep == "first":
  818                      cols = ", ".join(_sql_quote(col) for col in subset if isinstance(col, str))

backend • modules/export/service.py:
  42  
  43:     if format_name == "polars":
  44          code, warnings = generate_polars_code(selection, datasources_by_id)
  45:     elif format_name == "sql":
  46          code, warnings = generate_sql_code(selection, datasources_by_id)

backend • modules/export/utils.py:
  11  def build_export_filename(analysis_name: str, tab_name: str | None, format_name: str) -> str:
  12:     extension = "py" if format_name == "polars" else "sql"
  13      analysis_slug = export_slug(analysis_name, fallback="analysis")

backend • modules/mcp/executor.py:
  73              )
  74:         elif method == "DELETE":
  75              resp = await client.request(method, url, params=query_params, headers=headers)

backend • modules/mcp/registry.py:
  159          properties[name] = schema
  160:         is_required = bool(param.get("required", p_in == "path"))
  161          if is_required and name not in required:

  168          }
  169:         if p_in == "path":
  170              path_params.append(item)
  171:         if p_in == "query":
  172              query_params.append(item)

backend • modules/mcp/tool_output.py:
  10          return []
  11:     if schema.get("type") == "object":
  12          props = schema.get("properties")

  15          return [key for key in props if isinstance(key, str)]
  16:     if schema.get("type") == "array":
  17          items = schema.get("items")

backend • modules/mcp/validation.py:
  120          return f"{message}. Check input against schema."
  121:     if key == "required":
  122          return f"{message}. Provide all required fields."
  123:     if key == "additionalProperties":
  124          return f"{message}. Remove unknown fields or use documented parameter names."
  125:     if key == "enum":
  126          return f"{message}. Use one of the documented enum values."
  127:     if key == "type":
  128          return f"{message}. Use the documented JSON type for this field."

  140          if name in result:
  141:             if isinstance(result[name], dict) and prop.get("type") == "object":
  142                  result[name] = apply_defaults(prop, result[name])

  149              continue
  150:         if prop.get("type") == "object":
  151              result[name] = apply_defaults(prop, {})

backend • modules/telegram/bot.py:
  226          command = text.strip().lower()
  227:         if command == "/subscribe":
  228              self._handle_subscribe(chat_id, title)
  229:         elif command == "/unsubscribe":
  230              self._handle_unsubscribe(chat_id)
  231:         elif command == "/start":
  232              self._send_message(chat_id, "Welcome! Use /subscribe to receive build notifications.")

scheduler • main.py:
  174  async def handle_runtime_payload(payload: dict[str, object]) -> None:
  175:     if payload.get("kind") == "job":
  176          build_job_hub.publish()

  210  
  211: if __name__ == "__main__":
  212      asyncio.run(main())

scheduler • scheduler_service.py:
  680      dialect = session.get_bind().dialect.name
  681:     stmt = base.with_for_update(skip_locked=True) if dialect == "postgresql" else base
  682      schedules = list(session.execute(stmt).scalars().all())

worker-manager • main.py:
  335  
  336: if __name__ == "__main__":
  337      asyncio.run(main())

worker-manager • builds/build_execution.py:
  146      engine_run_kind = EngineRunKind.parse(build.current_kind)
  147:     is_schedule_build = engine_run_kind == EngineRunKind.BUILD and starter.triggered_by == "schedule"
  148      if current_kind == DataSourceTargetKind.RAW.value or is_schedule_build:

worker-manager • datasources/datasource_loading.py:
  137              raise ValueError("Datasource file loading requires file_path and file_type")
  138:         if file_type == "excel" and _has_bounds(config):
  139              return _read_excel_bounds(config)

  143          opts = _merge_excel_opts(config, opts)
  144:         if file_type == "csv":
  145              return pl.scan_csv(file_path, **_csv_opts(opts))
  146:         if file_type == "parquet":
  147              return pl.scan_parquet(file_path)
  148:         if file_type == "json":
  149              return pl.read_json(file_path).lazy()
  150:         if file_type == "ndjson":
  151              return pl.scan_ndjson(file_path)
  152:         if file_type == "excel":
  153              return _read_excel(file_path, opts)

worker-manager • datasources/datasource_schemas.py:
  215              return None
  216:         if value.strip() == "":
  217              return None

worker-manager • datasources/datasource_service.py:
   59      arrow_table = lazy.collect().to_arrow()
   60:     if build_mode == "recreate" and catalog.table_exists(identifier):
   61          catalog.drop_table(identifier)

   63          table = catalog.load_table(identifier)
   64:         if build_mode == "incremental":
   65              table.append(arrow_table)

  259          raise ValueError(f"Path must be a file for type: {file_type}")
  260:     if file_type == "parquet" and not (resolved_path.is_file() or resolved_path.is_dir()):
  261          raise ValueError("Parquet path must be a file or directory")

worker-manager • operations/datasource.py:
  289          analysis_id = str(analysis_id) if analysis_id is not None else None
  290:         if analysis_id and merged.get("source_type") == "analysis" and str(merged.get("analysis_id")) == analysis_id:
  291              merged = {**merged, "analysis_pipeline": pipeline}

  396                  next_config = _resolve_pipeline_datasource(pipeline, raw)
  397:                 if next_config.get("source_type") == "analysis":
  398                      next_config = {**next_config, "analysis_pipeline": pipeline}

worker-manager • operations/fill_null.py:
  38  
  39:         if validated.strategy == "literal":
  40              value = cast_value(validated.value, validated.value_type)

  57  
  58:         if validated.strategy == "drop_rows":
  59              if columns:

worker-manager • operations/filter.py:
  200  
  201:         if validated.logic == "AND":
  202              return lf.filter(pl.all_horizontal(exprs))
  203:         if validated.logic == "OR":
  204              return lf.filter(pl.any_horizontal(exprs))

  229  
  230:         if is_date_only and is_datetime_col and cond.value_type == "datetime":
  231              return get_operator(cond.operator)(pl.col(cond.column).dt.date(), FilterValueType.DATE.coerce(cond.value))

  234          op = get_operator(cond.operator)
  235:         if cond.operator == "regex" and coerced == "":
  236              return pl.lit(False)
  237:         if cond.operator == "regex" and isinstance(coerced, str):
  238              validate_regex_pattern(coerced)

  245                  return op(left, coerced)
  246:             if cond.operator == "not_contains":
  247                  combined = op(left, coerced[0])

worker-manager • operations/plot.py:
  376              return df
  377:     if order is None and value_col == "y":
  378          order_source = df

worker-manager • operations/step_converter.py:
  97  def step_display_name(step_type: str, config: Mapping[str, object]) -> str:
  98:     if step_type == "chart":
  99          chart_type = config.get("chart_type")

worker-manager • runtime/compute_engine.py:
   66              return "value_error", {}
   67:         if isinstance(exc, pl.exceptions.ComputeError) and str(exc) == "at least one key is required in a group_by operation":
   68              return "value_error", {}

  326              status, payload = self._wait_for_queue_message(self.result_queue, timeout=remaining)
  327:             if status == "timeout":
  328                  return None
  329:             if status == "process_exit":
  330                  exit_code = self.process.exitcode if self.process else None

  397              status, payload = self._wait_for_queue_message(self.result_queue, timeout=remaining)
  398:             if status == "timeout":
  399                  return False
  400:             if status == "process_exit":
  401                  return self.process is not None and self.process.exitcode == 0

  501                      if isinstance(command, dict):
  502:                         if command.get("type") == "shutdown":
  503                              result_queue.put(ShutdownAck())

worker-manager • runtime/compute_service.py:
   351  
   352:     if error_kind == "pipeline_validation":
   353          validation_details = error_details.get("details")

   358  
   359:     if error_kind == "value_error":
   360          raise PipelineValidationError(

   368  
   369:     if error_kind == "datasource_metadata_missing":
   370          snapshot_details: dict[str, object] = {

   489          return scanner(output_path)
   490:     if export_format == "json":
   491          return pl.read_json(output_path).lazy()

   505          body_template = output_notification.get("body_template", "")
   506:         if recipient and method == "email":
   507              subject = render_template(subject_template, context)

   531              excluded: set[str] = set()
   532:             if output_notification and output_notification.get("method") == "telegram":
   533                  raw_targets = run_db(list_active_subscriber_targets)

   775      category = entry.get("category")
   776:     if category == "read":
   777          return "read"
   778:     if category == "write":
   779          return "write"

  1152                  continue
  1153:             if analysis_id and config_override.get("source_type") == "analysis":
  1154                  config_override = {

  1359      analysis_id = str(analysis_id) if analysis_id is not None else None
  1360:     if analysis_id and merged.get("source_type") == "analysis" and str(merged.get("analysis_id")) == analysis_id:
  1361          merged = {**merged, "analysis_pipeline": pipeline}

  1421  
  1422:     if target_step_id == "source":
  1423          preview_steps = []

  1598  
  1599:     if target_step_id == "source":
  1600          schema_steps = []

  1676  
  1677:     if target_step_id == "source":
  1678          count_steps = []

  1858  
  1859:     if target_step_id == "source":
  1860          export_steps = []

  2032          arrow_table = pl.read_parquet(tmp_output).to_arrow()
  2033:         if build_mode == "recreate" and catalog.table_exists(identifier):
  2034              catalog.drop_table(identifier)

  2037              iceberg_table = catalog.load_table(identifier)
  2038:             if build_mode == "incremental":
  2039                  iceberg_table.append(arrow_table)

  2079              is_hidden=output_hidden,
  2080:             keep_schema_cache=build_mode == "incremental",
  2081          )

  2292      target_step = next((step for step in steps if step.get("id") == target_step_id), None)
  2293:     if target_step and target_step.get("type") == "download":
  2294          depends_on = target_step.get("depends_on") or []

  2304  
  2305:     if target_step_id == "source":
  2306          download_steps = []

  2657  
  2658:         if emitted_type == "step_complete":
  2659              completed_steps += 1

  2678              )
  2679:         if emitted_type == "compute_start":
  2680              elapsed_ms = int((time.perf_counter() - started_perf) * 1000)

  2696              )
  2697:         if emitted_type == "step_failed":
  2698              elapsed_ms = int((time.perf_counter() - started_perf) * 1000)

  3168                  async def emit_stage_updates() -> None:
  3169:                     if stage == "write_start":
  3170                          if not current_read_stage.completed:

  3242  
  3243:                     if stage == "write_complete":
  3244                          write_duration_ms = info.get("write_duration_ms")

worker-manager • runtime/compute_utils.py:
   9  def find_step_index(steps: list[dict], target_step_id: str) -> int:
  10:     if target_step_id == "source":
  11          return -1

  68  def resolve_applied_target(steps: list[dict], target_step_id: str) -> str:
  69:     if target_step_id == "source":
  70          return "source"

worker-manager • runtime/runtime_notifications.py:
   8      kind = payload.get("kind")
   9:     if kind == "job":
  10          build_job_hub.publish()
  11          return
  12:     if kind == "compute_request":
  13          request_hub.publish()

worker-manager • runtime/worker_runtime.py:
  89      async def handle_runtime_payload(payload: dict[str, object]) -> None:
  90:         if payload.get("kind") == "job":
  91              wake_event.set()
