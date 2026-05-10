---
name: Academic Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#424750'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
  outline: '#737781'
  outline-variant: '#c3c6d1'
  surface-tint: '#335f99'
  primary: '#003466'
  on-primary: '#ffffff'
  primary-container: '#1a4b84'
  on-primary-container: '#93bcfc'
  inverse-primary: '#a6c8ff'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#313536'
  on-tertiary: '#ffffff'
  tertiary-container: '#484b4d'
  on-tertiary-container: '#b8bbbd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a6c8ff'
  on-primary-fixed: '#001c3b'
  on-primary-fixed-variant: '#144780'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#e0e3e5'
  tertiary-fixed-dim: '#c4c7c9'
  on-tertiary-fixed: '#191c1e'
  on-tertiary-fixed-variant: '#444749'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
typography:
  h1:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

This design system is built to balance the rigorous authority of traditional academia with the approachable, forward-thinking nature of AI-driven guidance. The brand personality is that of a "Brilliant Mentor"—highly knowledgeable and professional, yet encouraging and accessible to students and parents navigating the high-stakes world of admissions.

The visual style follows a **Corporate / Modern** aesthetic with a "Digital Academic" twist. It utilizes generous whitespace to reduce cognitive load during complex application processes, paired with sophisticated micro-interactions that signal intelligence. The interface avoids cold, clinical minimalism in favor of a warmer, human-centric approach that feels supportive rather than purely transactional.

## Colors

The palette is anchored by **Trustworthy Blue**, a deep, stable navy that evokes the heritage of Ivy League institutions. This is contrasted by **Academic Gold**, used sparingly as a "prestige" accent for achievements, calls to action, and premium AI insights. 

**Clean White** serves as the primary canvas, ensuring maximum readability. For data visualization and AI feedback, a secondary scale of softer blues and grays is utilized to prevent visual fatigue. Success states leverage a sophisticated emerald green, while informational highlights use a bright azure to distinguish AI-generated suggestions from static content.

## Typography

The design system exclusively utilizes **Inter** for its exceptional legibility on digital screens and its neutral, systematic feel. Headlines use tighter letter spacing and heavier weights to command authority, while body text uses a generous line height (1.6) to ensure long-form essay reviews and admission guides remain legible. Label styles are set in medium or semi-bold weights with slight tracking increases to ensure they remain distinct when used in data-heavy dashboards or small UI components.

## Layout & Spacing

This design system employs a **Fixed Grid** model for desktop views to maintain a professional, structured editorial feel, centered within a 1280px container. A 12-column system provides flexibility for dashboard layouts, where a 4-column sidebar often houses AI navigation and an 8-column main area displays content.

The spacing rhythm is based on a **4px baseline grid**. Vertical rhythm is strictly enforced using stack increments (8px, 16px, 32px) to ensure a sense of order and "intelligence" in the layout. Whitespace is treated as a functional element to separate disparate sections of a student's profile, preventing the interface from feeling cluttered or overwhelming.

## Elevation & Depth

To convey a modern and intelligent feel, depth is created through **Tonal Layers** and **Ambient Shadows**. Surfaces are rarely "flat"; instead, the system uses a tiered background approach where the lowest layer is a very light gray (Tertiary), and active workspaces are pure white cards.

Shadows are used sparingly and are highly diffused (large blur, low opacity) with a subtle Blue-Gray tint to avoid a "dirty" look. This creates a soft lifting effect that suggests the UI is composed of lightweight, modular sheets. AI-driven elements (like suggestion popovers) may use a subtle glow effect or a slightly higher elevation to draw immediate focus.

## Shapes

The shape language is **Rounded (Level 2)**. Standard components like input fields and buttons feature a 0.5rem radius, providing a friendly and accessible appearance that softens the inherent "seriousness" of university admissions. For larger containers like cards and modal dialogs, a 1rem radius is used to create a modern, "app-like" feel. Pill-shaped elements (Level 3) are reserved specifically for status chips (e.g., "In Progress," "Submitted") and AI tag suggestions to differentiate them from actionable buttons.

## Components

### Buttons
Primary buttons use the Trustworthy Blue with white text. Secondary buttons use a subtle Blue-Gray outline. High-priority AI actions (e.g., "Analyze Essay") may use a subtle gradient from Primary Blue to a slightly lighter variant to signal "power."

### Cards
Cards are the primary container. They feature a white background, a 1px soft border (#E2E8F0), and a low-intensity ambient shadow. This makes the system feel modular and organized.

### Input Fields
Inputs use a 1px border and a slightly recessed background color (#F1F5F9) when inactive, moving to a white background with a Trustworthy Blue border on focus. This "lit from within" effect guides the student's focus during form entry.

### AI Suggestion Chips
These are distinct from standard tags. They feature a light blue background and a small "sparkle" icon, using the Academic Gold for the icon to denote "value" and "insight."

### Progress Indicators
Steppers and progress bars use the Trustworthy Blue for completed states and a soft gray for upcoming steps. When a student reaches a milestone, the Gold accent is used for celebratory feedback.

### Dashboards
The dashboard uses a "modular tile" approach, allowing students to see their application status, AI feedback, and upcoming deadlines in a high-glanceability grid.