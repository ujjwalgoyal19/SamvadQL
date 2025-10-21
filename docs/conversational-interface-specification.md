# Conversational Interface Specification for SamvadQL

**Version:** 2.0
**Date:** October 17, 2025
**Status:** 🎯 Implementation Ready

## Table of Contents

1. [Core Philosophy](#1-core-philosophy)
2. [Dual-View Architecture](#2-dual-view-architecture)
3. [Conversational Patterns](#3-conversational-patterns)
4. [Agent Thinking & Verbosity](#4-agent-thinking--verbosity)
5. [UI Component Specifications](#5-ui-component-specifications)
6. [Technical Implementation](#6-technical-implementation)
7. [Success Metrics](#7-success-metrics)

---

## 1. Core Philosophy

### 1.1 Chat is De Facto

**Every interaction is a conversation.** No fixed workflows, no rigid steps. The interface adapts to the user's needs in real-time.

**Key Principles:**

- 🗣️ **Conversational by default** - Natural language is the primary input method
- 🌊 **Fluid, not discrete** - No step 1, 2, 3... flow adapts to context
- 🧠 **Think out loud** - Agent shows its reasoning process (verbosity controlled by user)
- 🤝 **Collaborative** - User and agent work together, not user commanding tool
- 💡 **Ask, don't guess** - When uncertain, clarify instead of assuming

### 1.2 Inspiration Sources

**AI Coding Agents:**

- Cursor (thinking process, artifact embedding)
- GitHub Copilot Chat (inline suggestions, explanations)
- Cline/Windsurf (step-by-step reasoning, user confirmation)
- v0.dev (artifact pattern, visual components)

**Conversational AI:**

- Claude (artifact embedding, clear reasoning)
- ChatGPT (conversation threading, context memory)
- Perplexity (source transparency, follow-up suggestions)

**Data Tools:**

- DataGrip (SQL editor integration, schema awareness)
- Tableau Ask Data (natural language to viz)
- Looker (exploration + conversation hybrid)

### 1.3 What Makes This Different

**Traditional BI Tools:** Form → Configure → Run → Results

**SamvadQL Approach:** Conversation → Clarify → Generate → Refine → Explore

**Key Differences:**
| Traditional Tools | SamvadQL |
|---|---|
| Fixed workflow | Adaptive flow |
| Choose from dropdowns | Describe in natural language |
| Multi-step wizards | Single conversation thread |
| Results separate from query | Everything in context |
| Manual SQL editing | Conversational refinement |
| Silent execution | Transparent reasoning |
| One query at a time | Continuous exploration |

---

## 2. Dual-View Architecture

### 2.1 View Overview

SamvadQL offers **two complementary interfaces** that users can switch between based on their needs:

1. **Workspace Mode** - Multi-tasking, exploration, team collaboration
2. **Focus Mode** - Single-task, distraction-free, quick queries

### 2.2 Workspace Mode (Developer/Explorer View)

**When to use:**

- Working on multiple analyses simultaneously
- Exploring unfamiliar databases
- Team collaboration on complex problems
- Need quick reference to schema/history
- Power users who want full control

**Layout:**

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🏠 SamvadQL  [Focus Mode ⇆] [DB: production_v2 ▼] [Team ▼] [⚙️] [👤] │
├──────────────┬──────────────────────────────────┬──────────────────────┤
│              │                                  │                      │
│ LEFT NAV     │  MAIN WORKSPACE                  │  RIGHT INSPECTOR     │
│ (240px)      │  (Flexible)                      │  (320px, collapsible)│
│              │                                  │                      │
│ 📂 Chats     │  ┌─────────────────────────────┐│  ┌────────────────┐ │
│  🟢 Active   │  │ Chat: Sales Q3 Analysis     ││  │ 🔍 Search      │ │
│  • Sales Q3  │  │ ─────────────────────────── ││  │ [Search...]    │ │
│  • User Seg  │  │                             ││  └────────────────┘ │
│  • Churn     │  │ [Conversation thread]       ││                      │
│              │  │                             ││  📊 Schema           │
│ 💾 Saved     │  │ User: Show me revenue...    ││   └─ 📁 Tables      │
│  • Reports   │  │ Agent: [Thinking...]        ││      ├─ customers   │
│  • KPIs      │  │ Agent: Here's your query... ││      ├─ orders      │
│              │  │ [SQL + Results embedded]    ││      ├─ products    │
│ 📚 History   │  │                             ││      └─ ...         │
│  Today       │  │ User: Add time breakdown... ││                      │
│  Yesterday   │  │ Agent: Updated!             ││  🔖 Current Query    │
│  Last week   │  │                             ││  Status: ✓ Valid    │
│              │  └─────────────────────────────┘│  Rows: ~1,250       │
│ 🗄️ Databases  │                                  │  Time: 0.34s        │
│  • prod_v2   │  ┌──────────────────────────┐   │  [View Plan]        │
│  • staging   │  │ Input field (bottom)     │   │                      │
│  • analytics │  │ [Type your message...]   │   │  💡 Suggestions      │
│              │  │ [Send] [Attach] [🎤]     │   │  • Add date filter  │
│ 👥 Team      │  └──────────────────────────┘   │  • Group by region  │
│  • Shared    │                                  │  • Export results   │
│  • Mentions  │  Tab Bar (top of workspace):    │                      │
│              │  [Sales Q3*] [User Seg] [+New]  │                      │
└──────────────┴──────────────────────────────────┴──────────────────────┘
```

**Key Features:**

**Left Sidebar:**

- **Chat Organization** - All conversations in one place
- **Saved Queries** - Quick access to templates
- **History** - Time-based organization
- **Databases** - Switch connections easily
- **Team** - Shared chats and mentions

**Main Workspace:**

- **Tabbed Interface** - Multiple chats open like IDE tabs
- **Conversation Thread** - Full chat history with embedded artifacts
- **Bottom Input** - Always accessible, never scrolls away
- **Rich Artifacts** - SQL, results, visualizations inline

**Right Inspector:**

- **Schema Browser** - Quick table/column lookup
- **Query Details** - Real-time validation status
- **Suggestions** - Context-aware next steps
- **Execution Plans** - Performance insights

### 2.3 Focus Mode (Distraction-Free Chat)

**When to use:**

- Quick ad-hoc queries
- Single problem focus
- Mobile or small screens
- Minimal distractions needed
- Learning the tool

**Layout:**

````
┌────────────────────────────────────────────────────────────────────────┐
│  ≡  SamvadQL Chat       [Workspace Mode ⇆]   [DB: prod ▼]   [👤]      │
├────┬───────────────────────────────────────────────────────────────────┤
│    │                                                                   │
│ H  │                 💬 Conversation                                   │
│ I  │                                                                   │
│ S  │  ┌──────────────────────────────────────────────────────────────┐│
│ T  │  │ You: Show me revenue by region for last quarter              ││
│ O  │  └──────────────────────────────────────────────────────────────┘│
│ R  │                                                                   │
│ Y  │  ┌──────────────────────────────────────────────────────────────┐│
│    │  │ 🤖 Agent:                                                    ││
│ 🔍 │  │                                                              ││
│    │  │ [💭 Thinking expanded - click to collapse]                  ││
│ 🕐 │  │ 💭 Understanding: "revenue by region for last quarter"       ││
│ 🕑 │  │ 🔍 Found tables: sales_transactions, regions                ││
│ 🕒 │  │ ✅ Query ready!                                              ││
│    │  │                                                              ││
│ +  │  │ Here's your revenue breakdown by region for Q3 2025:        ││
│    │  │                                                              ││
│    │  │ ┌────────────────────────────────────────────────────────┐  ││
│    │  │ │ 📊 Artifact: Revenue by Region Query                  │  ││
│    │  │ │ ────────────────────────────────────────────────────── │  ││
│    │  │ │ [SQL] [Results] [Visualization]                       │  ││
│    │  │ │                                                        │  ││
│    │  │ │ ```sql                                                 │  ││
│    │  │ │ SELECT r.name, SUM(s.amount) as revenue              │  ││
│    │  │ │ FROM sales_transactions s                            │  ││
│    │  │ │ JOIN regions r ON s.region_id = r.id                 │  ││
│    │  │ │ WHERE s.date >= '2025-07-01'                         │  ││
│    │  │ │   AND s.date < '2025-10-01'                          │  ││
│    │  │ │ GROUP BY r.name                                       │  ││
│    │  │ │ ORDER BY revenue DESC                                 │  ││
│    │  │ │ ```                                                    │  ││
│    │  │ │                                                        │  ││
│    │  │ │ [▶ Execute] [✏️ Edit] [💾 Save] [🔗 Share]           │  ││
│    │  │ └────────────────────────────────────────────────────────┘  ││
│    │  │                                                              ││
│    │  │ ┌────────────────────────────────────────────────────────┐  ││
│    │  │ │ 📈 Results (4 rows) • 0.23s                           │  ││
│    │  │ │ Region      | Revenue                                 │  ││
│    │  │ │ West        | $1,245,890                              │  ││
│    │  │ │ East        | $987,234                                │  ││
│    │  │ │ South       | $765,432                                │  ││
│    │  │ │ North       | $543,210                                │  ││
│    │  │ │                                                        │  ││
│    │  │ │ [📊 Visualize] [⬇️ Export] [🔍 Explore More]         │  ││
│    │  │ └────────────────────────────────────────────────────────┘  ││
│    │  │                                                              ││
│    │  │ Quick actions:                                               ││
│    │  │ • Add time-based trend                                       ││
│    │  │ • Break down by product category                             ││
│    │  │ • Compare to previous quarter                                ││
│    │  └──────────────────────────────────────────────────────────────┘│
│    │                                                                   │
│    │  ┌─────────────────────────────────────────────────────────┐    │
│    │  │ 💬 Ask a follow-up or start something new...            │    │
│    │  │ [Type here...]                                          │    │
│    │  │                                                         │    │
│    │  │ [Send (Ctrl+Enter)] [Attach SQL] [🎤 Voice]            │    │
│    │  └─────────────────────────────────────────────────────────┘    │
└────┴───────────────────────────────────────────────────────────────────┘
````

**Key Features:**

**Minimal Sidebar:**

- Only history - collapsible to icon bar
- Quick search conversations
- New chat button

**Clean Chat:**

- Full-width conversation
- No distracting panels
- Everything in conversation flow
- Inline artifacts and results

**Always-Visible Input:**

- Bottom-pinned input field
- Quick actions for common tasks
- Voice input option

### 2.4 Switching Between Views

**Toggle:** `Ctrl/Cmd + Shift + W` (Workspace) or `Ctrl/Cmd + Shift + F` (Focus)

**Button:** Prominent toggle in header

**Smart persistence:**

- Remember last view per user
- Maintain conversation state when switching
- Responsive: Auto-switch to Focus on small screens (<1024px)

---

## 3. Conversational Patterns

### 3.1 Adaptive Flow - No Fixed Steps

**Core Principle:** The conversation flow adapts based on query clarity and context.

#### Pattern A: Clear Query → Direct Execution

```
User: "Show me top 10 customers by revenue in 2025"

Agent: 💭 This is clear - I know exactly what to do
       [Generates SQL immediately]
       [Executes and shows results]

       Here are your top 10 customers by revenue in 2025:
       [Results embedded]
```

**No intermediate steps needed** - Agent has enough context

#### Pattern B: Ambiguous Query → Clarification

```
User: "Show me sales"

Agent: 🤔 I need a bit more information...

       Your query: "Show me sales"

       A few quick questions:

       1️⃣ Time period?
          [Last week] [Last month] [Last quarter] [Custom...]

       2️⃣ Break down by?
          [Product] [Region] [Sales rep] [Date] [No breakdown]

       3️⃣ Which metrics?
          ☑ Revenue  ☑ Units sold  ☐ Profit margin

       Or just tell me: [Text input field]

       [Skip - Use your best judgment]
```

**Clarification is interactive and quick** - Buttons for fast answers

#### Pattern C: Uncertain Table Selection

```
User: "Show me customer satisfaction scores"

Agent: 🔍 Found multiple possible data sources...

       Option 1: customer_feedback table ⭐ Recommended
       ├─ Confidence: 95%
       ├─ Has: rating, comment, nps_score
       ├─ 12,450 records, updated 2 hours ago
       └─ [Use this]

       Option 2: nps_surveys table
       ├─ Confidence: 70%
       ├─ Has: score, response_date
       ├─ 8,230 records, updated daily
       └─ [Use this]

       Option 3: support_tickets table
       ├─ Confidence: 40%
       ├─ Indirect measure via ticket sentiment
       └─ [Use this]

       [Search all tables manually] [Describe which data you want]
```

**Show confidence levels** - Let user make informed choice

#### Pattern D: Complex Multi-Step

```
User: "Analyze customer churn for high-value customers"

Agent: 💭 This is complex - let me break it down...

       Step 1: Define "high-value customers"
       🤔 What threshold? (I can suggest based on data)
       • Top 10% by lifetime value?
       • Over $10,000 annual spend?
       • Other criteria?
       [Suggest for me]

       → User selects or describes

       Step 2: Define "churn"
       🤔 How do you want to measure churn?
       • No orders in last 90 days?
       • Cancelled subscription?
       • Other definition?
       [Continue]

       → User selects

       Step 3: Build analysis
       ✅ Got it! Building churn analysis for customers with >$10K
          spend who haven't ordered in 90+ days...
       [Generates complex multi-table query]
```

**Break down complexity naturally** - Guide user through decisions

### 3.2 Iterative Refinement Pattern

**Context is maintained throughout the conversation:**

```
┌──────────────────────────────────────────────────────────────┐
│ 🧵 Thread Context                                            │
│ Topic: Revenue Analysis                                      │
│ Database: production_v2                                      │
│ Current focus: sales_transactions, regions                   │
└──────────────────────────────────────────────────────────────┘

User: "Show me revenue by product"

Agent: [Generates SQL, executes]
       📊 Showing revenue for all 127 products

User: "Filter to electronics only"

Agent: ✏️ Updated query (added category filter)
       [Shows diff: + WHERE category = 'electronics']
       📊 Now showing 23 electronics products

User: "Sort highest revenue first"

Agent: ✏️ Updated query (added ORDER BY)
       [Shows diff: + ORDER BY revenue DESC]
       📊 Re-sorted with top products first

User: "Compare to last year"

Agent: ✏️ Rebuilt query (added year-over-year comparison)
       [Shows new query with YEAR() and previous period JOIN]
       📊 Now showing YoY comparison

User: "Perfect! Save this as 'Electronics YoY Report'"

Agent: ✅ Saved!
       You can find it in Saved Queries.

       🔗 Quick link: samvadql://saved/electronics-yoy-report
```

**Key principles:**

- Every refinement maintains context
- Show what changed (diffs)
- Natural language references ("that query", "those results")
- Build progressively complex queries through conversation

### 3.3 Embedded Artifacts

**Rich interactive components embedded in conversation:**

````
┌────────────────────────────────────────────────────────────┐
│ 🤖 Agent: Here's your revenue analysis                     │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📊 Artifact: Revenue Analysis                          │ │
│ │ [SQL] [Results] [Viz] [Explain] [Optimize]            │ │
│ │ ──────────────────────────────────────────────────────  │ │
│ │                                                        │ │
│ │ ```sql                                                 │ │
│ │ -- Revenue by region for Q3 2025                      │ │
│ │ SELECT r.region_name,                                 │ │
│ │        SUM(s.amount) as total_revenue,                │ │
│ │        COUNT(s.id) as order_count                     │ │
│ │ FROM sales_transactions s                             │ │
│ │ JOIN regions r ON s.region_id = r.id                  │ │
│ │ WHERE s.transaction_date >= '2025-07-01'              │ │
│ │   AND s.transaction_date < '2025-10-01'               │ │
│ │ GROUP BY r.region_name                                │ │
│ │ ORDER BY total_revenue DESC;                          │ │
│ │ ```                                                    │ │
│ │                                                        │ │
│ │ ✓ Query validated  •  Estimated: ~1,200 rows  •  <1s │ │
│ │                                                        │ │
│ │ [▶ Execute] [✏️ Edit SQL] [📋 Copy] [💾 Save]        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📈 Results (4 rows) • Executed in 0.23s               │ │
│ │ ──────────────────────────────────────────────────────  │ │
│ │ Region      Revenue        Orders    Growth           │ │
│ │ West        $1,245,890    3,421      +15%             │ │
│ │ East        $987,234      2,876      +8%              │ │
│ │ South       $765,432      2,103      -3%              │ │
│ │ North       $543,210      1,567      +12%             │ │
│ │                                                        │ │
│ │ [Sort ↕] [Filter 🔍] [Export ⬇] [Visualize 📊]      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ Key insights:                                              │
│ • West region leads with $1.2M revenue (+15% growth)      │
│ • South is only declining region (-3%)                    │
│ • Total: $3.5M across all regions                         │
│                                                             │
│ What would you like to do next?                            │
│ • Drill into South region decline                         │
│ • See product breakdown                                    │
│ • Compare to previous quarter                              │
│ • Something else?                                          │
└────────────────────────────────────────────────────────────┘
````

**Artifact Types:**

1. **SQL Query Block**

   - Syntax highlighted, editable
   - Show validation status
   - Quick actions (execute, copy, save, share)

2. **Results Table**

   - Interactive (sort, filter, search)
   - Formatted data (currency, dates, numbers)
   - Export options
   - Pagination for large results

3. **Visualization**

   - Auto-generated charts
   - Interactive (hover, zoom, filter)
   - Multiple chart types

4. **Explanation Block**

   - Plain language query logic
   - Collapsible sections
   - Educational content

5. **Diff View**

   - Show changes between iterations
   - Highlight added/removed/modified

6. **Schema Preview**

   - Table structure
   - Sample data
   - Relationship diagram

7. **Execution Plan**
   - Query performance analysis
   - Optimization suggestions
   - Visual execution tree

### 3.4 Multimodal Input

#### Voice Input

```
User: [Holds 🎤 button, speaks]
      "Show me revenue by region for last quarter"

Agent: 🎧 Heard: "Show me revenue by region for last quarter"
       [Processes as text query]
       [Standard response flow]
```

**Features:**

- Push-to-talk or toggle modes
- Real-time transcription shown
- Edit transcription before submit
- Multi-language support

#### Paste SQL Directly

```
User: [Pastes SQL from elsewhere]

SELECT c.name, COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
WHERE o.created_at >= '2025-01-01'
GROUP BY c.name
HAVING COUNT(o.id) > 10;

Agent: 📋 I see you pasted a SQL query.

       This query shows customers with >10 orders since Jan 2025.

       What would you like me to do?
       [▶ Execute as-is]
       [📖 Explain what it does]
       [🔧 Optimize it]
       [✏️ Let me modify it]
```

#### Image/Screenshot Analysis

```
User: [Uploads screenshot of error message]
      "Why is this failing?"

Agent: 👀 Analyzing your error message...

       I can see:
       • Error: "column 'reveue' does not exist"
       • Line 4 of your query
       • SQL state: 42703

       The issue: Typo in column name
       ❌ reveue
       ✅ revenue

       Would you like me to fix this?
       [Yes, fix it] [Show me the corrected query]
```

#### Attach CSV/Excel for Quick Analysis

```
User: [Drops customers.csv file]
      "Analyze this for me"

Agent: 📂 Uploaded: customers.csv (2.3 MB, 15,420 rows)

       Quick preview:
       • 4 columns: id, name, email, signup_date
       • Date range: 2020-2025
       • No missing values detected

       What would you like to know?
       [Show summary stats]
       [Find patterns/trends]
       [Compare to database data]
       [Let me ask specific questions]
```

### 3.5 Uncertainty & Confidence Handling

**Show confidence, ask when unsure:**

```
Agent: 🤔 I'm interpreting your query, but I'm not 100% certain...

       Your query: "Show me engagement metrics"

       Confidence breakdown:

       ✅ High confidence (85%+)
       └─ You want some kind of user engagement data

       ⚠️ Medium confidence (60-85%)
       ├─ Time period: Assume all-time? Or recent?
       └─ Metrics: Login frequency? Feature usage? Session duration?

       ❌ Low confidence (<60%)
       └─ Which user segment? All users or specific group?

       Can you clarify:
       • What time period should I analyze?
       • Which engagement metrics matter most?
       • Any specific user segments to focus on?

       [Answer questions] [Let agent decide] [Rephrase query]
```

**Better to ask than guess wrong** - Transparency builds trust

### 3.6 Suggested Actions & Quick Replies

**Context-aware suggestions after each interaction:**

```
After showing results:

Agent: Here are your top 10 products by revenue.

       [Results displayed]

       Common next steps:
       [🔍 Filter by category]
       [📊 Show trend over time]
       [💰 Add profit margin]
       [📥 Export to Excel]
       [🔗 Join customer data]

       Or ask me anything else...
```

**After showing SQL without executing:**

```
Agent: Here's the SQL I generated:

       [SQL displayed]

       What would you like to do?
       [▶ Execute it]
       [✏️ Let me edit first]
       [💡 Explain how it works]
       [🔧 Optimize for performance]
       [❓ Ask questions about it]
```

**When query fails:**

```
Agent: ❌ Query failed: Table 'sales' does not exist

       Let me help:
       [🔍 Search for similar tables]
       [📋 Show all available tables]
       [🔄 Try a different approach]
       [💬 Explain what you're looking for]
```

---

## 4. Agent Thinking & Verbosity

### 4.1 Verbosity Levels

Users control how much reasoning they see:

#### Level 0: Silent Mode 🤫

```
User: Show me revenue by region

Agent: [SQL + Results immediately]
```

**When to use:** Expert users, quick queries, low-latency priority

#### Level 1: Brief Mode 💬 (Default)

```
User: Show me revenue by region

Agent: 💭 Found sales_transactions and regions tables...

       [SQL + Results]
```

**When to use:** Most users, balanced speed and transparency

#### Level 2: Detailed Mode 🧠

```
User: Show me revenue by region

Agent: 💭 Agent Thinking...
       ───────────────────────────────────────
       Understanding query...
       ✓ Metric: revenue (SUM of amounts)
       ✓ Grouping: by region
       ✓ Time: no filter (all-time)

       Searching relevant tables...
       ✓ sales_transactions (primary data)
       ✓ regions (for region names)

       Building query...
       • JOIN regions for readable names
       • SUM amount field
       • GROUP BY region
       • ORDER BY revenue DESC

       [SQL + Results]
```

**When to use:** Learning, debugging, building trust

#### Level 3: Debug Mode 🐛

```
User: Show me revenue by region

Agent: 💭 Agent Thinking (Debug Mode)
       ═══════════════════════════════════════
       [Step 1/7] Parsing natural language...
       ├─ Tokens: ["show", "me", "revenue", "by", "region"]
       ├─ Intent: query_data
       ├─ Entities: {metric: "revenue", group_by: "region"}
       └─ Time: 45ms

       [Step 2/7] Schema search...
       ├─ Embedding query: "revenue region sales"
       ├─ Vector search results (top 5):
       │  1. sales_transactions (score: 0.95)
       │  2. regions (score: 0.89)
       │  3. revenue_summary (score: 0.72)
       │  4. customer_regions (score: 0.61)
       │  5. product_revenue (score: 0.58)
       └─ Time: 120ms

       [Step 3/7] Table selection...
       ├─ Selected: sales_transactions (primary)
       ├─ Selected: regions (for JOIN)
       ├─ Rejected: revenue_summary (pre-aggregated, less flexible)
       └─ Time: 35ms

       [Step 4/7] Query construction...
       ├─ SELECT: SUM(amount) AS revenue
       ├─ FROM: sales_transactions
       ├─ JOIN: regions ON region_id
       ├─ GROUP BY: region_name
       ├─ ORDER BY: revenue DESC
       └─ Time: 78ms

       [Step 5/7] SQL validation...
       ├─ Syntax check: ✓ PASSED
       ├─ Table exists: ✓ PASSED
       ├─ Columns exist: ✓ PASSED
       ├─ Dry-run EXPLAIN: ✓ PASSED
       └─ Time: 156ms

       [Step 6/7] Generating explanation...
       └─ Time: 89ms

       [Step 7/7] Ready to execute

       Total thinking time: 523ms
       ═══════════════════════════════════════

       [SQL + Results]
```

**When to use:** Developers, debugging issues, understanding system behavior

### 4.2 Verbosity Controls

**Toggle in UI:**

```
Top bar: [🤫 Silent] [💬 Brief] [🧠 Detailed] [🐛 Debug]
         └─ Hover tooltip: "Ctrl+Shift+V to cycle"
```

**Keyboard shortcut:** `Ctrl/Cmd + Shift + V` - Cycle through levels

**Per-conversation setting:** Persists within conversation thread

**Global default:** User preference in settings

### 4.3 Collapsible Thinking Sections

```
┌────────────────────────────────────────────────────────────┐
│ Agent: 💭 Agent Thinking...  [Collapse ▼]                 │
│ ───────────────────────────────────────────────────────────│
│ Understanding query...                                     │
│ ✓ Found tables: sales_transactions, regions               │
│ ✓ Building JOIN query...                                  │
│ ───────────────────────────────────────────────────────────│
│                                                            │
│ Here's your revenue by region:                            │
│ [SQL + Results]                                           │
└────────────────────────────────────────────────────────────┘

After collapse:

┌────────────────────────────────────────────────────────────┐
│ Agent: 💭 [Thinking collapsed - click to expand ▶]        │
│                                                            │
│ Here's your revenue by region:                            │
│ [SQL + Results]                                           │
└────────────────────────────────────────────────────────────┘
```

**Auto-collapse after 3 seconds** - Keep conversation clean

**Click to expand** - Review reasoning anytime

---

## 5. UI Component Specifications

### 5.1 Message Bubbles

**User Message:**

```
┌────────────────────────────────────────────────────────────┐
│                                                       You: │
│                                                            │
│                 Show me revenue by region last quarter  │
│                                                            │
│                                              10:34 AM    │
└────────────────────────────────────────────────────────────┘
```

**Styling:**

- Right-aligned
- Primary blue background (#2563EB)
- White text
- Rounded corners (12px)
- Max-width: 70% of container
- Padding: 12px 16px
- Font: 14px, line-height: 1.5

**Agent Message:**

```
┌────────────────────────────────────────────────────────────┐
│ 🤖 Agent:                                                  │
│                                                            │
│ Here's your revenue breakdown...                          │
│                                                            │
│ [Artifact embedded here]                                  │
│                                                            │
│ 10:34 AM                                                  │
└────────────────────────────────────────────────────────────┘
```

**Styling:**

- Left-aligned
- Light gray background (#F3F4F6)
- Dark text (#111827)
- Rounded corners (12px)
- Max-width: 85% of container
- Padding: 16px 20px
- Font: 14px, line-height: 1.6
- Agent avatar/icon: 32px circle

### 5.2 SQL Artifact Component

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Artifact: Revenue Analysis Query                       │
│ ───────────────────────────────────────────────────────────│
│ [SQL] [Results] [Visualization] [Explain] [Optimize]     │
│                                                            │
│ ╭──────────────────────────────────────────────────────╮  │
│ │ 1  -- Revenue by region for Q3 2025                 │  │
│ │ 2  SELECT r.region_name,                             │  │
│ │ 3         SUM(s.amount) AS total_revenue             │  │
│ │ 4  FROM sales_transactions s                         │  │
│ │ 5  JOIN regions r ON s.region_id = r.id              │  │
│ │ 6  WHERE s.transaction_date >= '2025-07-01'          │  │
│ │ 7    AND s.transaction_date < '2025-10-01'           │  │
│ │ 8  GROUP BY r.region_name                            │  │
│ │ 9  ORDER BY total_revenue DESC;                      │  │
│ ╰──────────────────────────────────────────────────────╯  │
│                                                            │
│ ✓ Validated  •  ~1,200 rows  •  <1s estimated             │
│                                                            │
│ [▶ Execute] [✏️ Edit] [📋 Copy] [💾 Save] [🔗 Share]     │
└────────────────────────────────────────────────────────────┘
```

**Styling:**

- Border: 1px solid #E5E7EB
- Border-radius: 8px
- Background: #FFFFFF
- Shadow: subtle (0 1px 3px rgba(0,0,0,0.1))
- Code font: Fira Code, 14px
- Line numbers: visible
- Syntax highlighting: standard SQL colors
- Editable: click to enter edit mode

### 5.3 Results Table Component

```
┌────────────────────────────────────────────────────────────┐
│ 📈 Results (4 rows) • Executed in 0.23s                   │
│ ───────────────────────────────────────────────────────────│
│ Region        Revenue          Orders      Growth    ↕    │
│ ───────────────────────────────────────────────────────────│
│ West          $1,245,890       3,421       +15%     ↑     │
│ East          $987,234         2,876       +8%      ↑     │
│ South         $765,432         2,103       -3%      ↓     │
│ North         $543,210         1,567       +12%     ↑     │
│ ───────────────────────────────────────────────────────────│
│ Showing 1-4 of 4 rows                                      │
│                                                            │
│ [Sort ↕] [Filter 🔍] [Export ⬇] [Visualize 📊]          │
└────────────────────────────────────────────────────────────┘
```

**Styling:**

- Zebra striping: alternating #FFFFFF and #F9FAFB
- Header: sticky, bold, #111827
- Hover row: #F3F4F6
- Text align: left for text, right for numbers
- Font: SF Mono, 13px
- Cell padding: 8px 12px
- Borders: subtle horizontal dividers
- Number formatting: auto (currency, percentages, etc.)

### 5.4 Input Field

```
┌────────────────────────────────────────────────────────────┐
│ 💬 Ask a question or describe what you need...            │
│ [Multiline text input area, expands as user types]        │
│                                                            │
│                                                            │
│ ────────────────────────────────────────────────────────── │
│ [📎 Attach] [🎤 Voice] [💾 Saved] [⌨️ Cmd+Enter to send] │
└────────────────────────────────────────────────────────────┘
```

**Styling:**

- Min-height: 44px (single line)
- Max-height: 200px (auto-scrolls beyond)
- Border: 1px solid #E5E7EB
- Border-radius: 12px
- Padding: 12px 16px
- Font: 14px, line-height: 1.5
- Placeholder: #9CA3AF
- Focus: border #2563EB, shadow glow

**Auto-complete suggestions:**

```
┌────────────────────────────────────────────────────────────┐
│ Show me rev█                                               │
│ ├─ revenue by region                                       │
│ ├─ revenue over time                                       │
│ └─ revenue by product category                             │
└────────────────────────────────────────────────────────────┘
```

### 5.5 Quick Action Buttons

**After results:**

```
[🔍 Filter]  [📊 Visualize]  [⬇️ Export]  [➕ Add column]
└─ Tooltip on hover explaining what each does
```

**Button styling:**

- Height: 32px
- Padding: 6px 12px
- Border-radius: 6px
- Background: #F3F4F6 (hover: #E5E7EB)
- Font: 13px, medium weight
- Icon + text
- Keyboard shortcut shown in tooltip

### 5.6 Loading & Streaming States

**Initial thinking:**

```
┌────────────────────────────────────────────────────────────┐
│ 🤖 Agent:                                                  │
│                                                            │
│ 💭 Understanding your query...                            │
│    [Animated dots ...]                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Streaming SQL generation:**

````
┌────────────────────────────────────────────────────────────┐
│ 🤖 Agent:                                                  │
│                                                            │
│ 💭 Building your query...                                 │
│                                                            │
│ ```sql                                                     │
│ SELECT r.region_name,                                      │
│        SUM(s.amount) AS revenue                            │
│ FROM sales_transactions s                                  │
│ JOIN regions r ON s.region_id █                           │
│                                                            │
│ [Cursor blinks as SQL streams in]                         │
└────────────────────────────────────────────────────────────┘
````

**Query execution:**

```
┌────────────────────────────────────────────────────────────┐
│ ⏳ Executing query...                                      │
│ ████████████░░░░░░░░░  60%  •  1.2s elapsed               │
│                                                            │
│ [Cancel]                                                   │
└────────────────────────────────────────────────────────────┘
```

### 5.7 Error States

**Validation error:**

```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ SQL Validation Error                                    │
│ ───────────────────────────────────────────────────────────│
│ Line 4: Column 'reveue' does not exist                    │
│                                                            │
│ 3  FROM sales_transactions s                               │
│ 4  JOIN regions r ON s.reveue_id = r.id                   │
│                      ^^^^^^                                │
│                                                            │
│ Did you mean 'revenue'?                                    │
│                                                            │
│ [Fix automatically] [Edit manually] [Try different tables]│
└────────────────────────────────────────────────────────────┘
```

**Execution error:**

```
┌────────────────────────────────────────────────────────────┐
│ ❌ Query Failed                                            │
│ ───────────────────────────────────────────────────────────│
│ Error: Permission denied for table 'sensitive_data'       │
│                                                            │
│ You don't have access to this table.                       │
│ Contact your database administrator or try a different     │
│ data source.                                               │
│                                                            │
│ [Search other tables] [Contact admin] [Go back]           │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Technical Implementation

### 6.1 Technology Stack

**Frontend:**

- **Framework:** React 18+ with TypeScript
- **UI Components:** shadcn/ui (already in codebase)
- **State Management:** Zustand (already in codebase)
- **Data Grid:** TanStack Table v8 (React Table)
- **Code Editor:** Monaco Editor (VS Code engine)
- **Streaming:** Socket.io for WebSocket
- **Icons:** Lucide Icons
- **Animations:** Framer Motion (selective use)
- **Forms:** React Hook Form + Zod

**Backend:**

- **API:** FastAPI (already in codebase)
- **Streaming:** Server-Sent Events (SSE) or WebSocket
- **LLM Integration:** OpenAI, Llama, DeepSeek clients
- **Vector Search:** Qdrant or OpenSearch
- **Cache:** Redis
- **Database:** PostgreSQL for metadata

### 6.2 Conversation State Management

```typescript
interface ConversationState {
  id: string;
  title: string;
  databaseId: string;
  messages: Message[];
  context: ConversationContext;
  artifacts: Artifact[];
  createdAt: Date;
  updatedAt: Date;
}

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  artifacts?: Artifact[];
  thinking?: ThinkingProcess;
}

interface ConversationContext {
  currentTables: string[];
  referencedColumns: string[];
  lastQuery?: {
    sql: string;
    results?: QueryResults;
  };
  userPreferences: {
    dateFormat: string;
    verbosityLevel: VerbosityLevel;
  };
}

interface Artifact {
  id: string;
  type: 'sql' | 'results' | 'visualization' | 'explanation';
  data: any;
  metadata: {
    validated: boolean;
    executed: boolean;
    executionTime?: number;
  };
}
```

### 6.3 Streaming Architecture

**SQL Generation Streaming:**

```typescript
// Backend (FastAPI)
async def stream_sql_generation(query: str, context: Context):
    async for chunk in llm_client.stream(
        prompt=build_prompt(query, context),
        model="gpt-4"
    ):
        yield {
            "type": "sql_chunk",
            "content": chunk,
            "timestamp": datetime.utcnow()
        }

// Frontend (React)
function useSQLStream(query: string) {
  const [sql, setSQL] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`/api/stream/sql?q=${query}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSQL(prev => prev + data.content);
    };

    eventSource.onerror = () => {
      setIsStreaming(false);
      eventSource.close();
    };

    return () => eventSource.close();
  }, [query]);

  return { sql, isStreaming };
}
```

**Thinking Process Streaming:**

```typescript
// Stream thinking steps as they happen
async for step in agent.think(query):
    yield {
        "type": "thinking_step",
        "step": step.name,
        "status": step.status,  // 'running', 'complete', 'failed'
        "details": step.details,
        "confidence": step.confidence
    }
```

### 6.4 Context Window Management

**Conversation memory limits:**

- Keep last 10 message pairs in active memory
- Summarize older messages for context
- Maintain semantic embeddings of conversation for retrieval

```typescript
interface ContextWindow {
  recentMessages: Message[]; // Last 10 pairs
  conversationSummary: string; // Summarized older context
  semanticIndex: EmbeddingIndex; // For retrieval
  relevantTables: string[]; // Currently discussed tables
  userPreferences: UserPreferences;
}

async function buildPromptContext(conversation: Conversation): string {
  const context = {
    recent: conversation.messages.slice(-20), // Last 10 pairs
    summary: await summarizeOlderMessages(conversation),
    schema: await getRelevantSchema(conversation.context.currentTables),
    examples: await getRelevantExamples(conversation)
  };

  return formatPrompt(context);
}
```

### 6.5 Performance Optimizations

**Caching strategy:**

```typescript
// Multi-level cache
const cache = {
  L1_Memory: new Map(), // In-memory, 100 items
  L2_LocalStorage: localStorage, // Browser, 10MB
  L3_Redis: redisClient, // Server-side, 1GB
  L4_Database: postgresClient // Persistent
};

// Cache query results
async function getCachedResults(sql: string): QueryResults | null {
  // Check L1 first (fastest)
  if (cache.L1_Memory.has(sql)) {
    return cache.L1_Memory.get(sql);
  }

  // Check L2 (browser)
  const local = cache.L2_LocalStorage.getItem(`query:${hashSQL(sql)}`);
  if (local) {
    return JSON.parse(local);
  }

  // Check L3 (Redis)
  const cached = await cache.L3_Redis.get(`query:${hashSQL(sql)}`);
  if (cached) {
    return JSON.parse(cached);
  }

  return null;
}
```

**Debouncing and throttling:**

```typescript
// Debounce schema search
const debouncedSearch = useMemo(() => debounce(searchSchema, 300), []);

// Throttle typing indicators
const throttledTypingIndicator = useThrottle(() => {
  socket.emit('user_typing');
}, 1000);
```

**Virtual scrolling for results:**

```typescript
// Use react-window for large result sets
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={results.length}
  itemSize={40}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <ResultRow data={results[index]} />
    </div>
  )}
</FixedSizeList>;
```

### 6.6 Real-Time Collaboration (Future)

```typescript
// Multiple users working on same conversation
interface CollaborationState {
  conversationId: string;
  activeUsers: User[];
  userCursors: Map<string, CursorPosition>;
  locks: Map<string, Lock>; // Who's editing what
}

// Broadcast user actions
socket.on('user_action', (action) => {
  switch (action.type) {
    case 'typing':
      showTypingIndicator(action.userId);
      break;
    case 'editing_sql':
      showEditingIndicator(action.userId, action.artifactId);
      break;
    case 'cursor_move':
      updateCursorPosition(action.userId, action.position);
      break;
  }
});
```

---

## 7. Success Metrics

### 7.1 Conversation Quality Metrics

**Primary Metrics:**

- **Query Success Rate:** >85% of conversations result in successful query execution
- **Iterations to Success:** <2 average refinements needed
- **Clarification Rate:** <30% of queries need clarification
- **Confidence Accuracy:** When agent shows >90% confidence, success rate >95%

**Conversation Flow:**

- **Avg messages per conversation:** 5-8 (efficient but thorough)
- **Time to first SQL:** <3 seconds from query submission
- **Time to results:** <5 seconds total (query + execution)

### 7.2 User Engagement Metrics

**Adoption:**

- **Daily Active Users (DAU):** Track growth
- **Conversations per user:** >3 per week (engaged users)
- **Return rate:** >60% users return within 7 days
- **View mode preference:** Track Workspace vs Focus usage

**Satisfaction:**

- **Query acceptance rate:** >85% of generated SQL accepted
- **Explicit feedback:** >4.5/5 average rating
- **Verbosity preference:** Track which levels users prefer
- **Feature discovery:** >50% users try voice input within first month

### 7.3 Technical Performance Metrics

**Speed:**

- **SQL generation latency:** <3s p95
- **Query execution time:** <5s p95 (depends on query complexity)
- **First token to user:** <500ms
- **UI responsiveness:** <100ms for all interactions

**Reliability:**

- **System uptime:** >99.5%
- **Error rate:** <5% of queries fail
- **Auto-correction success:** >90% of validation errors fixed automatically
- **Cache hit rate:** >40%

**Scalability:**

- **Concurrent users:** Support 1000+ simultaneous conversations
- **Messages per second:** Handle 100+ across all users
- **Database connections:** Efficient pooling, <50ms connection time

### 7.4 Learning & Improvement Metrics

**Agent Intelligence:**

- **Table selection accuracy:** >95% relevant tables chosen
- **Confidence calibration:** Actual success rate matches predicted confidence
- **User edit patterns:** Track what users change (learn from edits)
- **Query complexity:** Handle progressively more complex queries over time

**User Learning:**

- **SQL understanding:** Users review SQL <30% of time (trust increases)
- **Feature adoption:** Progressive discovery of advanced features
- **Query sophistication:** Users ask more complex questions over time

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

- ✅ Dual-view architecture (Workspace + Focus modes)
- ✅ Basic conversation interface
- ✅ Message bubbles and threading
- ✅ Simple SQL artifact embedding
- ✅ Streaming SQL generation
- ✅ Basic verbosity controls (Silent, Brief, Detailed)

### Phase 2: Core Conversational Patterns (Weeks 5-8)

- ✅ Adaptive flow logic (clarity detection)
- ✅ Clarification prompts with quick-pick buttons
- ✅ Iterative refinement with context memory
- ✅ Embedded artifacts (SQL, Results, Visualizations)
- ✅ Confidence indicators
- ✅ Error handling and auto-correction

### Phase 3: Advanced Interactions (Weeks 9-12)

- ✅ Voice input support
- ✅ Paste SQL analysis
- ✅ Screenshot/image analysis
- ✅ Quick actions and suggestions
- ✅ Keyboard shortcuts
- ✅ Multimodal input handling

### Phase 4: Intelligence & Polish (Weeks 13-16)

- ✅ Debug mode verbosity
- ✅ Thinking process visualization
- ✅ User preference learning
- ✅ Performance optimizations
- ✅ Mobile responsive design
- ✅ Accessibility compliance

### Phase 5: Collaboration & Scale (Future)

- Real-time collaboration
- Team shared conversations
- Advanced caching strategies
- Horizontal scaling
- Enterprise features

---

## 9. Design System Quick Reference

### Colors

**Primary Palette:**

- Primary Blue: `#2563EB`
- Success Green: `#10B981`
- Warning Amber: `#F59E0B`
- Error Red: `#EF4444`
- Info Purple: `#8B5CF6`

**Neutral Palette:**

- Background: `#FFFFFF` (Light) / `#1E1E1E` (Dark)
- Surface: `#F9FAFB` / `#2D2D2D`
- Border: `#E5E7EB` / `#404040`
- Text Primary: `#111827` / `#E5E7EB`
- Text Secondary: `#6B7280` / `#9CA3AF`

### Typography

**Fonts:**

- Interface: Inter, system fonts
- Code: Fira Code, JetBrains Mono
- Data: SF Mono, Roboto Mono

**Sizes:**

- Hero (Input): 18px / 1.6
- Body: 14px / 1.5
- Code: 14px / 1.5
- Small: 12px / 1.4

### Spacing

**Scale:** 8px base unit

- Micro: 4px
- Small: 8px
- Medium: 16px
- Large: 24px
- XL: 32px

### Components

**Buttons:** 32-40px height, 6-12px padding, 6px border-radius
**Inputs:** 44px height, 12-16px padding, 12px border-radius
**Messages:** 12-16px padding, 12px border-radius, max-width 70-85%
**Artifacts:** 8px border-radius, 1px border, subtle shadow

---

## 10. Accessibility Checklist

- [ ] WCAG 2.1 AA color contrast (4.5:1 text, 3:1 large text)
- [ ] Full keyboard navigation (Tab, Enter, Esc, Arrow keys)
- [ ] Screen reader support (ARIA labels, semantic HTML)
- [ ] Focus indicators (2px outline, clear visual state)
- [ ] Error announcements (screen reader alerts)
- [ ] Resizable text (support up to 200% zoom)
- [ ] Reduced motion support (respect prefers-reduced-motion)
- [ ] High contrast mode
- [ ] Skip links (jump to main content)
- [ ] Alt text for all images/icons

---

## 11. FAQ

**Q: Why two views instead of one flexible interface?**
A: Different tasks need different contexts. Workspace mode is for exploration and multi-tasking, Focus mode is for single-task efficiency. Users can choose based on their workflow.

**Q: Won't showing thinking slow things down?**
A: Verbosity is user-controlled. Default (Brief) shows minimal thinking. Silent mode shows none. Streaming means users see progress in real-time, which feels faster than waiting for a complete response.

**Q: How do you handle very long conversations?**
A: We maintain a context window of the last 10 message pairs, summarize older messages, and use semantic search to retrieve relevant past context when needed.

**Q: What if the agent makes mistakes?**
A: Users can always edit SQL directly. The agent learns from edits. Confidence indicators help users know when to review more carefully. Validation catches syntax errors before execution.

**Q: How is this different from ChatGPT + SQL?**
A: SamvadQL is purpose-built for SQL/database work:

- Integrated schema awareness
- Real-time SQL validation
- Embedded execution and results
- Database-specific optimizations
- Query refinement within conversation
- Professional data tooling integration

---

**Document Status:** ✅ Ready for Implementation
**Next Steps:**

1. Review with product and engineering teams
2. Create high-fidelity mockups (Figma)
3. Build component prototypes (Storybook)
4. User testing with 5-10 data analysts
5. Iterate based on feedback
6. Begin phased implementation

**Questions?** Contact the design team or open an issue.
