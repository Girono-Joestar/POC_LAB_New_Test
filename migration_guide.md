# Production Migration Guide: POC AI Lab

I have migrated your Streamlit prototype to a professional **FastAPI + HTML/CSS** architecture optimized for **Vercel**.

## 🏗️ New Architecture
- **Backend (`api/main.py`)**: A FastAPI server that handles data retrieval, AI chat with LangChain + NVIDIA NIM, and secure admin updates.
- **Frontend (`public/`)**: A modern, premium dark-themed UI.
- **Admin Portal**: Hidden at `/secret-admin-portal`. Use your `ADMIN_TOKEN` to login.
- **Dynamic Configuration**: You can change the **API Key**, **thumbnail URLs**, and experiment data directly from the Admin Portal!

## 🔒 Security & Persistence
- **API Key**: The key is stored in `data/settings.json`.
- **Vercel Note**: Vercel's filesystem is read-only. Changes made via the Admin Portal on Vercel will not persist after a redeploy/restart. For permanent changes, please update the environment variables (`NVIDIA_API_KEY`) in your Vercel Dashboard or contact me to integrate a database (like Redis).
- **Hidden Data**: `exps.json` is not in the `public/` folder, preventing direct browser access.

## 📁 Project Cleanup
- **Prototype Backup**: All old Streamlit prototyping files have been moved to the `prototype_backup/` folder to keep your production workspace clean.
- **Dependencies**: All required packages are installed in the `.venv` in this folder.

## 🚀 Deployment
- **Local Test**: Run `.\.venv\Scripts\python -m uvicorn api.main:app --reload`.
- **Vercel**: Run `vercel`.

## 🚀 How to Deploy to Vercel
1.  **Install Vercel CLI**: `npm i -g vercel` (if not already installed).
2.  **Login**: `vercel login`.
3.  **Deploy**: Run `vercel` in the root directory.
4.  **Environment Variables**: In the Vercel Dashboard, set the following:
    - `NVIDIA_API_KEY`: Your NVIDIA NIM API Key.
    - `ADMIN_TOKEN`: A secret password for admin edits (default is `supersecret`).

## 🔑 Accessing the Admin Portal
- **URL**: `YOUR_DEPLOYED_URL/secret-admin-portal`
- **Login**: Enter your `ADMIN_TOKEN` to view and edit the raw experiment data.
- **Save**: Changes are saved directly back to `exps.json` on the server.

## 📁 Key File Changes
- `api/main.py`: The new backend logic.
- `public/index.html`: The main landing page.
- `public/style.css`: Premium styling.
- `public/app.js`: Frontend logic for experiments and chat.
- `data/exps.json`: Updated to point to the new `public/audio/` path.
- `vercel.json`: Handles routing and deployment settings.
