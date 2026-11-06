---
name: Bolti Slip
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf4'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dde9ff'
  surface-container-highest: '#d5e3fd'
  on-surface: '#0d1c2f'
  on-surface-variant: '#464555'
  inverse-surface: '#233144'
  inverse-on-surface: '#ebf1ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#684000'
  on-tertiary: '#ffffff'
  tertiary-container: '#885500'
  on-tertiary-container: '#ffd4a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f8f9ff'
  on-background: '#0d1c2f'
  surface-variant: '#d5e3fd'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-xs:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system is structured for Indian electronics and appliance repair shop owners who need speed, tactile clarity, and distraction-free voice input. The tone is utilitarian, dependable, and uncluttered. It mirrors the physical efficiency of a paper carbon-copy repair slip, elevated by modern digital precision.

### Aesthetic Style
- **Corporate & Modern Utility**: High legibility, crisp 1px borders, quiet structural whites, and functional status colors.
- **Strict Guidelines**:
  - No emojis anywhere in the interface (e.g., avoid waving hands, decorative icons disguised as emojis).
  - No gradients, glow states, or glassmorphism.
  - Light mode only; no dark mode toggle or high-contrast neon variants.
  - Zero placeholder Latin text (`Lorem Ipsum`); all empty states, samples, and mock copy must reflect realistic shop context (e.g., fan motor rewind, cracked LED screen, PCB board repair).
  - Strictly at most one primary action button per screen to maintain a single focal action path (typically "Record Slip" or "Save Ticket").

## Colors

The palette balances a clean off-white background with a focused indigo accent and semantic color tokens for ticketing states.

### Core Application Surfaces
- **Canvas / Page Background**: `#F8FAFC`
- **Surface / Card Background**: `#FFFFFF`
- **Border / Divider**: `#E2E8F0` (solid 1px)

### Text & Typography
- **Headings & Primary Titles**: `#0F172A` (deep navy)
- **Body & Default Labels**: `#334155` (slate)
- **Muted, Subtext, & Meta Details**: `#64748B` (slate muted)

### Primary Accent
- **Primary Base**: `#4F46E5` (reserved strictly for the main action button, active navigation states, and text links)
- **Primary Hover**: `#4338CA`
- **Primary Tint / Soft Fill**: `#EEF2FF`

### Status Badges (Pill Fill, Text, and Dot)
- **Pending**: Text `#B45309`, Background `#FEF3C7`, Dot `#D97706`
- **In Progress**: Text `#1D4ED8`, Background `#DBEAFE`, Dot `#2563EB`
- **Completed**: Text `#047857`, Background `#D1FAE5`, Dot `#059669`

### Attention & Missing-Information Alert
- **Missing Highlight Fill**: `#FFFBEB`
- **Missing Highlight Border**: `#F59E0B`
- **Missing Label / Text**: `#B45309`

### Formatting Standards
- **Currency**: Indian Rupee symbol `₹` with standard Indian numbering comma separation (e.g., `₹1,200`, `₹45,500`).
- **Dates**: Day Month Year format without leading zeros on double digits (e.g., `31 Oct 2026`).

## Typography

The design system relies on `Inter` as the primary Latin and numeric typeface. For bilingual Devanagari text rendering (customer notes, voice transcriptions in Hindi/Marathi), `Noto Sans Devanagari` serves as the immediate font fallback.

### Type Scale Roles
- **Page Titles (`headline-lg`)**: `28px / 600`, color `#0F172A`. Used strictly once at the top of main screens.
- **Section Titles (`headline-sm`)**: `18px / 600`, color `#0F172A`. Used for card headers, modal titles, and section splits.
- **Standard Body (`body-md`)**: `14px / 400`, color `#334155`. Default across all slip details, notes, and transcript logs.
- **Table Headers & Overlines (`label-sm`)**: `12px / 600`, uppercase, letter spacing `0.05em`, color `#64748B`.
- **Badge & Metric Labels (`label-xs`)**: `11px / 600`, uppercase or tabular numeric data.

## Layout & Spacing

The interface uses an 8px grid system structured around a fixed navigation sidebar and a fluid dashboard workspace.

### Structural Frame
- **Sidebar**: Fixed width `248px`, full height, pinned to the left. Border-right: 1px solid `#E2E8F0`.
- **Top Header**: Height `64px`, sticky, white background, bottom border 1px solid `#E2E8F0`. Contains the current view title on the left, and search bar, notification bell, and shop avatar on the right.
- **Main Canvas**: Page padding of `32px` (`2rem`) surrounding the content workspace. Background: `#F8FAFC`.

### Spatial Rhythm
- **Card-to-Card Grid Gap**: `24px` (`1.5rem`).
- **Internal Card Padding**: `20px` to `24px`.
- **Stack Gaps (Form fields & lists)**: `16px` (`1rem`).
- **Micro Gaps (Icons, label pairings, badges)**: `8px` (`0.5rem`).

## Elevation & Depth

Visual hierarchy is maintained via clean planar surfaces and low-contrast borders rather than deep elevation tiers.

### Depth Hierarchy
- **Canvas**: Flat baseline `#F8FAFC`.
- **Cards & Data Tables**: Surface `#FFFFFF` layered with a crisp `1px solid #E2E8F0` and an ultra-subtle ambient shadow:
  - `box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.06);`
- **Modals & Flyouts**: Elevated surface `#FFFFFF`, border `1px solid #E2E8F0`, with `box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)`.
- **Interactive State**: Active and focused elements do not cast dramatic drop shadows; focus states rely on an outline: `2px solid #4F46E5` with `2px offset`.

## Shapes

The design uses balanced, modern geometric radii to maintain approachable boundaries without appearing toy-like.

### Radii Tokens
- **Cards & Data Panels**: `16px` corner radius.
- **Buttons, Form Inputs, & Modals**: `10px` corner radius.
- **Status Badges & Voice Indicator Pills**: Full pill radius (`9999px`).
- **Sidebar Identity Mark**: `10px` rounded-square container housing the microphone icon.

## Components

### Buttons
- **Primary Button**: Strictly one per page. Indigo `#4F46E5` background, `#FFFFFF` text, radius `10px`, height `40px`, padding `0 16px`. Hover state: `#4338CA`. Active state: `#3730A3`.
- **Secondary Button**: `#FFFFFF` background, border `1px solid #E2E8F0`, `#334155` text, radius `10px`. Hover: `#F8FAFC` background with border `#CBD5E1`.
- **Ghost Button**: Transparent background, `#64748B` text, radius `10px`. Hover: `#F1F5F9` background, `#0F172A` text.

### Status Badges
- Constructed as horizontal pills with a height of `24px`, padding `0 10px`, radius `9999px`.
- Composed of a `6px` circular solid dot, a `6px` gap, and uppercase `11px` bold text (`label-xs`).
  - **Pending**: Dot `#D97706`, text `#B45309`, background `#FEF3C7`.
  - **In Progress**: Dot `#2563EB`, text `#1D4ED8`, background `#DBEAFE`.
  - **Completed**: Dot `#059669`, text `#047857`, background `#D1FAE5`.

### Missing-Info Alert Containers
- Used when voice parsing fails to extract required ticket data (e.g., customer phone number, advance payment, device serial).
- **Styling**: Background `#FFFBEB`, border `1px solid #F59E0B`, radius `10px`, padding `12px 16px`.
- Includes an inline badge with text "Missing" in `#B45309` (`label-xs`), paired with concise instructional text indicating what detail to supply.

### Form Inputs & Textareas
- Height `40px` (inputs), radius `10px`, border `1px solid #E2E8F0`, background `#FFFFFF`.
- Placeholder color `#94A3B8`, active text `#0F172A`.
- Focus state: border color `#4F46E5`, box-shadow `0 0 0 1px #4F46E5`.

### Navigation Sidebar
- Width `248px`, background `#FFFFFF`, border-right `1px solid #E2E8F0`.
- **Header**: Indigo rounded-square mic icon (`36px × 36px`, background `#4F46E5`, white clean line mic glyph) paired with the "Bolti Slip" wordmark (`16px / 600 #0F172A`).
- **Nav Links**: Height `40px`, padding `0 12px`, radius `8px`, font size `14px / 500`. Simple neutral stroke icons.
  - Default: Text `#475569`, transparent background.
  - Active: Text `#4F46E5`, background `#EEF2FF`, icon stroke `#4F46E5`.
- **Footer**: Shop profile snippet with avatar initial circle (`32px`, `#F1F5F9`), title "Sharma Electronics", subtitle "Pune" in `#64748B`.

### Voice Input Bar
- Floating or embedded panel dedicated to voice recording.
- Includes a dedicated record button (`44px × 44px` circle or `10px` rounded square in primary `#4F46E5`), real-time transcript preview in `14px #334155`, and clean line mic indicator.