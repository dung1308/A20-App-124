## 1. Weak confidence feels like failure
Pain: When the AI is uncertain, users may see an answer that feels incomplete or too generic.
Why it matters: Students need a safe next step, not just an apology.
Feature idea: Add a structured fallback card with reasons for low confidence, recommended next action, and a human consultation CTA.

## 2. Users do not know why a major was recommended
Pain: Top 3 recommendations can feel like a black box.
Why it matters: Trust increases when the app explains fit in plain language.
Feature idea: Add a “Why this matches you” breakdown with 3–5 matched signals and 1–2 tradeoffs per major.

## 3. Profile/CV edits are not clearly controlled
Pain: Users may worry that uploaded CV data overwrites profile data incorrectly.
Why it matters: Students need confidence before confirming imported data.
Feature idea: Add a review-and-confirm diff view showing what will be added, kept, or skipped before merge.

## 4. Retry and recovery are too hidden
Pain: Network or AI failures can leave users stuck.
Why it matters: A good student workflow should always recover gracefully.
Feature idea: Add visible retry, reset, and continue-later actions on wizard, chat, and report screens.

## 5. Citations are not easy to scan
Pain: Source citations can be present but still hard to understand quickly.
Why it matters: Students need fast verification, not only raw links.
Feature idea: Add a compact source panel with labels like “official”, “derived”, and “profile-based”.

## 6. Chat and report feel disconnected
Pain: Users may ask follow-up questions after seeing recommendations but lose context.
Why it matters: The report should lead naturally into follow-up guidance.
Feature idea: Add “ask about this major” quick prompts on each major card that open chat with context prefilled.

## 7. Handoff status is unclear
Pain: Users may not know whether a human advisor has been engaged.
Why it matters: Escalation should feel reassuring, not invisible.
Feature idea: Add a handoff status banner with queue state, timestamp, and last staff message.

## 8. Wizard progress is too abstract
Pain: Students may not understand what remains in the flow.
Why it matters: Progress indicators reduce dropout.
Feature idea: Add step labels, estimated time, and completion hints across the wizard.

## 9. Empty states do not teach users what to do
Pain: Blank screens can feel like dead ends.
Why it matters: First-time users need guidance.
Feature idea: Add educational empty states for profile, report, chat, and resources pages.

## 10. Admin tools are useful but not productized
Pain: Operational views are hard to use as a developer feature testbed.
Why it matters: Better ops tools help support fast iteration.
Feature idea: Add simple health/status badges for token usage, prompt version, and handoff volume.

## 11. There is no “feature explainability” layer
Pain: Developers and staff may not see which rule or signal triggered a behavior.
Why it matters: This slows debugging during a short deadline.
Feature idea: Add a lightweight decision trace object for routing, fallback, and recommendation generation.

## 12. Resources are not tied to user intent
Pain: Help pages can become generic documentation.
Why it matters: Users need just-in-time guidance.
Feature idea: Add context-aware resource snippets based on where the user is in the flow.

## Short-term priority
Pain: The project needs features that can be delivered safely in 3 days.
Why it matters: Small, visible improvements beat large risky rewrites.
Feature idea: Focus on fallback UX, explanation panels, retry actions, and review-before-confirm flows.