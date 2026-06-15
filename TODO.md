# Dashboard Layout & Spacing Improvements - TODO

## Task List
- [x] 1. Update DashboardPage.module.css - Increase section gaps and make width responsive
- [x] 2. Update KpisRow.module.css - Add max-width constraint and improve grid breakpoints
- [x] 3. Update JumpBackInRow.module.css - Add breathing room to section header and cards
- [x] 4. Update LibraryGrid.module.css - Improve spacing consistency
- [x] 5. Update WelcomeHeader.module.css - Add responsive constraints

## Completed Changes Summary

### 1. DashboardPage.module.css
- Increased gap from `var(--space-2)` (8px) to `var(--space-6)` (32px)
- Added max-width: 1400px with margin: 0 auto
- Removed forced 90% width constraint

### 2. KpisRow.module.css
- Added `.row-container` wrapper with proper spacing
- Increased minmax from 240px to 260px for better card sizing
- Added max-width: 1200px to prevent over-stretching
- Reduced padding from var(--space-6) to var(--space-5)

### 3. JumpBackInRow.module.css
- Increased gap from var(--space-1) (4px) to var(--space-4) (16px) between cards
- Added proper vertical alignment to header
- Increased padding from var(--space-1) to var(--space-3)

### 4. LibraryGrid.module.css
- Increased gap between elements
- Improved header responsive wrapping
- Added flex-wrap and gap to header for mobile responsiveness

### 5. WelcomeHeader.module.css
- Added flex-wrap and gap for responsive behavior
- Added max-width: 400px to search section to prevent unbalanced whitespace
- Reduced min-width from 320px to 280px

## Result
- Better visual hierarchy between sections
- More consistent spacing throughout the dashboard
- Improved responsiveness on smaller viewports
- KPI cards no longer look like stretched banners
