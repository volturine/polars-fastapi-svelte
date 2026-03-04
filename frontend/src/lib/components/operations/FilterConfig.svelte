<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import { X, Plus } from 'lucide-svelte';
	import ColumnDropdown from '$lib/components/common/ColumnDropdown.svelte';
	import DateTimeInput from '$lib/components/common/DateTimeInput.svelte';
	import { css } from '$lib/styles/panda';

	const uid = $props.id();

	type ValueType = 'string' | 'number' | 'date' | 'datetime' | 'column' | 'boolean';

	interface Condition {
		column: string;
		operator: string;
		value: string | number | boolean | string[] | null;
		value_type: ValueType;
		compare_column?: string;
	}

	interface FilterConfigData {
		conditions: Condition[];
		logic: 'AND' | 'OR';
	}

	interface Props {
		schema: Schema;
		config?: FilterConfigData;
	}

	const defaultCondition: Condition = {
		column: '',
		operator: '=',
		value: '',
		value_type: 'string'
	};

	let { schema, config = $bindable({ conditions: [defaultCondition], logic: 'AND' }) }: Props =
		$props();

	const conditions = $derived(config.conditions ?? [defaultCondition]);

	const COMPARISON_OPS = ['=', '!=', '>', '<', '>=', '<='];
	const LIST_OPS = ['in', 'not_in'];
	const STRING_OPS = ['contains', 'not_contains', 'starts_with', 'ends_with', 'regex'];
	const NULL_OPS = ['is_null', 'is_not_null'];

	const OPERATOR_LABELS: Record<string, string> = {
		'=': '=',
		'!=': '!=',
		'>': '>',
		'<': '<',
		'>=': '>=',
		'<=': '<=',
		contains: 'contains',
		not_contains: 'not contains',
		starts_with: 'starts with',
		ends_with: 'ends with',
		regex: 'regex',
		in: 'in',
		not_in: 'not in',
		is_null: 'is null',
		is_not_null: 'is not null'
	};

	function getColumnType(name: string): 'string' | 'number' | 'datetime' | 'date' | 'boolean' {
		const col = schema.columns.find((c) => c.name === name);
		if (!col) return 'string';
		const dtype = col.dtype.toLowerCase();
		if (dtype.includes('int') || dtype.includes('float') || dtype.includes('decimal'))
			return 'number';
		if (dtype.includes('datetime')) return 'datetime';
		if (dtype.includes('date')) return 'date';
		if (dtype.includes('bool')) return 'boolean';
		return 'string';
	}

	function getOperatorsForType(type: string, isColumnMode: boolean): string[] {
		if (isColumnMode) return COMPARISON_OPS;
		if (type === 'string') return [...COMPARISON_OPS, ...LIST_OPS, ...STRING_OPS, ...NULL_OPS];
		return [...COMPARISON_OPS, ...NULL_OPS];
	}

	function isNullOperator(op: string): boolean {
		return NULL_OPS.includes(op);
	}

	function addCondition() {
		config.conditions = [
			...conditions,
			{ column: '', operator: '=', value: '', value_type: 'string' as ValueType }
		];
	}

	function updateCondition(idx: number, updates: Partial<Condition>, coerce = true) {
		const next = { ...conditions[idx], ...updates } as Condition;
		if (coerce && next.value_type === 'number' && typeof next.value === 'string') {
			const trimmed = next.value.trim();
			if (trimmed === '') {
				next.value = '';
			} else {
				next.value = Number(trimmed);
			}
		}
		config.conditions = conditions.map((c, i) => (i === idx ? next : c));
	}

	function isMultiLiteralOperator(op: string): boolean {
		return op !== 'regex' && op !== 'is_null' && op !== 'is_not_null';
	}

	function getLiteralList(value: string | number | boolean | string[] | null): string[] {
		if (Array.isArray(value)) return value;
		if (value === null || value === undefined) return [];
		if (value === '') return [];
		return [String(value)];
	}

	function setLiteralList(idx: number, values: string[]) {
		const next = values.length === 0 ? '' : values;
		updateCondition(idx, { value: next });
	}

	function appendLiteralToken(idx: number, token: string) {
		const trimmed = token.trim();
		if (!trimmed) return;
		const next = [...getLiteralList(conditions[idx].value), trimmed];
		setLiteralList(idx, next);
	}

	function removeLiteralToken(idx: number, tokenIndex: number) {
		const next = getLiteralList(conditions[idx].value).filter((_, i) => i !== tokenIndex);
		setLiteralList(idx, next);
	}

	function removeCondition(idx: number) {
		config.conditions = conditions.filter((_, i) => i !== idx);
	}

	function handleColumnChange(idx: number, col: string) {
		const type = getColumnType(col);
		const cond = conditions[idx];
		const isColumn = cond.value_type === 'column';
		const ops = getOperatorsForType(type, isColumn);
		const op = ops.includes(cond.operator) ? cond.operator : '=';
		updateCondition(idx, {
			column: col,
			operator: op,
			value_type: isColumn ? 'column' : type,
			value: isColumn ? cond.value : ''
		});
	}

	function handleModeChange(idx: number, mode: 'value' | 'column') {
		const cond = conditions[idx];
		const colType = getColumnType(cond.column);
		const isColumn = mode === 'column';
		const ops = getOperatorsForType(colType, isColumn);
		const op = ops.includes(cond.operator) ? cond.operator : '=';

		if (isColumn) {
			updateCondition(idx, { value_type: 'column', compare_column: '', operator: op, value: '' });
		} else {
			updateCondition(idx, {
				value_type: colType,
				compare_column: undefined,
				operator: op,
				value: ''
			});
		}
	}

	function handleOperatorChange(idx: number, op: string) {
		const updates: Partial<Condition> = { operator: op };
		if (isNullOperator(op)) {
			updates.value = '';
			updates.compare_column = undefined;
		}
		if (op === 'regex' && Array.isArray(conditions[idx].value)) {
			updates.value = '';
		}
		updateCondition(idx, updates);
	}

	function formatDatetimeForInput(val: string | number | boolean | string[] | null): string {
		if (!val) return '';
		if (Array.isArray(val)) return '';
		const str = String(val);
		// If already in datetime-local format (YYYY-MM-DDTHH:MM), return as-is
		if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(str)) return str.slice(0, 16);
		// If ISO format with Z or offset, parse and format without TZ conversion
		const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(str);
		if (match) return `${match[1]}T${match[2]}`;
		// If date-only format (YYYY-MM-DD), return as-is (no time component)
		if (/^\d{4}-\d{2}-\d{2}$/.test(str)) return str;
		return '';
	}

	function formatDateForInput(val: string | number | boolean | string[] | null): string {
		if (!val) return '';
		if (Array.isArray(val)) return '';
		const str = String(val);
		// If already in date format (YYYY-MM-DD), return as-is
		if (/^\d{4}-\d{2}-\d{2}$/.test(str)) return str;
		// Extract date part from ISO string
		const match = /^(\d{4}-\d{2}-\d{2})/.exec(str);
		if (match) return match[1];
		return '';
	}
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Filter configuration"
>
	<div role="group" aria-labelledby="{uid}-conditions-heading">
		<div
			class={css({
				marginBottom: '5',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'space-between'
			})}
		>
			<h4
				id="{uid}-conditions-heading"
				class={css({
					marginTop: '0',
					marginBottom: '0',
					fontSize: '0.6875rem',
					fontWeight: '600',
					color: 'fg.muted',
					textTransform: 'uppercase',
					letterSpacing: '0.08em'
				})}
			>
				Conditions
			</h4>
			<div class={css({ display: 'flex', alignItems: 'center', gap: '2' })}>
				<div class={css({ display: 'flex' })} role="radiogroup" aria-label="Condition logic">
					<button
						type="button"
						class={config.logic === 'AND'
							? css({
									display: 'flex',
									cursor: 'pointer',
									alignItems: 'center',
									justifyContent: 'center',
									borderWidth: '1px',
									borderStyle: 'solid',
									borderColor: 'border.primary',
									borderRadius: 'sm 0 0 sm',
									backgroundColor: 'accent.bg',
									color: 'accent.primary',
									paddingX: '2',
									paddingY: '1',
									fontSize: 'xs',
									boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
									position: 'relative',
									zIndex: '1'
								})
							: css({
									display: 'flex',
									cursor: 'pointer',
									alignItems: 'center',
									justifyContent: 'center',
									borderWidth: '1px',
									borderStyle: 'solid',
									borderColor: 'border.tertiary',
									borderRadius: 'sm 0 0 sm',
									backgroundColor: 'transparent',
									paddingX: '2',
									paddingY: '1',
									fontSize: 'xs',
									color: 'fg.muted',
									_hover: { backgroundColor: 'bg.hover', color: 'fg.secondary' }
								})}
						onclick={() => (config.logic = 'AND')}
						aria-pressed={config.logic === 'AND'}
					>
						AND
					</button>
					<button
						type="button"
						class={config.logic === 'OR'
							? css({
									display: 'flex',
									cursor: 'pointer',
									alignItems: 'center',
									justifyContent: 'center',
									borderWidth: '1px',
									borderStyle: 'solid',
									borderColor: 'border.primary',
									borderRadius: '0 sm sm 0',
									backgroundColor: 'accent.bg',
									color: 'accent.primary',
									paddingX: '2',
									paddingY: '1',
									fontSize: 'xs',
									boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
									position: 'relative',
									zIndex: '1'
								})
							: css({
									display: 'flex',
									cursor: 'pointer',
									alignItems: 'center',
									justifyContent: 'center',
									borderWidth: '1px',
									borderStyle: 'solid',
									borderColor: 'border.tertiary',
									borderRadius: '0 sm sm 0',
									backgroundColor: 'transparent',
									paddingX: '2',
									paddingY: '1',
									fontSize: 'xs',
									color: 'fg.muted',
									_hover: { backgroundColor: 'bg.hover', color: 'fg.secondary' }
								})}
						onclick={() => (config.logic = 'OR')}
						aria-pressed={config.logic === 'OR'}
					>
						OR
					</button>
				</div>
				<button
					type="button"
					class={css({
						display: 'flex',
						height: '7',
						width: '7',
						cursor: 'pointer',
						alignItems: 'center',
						justifyContent: 'center',
						borderWidth: '1px',
						borderStyle: 'solid',
						borderColor: 'border.tertiary',
						backgroundColor: 'bg.tertiary',
						padding: '0',
						color: 'fg.secondary',
						_hover: { backgroundColor: 'bg.hover', color: 'fg.primary' }
					})}
					onclick={addCondition}
					aria-label="Add filter condition"
				>
					<Plus size={16} aria-hidden="true" />
				</button>
			</div>
		</div>

		{#if conditions.length === 0}
			<p
				class={css({
					color: 'fg.muted',
					fontStyle: 'italic',
					textAlign: 'center',
					padding: '4',
					margin: '0'
				})}
				role="status"
			>
				No conditions configured. Click "+ Add" to create one.
			</p>
		{:else}
			<div
				class={css({ display: 'flex', flexDirection: 'column', gap: '4' })}
				role="list"
				aria-label="Filter conditions"
				aria-live="polite"
			>
				{#each conditions as cond, i (i)}
					{@const colType = getColumnType(cond.column)}
					{@const isColumn = cond.value_type === 'column'}
					{@const isNull = isNullOperator(cond.operator)}
					{@const multiLiteral =
						!isColumn && !isNull && colType === 'string' && isMultiLiteralOperator(cond.operator)}
					{@const ops = getOperatorsForType(colType, isColumn)}

					<div
						class={css({
							borderLeftWidth: '2px',
							borderLeftStyle: 'solid',
							borderLeftColor: 'border.tertiary',
							paddingLeft: '4',
							paddingBottom: '2'
						})}
						role="listitem"
					>
						<div
							class={css({
								marginBottom: '3',
								display: 'flex',
								alignItems: 'center',
								gap: '2',
								paddingBottom: '2'
							})}
						>
							<span class={css({ fontSize: 'xs', fontWeight: 'semibold', color: 'fg.muted' })}
								>#{i + 1}</span
							>
							{#if cond.column}
								<span class={css({ fontSize: 'sm', fontWeight: 'medium', color: 'fg.primary' })}
									>{cond.column}</span
								>
							{/if}
							<button
								type="button"
								class={css({
									marginLeft: 'auto',
									display: 'flex',
									height: '6',
									width: '6',
									cursor: 'pointer',
									alignItems: 'center',
									justifyContent: 'center',
									borderWidth: '1px',
									borderStyle: 'solid',
									borderColor: 'border.transparent',
									backgroundColor: 'transparent',
									padding: '0',
									color: 'fg.muted',
									_hover: {
										borderColor: 'error.border',
										backgroundColor: 'error.bg',
										color: 'error.fg'
									},
									_disabled: { cursor: 'not-allowed', opacity: '0.3' }
								})}
								onclick={() => removeCondition(i)}
								disabled={conditions.length === 1}
								aria-label={`Remove condition ${i + 1}`}
							>
								<X size={14} aria-hidden="true" />
							</button>
						</div>

						<div
							class={css({
								position: 'relative',
								display: 'flex',
								flexWrap: 'wrap',
								alignItems: 'start',
								gap: '4'
							})}
						>
							<div
								class={css({
									display: 'flex',
									flex: '2',
									flexDirection: 'column',
									gap: '1',
									minWidth: '55'
								})}
							>
								<span
									class={css({
										marginBottom: '0',
										fontSize: 'xs',
										fontWeight: 'normal',
										color: 'fg.muted'
									})}>Column</span
								>
								<ColumnDropdown
									{schema}
									value={cond.column}
									onChange={(val) => handleColumnChange(i, val)}
									placeholder="Select..."
									containerClass={css({ position: 'static' })}
									triggerClass={css({ width: '100%' })}
									menuClass={css({ top: 'inherit', marginTop: '48px' })}
								/>
							</div>

							<div
								class={css({
									display: 'flex',
									flex: '1',
									flexDirection: 'column',
									gap: '1',
									minWidth: '37.5'
								})}
							>
								<label
									class={css({
										fontSize: 'xs',
										fontWeight: 'normal',
										marginBottom: '0',
										color: 'fg.muted'
									})}
									for="{uid}-operator-{i}">Operator</label
								>
								<select
									id="{uid}-operator-{i}"
									data-testid={`filter-operator-select-${i}`}
									value={cond.operator}
									onchange={(e) => handleOperatorChange(i, e.currentTarget.value)}
								>
									{#each ops as op (op)}
										<option value={op}>{OPERATOR_LABELS[op]}</option>
									{/each}
								</select>
							</div>

							{#if !isNull}
								<div
									class={css({
										display: 'flex',
										flex: '2',
										flexDirection: 'column',
										gap: '1',
										minWidth: '60'
									})}
								>
									<div
										class={css({
											display: 'flex',
											alignItems: 'center',
											justifyContent: 'space-between',
											gap: '2'
										})}
									>
										<span class={css({ fontSize: 'xs', fontWeight: 'normal', color: 'fg.muted' })}
											>Compare to</span
										>
										<div class={css({ display: 'flex' })} role="radiogroup" aria-label="Value mode">
											<button
												type="button"
												class={!isColumn
													? css({
															display: 'flex',
															alignItems: 'center',
															justifyContent: 'center',
															paddingX: '2',
															paddingY: '1',
															fontSize: 'xs',
															cursor: 'pointer',
															borderWidth: '1px',
															borderStyle: 'solid',
															borderColor: 'border.primary',
															borderRadius: 'sm 0 0 sm',
															backgroundColor: 'accent.bg',
															color: 'accent.primary',
															boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
															position: 'relative',
															zIndex: '1'
														})
													: css({
															display: 'flex',
															alignItems: 'center',
															justifyContent: 'center',
															paddingX: '2',
															paddingY: '1',
															fontSize: 'xs',
															cursor: 'pointer',
															borderWidth: '1px',
															borderStyle: 'solid',
															borderColor: 'border.tertiary',
															borderRadius: 'sm 0 0 sm',
															backgroundColor: 'transparent',
															color: 'fg.muted',
															_hover: { backgroundColor: 'bg.hover', color: 'fg.secondary' }
														})}
												onclick={() => handleModeChange(i, 'value')}
												aria-pressed={!isColumn}
											>
												Value
											</button>
											<button
												type="button"
												class={isColumn
													? css({
															display: 'flex',
															alignItems: 'center',
															justifyContent: 'center',
															paddingX: '2',
															paddingY: '1',
															fontSize: 'xs',
															cursor: 'pointer',
															borderWidth: '1px',
															borderStyle: 'solid',
															borderColor: 'border.primary',
															borderRadius: '0 sm sm 0',
															backgroundColor: 'accent.bg',
															color: 'accent.primary',
															boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
															position: 'relative',
															zIndex: '1'
														})
													: css({
															display: 'flex',
															alignItems: 'center',
															justifyContent: 'center',
															paddingX: '2',
															paddingY: '1',
															fontSize: 'xs',
															cursor: 'pointer',
															borderWidth: '1px',
															borderStyle: 'solid',
															borderColor: 'border.tertiary',
															borderRadius: '0 sm sm 0',
															backgroundColor: 'transparent',
															color: 'fg.muted',
															_hover: { backgroundColor: 'bg.hover', color: 'fg.secondary' }
														})}
												onclick={() => handleModeChange(i, 'column')}
												aria-pressed={isColumn}
											>
												Column
											</button>
										</div>
									</div>

									{#if isColumn}
										<ColumnDropdown
											{schema}
											value={cond.compare_column ?? ''}
											onChange={(val) => updateCondition(i, { compare_column: val })}
											placeholder="Select..."
											containerClass={css({ position: 'static' })}
											triggerClass={css({ width: '100%' })}
											menuClass={css({ top: 'inherit', marginTop: '48px' })}
										/>
									{:else if colType === 'number'}
										<input
											id="{uid}-value-{i}"
											data-testid={`filter-value-input-${i}`}
											type="number"
											step="any"
											value={typeof cond.value === 'number'
												? String(cond.value)
												: (cond.value ?? '')}
											oninput={(e) => updateCondition(i, { value: e.currentTarget.value }, false)}
											onblur={(e) => updateCondition(i, { value: e.currentTarget.value })}
											placeholder="0"
										/>
									{:else if colType === 'datetime'}
										<DateTimeInput
											id="{uid}-value-{i}"
											value={formatDatetimeForInput(cond.value)}
											onChange={(val) => updateCondition(i, { value: val })}
										/>
									{:else if colType === 'date'}
										<input
											id="{uid}-value-{i}"
											data-testid={`filter-value-input-${i}`}
											type="date"
											value={formatDateForInput(cond.value)}
											onchange={(e) => updateCondition(i, { value: e.currentTarget.value })}
										/>
									{:else if colType === 'boolean'}
										<select
											id="{uid}-value-{i}"
											data-testid={`filter-value-input-${i}`}
											value={String(cond.value ?? 'true')}
											onchange={(e) =>
												updateCondition(i, { value: e.currentTarget.value === 'true' })}
										>
											<option value="true">true</option>
											<option value="false">false</option>
										</select>
									{:else if multiLiteral}
										{@const tokens = getLiteralList(cond.value)}
										<div class={css({ display: 'flex', flexDirection: 'column', gap: '2' })}>
											<input
												id="{uid}-value-{i}"
												data-testid={`filter-value-input-${i}`}
												type="text"
												value=""
												onkeydown={(e) => {
													if (e.key !== 'Enter') return;
													e.preventDefault();
													const target = e.currentTarget as HTMLInputElement;
													appendLiteralToken(i, target.value);
													target.value = '';
												}}
												placeholder="Type value and press Enter"
											/>
											{#if tokens.length > 0}
												<div
													class={css({ display: 'flex', flexWrap: 'wrap', gap: '2' })}
													role="list"
													aria-label="Filter values"
												>
													{#each tokens as token, tokenIndex (tokenIndex)}
														<span
															class={css({
																display: 'inline-flex',
																alignItems: 'center',
																gap: '1',
																borderWidth: '1px',
																borderStyle: 'solid',
																borderColor: 'border.tertiary',
																backgroundColor: 'bg.tertiary',
																color: 'fg.primary',
																fontSize: '0.75rem',
																paddingY: '1',
																paddingX: '2'
															})}
															role="listitem"
														>
															<span
																class={css({
																	maxWidth: '55',
																	overflow: 'hidden',
																	textOverflow: 'ellipsis',
																	whiteSpace: 'nowrap'
																})}>{token}</span
															>
															<button
																class={css({
																	display: 'inline-flex',
																	alignItems: 'center',
																	justifyContent: 'center',
																	padding: '0',
																	border: 'none',
																	background: 'transparent',
																	color: 'fg.muted',
																	cursor: 'pointer',
																	_hover: { backgroundColor: 'bg.hover', color: 'fg.primary' }
																})}
																onclick={() => removeLiteralToken(i, tokenIndex)}
																aria-label={`Remove ${token}`}
																type="button"
															>
																<X size={12} />
															</button>
														</span>
													{/each}
												</div>
											{/if}
										</div>
									{:else}
										<input
											id="{uid}-value-{i}"
											data-testid={`filter-value-input-${i}`}
											type="text"
											value={cond.value ?? ''}
											oninput={(e) => updateCondition(i, { value: e.currentTarget.value })}
											placeholder={cond.operator === 'regex' ? 'pattern' : 'value'}
										/>
									{/if}
								</div>
							{:else}
								<div
									class={css({
										display: 'flex',
										flex: '2',
										flexDirection: 'column',
										gap: '1',
										minWidth: '60'
									})}
								>
									<span class={css({ fontSize: 'xs', fontWeight: 'normal', color: 'fg.muted' })}
										>Value</span
									>
									<div
										class={css({
											display: 'flex',
											alignItems: 'center',
											height: '9',
											paddingX: '3',
											fontSize: 'xs',
											fontStyle: 'italic',
											color: 'fg.muted'
										})}
									>
										<span>No value needed</span>
									</div>
								</div>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
