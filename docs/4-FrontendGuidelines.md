# Frontend Design Guidelines

This document outlines the design guidelines for the Facial Recognition Processing Pipeline application. These guidelines ensure a consistent, accessible, and modern user experience across the application built with React, Next.js, and shadcn/ui.

## Core Technologies

- **Framework**: Next.js 14+ (App Router)
- **Library**: React 18+
- **UI Components**: shadcn/ui (built on Radix UI)
- **Styling**: Tailwind CSS
- **State Management**: React Context + Hooks
- **Data Fetching**: React Query (for GraphQL)

## Typography

### Font Family

We use the Inter font family as our primary typeface, which is the default in shadcn/ui, providing excellent readability at all sizes and a modern appearance.

- **Primary Font**: Inter
- **Fallback Fonts**: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
- **Monospace Font**: JetBrains Mono (for technical information, code, and IDs)

### Font Sizes

We follow Tailwind CSS's type scale, which aligns well with shadcn/ui components:

| Element | Tailwind Class | Size | Weight | Line Height |
|---------|---------------|------|--------|-------------|
| Display | text-4xl | 36px | 700 | 1.2 |
| H1 | text-3xl | 30px | 700 | 1.2 |
| H2 | text-2xl | 24px | 600 | 1.3 |
| H3 | text-xl | 20px | 600 | 1.4 |
| H4 | text-lg | 18px | 600 | 1.4 |
| Body | text-base | 16px | 400 | 1.5 |
| Small/Caption | text-sm | 14px | 400 | 1.5 |
| Tiny | text-xs | 12px | 400 | 1.5 |

### Font Weights

Using Tailwind CSS classes:
- **Regular**: font-normal (400)
- **Medium**: font-medium (500)
- **Semibold**: font-semibold (600)
- **Bold**: font-bold (700)

## Color Palette

Our color system leverages shadcn/ui's theming capabilities with Tailwind CSS, focusing on clear status indicators for the processing pipeline.

### Base Colors

Using shadcn/ui's variables to maintain consistent theming across light and dark modes:

| Color | CSS Variable | Light Mode | Dark Mode | Usage |
|-------|-------------|------------|-----------|-------|
| Background | --background | #FFFFFF | #09090B | Main background |
| Foreground | --foreground | #09090B | #FFFFFF | Text on background |
| Card | --card | #FFFFFF | #111112 | Cards, panels, dialogs |
| Card Foreground | --card-foreground | #09090B | #FFFFFF | Text on cards |
| Popover | --popover | #FFFFFF | #111112 | Tooltips, dropdowns |
| Popover Foreground | --popover-foreground | #09090B | #FFFFFF | Text on popovers |
| Primary | --primary | #0F172A | #FFFFFF | Primary elements |
| Primary Foreground | --primary-foreground | #FFFFFF | #0F172A | Text on primary elements |
| Secondary | --secondary | #F1F5F9 | #1E293B | Secondary elements |
| Secondary Foreground | --secondary-foreground | #0F172A | #FFFFFF | Text on secondary elements |
| Muted | --muted | #F1F5F9 | #1E293B | Subdued backgrounds |
| Muted Foreground | --muted-foreground | #64748B | #94A3B8 | Subdued text |
| Accent | --accent | #F1F5F9 | #1E293B | Highlighted elements |
| Accent Foreground | --accent-foreground | #0F172A | #FFFFFF | Text on accent elements |
| Destructive | --destructive | #EF4444 | #EF4444 | Error indicators |
| Destructive Foreground | --destructive-foreground | #FFFFFF | #FFFFFF | Text on error elements |
| Border | --border | #E2E8F0 | #1E293B | Borders |
| Input | --input | #E2E8F0 | #1E293B | Form input borders |
| Ring | --ring | #94A3B8 | #94A3B8 | Focus rings |

### Status Colors

Extending the shadcn/ui theme with application-specific colors:

| Status | Tailwind Class | Light Mode | Dark Mode | Usage |
|--------|---------------|------------|-----------|-------|
| Success | text-green-500 | #10B981 | #10B981 | Completed processes, matched faces |
| Warning | text-amber-500 | #F59E0B | #F59E0B | Pending processes, attention needed |
| Error | text-destructive | #EF4444 | #EF4444 | Failed processes, unmatched faces |
| Info | text-blue-500 | #3B82F6 | #3B82F6 | Information, processing in progress |
| Neutral | text-muted-foreground | #64748B | #94A3B8 | Disabled states, no action needed |

### Visual Indicators for Face Recognition

| Indicator | Color | Usage |
|-----------|-------|-------|
| Matched Face | border-green-500 | Green bounding box around matched faces |
| Unmatched Face | border-red-500 | Red bounding box around unmatched faces |
| Processing | border-blue-500 | Blue bounding box for faces being processed |

## Spacing and Layout

We follow Tailwind CSS spacing scale which integrates perfectly with shadcn/ui components.

### Spacing Scale

Using Tailwind CSS spacing classes:

| Tailwind Class | Value | Usage |
|---------------|-------|-------|
| p-1, m-1 | 0.25rem (4px) | Minimal spacing between related elements |
| p-2, m-2 | 0.5rem (8px) | Default inner spacing (padding) |
| p-4, m-4 | 1rem (16px) | Standard spacing between elements |
| p-6, m-6 | 1.5rem (24px) | Spacing between component groups |
| p-8, m-8 | 2rem (32px) | Section spacing |
| p-12, m-12 | 3rem (48px) | Major section divisions |
| p-16, m-16 | 4rem (64px) | Page-level spacing |

### Layout Composition

- Use Next.js App Router for page layouts and routing
- Implement responsive designs using Tailwind CSS utility classes
- Follow a composition-based approach with reusable components

### Container Widths

Using Tailwind CSS container classes:

| Screen Size | Max Width | Class |
|-------------|-----------|-------|
| Default | 100% | container |
| sm (640px+) | 640px | container |
| md (768px+) | 768px | container |
| lg (1024px+) | 1024px | container |
| xl (1280px+) | 1280px | container |
| 2xl (1536px+) | 1440px | container |

### Component Spacing

- Cards and panels: p-6 (24px padding)
- Form groups: space-y-4 (16px spacing between items)
- Related buttons: space-x-2 (8px spacing)
- Section headings: mb-6 (24px bottom margin)
- List items: space-y-3 (12px spacing)

### Responsive Breakpoints

Using Tailwind CSS breakpoints:

| Breakpoint | Width | Description |
|------------|-------|-------------|
| Default | < 640px | Mobile devices |
| sm | ≥ 640px | Small tablets |
| md | ≥ 768px | Tablets |
| lg | ≥ 1024px | Desktops |
| xl | ≥ 1280px | Large desktops |
| 2xl | ≥ 1536px | Extra large screens |

## UI Components

We use shadcn/ui components for a modern, cohesive design that works seamlessly with React and Next.js.

### Component Installation

Install shadcn/ui components as needed using the CLI:

```bash
npx shadcn-ui@latest add [component-name]
```

### Key Components

- **Buttons**:
  - Primary: `<Button>` (default variant)
  - Secondary: `<Button variant="secondary">`
  - Outline: `<Button variant="outline">`
  - Ghost: `<Button variant="ghost">`
  - Destructive: `<Button variant="destructive">`
  - Link: `<Button variant="link">`

- **Cards**:
  - Use the `<Card>` component with `<CardHeader>`, `<CardTitle>`, `<CardDescription>`, `<CardContent>`, and `<CardFooter>`
  - For project cards, add hover effects using Tailwind's `hover:` classes

- **Data Display**:
  - Tables: Use the `<Table>` component for structured data
  - For the results view, use `<DataTable>` with filtering capabilities
  - Implement virtualized lists for consent profiles using `react-virtuoso`

- **Forms**:
  - Use shadcn/ui form components with React Hook Form
  - Text inputs: `<Input>`
  - Select menus: `<Select>`
  - Checkboxes: `<Checkbox>`
  - Radio groups: `<RadioGroup>` and `<RadioGroupItem>`
  - Toggle switches: `<Switch>`

- **Dialogs & Modals**:
  - Use `<Dialog>` for standard modals
  - Use `<AlertDialog>` for confirmations
  - Use `<Drawer>` for mobile-friendly side panels

- **Navigation**:
  - Breadcrumbs: Custom component using Next.js Link
  - Tabs: `<Tabs>` with `<TabsList>`, `<TabsTrigger>`, and `<TabsContent>`
  - Sidebar: Custom component with collapsible sections

- **Feedback**:
  - Alerts: `<Alert>` with variants for different statuses
  - Toast notifications: `<Toaster>` and `<Toast>` for temporary feedback
  - Progress indicators: `<Progress>` for deterministic processes

- **Data Visualization**:
  - Use Recharts for charts and graphs
  - Implement custom face detection visualization with React and HTML Canvas

## Icons

We use a consistent icon system that integrates well with shadcn/ui and React components.

### Icon Library

- **Primary Icons**: Lucide React
- **Installation**: `npm install lucide-react`
- **Format**: React components (SVG-based)

### Icon Usage

```jsx
import { Camera, Upload, Play } from "lucide-react";

// In component
<Button>
  <Upload className="mr-2 h-4 w-4" />
  Upload
</Button>
```

### Icon Sizes

Use Tailwind classes to maintain consistent sizing:

| Usage | Tailwind Classes | Dimensions |
|-------|-----------------|------------|
| Inline text | h-4 w-4 | 16×16px |
| Small buttons | h-5 w-5 | 20×20px |
| Standard UI | h-6 w-6 | 24×24px |
| Featured elements | h-8 w-8 | 32×32px |
| Empty states | h-12 w-12 | 48×48px |

### Icon Color

Icons inherit text color by default. Use Tailwind text color classes to change icon colors:

```jsx
<Camera className="text-primary" />
<Upload className="text-muted-foreground" />
<Play className="text-green-500" />
```

## Animation and Transitions

Use subtle animations to enhance the user experience, leveraging Framer Motion for React components.

### Animation Library

- **Primary Library**: Framer Motion
- **Installation**: `npm install framer-motion`

### Common Animations

```jsx
import { motion } from "framer-motion";

// Fade in component
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.3 }}
>
  Content
</motion.div>
```

### Transition Guidelines

- Page transitions: Simple fade (duration: 0.3s)
- Modal/dialog: Scale + fade (duration: 0.2s)
- List items: Staggered fade (stagger: 0.05s, item duration: 0.15s)
- Hover states: Quick ease (duration: 0.1s)
- Loading indicators: Smooth looping animations

## Application-Specific Components

### Watch Folder Status Indicator

```jsx
<Badge 
  variant={
    status === 'idle' ? 'secondary' : 
    status === 'watching' ? 'default' : 
    'destructive'
  }
>
  {status === 'idle' ? 'Idle' : 
   status === 'watching' ? 'Watching' : 
   'Error'}
</Badge>
```

### Processing Status Progress

```jsx
<div className="space-y-2">
  <div className="flex justify-between">
    <span className="text-sm font-medium">Processing Clip: {clipName}</span>
    <span className="text-sm text-muted-foreground">{processedFrames}/{totalFrames}</span>
  </div>
  <Progress value={(processedFrames/totalFrames) * 100} />
</div>
```

### Face Detection Visualization

Custom component for rendering face detection results on images, with proper bounding boxes and status indicators.

## Accessibility

The application must be accessible to all users, following these guidelines:

- Use semantic HTML throughout the application
- Ensure all interactive elements are keyboard accessible
- Implement proper focus management
- Provide appropriate ARIA attributes when necessary
- Maintain color contrast ratios of at least 4.5:1 for text
- Support both light and dark modes
- Test with screen readers

## Dark Mode Implementation

shadcn/ui has built-in dark mode support. Implement theme switching using:

```jsx
// In layout component
"use client"

import { ThemeProvider } from "next-themes"

export function Providers({ children }) {
  return (
    <ThemeProvider 
      attribute="class" 
      defaultTheme="system" 
      enableSystem
    >
      {children}
    </ThemeProvider>
  )
}
```

Use the `useTheme` hook to toggle between themes:

```jsx
import { useTheme } from "next-themes"

function ThemeToggle() {
  const { setTheme, theme } = useTheme()
  
  return (
    <Button 
      variant="ghost" 
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </Button>
  )
}
```

## File Organization

```
src/
├── app/
│   ├── (dashboard)/        # Main application routes
│   │   ├── page.tsx        # Projects dashboard
│   │   ├── layout.tsx      # Dashboard layout
│   │   ├── [projectId]/    # Project details routes
│   │   │   ├── page.tsx
│   │   │   ├── [cardId]/   # Card details routes
│   │   │   │   ├── page.tsx
│   │   │   │   └── results/
│   │   │   └── ...
│   ├── api/                # API routes
│   └── ...
├── components/
│   ├── ui/                 # shadcn components
│   ├── cards/              # Project and card components
│   ├── consent/            # Consent profile components
│   ├── processing/         # Processing related components
│   ├── results/            # Results display components
│   └── layout/             # Layout components
├── hooks/                  # Custom React hooks
├── lib/                    # Utility functions
├── store/                  # State management
└── types/                  # TypeScript types
```

## Best Practices

- Use TypeScript for all components and functions
- Follow a component-first approach to UI development
- Implement responsive designs using Tailwind's utility classes
- Leverage React Server Components where possible for better performance
- Use Client Components only when necessary (interactivity, hooks, etc.)
- Keep components focused and maintainable
- Follow the principle of composition over inheritance
- Optimize image handling with Next.js Image component
- Implement proper loading states for all async operations