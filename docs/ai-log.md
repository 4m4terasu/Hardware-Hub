# AI Development Log

## Tools Used

### ChatGPT
I used ChatGPT as my primary planning and implementation partner throughout the assignment. It helped me structure the work into clear milestones, reason about scope, and implement backend, frontend, audit, and testing steps incrementally.

### Claude
I used Claude as a cross-verification tool for technical decisions and scope control. Its role was not to replace implementation, but to pressure-test architecture choices, catch avoidable mistakes, and confirm whether a proposed step was still aligned with the MVP.

### Gemini
I used Gemini inside the application itself for the Inventory Auditor feature. Importantly, Gemini is not the source of truth for findings — it is only used to summarize and prioritize the results of a deterministic backend audit.

## Data Strategy

The provided seed dataset was intentionally dirty, so I did not treat it like clean operational data.

My approach was:

1. **Preserve raw values first**
   - keep raw purchase date and status values
   - avoid normalizing away source issues too early

2. **Build deterministic audit rules on top**
   - future purchase date
   - malformed purchase date
   - missing purchase date
   - invalid status
   - missing brand
   - suspicious brand typo
   - safety-blocking notes
   - damage-related history
   - duplicate seed ID detected during import

3. **Use Gemini only for summarization**
   - deterministic code finds the facts
   - Gemini summarizes, prioritizes, and turns findings into a readable audit report

This split was intentional and important. It kept the AI-native layer useful without letting the model decide factual validation rules.

## Correction Story — Primary

### Deprecated startup event pattern

At one point, the backend setup used the `@app.on_event("startup")` pattern. Claude flagged that this was deprecated and that the warning would be visible in terminal output during a demo.

I immediately understood why this mattered:
- it creates visible noise during runtime
- it weakens polish during a live walkthrough
- it suggests I ignored framework evolution

I fixed it by switching to FastAPI's lifespan context manager pattern. That gave me the same startup behavior without carrying a deprecation warning into the demo.

## Correction Story — Secondary

### Browser autofill on the admin user creation form

During manual testing, I noticed the browser was autofilling the admin user-creation form with saved login credentials. That was not a backend bug, but it was a real product issue because it made the form feel confusing and incorrect.

I caught it myself while using the UI, described the behavior precisely, and then updated the form with better autocomplete-related attributes and field naming so the browser would stop treating it like the main login form.

## How I Used AI Responsibly

I did not treat AI output as final code.

My process was:
- define the exact scope of the next step
- implement one verifiable slice at a time
- manually test the result
- cross-check risky decisions
- correct weak suggestions before committing

That mattered most in:
- startup lifecycle handling
- auth and route protection
- rental guardrails
- UI bug fixes
- Gemini structured output and fallback behavior

## Prompt Trail

The prompt history that shaped the architecture, implementation flow, and deployment is documented in:

- `docs/prompt-trail.md`

## Final Reflection

The biggest value AI provided here was not just speed. It was helping me work in a structured, reviewable way:
- small milestones
- explicit decisions
- visible trade-offs
- fast feedback loops

The biggest responsibility on my side was deciding what **not** to trust automatically, and correcting it when needed.