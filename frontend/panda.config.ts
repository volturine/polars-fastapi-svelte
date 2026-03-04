import { defineConfig } from '@pandacss/dev';
import {
	navLink,
	iconButton,
	button,
	spinner,
	sectionHeader,
	panelHeader,
	panelFooter,
	menuItem,
	toggleButton,
	callout,
	tabButton,
	chip,
	emptyText,
	badge,
	input
} from './src/lib/styles/recipes';

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
					gap: [
						'0',
						'1',
						'2',
						'3',
						'4',
						'5',
						'6',
						'8',
						'px',
						'2px',
						'3px',
						'4px',
						'5px',
						'6px',
						'8px',
						'tight'
					],
					flexDirection: ['row', 'column'],
					flexWrap: ['wrap'],
					width: ['full'],
					minWidth: ['0'],
					maxWidth: ['100', '105', '120', '180', '275', '300'],
					paddingX: ['1', '1.5', '2', '2.5', '3', '3.5', '4', '5', '6', '8'],
					paddingY: ['0.5', '1', '1.5', '2', '2.5', '3', '3.5', '6', '7', '8', '12'],
					marginBottom: ['2', '4', '5', '6', '7', '8'],
					fontSize: ['xs', 'sm', 'md', 'lg', 'xl', '2xl', '2xs', '2xs2', 'xs2', '3xs'],
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
					borderWidth: ['0', '1px', '1', '2', '3', '4'],
					borderStyle: ['solid', 'dashed'],
					borderRadius: ['0', 'xxs', 'xs', 'md', 'sm2', 'pill', 'full', 'sm']
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
				spinner,
				sectionHeader,
				panelHeader,
				panelFooter,
				menuItem,
				toggleButton,
				callout,
				tabButton,
				chip,
				emptyText,
				badge,
				input
			},
			tokens: {
				fonts: {
					mono: { value: 'var(--font-mono)' }
				},
				fontSizes: {
					'2xs': { value: '0.625rem' },
					'2xs2': { value: '0.65rem' },
					xs2: { value: '0.6875rem' },
					'3xs': { value: '0.5625rem' }
				},
				letterSpacings: {
					tight2: { value: '0.02em' },
					wide2: { value: '0.04em' },
					wide3: { value: '0.08em' },
					max: { value: '0.2em' }
				},
				lineHeights: {
					base: { value: '1.6' }
				},
				borderWidths: {
					'1': { value: '1px' },
					'2': { value: '2px' },
					'3': { value: '3px' },
					'4': { value: '4px' }
				},
				spacing: {
					1: { value: 'var(--space-1)' },
					2: { value: 'var(--space-2)' },
					3: { value: 'var(--space-3)' },
					px: { value: '1px' },
					'2px': { value: '2px' },
					'3px': { value: '3px' },
					'4px': { value: '4px' },
					'5px': { value: '5px' },
					'6px': { value: '6px' },
					'8px': { value: '8px' },
					tight: { value: '0.15rem' }
				},
				radii: {
					sm: { value: 'var(--radius-sm)' },
					xxs: { value: '1px' },
					xs: { value: '2px' },
					md: { value: '3px' },
					sm2: { value: '6px' },
					pill: { value: '20px' },
					full: { value: '9999px' }
				},
				shadows: {
					drag: { value: 'var(--shadow-drag)' },
					menu: { value: '0 6px 16px rgba(0, 0, 0, 0.12)' },
					popup: { value: '0 2px 8px rgba(0, 0, 0, 0.15)' },
					panel: { value: '0 10px 24px rgba(0, 0, 0, 0.2)' },
					popover: { value: '0 10px 30px rgba(0, 0, 0, 0.08)' }
				},
				sizes: {
					operationsPanel: { value: 'var(--operations-panel-width)' },
					datasourcePanel: { value: 'var(--datasource-panel-width)' },
					pipelineConnection: { value: 'var(--pipeline-connection-height)' },
					px: { value: '1px' },
					'1.5px': { value: '1.5px' },
					'2px': { value: '2px' },
					'3px': { value: '3px' },
					'4px': { value: '4px' },
					'5px': { value: '5px' },
					'6px': { value: '6px' },
					'8px': { value: '8px' },
					'14px': { value: '14px' },
					'16px': { value: '16px' },
					'18px': { value: '18px' },
					'24px': { value: '24px' },
					'30px': { value: '30px' },
					'32px': { value: '32px' },
					'36px': { value: '36px' },
					'40px': { value: '40px' },
					'28px': { value: '28px' },
					'64px': { value: '64px' },
					'24p': { value: '2.4rem' },
					'4.5': { value: '1.125rem' },
					'12.5': { value: '3.125rem' },
					'13': { value: '3.25rem' },
					'15': { value: '3.75rem' },
					'25': { value: '6.25rem' },
					'30': { value: '7.5rem' },
					'35': { value: '8.75rem' },
					'37.5': { value: '9.375rem' },
					'40': { value: '10rem' },
					'50': { value: '12.5rem' },
					'55': { value: '13.75rem' },
					'60': { value: '15rem' },
					'70': { value: '17.5rem' },
					'75': { value: '18.75rem' },
					'80': { value: '20rem' },
					'90': { value: '22.5rem' },
					'100': { value: '25rem' },
					'105': { value: '26.25rem' },
					'120': { value: '30rem' },
					'125': { value: '31.25rem' },
					'180': { value: '45rem' },
					'200': { value: '50rem' },
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
