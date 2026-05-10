# 1. Front-end Architecture Report
**Overview** The front-end is a modern, responsive Single Page Application (SPA) built with **React** and **Vite**, styled using **Tailwind CSS**. It is designed to provide a seamless transition between a structured "Major Matching Wizard" and a free-form "AI Consultant" chat.

# Key Components & Layout

**Authenticated Layout**: Implements a persistent sidebar (LeftPanel) and a centralized header with a Navigation component. This ensures users have consistent access to their Dashboard, Profile, and AI Consultant.
**State Management**: Utilizes a central store (useStore) for global states like matchResults and userId.
**Intelligent Chat Interface**:
- useChat Hook: A sophisticated custom hook that manages message history, persists data to localStorage, and handles complex history filtering to ensure the backend receives clean role/content pairs.
- Initial Context: The ConsultantPage automatically injects major recommendations into the chat context if the user has completed the wizard, allowing the AI to reference specific results immediately.
- Dynamic Profile View: The ProfilePage fetches structured academic data (GPA, IELTS, etc.) from the PostgreSQL database, providing a mirrored view of what the CRMAgent "knows" about the student.
# Technical Excellence

Vietnamese Localization: All user-facing strings and error messages are localized for Vietnamese high school students.
Session Resilience: Implements session re-hydration from localStorage to prevent data loss on page refreshes.