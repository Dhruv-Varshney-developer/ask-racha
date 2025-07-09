// tailwind.config.js
import type { Config } from "tailwindcss";

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
                        'code::before': { content: '""' },
                        'code::after': { content: '""' },
                        'pre': {
                            backgroundColor: theme('colors.muted.DEFAULT'),
                            color: theme('colors.foreground'),
                            borderRadius: theme('borderRadius.md'),
                            padding: theme('spacing.4'),
                            overflowX: 'auto',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all',
                        },
                        'pre code': {
                            backgroundColor: 'transparent',
                            color: 'inherit',
                            fontSize: theme('fontSize.sm'),
                            lineHeight: theme('lineHeight.normal'),
                        },

                        'ul': {
                            marginTop: theme('spacing.4'),
                            marginBottom: theme('spacing.4'),
                            paddingLeft: theme('spacing.6'),
                            '& > li::marker': {
                                color: theme('colors.muted.foreground'),
                            },
                        },
                        'ol': {
                            marginTop: theme('spacing.4'),
                            marginBottom: theme('spacing.4'),
                            paddingLeft: theme('spacing.6'),
                            '& > li::marker': {
                                color: theme('colors.muted.foreground'),
                            },
                        },
                        'li': {
                            marginTop: theme('spacing.1'),
                            marginBottom: theme('spacing.1'),
                        },
                        'blockquote': {
                            borderLeftColor: theme('colors.border'),
                            paddingLeft: theme('spacing.4'),
                            color: theme('colors.muted.foreground'),
                            fontStyle: 'italic',
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
                        'h1, h2, h3, h4, h5, h6': {
                            color: theme('colors.foreground'),
                        },
                        'a': {
                            color: theme('colors.primary.DEFAULT'),
                            '&:hover': {
                                color: theme('colors.primary.foreground'),
                            },
                        },
                    },
                },

                dark: {
                    css: {
                        'pre': {
                            backgroundColor: theme('colors.secondary.DEFAULT'),
                            color: theme('colors.foreground'),
                        },
                        'blockquote': {
                            borderLeftColor: theme('colors.border'),
                            color: theme('colors.muted.foreground'),
                        },
                        'a': {
                            color: theme('colors.primary.DEFAULT'),
                            '&:hover': {
                                color: theme('colors.primary.foreground'),
                            },
                        },
                    },
                },
            }),
        }
    },
    plugins: [require("tailwindcss-animate"), require('@tailwindcss/typography')],
};

export default config;