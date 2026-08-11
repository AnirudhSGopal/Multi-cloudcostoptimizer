# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## How to Run the Application

To run the full application (frontend and backend) locally, follow these steps:

### 1. Backend (Flask)
Open a new terminal and navigate to the backend directory:
```bash
cd ../backend/securevault
```

**Activate the virtual environment:**
```bash
.\.venv\Scripts\activate
```

**Install dependencies (if not already installed):**
```bash
pip install -r requirements.txt
```

**Run the backend server:**
```bash
flask --app wsgi:app run
```
*(The backend should now be running on `http://127.0.0.1:5000`)*

### 2. Frontend (React + Vite)
Open a separate terminal and ensure you are in the `frontend` directory:
```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Start the development server:**
```bash
npm run dev
```

### 3. View the application
Open your browser and navigate to the URL provided in your frontend terminal (usually `http://localhost:5173/`).
