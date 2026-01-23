import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import DataTable from '../src/lib/components/viewers/DataTable.svelte';

describe('DataTable Component', () => {
	const mockData = [
		{ id: 1, name: 'Alice', age: 25 },
		{ id: 2, name: 'Bob', age: 30 },
		{ id: 3, name: 'Charlie', age: 35 }
	];

	const mockColumns = ['id', 'name', 'age'];

	it('should render table with data', () => {
		render(DataTable, {
			props: {
				data: mockData,
				columns: mockColumns
			}
		});

		expect(screen.getByText('Alice')).toBeTruthy();
		expect(screen.getByText('Bob')).toBeTruthy();
		expect(screen.getByText('Charlie')).toBeTruthy();
	});

	it('should render column headers', () => {
		render(DataTable, {
			props: {
				data: mockData,
				columns: mockColumns
			}
		});

		expect(screen.getByText('id')).toBeTruthy();
		expect(screen.getByText('name')).toBeTruthy();
		expect(screen.getByText('age')).toBeTruthy();
	});

	it('should render empty state when no data', () => {
		render(DataTable, {
			props: {
				data: [],
				columns: mockColumns
			}
		});

		// Should show empty state message
		expect(screen.queryByText('Alice')).toBeNull();
	});

	it('should handle null values', () => {
		const dataWithNull = [
			{ id: 1, name: 'Alice', age: null },
			{ id: 2, name: 'Bob', age: 30 }
		];

		render(DataTable, {
			props: {
				data: dataWithNull,
				columns: mockColumns
			}
		});

		expect(screen.getByText('Alice')).toBeTruthy();
	});

	it('should display correct number of rows', () => {
		const { container } = render(DataTable, {
			props: {
				data: mockData,
				columns: mockColumns
			}
		});

		const rows = container.querySelectorAll('tbody tr');
		expect(rows.length).toBe(3);
	});
});
