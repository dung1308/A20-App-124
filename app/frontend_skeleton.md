frontend/
  pages/
    WizardPage.jsx
    ReportPage.jsx
    ConsultantPage.jsx (AI Chat interface)
    ProfilePage.jsx (Academic profile management)
    AdminDashboard.jsx (PMF metrics and Audit logs)
    StaffDashboard.jsx (Handoff management and student context)
  components/
    Layout/
      LeftPanel.jsx (Persistent navigation)
      Header.jsx
    Wizard/
      Step1.jsx
      ...Step4.jsx
    Report/
      MajorCard.jsx
    Chat/
      ChatBox.jsx
    Admin/
      AuditTab.jsx
      JudgeResultModal.jsx
    Staff/
      HandoffList.jsx
  services/
    api.js (Auth, Chat, Match, Metrics, and Session endpoints)
  hooks/
    useChat.js
  state/
    store.js

Each component should be functional and reusable.