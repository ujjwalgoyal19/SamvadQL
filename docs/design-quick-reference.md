# SamvadQL Design Quick Reference

Quick visual reference inspired by VoidZero, OpenSpec, and Vite+ designs.

---

## Color Swatches

### Primary Palette

```
Background:    ████ #0a0a0a (Deep black)
Card:          ████ #1a1a1a (Slightly lighter)
Border:        ──── rgba(255,255,255,0.1) (Subtle line)
```

### Accent Colors

```
Primary Blue:  ████ #3b82f6 (Actions, links)
Purple:        ████ #8b5cf6 (AI features)
Cyan:          ████ #06b6d4 (Data flow)
Success:       ████ #10b981 (Success states)
```

### Text Colors

```
Primary:       ████ #ffffff (Headings)
Secondary:     ████ #a1a1aa (Body text)
Tertiary:      ████ #71717a (Muted text)
```

---

## Typography Scale

```
Hero:          60px / 3.75rem    "Next Generation SQL"
Section:       36px / 2.25rem    "Key Features"
Card Title:    24px / 1.5rem     "Natural Language Input"
Body:          16px / 1rem       "Transform questions into SQL"
Caption:       14px / 0.875rem   "Powered by AI"
```

**Font Stack:**

- Headings: Cabinet Grotesk / Inter (bold)
- Body: Inter (regular)
- Code: JetBrains Mono

---

## Spacing System (8px base)

```
4px   ▌ Tiny gaps
8px   ▌▌ Small spacing
16px  ▌▌▌▌ Default padding
24px  ▌▌▌▌▌▌ Section gaps
48px  ▌▌▌▌▌▌▌▌▌▌▌▌ Major sections
```

---

## Component Patterns

### Button Styles

```css
[Primary Button]   Blue background, white text, lift on hover
[Secondary]        Outlined, transparent, glow on hover
[Ghost]            Text only, background on hover
```

### Card Pattern

```
┌─────────────────────────────┐
│  [Icon]                     │
│                             │
│  Bold Title (20-24px)       │
│  Muted description text     │
│  (14-16px)                  │
│                             │
│  [Optional CTA] →           │
└─────────────────────────────┘

Background: #1a1a1a
Border: 1px solid rgba(255,255,255,0.1)
Border-radius: 12px
Padding: 32px
Hover: Lift 4px + glow
```

### Terminal Window

```
┌─ ● ● ● terminal ─────────────┐
│ $ samvad query               │
│ Show me top customers        │
│ ✓ Generated in 142ms         │
└──────────────────────────────┘

Background: Pure black (#000000)
Font: Monospace (JetBrains Mono)
Header: macOS-style traffic lights
```

### Code Block

```
┌─ query.sql ──────── SQL ─────┐
│  1  SELECT * FROM users      │
│  2  WHERE status = 'active'  │
│  3  LIMIT 10;                │
│                         [📋] │
└──────────────────────────────┘

Syntax highlighting: Night Owl theme
Copy button: Top-right corner
Line numbers: Optional
```

---

## Animation Timings

```
Fast (Hover):        200ms    Button hover, link effects
Normal (Transition): 300ms    Page transitions, modals
Slow (Reveal):       500ms    Fade-in on scroll
Typing:              50ms     Terminal typing effect
```

**Easing:** ease-in-out (default)

---

## Layout Grid

### Desktop (1280px+)

```
┌────────────────────────────────┐
│  Logo  [Nav Links]  [CTA]      │  ← Navbar (64px)
├────────────────────────────────┤
│                                │
│     [12-column grid]           │  ← Content
│                                │
└────────────────────────────────┘
│  Footer (4 columns)            │  ← Footer
└────────────────────────────────┘
```

### Mobile (< 768px)

```
┌──────────────┐
│  Logo  [☰]   │  ← Navbar
├──────────────┤
│              │
│  [Stack]     │  ← Single column
│              │
└──────────────┘
```

---

## Key Page Sections

### Homepage Structure

1. **Hero** - Full viewport, centered text, gradient headline
2. **Features** - 3-column grid, icon cards
3. **Demo** - Terminal/code showcase, interactive
4. **Stats** - Large numbers, 4-column layout
5. **Testimonials** - Cards or quotes
6. **CTA** - High contrast, prominent button
7. **Footer** - Multi-column links

### Dashboard Layout

```
┌─────────────────────────────────┐
│  Navbar                         │
├──────┬──────────────────────────┤
│ Side │  Main Workspace          │
│ bar  │  ┌──────────────────┐    │
│      │  │ Query Input      │    │
│ Hist │  └──────────────────┘    │
│ ory  │  ┌──────────────────┐    │
│      │  │ Results Table    │    │
│      │  └──────────────────┘    │
└──────┴──────────────────────────┘
```

---

## Icon Style Guide

**Style:** Outline/Stroke icons
**Weight:** 1.5-2px stroke
**Sizes:** 20px (small), 24px (default), 32px (large)

**Key Icons:**

- Database: 🗄️
- Query: 🔍
- AI: 🧠
- Success: ✓
- Error: ✗

---

## Interaction States

### Button States

```
Default:  [Get Started]
Hover:    [Get Started] ↑ (lift + glow)
Active:   [Get Started] ↓ (press down)
Disabled: [Get Started] (50% opacity)
```

### Input Focus

```
Default:  [____________]  Gray border
Focus:    [____________]  Blue border + glow
Error:    [____________]  Red border
Success:  [____________]  Green border
```

---

## Responsive Breakpoints

```
Mobile:       < 640px
Tablet:       640px - 1024px
Desktop:      1024px - 1280px
Large:        > 1280px
```

**Strategy:** Mobile-first, progressive enhancement

---

## Accessibility Checklist

- [ ] Color contrast ≥ 4.5:1 for text
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible (2px blue ring)
- [ ] ARIA labels on icons
- [ ] Alt text on images
- [ ] Reduced motion support
- [ ] Screen reader tested

---

## Performance Targets

```
First Contentful Paint:  < 1.5s
Time to Interactive:     < 3.0s
Lighthouse Score:        > 90
Bundle Size:             < 300kb (gzipped)
```

---

## Common Patterns

### Hero Headline

```tsx
<h1 className="text-6xl font-bold mb-6">
  <span className="gradient-text">Natural Language to SQL</span>
</h1>
```

### Feature Card

```tsx
<Card className="p-8 hover:-translate-y-1 transition-transform">
  <Icon className="w-12 h-12 text-accent-primary mb-4" />
  <h3 className="text-2xl font-semibold mb-2">Feature Title</h3>
  <p className="text-text-secondary">Description here</p>
</Card>
```

### Animated Stat

```tsx
<AnimatedMetric value={1247} suffix="ms" label="Avg Response Time" />
```

---

## Brand Voice

**Tone:** Professional, confident, helpful
**Style:** Clear, concise, technical but accessible
**Avoid:** Jargon, hype, complexity

**Good:** "Transform questions into SQL in milliseconds"
**Bad:** "Leverage our cutting-edge NLP paradigm"

---

## File Naming Conventions

```
Components:   PascalCase.tsx    (Button.tsx)
Pages:        PascalCase.tsx    (Dashboard.tsx)
Utilities:    camelCase.ts      (formatDate.ts)
Styles:       kebab-case.css    (global-styles.css)
```

---

## Git Commit Style

```
feat: Add terminal component
fix: Correct navbar z-index
style: Update button hover animation
docs: Add design system guide
refactor: Simplify card component
test: Add button component tests
```

---

## Quick Command Reference

```bash
# Install dependencies
pnpm install

# Dev server
pnpm dev

# Build
pnpm build

# Run tests
pnpm test

# Lint
pnpm lint

# Type check
pnpm type-check

# Storybook
pnpm storybook
```

---

## Helpful Links

- **Design System:** `/docs/design-system.md`
- **Implementation Plan:** `/docs/design-implementation-plan.md`
- **Component Library:** `http://localhost:6006` (Storybook)
- **Figma:** [Link to design files]
- **Slack Channel:** #design-system

---

## Need Help?

- **Design Questions:** @design-team
- **Implementation Issues:** @frontend-team
- **Accessibility:** @a11y-team

---

**Last Updated:** October 16, 2025
**Version:** 1.0
