# PAIMANA — Infrastructure Intelligence Platform
## Frontend Application Branch (`Frontend`)

PAIMANA is an advanced infrastructure project surveillance, risk forecasting, and decision-support platform designed for the Ministry of Statistics and Programme Implementation (MoSPI) and major national infrastructure agencies.

This branch contains the **complete, production-ready frontend application** and all static assets, datasets, 3D visualizations, and interactive analytics.

---

## 🏛️ Platform Architecture

The frontend is built using **Next.js 14 (App Router)**, **React 18**, **TypeScript**, and **Tailwind CSS**, featuring:
- **National Command Center**: Macro surveillance KPIs, GIS geographic distribution, and cross-quadrant risk prioritization matrix.
- **National Infrastructure Registry (`/projects`)**: Real-time search across 2,741 monitored projects by Project ID, Name, Agency, State, and Sector with multi-criteria filtering.
- **Project Intelligence Dossier (`/projects/[id]`)**: Comprehensive 9-section project deep dive, including longitudinal cost/schedule trajectory charts, physical progress vs financial burn, and decomposed risk drivers.
- **Custom Project Intake & Intelligence (`/custom-project` & `/custom-project/result`)**: Intake form for unlisted infrastructure assets, generating multi-dimensional risk predictions, milestone duration analysis, capital escalation audits, and ranked model-derived signals.
- **What-If Simulation Sandbox (`/simulation`)**: Interactive scenario modeling engine for evaluating intervention outcomes.
- **Theme Parity**: Complete Light Mode and Dark Mode support with cinematic high-contrast glassmorphic design.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18.17+ or v20+
- **npm**: v9+

### 2. Installation
Navigate into the `FRONTEND/` directory (or use workspace commands from root):

```bash
cd FRONTEND
npm install
```

### 3. Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Production Build
```bash
npm run build
npm run start
```

---

## 🔌 Backend API Integration

The frontend includes a Next.js API Gateway route (`/api/predict/project`) that dispatches inference requests to the external PAIMANA ML microservice:

- **Target Endpoint**: `POST http://127.0.0.1:8000/predict/project`
- **Payload Schema**:
  ```json
  {
    "project_id": "string",
    "project_name": "string",
    "agency": "string",
    "state": "string",
    "original_cost_crore": 1000.0,
    "revised_cost_crore": 1200.0,
    "approval_start_date": "YYYY-MM",
    "original_completion_date": "YYYY-MM",
    "revised_completion_date": "YYYY-MM",
    "physical_progress_percent": 45.0,
    "cumulative_expenditure_crore": 550.0,
    "is_completed": false
  }
  ```
- **Response**: Integrated risk score, component risks (schedule delay, cost overrun, schedule revision), risk band, dynamic model certainty, and ranked `model_risk_signals`.

*Note: The machine learning models and FastAPI microservice implementation reside in the dedicated backend repository and are decoupled from this frontend branch.*

---

## 📂 Directory Structure

```
FRONTEND/
├── app/                              # Next.js App Router pages & API routes
│   ├── page.tsx                      # National Command Center
│   ├── layout.tsx                    # Root HTML layout & Theme Provider
│   ├── globals.css                   # Global styles & design system tokens
│   ├── projects/page.tsx             # Project Search & Registry
│   ├── projects/[id]/page.tsx        # Project Dossier View
│   ├── custom-project/page.tsx       # Custom Project Intake Form
│   ├── custom-project/result/page.tsx # Custom Project Analytical Dashboard
│   ├── simulation/page.tsx           # What-If Simulation Sandbox
│   └── api/predict/project/route.ts  # Gateway proxy to ML service
├── components/                       # Modular UI components
│   ├── layout/                       # Navbar, ThemeToggle
│   ├── hero/                         # CommandHero, LandscapeCanvas (Three.js 3D)
│   ├── projects/                     # Search, Filters, Cards, Table
│   │   ├── dossier/                  # 9 Dossier Analytical Charts & Views
│   │   └── custom/analytics/         # 8 Custom Project Analytics & Transparency Views
│   ├── map/                          # GIS National Infrastructure Map
│   └── ...                           # Early Warning, Trust Layer, Anomalies
├── lib/                              # API clients, TypeScript types, utils, sector taxonomy
├── public/                           # Static assets
│   ├── data/                         # Pre-compiled longitudinal datasets & search indices
│   └── videos/                       # Platform video assets & demonstrations
├── package.json                      # Frontend dependencies & scripts
├── tailwind.config.ts                # Design tokens & color palette
├── tsconfig.json                     # TypeScript configuration
└── next.config.mjs                   # Next.js build configuration
```
