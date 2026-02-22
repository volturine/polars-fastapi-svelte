<script lang="ts">
	import * as d3 from 'd3';

	type ChartType = 'bar' | 'line' | 'pie' | 'histogram' | 'scatter' | 'boxplot';
	type Row = Record<string, unknown>;

	interface Props {
		data: Row[];
		chartType: ChartType;
		config: Record<string, unknown>;
	}

	const { data, chartType, config }: Props = $props();

	/* ── Enterprise color palette (Contour-inspired) ── */
	const PALETTE = [
		'#4A8FE7',
		'#50B88E',
		'#E8A838',
		'#E0687A',
		'#7F72B5',
		'#3AB4A0',
		'#EC8B56',
		'#9B8EC4'
	];

	const HOVER_DIM = 0.25;

	/* ── Refs ── */
	let chartEl: HTMLDivElement | undefined = $state();
	let wrapperEl: HTMLDivElement | undefined = $state();

	/* ── Tooltip state (reactive, avoids direct DOM manipulation) ── */
	let tipTitle = $state('');
	let tipLines: Array<{ label: string; value: string }> = $state([]);
	let tipX = $state(0);
	let tipY = $state(0);
	let tipVisible = $state(false);

	/* ── Primitive helpers ── */
	function num(v: unknown): number {
		if (typeof v === 'number') return v;
		if (typeof v === 'string') return Number(v) || 0;
		return 0;
	}

	function str(v: unknown): string {
		if (v == null) return '';
		return String(v);
	}

	/* Abbreviated format for axis ticks */
	function fmtAxis(v: number): string {
		if (Math.abs(v) >= 1e9) return d3.format('.1s')(v);
		if (Math.abs(v) >= 1e6) return d3.format('.2s')(v);
		if (Math.abs(v) >= 1e3) return d3.format(',.0f')(v);
		if (Number.isInteger(v)) return String(v);
		return d3.format('.2f')(v);
	}

	/* Full format for tooltips and value labels */
	function fmtFull(v: number): string {
		if (Number.isInteger(v)) return d3.format(',')(v);
		return d3.format(',.2f')(v);
	}

	/* Derive axis titles from config */
	function getXTitle(): string {
		return str(config.x_column) || 'Category';
	}

	function getYTitle(): string {
		const agg = str(config.aggregation);
		const col = str(config.y_column);
		if (chartType === 'histogram') return 'Count';
		if (chartType === 'scatter' || chartType === 'boxplot') return col || 'Value';
		if (!col) return 'Count';
		return `${agg.charAt(0).toUpperCase() + agg.slice(1)} of ${col}`;
	}

	/* ── Tooltip ── */
	function showTip(
		title: string,
		lines: Array<{ label: string; value: string }>,
		event: MouseEvent
	) {
		if (!wrapperEl) return;
		const rect = wrapperEl.getBoundingClientRect();
		let left = event.clientX - rect.left + 14;
		let top = event.clientY - rect.top - 14;
		if (left + 180 > rect.width) left = event.clientX - rect.left - 190;
		if (top < 4) top = event.clientY - rect.top + 14;
		tipTitle = title;
		tipLines = lines;
		tipX = left;
		tipY = top;
		tipVisible = true;
	}
	function hideTip() {
		tipVisible = false;
	}

	/* ── Shared D3 helpers ── */

	type Svg = d3.Selection<SVGGElement, unknown, null, undefined>;

	function addGrid(svg: Svg, y: d3.ScaleLinear<number, number>, w: number) {
		const grid = svg
			.append('g')
			.attr('class', 'grid')
			.call(
				d3
					.axisLeft(y)
					.ticks(5)
					.tickSize(-w)
					.tickFormat(() => '')
			);
		grid
			.selectAll('line')
			.attr('stroke', 'var(--border-primary)')
			.attr('stroke-opacity', 0.15)
			.attr('stroke-dasharray', '3,3');
		grid.select('.domain').remove();
	}

	function addTitles(svg: Svg, xLabel: string, yLabel: string, w: number, h: number) {
		svg
			.append('text')
			.attr('x', w / 2)
			.attr('y', h + 44)
			.attr('text-anchor', 'middle')
			.attr('fill', 'var(--fg-muted)')
			.style('font-size', '11px')
			.style('font-family', 'var(--font-mono)')
			.text(xLabel);
		svg
			.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('x', -h / 2)
			.attr('y', -48)
			.attr('text-anchor', 'middle')
			.attr('fill', 'var(--fg-muted)')
			.style('font-size', '11px')
			.style('font-family', 'var(--font-mono)')
			.text(yLabel);
	}

	function addLegend(svg: Svg, labels: string[], color: (l: string) => string, w: number) {
		const g = svg.append('g').attr('class', 'legend');
		let xOff = 0;
		for (const label of labels) {
			const item = g.append('g').attr('transform', `translate(${xOff}, 0)`);
			item
				.append('rect')
				.attr('width', 8)
				.attr('height', 8)
				.attr('y', -8)
				.attr('fill', color(label))
				.attr('rx', 1);
			const truncated = label.length > 14 ? label.slice(0, 14) + '…' : label;
			item
				.append('text')
				.attr('x', 12)
				.attr('fill', 'var(--fg-muted)')
				.style('font-size', '10px')
				.style('font-family', 'var(--font-mono)')
				.text(truncated);
			xOff += truncated.length * 6.2 + 24;
		}
		g.attr('transform', `translate(${w - xOff}, -8)`);
	}

	function styleChart(svg: Svg) {
		svg.selectAll('.domain').attr('stroke', 'var(--border-primary)');
		svg.selectAll('.tick line:not(.grid line)').attr('stroke', 'var(--border-primary)');
		svg
			.selectAll('.tick text')
			.attr('fill', 'var(--fg-tertiary)')
			.style('font-size', '10px')
			.style('font-family', 'var(--font-mono)');
	}

	function makeXAxis(
		svg: Svg,
		x: d3.ScaleBand<string> | d3.ScalePoint<string>,
		h: number,
		labels: string[]
	) {
		const maxLen = Math.max(...labels.map((l) => l.length));
		const shouldRotate = maxLen > 8 && labels.length > 4;
		const axis = svg
			.append('g')
			.attr('transform', `translate(0,${h})`)
			.call(d3.axisBottom(x).tickSizeOuter(0));
		if (shouldRotate) {
			axis
				.selectAll('text')
				.attr('transform', 'rotate(-35)')
				.attr('text-anchor', 'end')
				.attr('dx', '-0.5em')
				.attr('dy', '0.3em');
		}
	}

	function makeYAxis(svg: Svg, y: d3.ScaleLinear<number, number>) {
		svg.append('g').call(
			d3
				.axisLeft(y)
				.ticks(5)
				.tickFormat((d) => fmtAxis(d as number))
		);
	}

	/* ── Main render effect ── */

	// $derived is not sufficient: D3 requires imperative DOM access to render SVG
	$effect(() => {
		if (!chartEl || data.length === 0) return;

		let rafId = 0;

		function draw() {
			if (!chartEl) return;
			d3.select(chartEl).selectAll('svg').remove();
			const rect = chartEl.getBoundingClientRect();
			const w = rect.width || 400;
			const h = rect.height || 300;
			switch (chartType) {
				case 'bar':
					renderBar(chartEl, w, h);
					break;
				case 'line':
					renderLine(chartEl, w, h);
					break;
				case 'pie':
					renderPie(chartEl, w, h);
					break;
				case 'histogram':
					renderHistogram(chartEl, w, h);
					break;
				case 'scatter':
					renderScatter(chartEl, w, h);
					break;
				case 'boxplot':
					renderBoxplot(chartEl, w, h);
					break;
				default:
					renderBar(chartEl, w, h);
			}
		}

		// $derived cannot drive ResizeObserver — imperative resize tracking needed
		const observer = new ResizeObserver(() => {
			cancelAnimationFrame(rafId);
			rafId = requestAnimationFrame(draw);
		});

		observer.observe(chartEl);
		draw();

		return () => {
			observer.disconnect();
			cancelAnimationFrame(rafId);
			if (chartEl) d3.select(chartEl).selectAll('svg').remove();
		};
	});

	/* ═══════════════════════════════════════════════════
	   CHART RENDERERS
	   ═══════════════════════════════════════════════════ */

	function renderBar(el: HTMLDivElement, width: number, height: number) {
		const margin = { top: 28, right: 24, bottom: 56, left: 64 };
		const w = width - margin.left - margin.right;
		const h = height - margin.top - margin.bottom;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`) as Svg;

		const groupCol = config.group_column as string | null;
		const hasGroup = groupCol && data.length > 0 && groupCol in data[0];

		if (hasGroup) {
			const labels = [...new Set(data.map((r) => str(r.x)))];
			const groups = [...new Set(data.map((r) => str(r[groupCol])))];
			const color = d3.scaleOrdinal<string>().domain(groups).range(PALETTE);

			const x0 = d3.scaleBand().domain(labels).range([0, w]).padding(0.2);
			const x1 = d3.scaleBand().domain(groups).range([0, x0.bandwidth()]).padding(0.05);
			const y = d3
				.scaleLinear()
				.domain([0, d3.max(data, (r) => num(r.y)) ?? 0])
				.nice()
				.range([h, 0]);

			addGrid(svg, y, w);
			makeXAxis(svg, x0, h, labels);
			makeYAxis(svg, y);
			addTitles(svg, getXTitle(), getYTitle(), w, h);
			addLegend(svg, groups, (l) => color(l), w);

			for (const group of groups) {
				const rows = data.filter((r) => str(r[groupCol]) === group);
				svg
					.selectAll(`.bar-${CSS.escape(group)}`)
					.data(rows)
					.join('rect')
					.attr('class', 'chart-bar')
					.attr('x', (r) => (x0(str(r.x)) ?? 0) + (x1(group) ?? 0))
					.attr('y', (r) => y(num(r.y)))
					.attr('width', x1.bandwidth())
					.attr('height', (r) => h - y(num(r.y)))
					.attr('fill', color(group))
					.attr('rx', 2)
					.style('cursor', 'pointer')
					.on('mouseover', function (event: MouseEvent, r: Row) {
						svg.selectAll('.chart-bar').attr('opacity', HOVER_DIM);
						d3.select(this).attr('opacity', 1);
						showTip(str(r.x), [{ label: group, value: fmtFull(num(r.y)) }], event);
					})
					.on('mouseout', function () {
						svg.selectAll('.chart-bar').attr('opacity', 1);
						hideTip();
					});
			}

			/* Value labels for grouped (only when few groups) */
			if (groups.length <= 3) {
				for (const group of groups) {
					const rows = data.filter((r) => str(r[groupCol]) === group);
					svg
						.selectAll(`.vlabel-${CSS.escape(group)}`)
						.data(rows)
						.join('text')
						.attr('class', 'value-label')
						.attr('x', (r) => (x0(str(r.x)) ?? 0) + (x1(group) ?? 0) + x1.bandwidth() / 2)
						.attr('y', (r) => y(num(r.y)) - 5)
						.attr('text-anchor', 'middle')
						.attr('fill', 'var(--fg-tertiary)')
						.style('font-size', '9px')
						.style('font-family', 'var(--font-mono)')
						.style('pointer-events', 'none')
						.text((r) => fmtFull(num(r.y)));
				}
			}
		} else {
			const labels = data.map((r) => str(r.x));
			const x = d3.scaleBand().domain(labels).range([0, w]).padding(0.25);
			const y = d3
				.scaleLinear()
				.domain([0, d3.max(data, (r) => num(r.y)) ?? 0])
				.nice()
				.range([h, 0]);

			addGrid(svg, y, w);
			makeXAxis(svg, x, h, labels);
			makeYAxis(svg, y);
			addTitles(svg, getXTitle(), getYTitle(), w, h);

			svg
				.selectAll('.bar')
				.data(data)
				.join('rect')
				.attr('class', 'chart-bar')
				.attr('x', (r) => x(str(r.x)) ?? 0)
				.attr('y', (r) => y(num(r.y)))
				.attr('width', x.bandwidth())
				.attr('height', (r) => h - y(num(r.y)))
				.attr('fill', PALETTE[0])
				.attr('rx', 2)
				.style('cursor', 'pointer')
				.on('mouseover', function (event: MouseEvent, r: Row) {
					svg.selectAll('.chart-bar').attr('opacity', HOVER_DIM);
					d3.select(this).attr('opacity', 1);
					showTip(str(r.x), [{ label: getYTitle(), value: fmtFull(num(r.y)) }], event);
				})
				.on('mouseout', function () {
					svg.selectAll('.chart-bar').attr('opacity', 1);
					hideTip();
				});

			/* Value labels */
			svg
				.selectAll('.value-label')
				.data(data)
				.join('text')
				.attr('class', 'value-label')
				.attr('x', (r) => (x(str(r.x)) ?? 0) + x.bandwidth() / 2)
				.attr('y', (r) => y(num(r.y)) - 6)
				.attr('text-anchor', 'middle')
				.attr('fill', 'var(--fg-secondary)')
				.style('font-size', '10px')
				.style('font-family', 'var(--font-mono)')
				.style('pointer-events', 'none')
				.text((r) => fmtFull(num(r.y)));
		}

		styleChart(svg);
	}

	function renderLine(el: HTMLDivElement, width: number, height: number) {
		const margin = { top: 28, right: 24, bottom: 56, left: 64 };
		const w = width - margin.left - margin.right;
		const h = height - margin.top - margin.bottom;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`) as Svg;

		const groupCol = config.group_column as string | null;
		const hasGroup = groupCol && data.length > 0 && groupCol in data[0];
		const labels = [...new Set(data.map((r) => str(r.x)))];

		const x = d3.scalePoint().domain(labels).range([0, w]).padding(0.5);
		const y = d3
			.scaleLinear()
			.domain([0, d3.max(data, (r) => num(r.y)) ?? 0])
			.nice()
			.range([h, 0]);

		addGrid(svg, y, w);
		makeXAxis(svg, x, h, labels);
		makeYAxis(svg, y);
		addTitles(svg, getXTitle(), getYTitle(), w, h);

		if (hasGroup) {
			const groups = [...new Set(data.map((r) => str(r[groupCol])))];
			const color = d3.scaleOrdinal<string>().domain(groups).range(PALETTE);
			addLegend(svg, groups, (l) => color(l), w);

			for (const group of groups) {
				const rows = data
					.filter((r) => str(r[groupCol]) === group)
					.sort((a, b) => labels.indexOf(str(a.x)) - labels.indexOf(str(b.x)));

				const line = d3
					.line<Row>()
					.x((r) => x(str(r.x)) ?? 0)
					.y((r) => y(num(r.y)))
					.curve(d3.curveMonotoneX);

				const area = d3
					.area<Row>()
					.x((r) => x(str(r.x)) ?? 0)
					.y0(h)
					.y1((r) => y(num(r.y)))
					.curve(d3.curveMonotoneX);

				svg
					.append('path')
					.datum(rows)
					.attr('d', area)
					.attr('fill', color(group))
					.attr('opacity', 0.08);
				svg
					.append('path')
					.datum(rows)
					.attr('d', line)
					.attr('fill', 'none')
					.attr('stroke', color(group))
					.attr('stroke-width', 2);

				/* Dots with hover */
				svg
					.selectAll(`.dot-${CSS.escape(group)}`)
					.data(rows)
					.join('circle')
					.attr('class', 'chart-dot')
					.attr('cx', (r) => x(str(r.x)) ?? 0)
					.attr('cy', (r) => y(num(r.y)))
					.attr('r', 3.5)
					.attr('fill', color(group))
					.attr('stroke', 'var(--bg-primary)')
					.attr('stroke-width', 1.5)
					.style('cursor', 'pointer')
					.on('mouseover', function (event: MouseEvent, r: Row) {
						d3.select(this).attr('r', 6);
						showTip(str(r.x), [{ label: group, value: fmtFull(num(r.y)) }], event);
					})
					.on('mouseout', function () {
						d3.select(this).attr('r', 3.5);
						hideTip();
					});
			}
		} else {
			const sorted = [...data].sort((a, b) => labels.indexOf(str(a.x)) - labels.indexOf(str(b.x)));

			const line = d3
				.line<Row>()
				.x((r) => x(str(r.x)) ?? 0)
				.y((r) => y(num(r.y)))
				.curve(d3.curveMonotoneX);

			const area = d3
				.area<Row>()
				.x((r) => x(str(r.x)) ?? 0)
				.y0(h)
				.y1((r) => y(num(r.y)))
				.curve(d3.curveMonotoneX);

			svg
				.append('path')
				.datum(sorted)
				.attr('d', area)
				.attr('fill', PALETTE[0])
				.attr('opacity', 0.08);
			svg
				.append('path')
				.datum(sorted)
				.attr('d', line)
				.attr('fill', 'none')
				.attr('stroke', PALETTE[0])
				.attr('stroke-width', 2);

			svg
				.selectAll('.chart-dot')
				.data(sorted)
				.join('circle')
				.attr('class', 'chart-dot')
				.attr('cx', (r) => x(str(r.x)) ?? 0)
				.attr('cy', (r) => y(num(r.y)))
				.attr('r', 3.5)
				.attr('fill', PALETTE[0])
				.attr('stroke', 'var(--bg-primary)')
				.attr('stroke-width', 1.5)
				.style('cursor', 'pointer')
				.on('mouseover', function (event: MouseEvent, r: Row) {
					d3.select(this).attr('r', 6);
					showTip(str(r.x), [{ label: getYTitle(), value: fmtFull(num(r.y)) }], event);
				})
				.on('mouseout', function () {
					d3.select(this).attr('r', 3.5);
					hideTip();
				});
		}

		styleChart(svg);
	}

	function renderPie(el: HTMLDivElement, width: number, height: number) {
		const margin = 16;
		const radius = Math.min(width, height) / 2 - margin;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${width / 2},${height / 2})`) as Svg;

		const values = data.map((r) => num(r.y));
		const labels = data.map((r) => str(r.label));
		const color = d3.scaleOrdinal<number, string>().domain(d3.range(values.length)).range(PALETTE);
		const total = d3.sum(values);

		const pie = d3.pie<number>().sort(null);
		const arc = d3
			.arc<d3.PieArcDatum<number>>()
			.innerRadius(radius * 0.4)
			.outerRadius(radius);
		const hoverArc = d3
			.arc<d3.PieArcDatum<number>>()
			.innerRadius(radius * 0.4)
			.outerRadius(radius + 6);
		const labelArc = d3
			.arc<d3.PieArcDatum<number>>()
			.innerRadius(radius * 0.65)
			.outerRadius(radius * 0.65);

		const arcs = svg.selectAll('.arc').data(pie(values)).join('g').attr('class', 'arc');

		arcs
			.append('path')
			.attr('d', arc)
			.attr('fill', (_, i) => color(i))
			.attr('stroke', 'var(--bg-primary)')
			.attr('stroke-width', 2)
			.style('cursor', 'pointer')
			.on('mouseover', function (event: MouseEvent, d) {
				d3.select(this).transition().duration(120).attr('d', hoverArc(d));
				svg.selectAll('.arc path').attr('opacity', HOVER_DIM);
				d3.select(this).attr('opacity', 1);
				const i = d.index;
				const pct = ((values[i] / total) * 100).toFixed(1);
				showTip(labels[i], [{ label: '', value: `${fmtFull(values[i])} (${pct}%)` }], event);
			})
			.on('mouseout', function (_, d) {
				d3.select(this).transition().duration(120).attr('d', arc(d));
				svg.selectAll('.arc path').attr('opacity', 1);
				hideTip();
			});

		/* Labels for slices > 8% */
		arcs
			.filter((d) => (d.endAngle - d.startAngle) / (2 * Math.PI) > 0.08)
			.append('text')
			.attr('transform', (d) => `translate(${labelArc.centroid(d)})`)
			.attr('text-anchor', 'middle')
			.attr('dominant-baseline', 'central')
			.attr('fill', 'var(--fg-primary)')
			.style('font-size', '10px')
			.style('font-family', 'var(--font-mono)')
			.style('pointer-events', 'none')
			.text((_, i) => {
				const pct = ((values[i] / total) * 100).toFixed(0);
				const lbl = labels[i].length > 8 ? labels[i].slice(0, 8) + '…' : labels[i];
				return `${lbl} ${pct}%`;
			});
	}

	function renderHistogram(el: HTMLDivElement, width: number, height: number) {
		const margin = { top: 28, right: 24, bottom: 56, left: 64 };
		const w = width - margin.left - margin.right;
		const h = height - margin.top - margin.bottom;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`) as Svg;

		const xMin = d3.min(data, (r) => num(r.bin_start)) ?? 0;
		const xMax = d3.max(data, (r) => num(r.bin_end)) ?? 1;
		const x = d3.scaleLinear().domain([xMin, xMax]).range([0, w]);
		const y = d3
			.scaleLinear()
			.domain([0, d3.max(data, (r) => num(r.count)) ?? 0])
			.nice()
			.range([h, 0]);

		addGrid(svg, y, w);

		svg
			.append('g')
			.attr('transform', `translate(0,${h})`)
			.call(
				d3
					.axisBottom(x)
					.ticks(6)
					.tickFormat((d) => fmtAxis(d as number))
			);

		makeYAxis(svg, y);
		addTitles(svg, getXTitle(), 'Count', w, h);

		svg
			.selectAll('.bin')
			.data(data)
			.join('rect')
			.attr('class', 'chart-bar')
			.attr('x', (r) => x(num(r.bin_start)))
			.attr('y', (r) => y(num(r.count)))
			.attr('width', (r) => Math.max(0, x(num(r.bin_end)) - x(num(r.bin_start)) - 1))
			.attr('height', (r) => h - y(num(r.count)))
			.attr('fill', PALETTE[0])
			.attr('rx', 1)
			.style('cursor', 'pointer')
			.on('mouseover', function (event: MouseEvent, r: Row) {
				svg.selectAll('.chart-bar').attr('opacity', HOVER_DIM);
				d3.select(this).attr('opacity', 1);
				showTip(
					`${fmtFull(num(r.bin_start))} – ${fmtFull(num(r.bin_end))}`,
					[{ label: 'Count', value: fmtFull(num(r.count)) }],
					event
				);
			})
			.on('mouseout', function () {
				svg.selectAll('.chart-bar').attr('opacity', 1);
				hideTip();
			});

		styleChart(svg);
	}

	function renderScatter(el: HTMLDivElement, width: number, height: number) {
		const margin = { top: 28, right: 24, bottom: 56, left: 64 };
		const w = width - margin.left - margin.right;
		const h = height - margin.top - margin.bottom;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`) as Svg;

		const xExtent = d3.extent(data, (r) => num(r.x)) as [number, number];
		const yExtent = d3.extent(data, (r) => num(r.y)) as [number, number];
		const x = d3.scaleLinear().domain(xExtent).nice().range([0, w]);
		const y = d3.scaleLinear().domain(yExtent).nice().range([h, 0]);

		addGrid(svg, y, w);

		/* Vertical grid lines for scatter */
		const vGrid = svg
			.append('g')
			.attr('class', 'grid-v')
			.call(
				d3
					.axisBottom(x)
					.ticks(6)
					.tickSize(-h)
					.tickFormat(() => '')
			);
		vGrid.attr('transform', `translate(0,${h})`);
		vGrid
			.selectAll('line')
			.attr('stroke', 'var(--border-primary)')
			.attr('stroke-opacity', 0.15)
			.attr('stroke-dasharray', '3,3');
		vGrid.select('.domain').remove();

		svg
			.append('g')
			.attr('transform', `translate(0,${h})`)
			.call(
				d3
					.axisBottom(x)
					.ticks(6)
					.tickFormat((d) => fmtAxis(d as number))
			);

		makeYAxis(svg, y);
		addTitles(svg, getXTitle(), getYTitle(), w, h);

		const hasGroup = data.length > 0 && 'group' in data[0];

		if (hasGroup) {
			const groups = [...new Set(data.map((r) => str(r.group)))];
			const color = d3.scaleOrdinal<string>().domain(groups).range(PALETTE);
			addLegend(svg, groups, (l) => color(l), w);

			svg
				.selectAll('.dot')
				.data(data)
				.join('circle')
				.attr('class', 'chart-dot')
				.attr('cx', (r) => x(num(r.x)))
				.attr('cy', (r) => y(num(r.y)))
				.attr('r', 3)
				.attr('fill', (r) => color(str(r.group)))
				.attr('opacity', 0.7)
				.style('cursor', 'pointer')
				.on('mouseover', function (event: MouseEvent, r: Row) {
					d3.select(this).attr('r', 6).attr('opacity', 1);
					showTip(
						str(r.group),
						[
							{ label: getXTitle(), value: fmtFull(num(r.x)) },
							{ label: getYTitle(), value: fmtFull(num(r.y)) }
						],
						event
					);
				})
				.on('mouseout', function () {
					d3.select(this).attr('r', 3).attr('opacity', 0.7);
					hideTip();
				});
		} else {
			svg
				.selectAll('.dot')
				.data(data)
				.join('circle')
				.attr('class', 'chart-dot')
				.attr('cx', (r) => x(num(r.x)))
				.attr('cy', (r) => y(num(r.y)))
				.attr('r', 3)
				.attr('fill', PALETTE[0])
				.attr('opacity', 0.7)
				.style('cursor', 'pointer')
				.on('mouseover', function (event: MouseEvent, r: Row) {
					d3.select(this).attr('r', 6).attr('opacity', 1);
					showTip(
						'',
						[
							{ label: getXTitle(), value: fmtFull(num(r.x)) },
							{ label: getYTitle(), value: fmtFull(num(r.y)) }
						],
						event
					);
				})
				.on('mouseout', function () {
					d3.select(this).attr('r', 3).attr('opacity', 0.7);
					hideTip();
				});
		}

		styleChart(svg);
	}

	function renderBoxplot(el: HTMLDivElement, width: number, height: number) {
		const margin = { top: 20, right: 24, bottom: 48, left: 80 };
		const w = width - margin.left - margin.right;
		const h = height - margin.top - margin.bottom;

		const svg = d3
			.select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.append('g')
			.attr('transform', `translate(${margin.left},${margin.top})`) as Svg;

		const groups = data.map((r) => str(r.group));
		const y = d3.scaleBand().domain(groups).range([0, h]).padding(0.3);

		const xMin = d3.min(data, (r) => num(r.min)) ?? 0;
		const xMax = d3.max(data, (r) => num(r.max)) ?? 1;
		const x = d3.scaleLinear().domain([xMin, xMax]).nice().range([0, w]);

		/* Vertical grid for boxplot */
		const vGrid = svg
			.append('g')
			.attr('class', 'grid-v')
			.call(
				d3
					.axisBottom(x)
					.ticks(6)
					.tickSize(-h)
					.tickFormat(() => '')
			);
		vGrid.attr('transform', `translate(0,${h})`);
		vGrid
			.selectAll('line')
			.attr('stroke', 'var(--border-primary)')
			.attr('stroke-opacity', 0.15)
			.attr('stroke-dasharray', '3,3');
		vGrid.select('.domain').remove();

		svg.append('g').call(d3.axisLeft(y).tickSizeOuter(0));

		svg
			.append('g')
			.attr('transform', `translate(0,${h})`)
			.call(
				d3
					.axisBottom(x)
					.ticks(6)
					.tickFormat((d) => fmtAxis(d as number))
			);

		addTitles(svg, getYTitle(), '', w, h);

		const bandH = y.bandwidth();

		for (const row of data) {
			const g = str(row.group);
			const cy = (y(g) ?? 0) + bandH / 2;
			const boxGroup = svg.append('g').attr('class', 'boxplot-group');

			/* Whisker line */
			boxGroup
				.append('line')
				.attr('x1', x(num(row.min)))
				.attr('x2', x(num(row.max)))
				.attr('y1', cy)
				.attr('y2', cy)
				.attr('stroke', PALETTE[0])
				.attr('stroke-width', 1);

			/* Box (Q1 to Q3) */
			const q1x = x(num(row.q1));
			const q3x = x(num(row.q3));
			boxGroup
				.append('rect')
				.attr('x', q1x)
				.attr('y', cy - bandH * 0.35)
				.attr('width', Math.max(0, q3x - q1x))
				.attr('height', bandH * 0.7)
				.attr('fill', PALETTE[0])
				.attr('opacity', 0.2)
				.attr('stroke', PALETTE[0])
				.attr('stroke-width', 1.5)
				.attr('rx', 2);

			/* Median line */
			boxGroup
				.append('line')
				.attr('x1', x(num(row.median)))
				.attr('x2', x(num(row.median)))
				.attr('y1', cy - bandH * 0.35)
				.attr('y2', cy + bandH * 0.35)
				.attr('stroke', PALETTE[0])
				.attr('stroke-width', 2.5);

			/* Whisker caps */
			for (const val of [num(row.min), num(row.max)]) {
				boxGroup
					.append('line')
					.attr('x1', x(val))
					.attr('x2', x(val))
					.attr('y1', cy - bandH * 0.2)
					.attr('y2', cy + bandH * 0.2)
					.attr('stroke', PALETTE[0])
					.attr('stroke-width', 1.5);
			}

			/* Hover area for tooltip */
			boxGroup
				.append('rect')
				.attr('x', x(num(row.min)))
				.attr('y', cy - bandH * 0.4)
				.attr('width', Math.max(0, x(num(row.max)) - x(num(row.min))))
				.attr('height', bandH * 0.8)
				.attr('fill', 'transparent')
				.style('cursor', 'pointer')
				.on('mouseover', function (event: MouseEvent) {
					boxGroup.select('rect:first-of-type').attr('opacity', 0.35);
					showTip(
						g,
						[
							{ label: 'Min', value: fmtFull(num(row.min)) },
							{ label: 'Q1', value: fmtFull(num(row.q1)) },
							{ label: 'Median', value: fmtFull(num(row.median)) },
							{ label: 'Q3', value: fmtFull(num(row.q3)) },
							{ label: 'Max', value: fmtFull(num(row.max)) }
						],
						event
					);
				})
				.on('mouseout', function () {
					boxGroup.select('rect:first-of-type').attr('opacity', 0.2);
					hideTip();
				});
		}

		styleChart(svg);
	}
</script>

<div class="chart-wrapper" bind:this={wrapperEl}>
	<div class="chart-area" bind:this={chartEl}>
		{#if data.length === 0}
			<div class="chart-empty">
				<span>No data to display</span>
			</div>
		{/if}
	</div>
	<div
		class="chart-tooltip"
		class:tip-visible={tipVisible}
		style:left="{tipX}px"
		style:top="{tipY}px"
	>
		{#if tipTitle}<strong>{tipTitle}</strong>{/if}
		{#each tipLines as line, i (i)}
			{#if tipTitle || tipLines.length > 1}<br />{/if}
			{#if line.label}{line.label}:
			{/if}{line.value}
		{/each}
	</div>
</div>

<style>
	.chart-wrapper {
		position: relative;
		width: 100%;
		height: 300px;
		background-color: var(--bg-primary);
		overflow: hidden;
		contain: content;
	}

	.chart-area {
		width: 100%;
		height: 100%;
	}

	.chart-empty {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--fg-muted);
		font-size: 0.75rem;
	}

	.chart-tooltip {
		position: absolute;
		pointer-events: none;
		opacity: 0;
		padding: 8px 12px;
		background-color: var(--bg-tertiary);
		border: 1px solid var(--border-primary);
		color: var(--fg-primary);
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		line-height: 1.6;
		white-space: nowrap;
		z-index: var(--z-tooltip);
		transition: opacity 80ms ease;
	}

	.chart-tooltip.tip-visible {
		opacity: 1;
	}
</style>
