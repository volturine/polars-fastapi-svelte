import { defineRecipe } from '@pandacss/dev';

export const button = defineRecipe({
	className: 'btn',
	base: {
		cursor: 'pointer',
		borderWidth: '1px',
		borderStyle: 'solid',
		fontFamily: 'var(--font-mono)',
		fontSize: 'sm',
		fontWeight: 'medium',
		transitionProperty: 'color, background-color, border-color, opacity',
		transitionDuration: '160ms',
		transitionTimingFunction: 'ease',
		_disabled: { opacity: '0.5', cursor: 'not-allowed' }
	},
	variants: {
		variant: {
			primary: {
				backgroundColor: 'accent.primary',
				color: 'bg.primary',
				borderColor: 'border.primary',
				_hover: { _notDisabled: { opacity: '0.9' } }
			},
			secondary: {
				backgroundColor: 'transparent',
				color: 'fg.primary',
				borderColor: 'border.primary',
				_hover: { _notDisabled: { backgroundColor: 'bg.hover', color: 'fg.secondary' } }
			},
			ghost: {
				backgroundColor: 'transparent',
				color: 'fg.secondary',
				borderColor: 'transparent',
				_hover: { _notDisabled: { backgroundColor: 'bg.hover', color: 'fg.primary' } }
			},
			danger: {
				backgroundColor: 'error.bg',
				color: 'error.fg',
				borderColor: 'error.border',
				_hover: { _notDisabled: { opacity: '0.85' } }
			}
		},
		size: {
			default: { paddingX: '4', paddingY: '2' },
			sm: { fontSize: 'xs', paddingX: '2', paddingY: '1' }
		}
	},
	defaultVariants: { variant: 'secondary', size: 'default' }
});

export const spinner = defineRecipe({
	className: 'spinner',
	base: {
		borderStyle: 'solid',
		borderColor: 'border.primary',
		borderTopColor: 'accent.secondary',
		borderRadius: '9999px',
		animation: 'spin 0.8s linear infinite',
		flexShrink: '0'
	},
	variants: {
		size: {
			default: { width: '40px', height: '40px', borderWidth: '4px' },
			sm: { width: '14px', height: '14px', borderWidth: '2px' },
			md: { width: '24px', height: '24px', borderWidth: '3px' }
		}
	},
	defaultVariants: { size: 'default' }
});

export const navLink = defineRecipe({
	className: 'nav-link',
	base: {
		borderWidth: '1px',
		borderStyle: 'solid',
		borderColor: 'transparent',
		paddingX: '3',
		paddingY: '1.5',
		fontSize: 'sm',
		color: 'fg.tertiary',
		textDecoration: 'none',
		transitionProperty: 'color',
		transitionDuration: '160ms',
		transitionTimingFunction: 'ease'
	},
	variants: {
		active: {
			true: {
				color: 'fg.primary',
				borderColor: 'border.primary',
				backgroundColor: 'bg.tertiary'
			}
		}
	}
});

export const iconButton = defineRecipe({
	className: 'icon-button',
	base: {
		display: 'inline-flex',
		alignItems: 'center',
		justifyContent: 'center',
		borderWidth: '1px',
		borderStyle: 'solid',
		borderColor: 'border.tertiary',
		backgroundColor: 'bg.primary',
		padding: '2',
		color: 'fg.secondary',
		transitionProperty: 'color, background-color, border-color, opacity',
		transitionDuration: '160ms',
		transitionTimingFunction: 'ease',
		_hover: {
			backgroundColor: 'bg.hover',
			color: 'fg.primary'
		}
	}
});
