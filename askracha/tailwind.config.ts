// tailwind.config.js
import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";
import tailwindcssTypography from "@tailwindcss/typography";

const config: Config = {
    darkMode: ["class", "class"],
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: [
                    'Inter',
                    'system-ui',
                    '-apple-system',
                    'sans-serif'
                ],
                mono: [
                    'ui-monospace',
                    'SFMono-Regular',
                    'Monaco',
                    'Consolas',
                    'Liberation Mono',
                    'Courier New',
                    'monospace'
                ]
            },
            colors: {
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))',
                }
            },
            animation: {
                bounce: 'bounce 3s ease-in-out infinite',
                pulse: 'pulse 3s ease-in-out infinite'
            },
            backdropBlur: {
                xs: '2px'
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            typography: ({ theme }) => ({
                DEFAULT: {
                    css: {
                        // Base typography improvements
                        fontSize: '1rem',
                        lineHeight: '1.75',
                        color: theme('colors.foreground'),
                        maxWidth: 'none',

                        // Enhanced paragraph styling with better spacing
                        'p': {
                            marginTop: '1.5em',
                            marginBottom: '1.5em',
                            lineHeight: '1.75',
                        },

                        // Remove default code pseudo-elements
                        'code::before': { content: '""' },
                        'code::after': { content: '""' },
                        // Enhanced code block styling with improved visibility
                        'pre': {
                            backgroundColor: theme('colors.secondary.DEFAULT'),
                            color: theme('colors.secondary.foreground'),
                            border: `2px solid ${theme('colors.border')}`,
                            borderRadius: theme('borderRadius.lg'),
                            padding: '1.5rem',
                            marginTop: '2rem',
                            marginBottom: '2rem',
                            overflowX: 'auto',
                            fontSize: '0.875rem',
                            lineHeight: '1.6',
                            fontFamily: theme('fontFamily.mono'),
                            whiteSpace: 'pre',
                            wordWrap: 'normal',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                        },
                        'pre code': {
                            backgroundColor: 'transparent',
                            color: 'inherit',
                            fontSize: 'inherit',
                            lineHeight: 'inherit',
                            padding: '0',
                            border: 'none',
                            borderRadius: '0',
                        },

                        // Enhanced inline code styling with better visibility
                        'code': {
                            backgroundColor: theme('colors.secondary.DEFAULT'),
                            color: theme('colors.secondary.foreground'),
                            padding: '0.25rem 0.5rem',
                            borderRadius: theme('borderRadius.sm'),
                            fontSize: '0.875em',
                            fontWeight: '600',
                            fontFamily: theme('fontFamily.mono'),
                            border: `1px solid ${theme('colors.border')}`,
                            marginLeft: '0.125rem',
                            marginRight: '0.125rem',
                        },

                        // Enhanced list styling with improved spacing
                        'ul': {
                            marginTop: '2em',
                            marginBottom: '2em',
                            paddingLeft: '2em',
                            listStyleType: 'disc',
                            '& > li': {
                                marginTop: '0.75em',
                                marginBottom: '0.75em',
                                lineHeight: '1.7',
                                paddingLeft: '0.5em',
                            },
                            '& > li::marker': {
                                color: theme('colors.primary.DEFAULT'),
                            },
                        },
                        'ol': {
                            marginTop: '2em',
                            marginBottom: '2em',
                            paddingLeft: '2em',
                            listStyleType: 'decimal',
                            '& > li': {
                                marginTop: '0.75em',
                                marginBottom: '0.75em',
                                lineHeight: '1.7',
                                paddingLeft: '0.5em',
                            },
                            '& > li::marker': {
                                color: theme('colors.primary.DEFAULT'),
                                fontWeight: '600',
                            },
                        },

                        // Improved nested list styling
                        'ul ul, ol ol, ul ol, ol ul': {
                            marginTop: '1em',
                            marginBottom: '1em',
                            paddingLeft: '1.5em',
                        },

                        // Better spacing for nested list items
                        'li > ul > li, li > ol > li': {
                            marginTop: '0.5em',
                            marginBottom: '0.5em',
                        },
                        // Enhanced blockquote styling with improved spacing
                        'blockquote': {
                            borderLeft: `4px solid ${theme('colors.primary.DEFAULT')}`,
                            backgroundColor: `${theme('colors.muted.DEFAULT')}33`,
                            paddingLeft: theme('spacing.6'),
                            paddingRight: theme('spacing.6'),
                            paddingTop: theme('spacing.4'),
                            paddingBottom: theme('spacing.4'),
                            marginTop: '2em',
                            marginBottom: '2em',
                            color: theme('colors.muted.foreground'),
                            fontStyle: 'italic',
                            borderRadius: theme('borderRadius.md'),
                            lineHeight: '1.7',
                        },
                        'table': {
                            width: '100%',
                            borderCollapse: 'collapse',
                            textAlign: 'left',
                            marginTop: theme('spacing.6'),
                            marginBottom: theme('spacing.6'),
                            '& thead': {
                                borderBottom: `1px solid ${theme('colors.border')}`,
                            },
                            '& th': {
                                padding: theme('spacing.2'),
                                fontWeight: theme('fontWeight.semibold'),
                            },
                            '& td': {
                                padding: theme('spacing.2'),
                                borderBottom: `1px solid ${theme('colors.border')}`,
                            },
                        },
                        // Enhanced heading hierarchy with improved spacing
                        'h1': {
                            color: theme('colors.foreground'),
                            fontSize: '1.875rem',
                            fontWeight: '700',
                            lineHeight: '1.2',
                            marginTop: '3rem',
                            marginBottom: '1.5rem',
                        },
                        'h2': {
                            color: theme('colors.foreground'),
                            fontSize: '1.5rem',
                            fontWeight: '600',
                            lineHeight: '1.3',
                            marginTop: '2.5rem',
                            marginBottom: '1.25rem',
                        },
                        'h3': {
                            color: theme('colors.foreground'),
                            fontSize: '1.25rem',
                            fontWeight: '600',
                            lineHeight: '1.4',
                            marginTop: '2rem',
                            marginBottom: '1rem',
                        },
                        'h4, h5, h6': {
                            color: theme('colors.foreground'),
                            fontSize: '1.125rem',
                            fontWeight: '500',
                            lineHeight: '1.5',
                            marginTop: '1.75rem',
                            marginBottom: '0.875rem',
                        },
                        'a': {
                            color: theme('colors.primary.DEFAULT'),
                            '&:hover': {
                                color: theme('colors.primary.foreground'),
                            },
                        },
                    },
                },

                // Dark theme overrides with improved spacing
                dark: {
                    css: {
                        color: theme('colors.foreground'),
                        'pre': {
                            backgroundColor: theme('colors.secondary.DEFAULT'),
                            color: theme('colors.secondary.foreground'),
                            border: `2px solid ${theme('colors.border')}`,
                            padding: '1.5rem',
                            marginTop: '2rem',
                            marginBottom: '2rem',
                            lineHeight: '1.6',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                        },
                        'code': {
                            backgroundColor: theme('colors.secondary.DEFAULT'),
                            color: theme('colors.secondary.foreground'),
                            border: `1px solid ${theme('colors.border')}`,
                            padding: '0.25rem 0.5rem',
                            marginLeft: '0.125rem',
                            marginRight: '0.125rem',
                            fontWeight: '600',
                        },
                        'blockquote': {
                            borderLeft: `4px solid ${theme('colors.primary.DEFAULT')}`,
                            backgroundColor: `${theme('colors.muted.DEFAULT')}33`,
                            color: theme('colors.muted.foreground'),
                            paddingLeft: theme('spacing.6'),
                            paddingRight: theme('spacing.6'),
                            paddingTop: theme('spacing.4'),
                            paddingBottom: theme('spacing.4'),
                            marginTop: '2em',
                            marginBottom: '2em',
                            lineHeight: '1.7',
                        },
                        'a': {
                            color: theme('colors.primary.DEFAULT'),
                            '&:hover': {
                                color: theme('colors.primary.DEFAULT'),
                                opacity: '0.8',
                            },
                        },
                        'h1, h2, h3, h4, h5, h6': {
                            color: theme('colors.foreground'),
                        },
                        'ul > li::marker': {
                            color: theme('colors.primary.DEFAULT'),
                        },
                        'ol > li::marker': {
                            color: theme('colors.primary.DEFAULT'),
                        },
                    },
                },

                // Storacha theme specific overrides with improved spacing
                storacha: {
                    css: {
                        color: theme('colors.foreground'),
                        'pre': {
                            backgroundColor: 'hsl(var(--secondary))',
                            color: 'hsl(var(--secondary-foreground))',
                            border: '2px solid hsl(var(--border))',
                            padding: '1.5rem',
                            marginTop: '2rem',
                            marginBottom: '2rem',
                            lineHeight: '1.6',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
                        },
                        'code': {
                            backgroundColor: 'hsl(var(--secondary))',
                            color: 'hsl(var(--secondary-foreground))',
                            border: '1px solid hsl(var(--border))',
                            padding: '0.25rem 0.5rem',
                            marginLeft: '0.125rem',
                            marginRight: '0.125rem',
                            fontWeight: '600',
                        },
                        'blockquote': {
                            borderLeft: '4px solid hsl(var(--primary))',
                            backgroundColor: 'hsl(var(--muted) / 0.3)',
                            color: 'hsl(var(--muted-foreground))',
                            paddingLeft: theme('spacing.6'),
                            paddingRight: theme('spacing.6'),
                            paddingTop: theme('spacing.4'),
                            paddingBottom: theme('spacing.4'),
                            marginTop: '2em',
                            marginBottom: '2em',
                            lineHeight: '1.7',
                        },
                        'a': {
                            color: 'hsl(var(--primary))',
                            '&:hover': {
                                color: 'hsl(var(--primary))',
                                opacity: '0.8',
                            },
                        },
                        'h1, h2, h3, h4, h5, h6': {
                            color: 'hsl(var(--foreground))',
                        },
                        'ul > li::marker': {
                            color: 'hsl(var(--primary))',
                        },
                        'ol > li::marker': {
                            color: 'hsl(var(--primary))',
                        },
                    },
                },
            }),
        }
    },
    plugins: [tailwindcssAnimate, tailwindcssTypography],
};

export default config;