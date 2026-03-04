import { defineConfig } from '@pandacss/dev';
import { navLink, iconButton, button, spinner } from './src/lib/styles/recipes';

export default defineConfig({
	preflight: false,
	include: ['./src/**/*.{js,ts,svelte}'],
	exclude: [],
	outdir: 'styled-system',
	importMap: {
		css: ['styled-system/css', '$lib/styles/panda'],
		recipes: ['styled-system/recipes', '$lib/styles/panda']
	},
	staticCss: {
		css: [
			{
				properties: {
					display: ['flex', 'grid', 'inline-flex', 'block'],
					alignItems: ['center', 'flex-start', 'flex-end', 'stretch'],
					justifyContent: ['center', 'space-between', 'flex-start', 'flex-end'],
					gap: ['0', '1', '2', '3', '4', '5', '6', '8'],
					flexDirection: ['row', 'column'],
					flexWrap: ['wrap'],
					width: ['full'],
					minWidth: ['0'],
					maxWidth: ['100', '105', '120', '180', '275', '300'],
					paddingX: ['2', '3', '4', '6', '8'],
					paddingY: ['1', '1.5', '2', '3', '6', '7', '12'],
					marginBottom: ['2', '4', '5', '6', '7', '8'],
					fontSize: ['xs', 'sm', 'md', 'lg', '2xl'],
					fontWeight: ['medium', 'semibold'],
					color: ['fg.primary', 'fg.secondary', 'fg.tertiary', 'fg.muted', 'fg.faint'],
					backgroundColor: [
						'bg.primary',
						'bg.secondary',
						'bg.tertiary',
						'bg.hover',
						'accent.primary',
						'error.bg'
					],
					borderColor: ['border.primary', 'border.tertiary', 'error.border'],
					borderWidth: ['0', '1px'],
					borderStyle: ['solid', 'dashed'],
					borderRadius: ['0']
				}
			}
		]
	},
	theme: {
		extend: {
			recipes: {
				navLink,
				iconButton,
				button,
				spinner
			},
			tokens: {
				fonts: {
					mono: { value: 'var(--font-mono)' }
				},
				spacing: {
					1: { value: 'var(--space-1)' },
					2: { value: 'var(--space-2)' },
					3: { value: 'var(--space-3)' }
				},
				radii: {
					sm: { value: 'var(--radius-sm)' }
				},
				shadows: {
					drag: { value: 'var(--shadow-drag)' }
				},
				sizes: {
					operationsPanel: { value: 'var(--operations-panel-width)' },
					datasourcePanel: { value: 'var(--datasource-panel-width)' },
					pipelineConnection: { value: 'var(--pipeline-connection-height)' },
					'4.5': { value: '1.125rem' },
					'30': { value: '7.5rem' },
					'37.5': { value: '9.375rem' },
					'50': { value: '12.5rem' },
					'55': { value: '13.75rem' },
					'75': { value: '18.75rem' },
					'90': { value: '22.5rem' },
					'100': { value: '25rem' },
					'105': { value: '26.25rem' },
					'120': { value: '30rem' },
					'180': { value: '45rem' },
					'240': { value: '60rem' },
					'275': { value: '68.75rem' },
					'300': { value: '75rem' }
				},
				zIndex: {
					dropdown: { value: 'var(--z-dropdown)' },
					sticky: { value: 'var(--z-sticky)' },
					header: { value: 'var(--z-header)' },
					engine: { value: 'var(--z-engine)' },
					modal: { value: 'var(--z-modal)' },
					tooltip: { value: 'var(--z-tooltip)' },
					popover: { value: 'var(--z-popover)' },
					overlay: { value: 'var(--z-overlay)' }
				}
			}
		},
		semanticTokens: {
			colors: {
				bg: {
					primary: { value: 'var(--bg-primary)' },
					secondary: { value: 'var(--bg-secondary)' },
					tertiary: { value: 'var(--bg-tertiary)' },
					muted: { value: 'var(--bg-muted)' },
					hover: { value: 'var(--bg-hover)' },
					panel: { value: 'var(--bg-primary)' },
					overlay: { value: 'var(--overlay-bg)' },
					overlaySoft: { value: 'var(--overlay-soft)' }
				},
				fg: {
					primary: { value: 'var(--fg-primary)' },
					secondary: { value: 'var(--fg-secondary)' },
					tertiary: { value: 'var(--fg-tertiary)' },
					muted: { value: 'var(--fg-muted)' },
					faint: { value: 'var(--fg-faint)' }
				},
				accent: {
					primary: { value: 'var(--accent-primary)' },
					secondary: { value: 'var(--accent-secondary)' },
					bg: { value: 'var(--accent-bg)' }
				},
				border: {
					primary: { value: 'var(--border-primary)' },
					tertiary: { value: 'var(--border-primary)' }
				},
				success: {
					fg: { value: 'var(--success-fg)' },
					bg: { value: 'var(--success-bg)' }
				},
				warning: {
					fg: { value: 'var(--warning-fg)' },
					bg: { value: 'var(--warning-bg)' },
					border: { value: 'var(--warning-border)' },
					contrast: { value: 'var(--warning-contrast)' }
				},
				error: {
					fg: { value: 'var(--error-fg)' },
					bg: { value: 'var(--error-bg)' },
					border: { value: 'var(--error-border)' }
				},
				canvas: {
					gridLine: { value: 'var(--pipeline-grid-line)' },
					lineageNode: { value: 'var(--lineage-node)' },
					lineageNodeBorder: { value: 'var(--lineage-node-border)' },
					lineageEdge: { value: 'var(--lineage-edge)' },
					lineageEdgeActive: { value: 'var(--lineage-edge-active)' }
				}
			}
		}
	}
});
