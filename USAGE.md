# Instantly.ai Analytics Flask App - Usage Guide

## Overview
This Flask app allows you to fetch and aggregate daily campaign analytics from multiple Instantly.ai workspaces (API keys) asynchronously. It provides endpoints to start analytics jobs, check their status, and view health information. Results are saved in JSON and can be converted to PDF.

---

## 1. Prerequisites
- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

---

## 2. Running the Flask Server
Start the server from your project directory:
```bash
python flask_server.py
```
- The server will run on `http://localhost:5000` by default.

---

## 3. API Endpoints

### a. Health Check
- **GET** `/health`
- **Purpose:** Check if the server is running.
- **Example:**
  ```bash
  curl http://localhost:5000/health
  ```

### b. Start Bulk Analytics Job
- **POST** `/analytics/bulk/start`
- **Purpose:** Start a new analytics job for one or more API keys.
- **Request Body Example:**
  ```json
  {
    "api_keys": [
      "YOUR_API_KEY_1",
      "YOUR_API_KEY_2"
    ],
    "start_date": "2025-08-11",
    "end_date": "2025-08-18"
  }
  ```
- **Example with curl:**
  ```bash
  curl -X POST http://localhost:5000/analytics/bulk/start \
    -H "Content-Type: application/json" \
    -d '{"api_keys": ["YOUR_API_KEY_1", "YOUR_API_KEY_2"], "start_date": "2025-08-11", "end_date": "2025-08-18"}'
  ```
- **Response:**
  ```json
  {
    "status": "accepted",
    "run_id": "<job-id>",
    "message": "Job started successfully"
  }
  ```

### c. Check Job Status & Results
- **GET** `/analytics/bulk/status/<run_id>`
- **Purpose:** Check the progress and results of a job.
- **Example:**
  ```bash
  curl http://localhost:5000/analytics/bulk/status/<run_id>
  ```
- **Response:**
  - Shows job status, completion %, and results (when done).
  - Includes per-workspace breakdown, errors, and daily totals.

---

## 4. Running the Test Script
- Edit `test_daily_sends.py` to add your API keys (or use placeholders for testing).
- Run the script:
  ```bash
  python test_daily_sends.py
  ```
- The script will:
  - Start a job
  - Poll for completion
  - Save results to `daily_sends.json`
  - Print a summary to the console

---

## 5. Converting Results to PDF
- Use the provided script to convert JSON results to PDF:
  ```bash
  python json_to_pdf.py
  ```
- Output: `analytics_report.pdf`

---

## 6. Error Handling
- Errors per workspace are reported in the job status response and in the PDF.
- Common issues:
  - Invalid API key
  - Network/SSL errors
  - API rate limits

---

## 7. Notes
- API keys should be kept secret. Use placeholders for public sharing.
- The app supports any number of workspaces (API keys) in a single request.
- Date format: `YYYY-MM-DD`.
- For large date ranges, the app splits requests into 7-day chunks for efficiency.

---

## 8. Example Workflow
1. Start the Flask server.
2. Run the test script or use curl to start a job.
3. Check job status until complete.
4. View results in `daily_sends.json` or convert to PDF.

---

## 9. Support
For questions or issues, open an issue in your repository or contact the maintainer.
