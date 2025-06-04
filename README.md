# ProjectX QA Report

ProjectX generates QA dashboards using Robot Framework and custom Python modules. It reads test result data and defect logs from JSON files and renders an interactive HTML report based on the templates under `TEMPLATES/`.

## Directory layout

- `CORE/` – core services and metrics logic for building the report.
- `DATA/` – example JSON files with test summaries and defects.
- `INFRASTRUCTURE/` – data loaders and the HTML renderer.
- `LOG/` – sample log files from previous runs.
- `REPORT/` – generated QA reports.
- `ROBOT/` – Robot Framework test suite (`Setup.robot`).
- `TASK/` – task configuration example.
- `TEMPLATES/` – HTML templates and front‑end assets.
- `UTILS/` – shared utility functions.
- `test-project/` – optional Playwright test project.

## Install Python requirements

Use Python 3.7+ and install dependencies from `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Robot tests

Execute the Robot suite to generate a new report:

```bash
robot ROBOT/Setup.robot
```

The standard Robot `report.html`, `log.html` and `output.xml` files will be created in the repository root. The QA report HTML will appear in the `REPORT/` directory.

## Optional: run Playwright tests

If you want to execute the Node.js Playwright tests:

```bash
cd test-project
npm install
npx playwright test
```

