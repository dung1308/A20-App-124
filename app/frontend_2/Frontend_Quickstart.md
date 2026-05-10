# VinUni Frontend Quick Start Guide

This guide helps you set up and run the VinUni Admission Assistant frontend interface.

## 1. Prerequisites
- **Node.js**: Version 18.x or higher.
- **npm**: (comes with Node.js) or **yarn**.

## 2. Environment Setup

Navigate to the frontend directory from the project root:

```bash
cd frontend
```

Install the necessary dependencies (including React, Vite, and Zustand for state management):

```bash
npm install
```

## 3. Configuration

Create a `.env` file in the `frontend/` directory. This ensures the frontend knows where to find the FastAPI backend:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
# LƯU Ý: Nếu thiếu VITE_GOOGLE_CLIENT_ID, tính năng Đăng nhập Google sẽ bị lỗi
```

## 4. Running the Application

Start the development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The frontend will typically be accessible at `http://localhost:5173`.

## 5. Verification
- **Initial Load**: Open your browser to the local URL. You should see the Admission Wizard landing page.
- **Integration**: Ensure the backend is running (see `backend/Backend_QuickStart.md`). Try submitting the wizard to verify the connection to `POST /api/match`.
- **Chat Check**: Navigate to the report page and use the `ChatBox` component. If `IS_DEMO_MODE` is enabled in the code, you will see a "Demo Mode" banner.

## 6. Common Commands
- `npm run build`: Build the production-ready assets.
- `npm run preview`: Preview the production build locally.
- `npm run lint`: Run linting checks on the codebase.