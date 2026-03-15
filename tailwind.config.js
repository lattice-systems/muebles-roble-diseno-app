/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./node_modules/flowbite/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          softer: 'var(--color-brand-softer)',
          soft: 'var(--color-brand-soft)',
          DEFAULT: 'var(--color-brand)',
          medium: 'var(--color-brand-medium)',
          strong: 'var(--color-brand-strong)',
        },
        neutral: {
          primary: {
            soft: 'var(--color-neutral-primary-soft)',
            DEFAULT: 'var(--color-neutral-primary)',
            medium: 'var(--color-neutral-primary-medium)',
            strong: 'var(--color-neutral-primary-strong)',
          },
          secondary: {
            soft: 'var(--color-neutral-secondary-soft)',
            DEFAULT: 'var(--color-neutral-secondary)',
            medium: 'var(--color-neutral-secondary-medium)',
            strong: 'var(--color-neutral-secondary-strong)',
          },
          tertiary: {
            soft: 'var(--color-neutral-tertiary-soft)',
            DEFAULT: 'var(--color-neutral-tertiary)',
            medium: 'var(--color-neutral-tertiary-medium)',
          },
        },
        success: {
          soft: 'var(--color-success-soft)',
          medium: 'var(--color-success-medium)',
          DEFAULT: 'var(--color-success)',
          strong: 'var(--color-success-strong)',
        },
        danger: {
          soft: 'var(--color-danger-soft)',
          medium: 'var(--color-danger-medium)',
          DEFAULT: 'var(--color-danger)',
          strong: 'var(--color-danger-strong)',
        },
        warning: {
          soft: 'var(--color-warning-soft)',
          medium: 'var(--color-warning-medium)',
          DEFAULT: 'var(--color-warning)',
          strong: 'var(--color-warning-strong)',
        },
        dark: {
          soft: 'var(--color-dark-soft)',
          DEFAULT: 'var(--color-dark)',
          strong: 'var(--color-dark-strong)',
        },
        body: {
          DEFAULT: 'var(--color-body)',
          subtle: 'var(--color-body-subtle)',
        },
        heading: 'var(--color-heading)',
        disabled: 'var(--color-disabled)',
        default: {
          DEFAULT: 'var(--color-default)',
          medium: 'var(--color-default-medium)',
          strong: 'var(--color-default-strong)',
        },
        fg: {
          success: { strong: 'var(--color-fg-success-strong)' },
          danger: { strong: 'var(--color-fg-danger-strong)' },
          warning: 'var(--color-fg-warning)',
          brand: { 
            DEFAULT: 'var(--color-fg-brand)',
            strong: 'var(--color-fg-brand-strong)'
          },
          disabled: 'var(--color-fg-disabled)',
          yellow: 'var(--color-fg-yellow)'
        }
      },
      borderRadius: {
        base: 'var(--radius-base, 0.5rem)',
      }
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
