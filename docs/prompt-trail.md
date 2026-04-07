# Prompt Trail

This is not the full chat history. It is a short selection of prompts that best show how I used AI during the project: architecture framing, adaptive scope control, cross-verification, and product-level bug reporting.

---

## Prompt 1 — Initial architecture context

### Prompt
> I am building an internal hardware management tool with:
> - backend: Python
> - frontend: Vue.js
> - database: SQLite
> - AI feature: Inventory Auditor
>
> I want a strong MVP, not a bloated feature list.
>
> Required areas:
> 1. Admin / User management
>    - admin can add hardware
>    - admin can delete hardware
>    - admin can toggle repair status
>    - admin can create user accounts
>    - only admin-created users can log in
> 2. Login system
>    - simple login screen
> 3. Smart dashboard
>    - list of hardware with Name, Brand, Purchase Date, Status
>    - sorting and filtering
> 4. Rental engine
>    - rent / return flow
>    - guardrails to prevent impossible states
> 5. AI-native layer
>    - Inventory Auditor
> 6. Testing
>    - at least 3 critical tests
> 7. Documentation
>    - README
>    - AI development log
>    - prompt trail
>    - at least one concrete correction of a bad AI suggestion
>
> Product direction:
> - deterministic validation rules in code
> - LLM used for interpretation / audit summary / recommendations
>
> I want practical, well-structured steps.
> Do not overscope.
> Keep everything explainable and interview-defensible.

### Commentary
This prompt shows that I set the architectural direction early instead of asking AI to invent the project shape for me. I was explicit about scope, priorities, the chosen AI feature, and the requirement that the system remain easy to explain afterward.

---

## Prompt 2 — Adaptive scope adjustment

### Prompt
> I think the model now has enough context that we can increase the scope of each step by roughly 50-100% without losing structure or explainability. Still keep steps verifiable and aligned with the brief. What would the next step look like at that scale?

### Commentary
This demonstrates that I did not keep the workflow rigid. Once the model had enough project context, I intentionally increased step size to move faster while still keeping the work testable and controlled.

---

## Prompt 3 — Technical correction catch

### Prompt
> Claude flagged that using `@app.on_event("startup")` is deprecated and that the warning would be visible during a demo. I want to preserve the current startup behavior, but switch to the correct modern pattern. Show me the minimal fix and keep the rest of the backend structure intact.

### Commentary
This was a cross-verification moment: one model surfaced a framework-quality issue in an earlier suggestion, and I understood immediately why it mattered. Instead of ignoring it, I corrected it right away and kept the implementation aligned with current FastAPI practices.

---

## Prompt 4 — Product-level bug report

### Prompt
> Overall everything seems to be working correctly. There is one slight issue that I think should be fixed. On the admin page, in the create user section, the data is automatically filled in. I think it is browser autofill of login data. Those fields should not be autofilled. autocomplete="off" should be applied in create user form.

### Commentary
This shows that I was testing the product myself and caught a UX issue the AI did not anticipate. I also identified the specific fix — and directed the AI to apply it correctly rather than asking for a rewrite.

---

## Prompt 5 — Deployment and environment wiring

### Prompt
> I want the realistic deployment path for this stack:
> - backend: Python + FastAPI + SQLite
> - frontend: Vue 3 + Vite + TypeScript
>
> Requirements:
> - backend and frontend must be reachable via public URLs
> - bootstrap admin seed must run on first startup
> - environment variables must be configurable on the deployment platform
> - SQLite is acceptable for this MVP deployment
> - frontend must point to the deployed backend URL, not localhost
>
> Give me the safest step-by-step deployment path without changing the stack.

### Commentary
This prompt shows that I used AI not only for coding, but also for deployment planning and configuration control. I kept the stack aligned with the assignment, preserved SQLite for the MVP, and used AI to help sequence Railway and Vercel setup without changing the product architecture late in the process.