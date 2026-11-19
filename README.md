#Project Structre

opspilot/
│
├── apps/
│   ├── api/
│   │   └── __init__.py
│   │
│   └── worker/
│       └── __init__.py
│
├── packages/
│   └── evidence/
│       └── __init__.py
│
├── testbed/
│   ├── scenarios/
│   ├── ground_truth/
│   └── snapshots/
│
├── evals/
│
├── infra/
│   └── docker/
│
├── tests/
│   └── evidence/
│
├── .github/
│   └── workflows/
│
├── .gitignore
├── .python-version
├── .env.example
├── README.md
├── pyproject.toml
└── uv.lock



What each directory contains
Directory	Responsibility
apps/api	FastAPI backend
apps/worker	LangGraph agent
packages/evidence	Deterministic Python investigation tools
testbed/scenarios	Incident generation scripts
testbed/ground_truth	Actual known root causes
testbed/snapshots	Frozen logs, metrics and traces
evals	AI agent evaluation
infra/docker	Docker Compose configuration
tests/evidence	Pytest tests for evidence tools
.github/workflows	GitHub Actions CI pipeline