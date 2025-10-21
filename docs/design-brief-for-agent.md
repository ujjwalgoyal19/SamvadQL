# **SamvadQL Design Brief**

**Date:** October 17, 2025
**Version:** 1.0
**For:** Design Agent Implementation
**Project:** SamvadQL - Conversational Text-to-SQL Platform

---

## **Project Overview**

SamvadQL is a **conversational AI-powered Text-to-SQL platform** that enables data analysts to interact with databases through natural language. Think of it as "ChatGPT meets DataGrip" - an intelligent assistant that understands your data questions and generates SQL queries through conversation.

**Target Users:** Data analysts, business analysts, developers, data scientists
**Primary Use Case:** Convert natural language questions into executable SQL queries
**Key Differentiator:** Conversational interface with transparent AI reasoning

---

## **Design Philosophy & Core Principles**

### **1. Conversational-First, Not Form-Based**

- **Every interaction is a conversation** - no rigid workflows or step-by-step wizards
- The AI agent thinks out loud, showing its reasoning process transparently
- Users describe what they want, the agent asks clarifying questions when needed
- Fluid, adaptive experience that feels like pair programming with an intelligent colleague

### **2. Developer & Data Analyst Focused**

- Professional, technical aesthetic
- Code-centric visual language
- Clean, minimal, distraction-free
- Trust and credibility through precision

### **3. Dark-First, Enterprise-Ready**

- Deep black backgrounds (#0a0a0a) with subtle contrast layers
- High-contrast text for readability
- Futuristic but not gimmicky
- Performance-oriented with smooth 60fps animations

---

## **Visual Language & Aesthetics**

### **Color Palette**

#### **Backgrounds (Dark Theme Primary):**

```css
--bg-primary: #0a0a0a; /* Deep black - main background */
--bg-secondary: #141414; /* Slightly lighter black */
--bg-tertiary: #1a1a1a; /* Cards/panels */
--bg-elevated: #242424; /* Hover states, modals */
```

#### **Accent Colors:**

```css
--accent-primary: #3b82f6; /* Primary Blue - SQL/Database theme */
--accent-secondary: #8b5cf6; /* Purple - AI/Intelligence theme */
--accent-tertiary: #06b6d4; /* Cyan - Data flow, connections */
--accent-success: #10b981; /* Green - Success states */
--accent-warning: #f59e0b; /* Orange - Warnings */
--accent-error: #ef4444; /* Red - Errors */
```

#### **Gradients:**

```css
--gradient-hero: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
--gradient-accent: linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%);
--gradient-card: linear-gradient(
  180deg,
  rgba(59, 130, 246, 0.1) 0%,
  transparent 100%
);
```

#### **Text Colors:**

```css
--text-primary: #ffffff; /* High contrast text */
--text-secondary: #a1a1aa; /* Muted text */
--text-tertiary: #71717a; /* Very muted text */
--text-inverse: #0a0a0a; /* Text on light backgrounds */
```

#### **Borders:**

```css
--border-primary: rgba(255, 255, 255, 0.1); /* Subtle borders */
--border-secondary: rgba(255, 255, 255, 0.05); /* Very subtle */
--border-accent: rgba(59, 130, 246, 0.3); /* Accent borders */
```

---

### **Typography**

#### **Font Families:**

- **Primary:** Inter (Clean, modern sans-serif for UI)
- **Monospace:** JetBrains Mono or Fira Code (For code, SQL, terminal output)
- **Fallback:** -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui

#### **Type Scale:**

```css
/* Display */
--text-display: 72px / 5rem; /* Bold 900 - Hero headlines */

/* Headings */
--text-h1: 48px / 3rem; /* Bold 700 */
--text-h2: 36px / 2.25rem; /* Semibold 600 */
--text-h3: 24px / 1.5rem; /* Medium 500 */
--text-h4: 20px / 1.25rem; /* Medium 500 */

/* Body */
--text-body-large: 18px / 1.125rem; /* Regular 400 */
--text-body: 16px / 1rem; /* Regular 400 */
--text-body-small: 14px / 0.875rem; /* Regular 400 */
--text-caption: 12px / 0.75rem; /* Medium 500 */
```

#### **Line Heights:**

- **Headings:** 1.2
- **Body:** 1.6
- **Code:** 1.5

#### **Letter Spacing:**

- **Headings:** -0.02em (tight)
- **Body:** 0 (normal)
- **Caps/Labels:** 0.05em (slightly loose)

---

## **Layout & Interface Structure**

### **Two Primary Modes:**

#### **1. Workspace Mode** (Power User / Explorer View)

**Purpose:** Multi-tasking, exploration, team collaboration
**Users:** Power users, data analysts working on complex problems

**Layout Structure:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Logo | [Focus Mode ⇆] | DB: production_v2 ▼ | Team ▼ | ⚙️ | 👤 │
├──────────────┬──────────────────────────────────┬───────────────────┤
│              │                                  │                   │
│ LEFT NAV     │  MAIN WORKSPACE (TABBED)         │  RIGHT INSPECTOR  │
│ (240px)      │  (Flexible width)                │  (320px)          │
│              │                                  │  (Collapsible)    │
│              │                                  │                   │
│ 📂 Chats     │  ┌─────────────────────────────┐│  ┌──────────────┐ │
│  🟢 Active   │  │ Chat: Sales Q3 Analysis     ││  │ 🔍 Search    │ │
│  • Sales Q3  │  │ ────────────────────────────││  │ [Search...]  │ │
│  • User Seg  │  │                             ││  └──────────────┘ │
│  • Churn     │  │ [Conversation Thread]       ││                   │
│              │  │                             ││  📊 Schema        │
│ 💾 Saved     │  │ User: Show me revenue...    ││   └─ 📁 Tables   │
│  • Reports   │  │                             ││      ├─ customers │
│  • KPIs      │  │ Agent: [Thinking...]        ││      ├─ orders   │
│              │  │ ━━━━━━━━━━━━━━━━━━━━━━━━━  ││      ├─ products │
│ 📚 History   │  │ 💭 Analyzed question        ││      └─ ...      │
│  Today       │  │ 🔍 Found tables             ││                   │
│  Yesterday   │  │ 📝 Generated query          ││  🔖 Query Info   │
│  Last week   │  │ ✅ Validated                ││  Status: ✓ Valid │
│              │  │ ━━━━━━━━━━━━━━━━━━━━━━━━━  ││  Rows: ~1,250    │
│ 🗄️ Databases  │  │                             ││  Time: 0.34s     │
│  • prod_v2   │  │ Agent: Here's your query:   ││  [View Plan]     │
│  • staging   │  │                             ││                   │
│  • analytics │  │ [SQL Code Artifact]         ││  💡 Suggestions  │
│              │  │ [Results Table]             ││  • Add date      │
│ 👥 Team      │  │                             ││  • Group by      │
│  • Shared    │  │ User: Add time breakdown... ││  • Export        │
│  • Mentions  │  │                             ││                   │
│              │  └─────────────────────────────┘│                   │
│              │                                  │                   │
│              │  ┌───────────────────────────┐  │                   │
│              │  │ 💬 Type your message...   │  │                   │
│              │  │ [📎] [🎤] [⚡]      [Send]│  │                   │
│              │  └───────────────────────────┘  │                   │
│              │                                  │                   │
│              │  Tab Bar: [Sales Q3*] [User Seg] [+New]             │
└──────────────┴──────────────────────────────────┴───────────────────┘
```

**Key Features:**

**Left Sidebar (240px):**

- **Chat Organization** - All conversations, active indicator
- **Saved Queries** - Templates and frequently used queries
- **History** - Time-based grouping (Today, Yesterday, Last week)
- **Databases** - Quick switcher for multiple connections
- **Team** - Shared chats, mentions, collaboration

**Main Workspace (Flexible):**

- **Tabbed Interface** - Like VS Code, multiple chats open
- **Conversation Thread** - Full history with context
- **Embedded Artifacts** - SQL code, results, visualizations inline
- **Bottom Input** - Always visible, never scrolls away
- **Smart Suggestions** - Context-aware quick actions

**Right Inspector (320px, Collapsible):**

- **Search** - Quick schema/table lookup
- **Schema Browser** - Tree view of tables/columns
- **Query Details** - Real-time validation, performance estimates
- **Suggestions** - AI-powered next steps

---

#### **2. Focus Mode** (Quick Query / Single Task View)

**Purpose:** Distraction-free, single query focus
**Users:** Quick ad-hoc queries, simple questions

**Layout Structure:**

```
┌─────────────────────────────────────────────────────────────┐
│ Minimal Header: Logo | [⇆ Workspace] | DB ▼ | Profile      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                                                             │
│                   CENTERED CONVERSATION                     │
│                   (Max width: 800px)                        │
│                                                             │
│              User: Show me top customers                    │
│                                                             │
│              Agent: [Thinking Process]                      │
│              ━━━━━━━━━━━━━━━━━━━━━━                       │
│              💭 Analyzed • 🔍 Found • ✅ Valid             │
│              ━━━━━━━━━━━━━━━━━━━━━━                       │
│                                                             │
│              [SQL Code Artifact Card]                       │
│              [Results Table Card]                           │
│                                                             │
│              ┌─────────────────────────────────┐           │
│              │ 💬 Ask me anything...           │           │
│              │ [Type here...]          [Send] │           │
│              └─────────────────────────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**

- Clean, centered content (ChatGPT-style)
- No sidebars, minimal distractions
- Focus on conversation flow
- Quick toggle to Workspace Mode for complexity

---

## **Key UI Components & Specifications**

### **1. Chat Message Bubbles**

#### **User Message:**

```
┌─────────────────────────────────────────────────┐
│                                        [Avatar] │
│                       Show me revenue by region │
│                          for Q3 2025, broken    │
│                             down by month       │
│                                                 │
│                               10:34 AM • Today  │
└─────────────────────────────────────────────────┘
```

**Specs:**

- Background: `#1a1a1a`
- Border-radius: `12px`
- Padding: `16px 20px`
- Max-width: `70%`
- Right-aligned
- Avatar (32px circle) on right
- Timestamp below (text-tertiary, 12px)

#### **Agent Message:**

```
┌─────────────────────────────────────────────────┐
│ [Agent                                          │
│  Icon]  I'll help you with that. Let me find   │
│         the right tables and build a query      │
│         for Q3 revenue by region and month.     │
│                                                 │
│         [Thinking Process - Expandable]         │
│         [SQL Artifact Card]                     │
│         [Results Card]                          │
│                                                 │
│ 10:34 AM • Today                                │
└─────────────────────────────────────────────────┘
```

**Specs:**

- Background: `#141414`
- Border-radius: `12px`
- Padding: `16px 20px`
- Max-width: `85%`
- Left-aligned
- Agent icon (32px circle) on left, with subtle glow when thinking
- Timestamp below

---

### **2. Agent Thinking Process** (Transparency Component)

#### **Collapsed State:**

```
┌────────────────────────────────────────────────────────┐
│ 🤖 Agent Thinking...                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ 💭 Analyzed your question                             │
│ 🔍 Found 3 relevant tables                            │
│ 📝 Generated SQL query                                │
│ ✅ Query validated successfully                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                              [Expand to see details ▼] │
└────────────────────────────────────────────────────────┘
```

#### **Expanded State:**

```
┌────────────────────────────────────────────────────────┐
│ 🤖 Agent Thinking...                        [Collapse ▲]│
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                        │
│ 💭 Understanding your question...                     │
│    "Show me revenue by region for Q3"                 │
│                                                        │
│ 🔍 Identifying relevant tables...                     │
│    ✓ sales_transactions (95% confidence)              │
│      - Has 'amount' field for revenue ✓               │
│      - Has 'transaction_date' for filtering ✓         │
│      - Has 'region_id' for grouping ✓                 │
│                                                        │
│    ✓ regions (70% confidence)                         │
│      - Provides region names for display              │
│      - Can join on region_id                          │
│                                                        │
│    ✗ customers (30% confidence)                       │
│      - Not needed for this specific query             │
│      - Skipping to simplify                           │
│                                                        │
│ 🤔 Query construction reasoning...                    │
│    • SELECT region_name, SUM(amount)                  │
│    • JOIN regions for readable names                  │
│    • WHERE for Q3 date range                          │
│    • GROUP BY region for aggregation                  │
│    • ORDER BY revenue DESC for insights               │
│                                                        │
│ 📝 Constructing SQL query...                          │
│    [SQL code preview with syntax highlighting]        │
│                                                        │
│ ✅ Validation checks passed                           │
│    ✓ Syntax: Valid SQL                                │
│    ✓ Safety: No destructive operations                │
│    ✓ Performance: Est. 0.3s, ~1,250 rows              │
│    ✓ Schema: All tables and columns exist             │
│                                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                        [Copy Reasoning] │
└────────────────────────────────────────────────────────┘
```

**User Controls:**

- **Verbosity Toggle** (in settings): Silent → Brief → Detailed → Debug
- **Expand/Collapse** individual sections
- **Copy** reasoning to clipboard
- **Skip** to results (auto-collapse thinking)

**Visual Design:**

- Background: `#0f0f0f` (slightly darker)
- Border: `1px solid rgba(59, 130, 246, 0.2)`
- Icons: Use emojis or Lucide icons
- Checkmarks/X: Color-coded (green/red)
- Confidence percentages: Color gradient based on value

---

### **3. SQL Code Artifact**

**Visual Design:**

```
┌──────────────────────────────────────────────────────────┐
│ 📝 Generated SQL Query              [Copy] [Edit] [Run] │
├──────────────────────────────────────────────────────────┤
│  1  SELECT                                               │
│  2      r.region_name,                                   │
│  3      SUM(st.amount) AS total_revenue,                 │
│  4      DATE_TRUNC('month', st.transaction_date) AS month│
│  5  FROM sales_transactions st                           │
│  6  JOIN regions r ON r.id = st.region_id                │
│  7  WHERE st.transaction_date >= '2025-07-01'            │
│  8    AND st.transaction_date < '2025-10-01'             │
│  9  GROUP BY r.region_name, DATE_TRUNC('month', ...)     │
│ 10  ORDER BY total_revenue DESC;                         │
├──────────────────────────────────────────────────────────┤
│ ✓ Valid • ~1,250 rows • Est. 0.34s • PostgreSQL         │
│ [Explain Query] [Optimize] [Save as Template]           │
└──────────────────────────────────────────────────────────┘
```

**Specs:**

- **Background:** `#0a0a0a` (darkest)
- **Border:** `1px solid rgba(255, 255, 255, 0.1)`
- **Border-radius:** `8px`
- **Padding:** `20px`
- **Font:** JetBrains Mono, 14px
- **Line-height:** 1.5
- **Line numbers:** Gray, right-aligned in 40px gutter
- **Syntax highlighting:** Use Prism.js or Shiki with custom theme
  - Keywords (SELECT, FROM, WHERE): `#8b5cf6` (purple)
  - Strings: `#10b981` (green)
  - Functions: `#3b82f6` (blue)
  - Comments: `#71717a` (gray)
  - Numbers: `#f59e0b` (orange)

**Action Buttons:**

- **Copy:** Copy SQL to clipboard
- **Edit:** Open inline editor
- **Run:** Execute query
- **Explain:** Show query execution plan
- **Optimize:** AI suggestions for performance
- **Save:** Save as template/snippet

**Status Bar:**

- Validation status with icon
- Estimated row count
- Estimated execution time
- Database type indicator

---

### **4. Results Table**

**Visual Design:**

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Query Results (1,250 rows)        [Export ▼] [Visualize]│
├───────────────────┬─────────────────┬──────────────────────┤
│ region_name ↓     │ total_revenue ↑ │ month                │
├───────────────────┼─────────────────┼──────────────────────┤
│ North America     │ $12,450,000     │ 2025-09-01           │
│ Europe            │ $9,230,000      │ 2025-09-01           │
│ Asia Pacific      │ $7,890,000      │ 2025-09-01           │
│ North America     │ $11,200,000     │ 2025-08-01           │
│ Europe            │ $8,900,000      │ 2025-08-01           │
│ ...               │ ...             │ ...                  │
├───────────────────┴─────────────────┴──────────────────────┤
│ Showing 1-100 of 1,250 rows • Query took 0.34s            │
│ [Load More 100] [Load All] [Export CSV/JSON/Excel]        │
└────────────────────────────────────────────────────────────┘
```

**Specs:**

- **Background:** `#141414`
- **Border:** `1px solid rgba(255, 255, 255, 0.1)`
- **Border-radius:** `8px`
- **Header:** `#1a1a1a` background, bold text
- **Rows:** Alternate (`#141414` / `#161616`) for zebra striping
- **Hover:** Row highlight `#1a1a1a`
- **Padding:** Cells 12px horizontal, 10px vertical
- **Font:** Inter, 14px

**Features:**

- **Sortable columns:** Click header to sort (↑↓ arrows)
- **Pagination:** Load more or infinite scroll
- **Export:** CSV, JSON, Excel formats
- **Quick visualize:** One-click chart generation
- **Cell copying:** Click to copy individual cell
- **Column resizing:** Drag header borders

**Number Formatting:**

- Currency: `$12,450,000` (with commas)
- Large numbers: `1.2M`, `450K` (abbreviated)
- Percentages: `45.67%`
- Dates: `2025-09-01` or `Sep 1, 2025` (configurable)

---

### **5. Input Field** (Bottom-Pinned Chat Input)

**Visual Design:**

```
┌────────────────────────────────────────────────────────────┐
│ 💬 Ask me anything about your data...                     │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Type your question here...                             │ │
│ │                                                        │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│ [📎 Attach] [🎤 Voice] [⚡ Quick Actions]         [Send →]│
└────────────────────────────────────────────────────────────┘
```

**Specs:**

- **Background:** `#1a1a1a`
- **Border:** `1px solid rgba(255, 255, 255, 0.1)`
- **Border-radius:** `12px`
- **Padding:** `16px`
- **Position:** Fixed/sticky at bottom of chat area
- **Max-height:** Auto-expand up to 200px, then scroll

**Features:**

- **Auto-expanding textarea** - Grows with content
- **Markdown support** - Bold, italic, code blocks
- **File attachment** - Upload CSV for context
- **Voice input** - Speech-to-text
- **Quick actions dropdown** - Common queries, templates
- **Keyboard shortcuts:**
  - `Cmd/Ctrl + Enter` - Send message
  - `Shift + Enter` - New line
  - `Cmd/Ctrl + K` - Clear input
  - `/` - Trigger command menu

**Smart Suggestions (Dropdown):**

```
┌────────────────────────────────────────┐
│ ⚡ Quick Actions                       │
├────────────────────────────────────────┤
│ 📊 Show me top 10 customers            │
│ 📈 Revenue trend last 6 months         │
│ 🔍 Find customers with no orders       │
│ 💰 Total sales by product category     │
│ ───────────────────────────────────────│
│ 📝 Templates                           │
│ 🕐 Recent queries                      │
└────────────────────────────────────────┘
```

---

### **6. Schema Browser** (Right Sidebar Inspector)

**Visual Design:**

```
┌────────────────────────────────────┐
│ 🔍 [Search schema...]              │
├────────────────────────────────────┤
│ 📁 Tables (24) ──────────── [▼]   │
│                                    │
│  📊 sales_transactions             │
│   ├─ 🔑 id (bigint, PK)            │
│   ├─ 💰 amount (decimal)           │
│   ├─ 📅 transaction_date (date)    │
│   ├─ 🔗 region_id (int, FK) ───┐  │
│   ├─ 🔗 customer_id (int, FK)   │  │
│   └─ 📝 notes (varchar)         │  │
│                                 │  │
│  📊 regions                      │  │
│   ├─ 🔑 id (int, PK) <──────────┘  │
│   ├─ 🏷️ region_name (varchar)     │
│   └─ 🌍 country_code (char)       │
│                                    │
│  📊 customers                      │
│   ├─ 🔑 id (int, PK)               │
│   ├─ 👤 name (varchar)             │
│   ├─ 📧 email (varchar)            │
│   └─ 📅 created_at (timestamp)    │
│                                    │
│  [+ Show 21 more tables]           │
│                                    │
├────────────────────────────────────┤
│ 🔗 Relationships (8)               │
│ 📈 Recent Tables                   │
│ ⭐ Favorites                       │
└────────────────────────────────────┘
```

**Specs:**

- **Background:** `#0f0f0f`
- **Padding:** 16px
- **Font:** Inter, 13px
- **Icons:** Use Lucide icons or emojis
- **Indent:** 16px per level

**Features:**

- **Search/Filter:** Type to filter tables/columns
- **Expandable tree:** Click to expand/collapse
- **Data types visible:** Show (type) next to column name
- **Key indicators:** PK (Primary Key), FK (Foreign Key)
- **Relationship lines:** Visual connection between FKs
- **Copy on click:** Click to copy table/column name
- **Hover preview:** Show sample data (first 5 rows)
- **Quick stats:** Row count, size, last updated

**Hover Preview:**

```
┌────────────────────────────────────┐
│ sales_transactions                 │
├────────────────────────────────────┤
│ 📊 1,245,678 rows                  │
│ 💾 124.5 MB                        │
│ 🕐 Updated 2 hours ago             │
│                                    │
│ Sample data:                       │
│ • id: 1, 2, 3, 4, 5...            │
│ • amount: $145.00, $67.50, ...    │
└────────────────────────────────────┘
```

---

### **7. Navigation & Header**

**Workspace Mode Header:**

```
┌──────────────────────────────────────────────────────────────┐
│ 🗣️ SamvadQL  [⇄ Focus Mode]  [DB: production_v2 ▼]  [Team ▼] [⚙️] [👤] │
└──────────────────────────────────────────────────────────────┘
```

**Specs:**

- **Height:** 60px
- **Background:** `#0a0a0a`
- **Border-bottom:** `1px solid rgba(255, 255, 255, 0.1)`
- **Padding:** 0 24px

**Elements:**

- **Logo:** Brand mark + "SamvadQL" text (20px)
- **Mode toggle:** Switch between Workspace ⇄ Focus
- **DB selector:** Dropdown with active database
- **Team menu:** Collaboration features
- **Settings:** Gear icon
- **Profile:** User avatar/menu

---

### **8. Buttons & Interactive Elements**

#### **Primary Button:**

```css
background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
color: #ffffff;
padding: 12px 24px;
border-radius: 8px;
font-weight: 600;
transition: transform 0.2s, box-shadow 0.2s;

hover:
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
```

#### **Secondary Button:**

```css
background: transparent;
color: #3b82f6;
border: 1px solid #3b82f6;
padding: 12px 24px;
border-radius: 8px;
font-weight: 600;

hover:
  background: rgba(59, 130, 246, 0.1);
  border-color: #60a5fa;
```

#### **Ghost Button:**

```css
background: transparent;
color: #a1a1aa;
padding: 8px 16px;
border-radius: 6px;

hover:
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
```

#### **Danger Button:**

```css
background: #ef4444;
color: #ffffff;
padding: 12px 24px;
border-radius: 8px;
font-weight: 600;

hover:
  background: #dc2626;
```

---

### **9. Cards & Containers**

**Standard Card:**

```css
background: #141414;
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 12px;
padding: 24px;
transition: transform 0.2s, box-shadow 0.2s;

hover:
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  border-color: rgba(59, 130, 246, 0.3);
```

**Feature Card (with gradient):**

```css
background: linear-gradient(
  180deg,
  rgba(59, 130, 246, 0.1) 0%,
  transparent 100%
);
border: 1px solid rgba(59, 130, 246, 0.2);
border-radius: 12px;
padding: 24px;
```

---

### **10. Modals & Overlays**

**Modal Container:**

```css
background: #1a1a1a;
border: 1px solid rgba(255, 255, 255, 0.1);
border-radius: 16px;
padding: 32px;
max-width: 600px;
box-shadow: 0 24px 48px rgba(0, 0, 0, 0.8);
```

**Backdrop:**

```css
background: rgba(0, 0, 0, 0.8);
backdrop-filter: blur(4px);
```

---

## **Animations & Interactions**

### **Performance Targets:**

- **60fps** smooth animations
- **< 100ms** UI response time
- **< 1.5s** First Contentful Paint
- **< 200ms** transition durations

### **Animation Patterns:**

#### **1. Fade & Slide In (New Messages):**

```css
@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

animation: fadeSlideIn 300ms cubic-bezier(0.4, 0, 0.2, 1);
```

#### **2. Agent Thinking Animation:**

```css
/* Pulsing glow on avatar */
@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
}

/* Typing indicator dots */
@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}
```

#### **3. Hover Effects:**

```css
/* Card lift */
transition: transform 200ms ease, box-shadow 200ms ease;
hover: transform: translateY(-4px);

/* Button scale */
transition: transform 200ms ease;
hover: transform: scale(1.02);

/* Link underline slide */
hover: text-decoration-line: underline;
text-underline-offset: 4px;
transition: text-underline-offset 200ms ease;
```

#### **4. Expand/Collapse:**

```css
/* Height transition */
transition: max-height 300ms ease;
max-height: 0 → max-height: 1000px;

/* Arrow rotation */
transition: transform 200ms ease;
transform: rotate(0deg) → rotate(180deg);

/* Fade content */
opacity: 0 → 1;
transition: opacity 200ms ease 100ms;
```

#### **5. Loading States:**

```css
/* Skeleton shimmer */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

background: linear-gradient(90deg, #141414 0%, #1a1a1a 50%, #141414 100%);
background-size: 1000px 100%;
animation: shimmer 2s infinite;
```

#### **6. Progress Indicators:**

```css
/* Indeterminate progress bar */
@keyframes indeterminate {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(300%);
  }
}

/* Spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

---

## **Spacing & Grid System**

### **Spacing Scale:**

```css
--space-0: 0;
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
```

### **Grid System:**

- **Container max-width:** 1440px
- **Gutter:** 24px
- **Columns:** 12-column grid
- **Breakpoints:**
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px
  - Wide: > 1440px

---

## **Inspiration References**

### **From VoidZero (voidzero.dev):**

✅ Deep black backgrounds (#0a0a0a)
✅ Large, bold typography with generous spacing
✅ Terminal aesthetic
✅ Clean card layouts with hover lift effects
✅ Metric displays (large numbers + context labels)
✅ Project cards with GitHub stats
✅ File reference style ("projects.json", "belief.md")

### **From OpenSpec (openspec.dev):**

✅ Extreme minimalism
✅ Monospace font dominance for technical feel
✅ Badge system ("SOON", "NATIVE SUPPORT")
✅ High-contrast CTAs
✅ Install command display in monospace
✅ Pure black background with high contrast

### **From Vite+ (viteplus.dev):**

✅ Gradient accents (subtle color transitions)
✅ Tabbed content for interactive exploration
✅ Framework logos as trust indicators
✅ Pricing tier comparison tables
✅ Feature showcase with detailed descriptions

### **From AI Coding Agents (Cursor, Copilot, Claude):**

✅ Artifact pattern (embedded code/results in chat)
✅ Thinking process transparency
✅ Conversational refinement workflow
✅ Inline explanations and reasoning
✅ Context-aware suggestions
✅ Step-by-step problem solving

### **From DataGrip/DBeaver:**

✅ Schema browser tree structure
✅ SQL editor with syntax highlighting
✅ Query execution details
✅ Results table with sorting/filtering

---

## **Mood & Feel**

### **It Should Feel Like:**

✅ A **smart colleague** who understands databases and SQL
✅ **Professional** but approachable - not intimidating
✅ **Fast and responsive** - no lag, instant feedback
✅ **Transparent** - you always know what it's thinking
✅ **Trustworthy** - enterprise-grade, reliable, secure
✅ **Modern** - cutting-edge but not trendy or gimmicky
✅ **Empowering** - makes you feel capable and productive

### **It Should NOT Feel Like:**

❌ A chatbot reading scripts
❌ A complex enterprise tool requiring training
❌ Gimmicky or toy-like
❌ Overwhelming with too many options
❌ Slow or laggy
❌ Unpredictable or mysterious
❌ Cold or mechanical

---

## **Target User Journey**

### **Scenario: Data Analyst using SamvadQL**

1. **Arrival**

   - Opens SamvadQL
   - Greeted with clean dark interface
   - Sees: "👋 Hi Sarah! Ready to explore your data?"

2. **Initial Query**

   - Types: "Show me top 10 customers by revenue last quarter"
   - Presses Enter or clicks Send

3. **Agent Processing** (Transparent)

   - Agent avatar pulses (thinking animation)
   - Thinking process expands (user can watch or collapse)
   - Shows: "Analyzing... Found tables... Building query... Validating..."

4. **SQL Generated**

   - Clean, syntax-highlighted SQL appears in artifact card
   - Status bar shows: "✓ Valid • ~150 rows • Est. 0.2s"
   - User reviews SQL

5. **Results Display**

   - Results table loads smoothly below SQL
   - Data formatted nicely (currency, dates)
   - Quick stats: "10 rows • Query took 0.18s"

6. **Refinement**

   - User says: "Add year-over-year comparison"
   - Agent updates SQL in place (no new artifact)
   - New results stream in

7. **Export**

   - User clicks [Export ▼] → CSV
   - File downloads instantly
   - Agent: "✓ Exported 10 rows to customers_revenue.csv"

8. **Follow-up**
   - Agent suggests: "💡 Would you like to see these customers' purchase patterns?"
   - User can accept, modify, or ask new question

### **Throughout the Journey:**

- **No waiting** - instant responses
- **No confusion** - clear labels, obvious actions
- **No errors** - validated before execution
- **No learning curve** - natural language works

---

## **Accessibility Requirements**

### **WCAG 2.1 AA Compliance:**

✅ **Color Contrast:**

- Text on background: Minimum 4.5:1 ratio
- Large text: Minimum 3:1 ratio
- Interactive elements: Clear focus indicators

✅ **Keyboard Navigation:**

- All features accessible via keyboard
- Logical tab order
- Visible focus states
- Keyboard shortcuts documented

✅ **Screen Reader Support:**

- Semantic HTML (headings, landmarks, lists)
- ARIA labels on interactive elements
- ARIA live regions for dynamic content
- Alt text on all images/icons

✅ **Motion & Animation:**

- Respect `prefers-reduced-motion`
- Option to disable animations
- No auto-playing videos/animations

✅ **Focus Indicators:**

```css
:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-radius: 4px;
}
```

### **Keyboard Shortcuts:**

- `Tab` / `Shift+Tab` - Navigate elements
- `Enter` - Activate buttons/links
- `Space` - Toggle checkboxes/expandables
- `Escape` - Close modals/dropdowns
- `Cmd/Ctrl + K` - Focus search/command palette
- `Cmd/Ctrl + Enter` - Send message
- `Cmd/Ctrl + /` - Show keyboard shortcuts

---

## **Technical Implementation Guidelines**

### **Frontend Stack:**

- **Framework:** React 18+ with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS 3.x
- **UI Components:** shadcn/ui (Radix primitives)
- **State Management:** Redux Toolkit or Zustand
- **WebSocket:** Socket.io for real-time streaming
- **Code Highlighting:** Prism.js or Shiki
- **Icons:** Lucide React
- **Animations:** Framer Motion or CSS transitions
- **Charts:** Recharts or Chart.js
- **Tables:** TanStack Table (React Table v8)

### **Responsive Breakpoints:**

```css
/* Mobile */
@media (max-width: 767px) {
  /* Stack layout, hide sidebars, full-width chat */
}

/* Tablet */
@media (min-width: 768px) and (max-width: 1023px) {
  /* Collapsible sidebars, 2-column layout */
}

/* Desktop */
@media (min-width: 1024px) {
  /* Full 3-column layout */
}

/* Wide */
@media (min-width: 1440px) {
  /* Max container width, more spacing */
}
```

### **Performance Optimizations:**

- **Code splitting:** Route-based and component-based
- **Lazy loading:** Images, components, data
- **Virtual scrolling:** For long tables/lists (react-window)
- **Debouncing:** Search inputs, auto-save
- **Memoization:** React.memo, useMemo, useCallback
- **Web Workers:** Heavy computations off main thread
- **Service Workers:** Offline support, caching

### **File Structure:**

```
src/
├── components/
│   ├── chat/
│   │   ├── MessageBubble.tsx
│   │   ├── AgentThinking.tsx
│   │   ├── ChatInput.tsx
│   │   └── ConversationThread.tsx
│   ├── sql/
│   │   ├── SQLArtifact.tsx
│   │   ├── QueryEditor.tsx
│   │   └── SyntaxHighlighter.tsx
│   ├── results/
│   │   ├── ResultsTable.tsx
│   │   ├── ResultsChart.tsx
│   │   └── ExportButton.tsx
│   ├── schema/
│   │   ├── SchemaTree.tsx
│   │   ├── TableNode.tsx
│   │   └── ColumnNode.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Modal.tsx
│       └── ...
├── layouts/
│   ├── WorkspaceLayout.tsx
│   ├── FocusLayout.tsx
│   └── Header.tsx
├── pages/
│   ├── Chat.tsx
│   ├── Login.tsx
│   └── Settings.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useChat.ts
│   └── useSchema.ts
├── services/
│   ├── api.ts
│   ├── websocket.ts
│   └── auth.ts
├── store/
│   ├── chatSlice.ts
│   ├── schemaSlice.ts
│   └── store.ts
├── types/
│   ├── chat.ts
│   ├── sql.ts
│   └── schema.ts
├── utils/
│   ├── sqlFormatter.ts
│   ├── validators.ts
│   └── helpers.ts
├── styles/
│   ├── globals.css
│   └── themes.css
└── App.tsx
```

---

## **Deliverables Expected**

### **Phase 1: Core UI Components**

✅ Design system setup (colors, typography, spacing)
✅ Button components (primary, secondary, ghost, danger)
✅ Input components (text, textarea, select)
✅ Card components (standard, feature, modal)
✅ Layout shells (Workspace, Focus)

### **Phase 2: Chat Interface**

✅ Message bubbles (user, agent)
✅ Agent thinking component
✅ Chat input field with actions
✅ Conversation thread container
✅ Message animations

### **Phase 3: SQL & Results**

✅ SQL artifact card
✅ Syntax highlighting
✅ Results table with sorting/pagination
✅ Export functionality UI
✅ Query status indicators

### **Phase 4: Schema Browser**

✅ Schema tree structure
✅ Search/filter functionality
✅ Table/column nodes
✅ Hover previews
✅ Relationship indicators

### **Phase 5: Additional Screens**

✅ Login/Signup pages
✅ Onboarding flow
✅ Database connection setup
✅ Settings/preferences
✅ Team collaboration features

### **Phase 6: Landing Page**

✅ Hero section with animated tagline
✅ Feature showcase
✅ Code demo/example
✅ Pricing/plans (if applicable)
✅ Footer with links

---

## **Success Metrics**

The design is successful if:

✅ **Usability:** Users understand interface in < 30 seconds
✅ **Performance:** 60fps animations, < 1.5s load time
✅ **Accessibility:** WCAG 2.1 AA compliant, keyboard navigable
✅ **User Satisfaction:** Feels natural, not forced
✅ **Task Completion:** Users can generate queries in < 2 minutes
✅ **Visual Appeal:** Professional, modern, trustworthy
✅ **Responsive:** Works seamlessly on all screen sizes
✅ **Brand Consistency:** Cohesive visual language throughout

---

## **Design Principles Summary**

1. **Conversation First** - Natural language is the primary interaction
2. **Transparency** - Show reasoning, don't hide behind magic
3. **Speed** - Instant feedback, no waiting
4. **Simplicity** - Minimal UI, maximum clarity
5. **Trust** - Professional, reliable, secure
6. **Empowerment** - Make users feel capable
7. **Accessibility** - Inclusive for all users
8. **Performance** - Smooth, fast, responsive

---

## **Final Notes for Design Agent**

- **Prioritize clarity over cleverness** - users need to get work done
- **Dark theme is primary** - optimize for extended use
- **Think in components** - build reusable, composable pieces
- **Test with real data** - use realistic SQL queries and results
- **Consider edge cases** - long queries, large result sets, errors
- **Mobile experience matters** - though desktop is primary
- **Consistency is key** - spacing, colors, typography should be uniform
- **Performance first** - beautiful but fast

**This is a professional tool for data analysts. Every design decision should serve their productivity and confidence.**

---

**End of Design Brief**

_Good luck! Build something incredible._ 🚀
