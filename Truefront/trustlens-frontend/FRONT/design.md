---
name: Ethos Narrative
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e5'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf9'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e1e2ed'
  on-surface: '#191b23'
  on-surface-variant: '#434655'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#943700'
  on-tertiary: '#ffffff'
  tertiary-container: '#bc4800'
  on-tertiary-container: '#ffede6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ed'
typography:
  metric-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  metric-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
  heading-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  heading-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  heading-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 32px
---

## Brand & Style

The brand personality of this design system is rooted in **objectivity, precision, and transparency**. As a platform dedicated to fairness in AI recruitment, the interface must project an aura of unbiased authority while remaining highly accessible to HR professionals and data scientists.

The design style follows a **Corporate / Modern** aesthetic. It prioritizes functional clarity and systematic organization, utilizing generous whitespace to reduce cognitive load when interpreting complex algorithmic data. The emotional response should be one of "calm confidence"—reassuring the user that the underlying AI is being held to the highest ethical standards through clean lines, stable layouts, and professional finishes.

## Colors

The color palette is anchored by a high-trust **Primary Blue**, used for key actions and navigational anchors. **Secondary Slate** provides a neutral foundation for UI borders, icons, and secondary metadata, ensuring the interface feels grounded.

The functional palette (Success, Warning, Error) is critical for this design system, as it communicates the health of fairness metrics. These colors are applied with high saturation to ensure they are immediately scannable against the **Background** and **Card White** surfaces. The high-contrast **Text Dark** ensures peak legibility for all analytical content.

## Typography

This design system utilizes **Inter** exclusively to leverage its exceptional readability on digital screens and its neutral, systematic character. 

The typographic hierarchy distinguishes between **Metrics** (for high-level fairness scores) and **Content**. Metrics use heavy weights and large sizes to provide instant data visibility. Headings are semi-bold to establish a clear information architecture, while the 14px body size ensures dense information can be parsed without fatigue. Labels use a medium weight to maintain legibility at smaller scales in data-heavy tables and forms.

## Layout & Spacing

The layout philosophy follows a **fluid grid** model with a strict 8px spacing rhythm. This ensures horizontal and vertical consistency across complex dashboards. 

A 12-column grid is used for the main dashboard content, with 24px gutters providing enough breathing room between disparate data visualizations. For sidebar navigation, a fixed-width of 256px is recommended to preserve horizontal real estate for data tables. All internal card padding should default to 24px (lg) to maintain a premium, airy feel within bounded surfaces.

## Elevation & Depth

Visual hierarchy in this design system is achieved through **tonal layers** and **ambient shadows**. The primary background (#F8FAFC) acts as the lowest plane. Elements that require interaction or display critical data are elevated on "Card White" surfaces.

Shadows are used sparingly and should be highly diffused:
- **Low Elevation:** 0px 1px 3px rgba(30, 41, 59, 0.05) for standard cards.
- **Mid Elevation:** 0px 4px 6px rgba(30, 41, 59, 0.08) for hover states and dropdown menus.
- **High Elevation:** 0px 10px 15px rgba(30, 41, 59, 0.1) for modals and critical pop-overs.

Surfaces should use subtle 1px borders in Secondary Slate at 10% opacity to define edges even in low-contrast environments.

## Shapes

The shape language is defined by **rounded** geometry, utilizing an 8px (0.5rem) base radius. This softening of the UI helps to humanize the algorithmic nature of the platform.

- **Standard Elements:** 8px radius for buttons, input fields, and small cards.
- **Large Containers:** 16px (1rem) radius for primary dashboard sections.
- **Pill Elements:** Full rounding for status chips and tags to distinguish them from actionable buttons.

## Components

### Buttons
Primary buttons use the Brand Blue with white text. Secondary buttons use a Slate-100 background or a ghost-style outline. All buttons feature the 8px corner radius and internal padding of 12px vertical / 20px horizontal.

### Cards
Cards are the primary container for data. They must include a 1px border (#E2E8F0) and the "Low Elevation" shadow. Header sections within cards should be separated by a subtle horizontal rule.

### Data Visualizations
Fairness metrics should utilize progress bars, gauge charts, and heatmaps. Use Success Green for "Fair," Warning Yellow for "Bias Detected," and Error Red for "Critical Bias." Avoid using complex gradients; stick to flat, accessible fills.

### Inputs & Selection
Text inputs should have a 1px border (#CBD5E1) that shifts to Brand Blue on focus. Checkboxes and radio buttons use the Brand Blue for active states. Use **Lucide icons** (at 18px size) within inputs for search or filtering contexts to provide visual cues.

### Chips & Tags
Used for displaying active filters or applicant statuses. Chips should have a light tinted background of their respective status color (e.g., Success Green at 10% opacity) with high-contrast text for maximum readability.