# Product Specification

## Product

**DomoNest** — a calm household operating system that reduces household mental load by connecting shopping, pantry awareness, meal planning, routines and actionable home knowledge.

## Product promise

A user should be able to answer these questions in seconds:

1. What needs my attention today?
2. What do I need to buy?
3. What should I use before it expires?
4. What is planned for dinner?
5. What home routine is due next?

## Primary problem

The household manager often stores important state in memory, notes, chats, calendar events, fridge magnets and separate apps. The cost is not merely disorganization; it is repeated remembering, rechecking, duplicate purchasing, food waste and missed routines.

DomoNest should reduce **mental load**, not create a second system that itself requires maintenance.

## Target users

Primary:
- People who carry significant responsibility for running a household.
- Families, couples and solo households.
- Mobile-first users.
- Users who value practical utility over configuration.

Secondary:
- Users looking for recipes or home guides who can convert editorial content into household actions.

The product is deliberately not gender-restricted in UI or language.

## Jobs to be done

### JTBD-01 — Know what matters now

> When I open the app, I want to immediately see the few things that need attention so I do not need to inspect several lists.

Success:
- actionable state visible without navigating modules;
- no vanity metrics above urgent actions;
- no information overload.

### JTBD-02 — Capture a shopping need immediately

> When I remember something I need, I want to add it in seconds before I forget.

Success:
- item can be captured with name only;
- sensible defaults;
- optional details remain progressive.

### JTBD-03 — Shop efficiently

> When I am in a store, I want a clean list grouped in a useful order and large tap targets so I can move quickly.

Success:
- one-tap completion;
- grouped categories;
- undo after accidental completion;
- no setup/editing noise in shopping mode.

### JTBD-04 — Reduce food waste

> When food is low or expiring, I want the system to surface it before I buy duplicates or throw it away.

Success:
- low-stock and use-soon states;
- human-readable dates;
- pantry can work with approximate quantities.

### JTBD-05 — Plan dinner with less work

> When I choose a meal, I want to know what I already have and add only missing ingredients to shopping.

Success:
- recipe/pantry reconciliation;
- one action to add missing ingredients;
- no duplicate shopping items.

### JTBD-06 — Maintain home routines without mental bookkeeping

> When I complete a recurring chore, I want the next occurrence to be scheduled automatically.

Success:
- completion history;
- next due date derived from recurrence;
- explicit skip/postpone paths;
- no guilt-oriented language.

### JTBD-07 — Turn home knowledge into action

> When a recipe or guide is useful, I want to apply it to my own household rather than only read it.

Success:
- recipe → shopping / meal plan;
- cleaning guide → routine;
- checklist → personal tasks where appropriate.

## Core product loop

```
Plan → Check home state → Buy / Do → Complete → System updates next useful state
```

Examples:

```
Recipe → compare with pantry → missing ingredients → shopping → purchased
```

```
Cleaning guide → add routine → complete → next recurrence
```

## North-star behavior

**Weekly completed household actions that originated from an intentional user plan or useful system signal.**

This measures actual household utility better than page views.

## Activation

A new user is activated when, in their first session, they complete one meaningful setup/action:
- add at least 3 shopping items, or
- add at least 3 pantry staples, or
- create/accept a recurring routine, or
- plan a meal and add missing ingredients.

## Core metrics

Portfolio/demo instrumentation may be simulated or documented rather than collected.

- Activation rate.
- Day-7 return.
- Shopping items completed per shopping session.
- Recipe → shopping conversion.
- Routine completion rate.
- Pantry use-soon item resolution.
- Cross-module adoption.

## MVP scope

In scope:
- Today dashboard.
- Quick Add.
- Shopping list.
- Low-maintenance pantry.
- Recurring home routines.
- Recipe content.
- Recipe → pantry → shopping.
- Basic dinner planning.
- Actionable Wagtail home guides.
- Search.
- Authentication.
- Responsive and accessible UI.

Out of scope for MVP:
- AI assistant.
- Push notifications.
- Household chat.
- Full expense/budgeting system.
- Grocery price comparison.
- Barcode scanner.
- Native apps.
- Voice assistant integrations.
- Social feed.
- Complex gamification.

## Product guardrails

1. Every new field adds user effort and must earn its place.
2. Default flows must work without advanced configuration.
3. A module that does not connect to another module needs a strong reason to exist.
4. Do not expose database structure as information architecture.
5. Do not use AI where deterministic behavior is sufficient.
6. Do not present analytics that do not improve a decision.
7. Avoid guilt, streak pressure and punitive overdue language.
8. Never fabricate privacy, savings or recommendation accuracy claims.

## MVP success criteria

The product is coherent when a user can complete this golden journey:

1. Open Today.
2. See dinner is unplanned and milk expires soon.
3. Select a recipe.
4. See which ingredients are at home.
5. Add missing ingredients to shopping in one action.
6. Complete those items in shopping mode.
7. Complete a due home routine.
8. See the routine's next occurrence generated correctly.

That journey is the primary end-to-end acceptance scenario.
