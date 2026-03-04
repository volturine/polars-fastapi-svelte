import { defineRecipe } from '@pandacss/dev';

export const sectionHeader = defineRecipe({
	className: 'section-header',
	base: {
		fontSize: 'xs',
		fontWeight: 'semibold',
		textTransform: 'uppercase',
		letterSpacing: 'wider',
		color: 'fg.tertiary'
	}
});

export const panelHeader = defineRecipe({
	className: 'panel-header',
	base: {
		display: 'flex',
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		borderBottomWidth: '1px',
		borderBottomStyle: 'solid',
		borderBottomColor: 'border.tertiary',
		padding: '4'
	}
});

export const panelFooter = defineRecipe({
	className: 'panel-footer',
	base: {
		display: 'flex',
		justifyContent: 'flex-end',
		gap: '3',
		borderTopWidth: '1px',
		borderTopStyle: 'solid',
		borderTopColor: 'border.tertiary',
		padding: '4'
	}
});

export const menuItem = defineRecipe({
	className: 'menu-item',
	base: {
		border: 'none',
		background: 'transparent',
		color: 'fg.primary',
		width: 'full',
		paddingX: '3',
		paddingY: '2',
		fontSize: 'xs',
		textAlign: 'left',
		cursor: 'pointer',
		borderBottomWidth: '1px',
		borderBottomStyle: 'solid',
		borderBottomColor: 'border.tertiary',
		_last: { borderBottomWidth: '0' },
		_hover: { backgroundColor: 'bg.hover' }
	}
});

export const toggleButton = defineRecipe({
	className: 'toggle-btn',
	base: {
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'center',
		cursor: 'pointer',
		borderWidth: '1px',
		borderStyle: 'solid',
		paddingX: '2',
		paddingY: '1',
		fontSize: 'xs'
	},
	variants: {
		active: {
			true: {
				borderColor: 'border.primary',
				backgroundColor: 'accent.bg',
				color: 'accent.primary',
				boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
				position: 'relative',
				zIndex: '1'
			},
			false: {
				borderColor: 'border.tertiary',
				backgroundColor: 'transparent',
				color: 'fg.muted',
				_hover: { backgroundColor: 'bg.hover', color: 'fg.secondary' }
			}
		},
		radius: {
			left: { borderRadius: 'sm 0 0 sm' },
			right: { borderRadius: '0 sm sm 0' },
			none: { borderRadius: '0' }
		}
	},
	defaultVariants: { active: false, radius: 'none' }
});

export const callout = defineRecipe({
	className: 'callout',
	base: {
		paddingX: '3',
		paddingY: '2.5',
		borderLeft: '2px solid',
		fontSize: 'xs',
		lineHeight: '1.5',
		color: 'fg.tertiary'
	},
	variants: {
		tone: {
			info: { borderLeftColor: 'accent.secondary', backgroundColor: 'transparent' },
			warn: { borderLeftColor: 'warning.border', backgroundColor: 'warning.bg' },
			error: { borderLeftColor: 'error.border', backgroundColor: 'error.bg', color: 'error.fg' }
		}
	},
	defaultVariants: { tone: 'info' }
});

export const button = defineRecipe({
	className: 'btn',
	base: {
		cursor: 'pointer',
		borderWidth: '1',
		borderStyle: 'solid',
		fontFamily: 'mono',
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
		borderRadius: 'full',
		animation: 'spin 0.8s linear infinite',
		flexShrink: '0'
	},
	variants: {
		size: {
			default: { width: '40px', height: '40px', borderWidth: '4' },
			sm: { width: '14px', height: '14px', borderWidth: '2' },
			md: { width: '24px', height: '24px', borderWidth: '3' }
		}
	},
	defaultVariants: { size: 'default' }
});

export const navLink = defineRecipe({
	className: 'nav-link',
	base: {
		borderWidth: '1',
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
		borderWidth: '1',
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

export const tabButton = defineRecipe({
	className: 'tab-button',
	base: {
		backgroundColor: 'transparent',
		borderBottomWidth: '2',
		borderBottomStyle: 'solid',
		borderBottomColor: 'transparent',
		marginBottom: '-1px',
		fontWeight: 'medium',
		color: 'fg.muted',
		_hover: { color: 'fg.secondary' }
	},
	variants: {
		active: {
			true: { color: 'accent.primary', borderBottomColor: 'accent.secondary' }
		},
		size: {
			default: { paddingX: '3', paddingY: '1.5', fontSize: 'xs' },
			lg: { paddingX: '6', paddingY: '3', fontSize: 'sm' }
		}
	},
	defaultVariants: { active: false, size: 'default' }
});

export const chip = defineRecipe({
	className: 'chip',
	base: {
		display: 'inline-flex',
		alignItems: 'center',
		paddingX: '1.5',
		paddingY: '0.5',
		fontSize: '2xs',
		fontWeight: 'medium',
		textTransform: 'uppercase',
		letterSpacing: 'wider'
	},
	variants: {
		tone: {
			accent: { backgroundColor: 'accent.bg', color: 'accent.primary' },
			neutral: { backgroundColor: 'bg.tertiary', color: 'fg.muted' },
			warning: { backgroundColor: 'warning.bg', color: 'warning.fg' },
			success: { backgroundColor: 'success.bg', color: 'success.fg' },
			error: { backgroundColor: 'error.bg', color: 'error.fg' }
		}
	},
	defaultVariants: { tone: 'neutral' }
});

export const emptyText = defineRecipe({
	className: 'empty-text',
	base: {
		color: 'fg.muted',
		textAlign: 'center'
	},
	variants: {
		size: {
			compact: { paddingY: '8', fontSize: 'xs' },
			panel: { padding: '6', fontSize: 'sm' },
			inline: { padding: '0', fontSize: 'sm' }
		}
	},
	defaultVariants: { size: 'compact' }
});

export const input = defineRecipe({
	className: 'input',
	base: {
		width: 'full',
		borderWidth: '1',
		borderStyle: 'solid',
		borderColor: 'border.tertiary',
		backgroundColor: 'transparent',
		paddingX: '2',
		paddingY: '1.5',
		fontSize: 'xs',
		color: 'fg.primary',
		_focus: { borderColor: 'accent.primary', outline: 'none' }
	},
	variants: {
		variant: {
			default: {},
			search: {
				paddingLeft: '8',
				paddingY: '1.5',
				fontSize: 'sm',
				backgroundColor: 'transparent',
				borderColor: 'border.tertiary'
			},
			searchCompact: {
				paddingLeft: '8',
				paddingY: '1',
				fontSize: 'xs',
				backgroundColor: 'bg.secondary',
				borderColor: 'border.tertiary'
			},
			menu: {
				borderColor: 'border.primary',
				backgroundColor: 'bg.secondary',
				paddingX: '3',
				paddingY: '2',
				fontSize: 'sm',
				_focus: { borderColor: 'border.primary', outline: 'none', backgroundColor: 'bg.primary' },
				_placeholder: { color: 'fg.muted' }
			},
			searchWide: {
				paddingY: '3',
				paddingLeft: '10',
				paddingRight: '10',
				backgroundColor: 'bg.primary',
				borderColor: 'border.primary',
				fontFamily: 'mono',
				fontSize: 'sm'
			}
		}
	},
	defaultVariants: { variant: 'default' }
});

export const badge = defineRecipe({
	className: 'badge',
	base: {
		display: 'inline-flex',
		alignItems: 'center',
		fontFamily: 'mono',
		borderWidth: '1px',
		borderStyle: 'solid',
		backgroundColor: 'accent.bg',
		color: 'accent.primary'
	},
	variants: {
		tone: {
			type: { borderColor: 'accent.secondary' },
			file: { borderColor: 'border.primary', textTransform: 'uppercase', letterSpacing: 'wider' }
		},
		size: {
			sm: { paddingX: '1.5', paddingY: '0.5', fontSize: '2xs' },
			md: { paddingX: '2', paddingY: '0.5', fontSize: 'xs' },
			lg: { paddingX: '2.5', paddingY: '0.5', fontSize: 'xs' }
		}
	},
	defaultVariants: { tone: 'type', size: 'md' }
});
