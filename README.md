# MediLens

### Verify medicine identity. Compare alternatives. Understand potential savings.

MediLens is a medicine identity and price-comparison tool. It helps users understand a branded medicine and compare it with lower-cost alternatives that pass its identity checks from the available dataset.

> **Retrieval is not verification.**

A fuzzy search can find a possible candidate, but it should not decide whether that candidate is a valid alternative. MediLens separates the two steps and verifies the **active ingredient, strength, and dosage form** before showing a result.

---

## The Problem

Finding a lower-cost medicine is not just a name-matching problem.

Two medicines with similar names can have different ingredients, strengths, or dosage forms. A system that relies only on fuzzy matching can return misleading results.

MediLens focuses on:

- Identifying the medicine behind a brand name
- Verifying its identity
- Comparing listed prices
- Calculating potential savings across multiple medicines

It is an informational comparison tool, not a prescription or diagnosis system.

---

## Architecture Diagram

![](Architecture%20diagram.png)

## How It Works

```text
Medicine Search
      ↓
Normalization
      ↓
Candidate Retrieval
      ↓
Identity Firewall
      ↓
Salt + Strength + Form Verification
      ↓
 ┌───────────┐
 │ Verified  │ → Price Comparison → Savings
 └───────────┘
      │
   Uncertain
      ↓
   Abstain
```

The **Identity Firewall** is the core of MediLens. Only candidates that pass the deterministic identity checks are shown as verified matches. When the system cannot confidently identify a medicine, it abstains instead of guessing.

Users can also add multiple medicines to a **prescription basket** to compare the original and alternative totals.

---

## Built on AWS

MediLens uses AWS serverless tooling through the Build It approach.

```text
Browser
   ↓
API Gateway
   ↓
AWS Lambda
   ↓
MediLens Engine
   ├── Candidate Retrieval
   ├── Identity Verification
   └── Price / Savings Calculation
```

### AWS technologies

| Component | Role |
|---|---|
| **AWS SAM** | Defines and builds the serverless application |
| **SAM Local** | Runs the API Gateway + Lambda workflow locally |
| **AWS Lambda runtime** | Executes the backend |
| **Docker** | Provides the local Lambda runtime |
| **Mangum** | Adapts FastAPI for Lambda |

The project deliberately uses only the infrastructure needed for the working flow rather than adding AWS services without a clear purpose.

---

## What I Learned

The biggest technical lesson was **separating retrieval from verification**. Fuzzy matching is useful for finding candidates, but similarity alone should not determine whether a medicine can be shown as a valid match.

I also learned how to take a FastAPI application and run it through a serverless AWS architecture using SAM, Lambda-compatible handlers, API Gateway configuration, Docker, and local Lambda execution.

---

## Data & Pricing

The processed dataset contains medicine identity information: brand name, active ingredient, strength, dosage form, and price.

Where usable market pricing was unavailable, synthetic demonstration prices were generated for the comparison workflow. **These should not be interpreted as current retail prices.**

---

## Safety

MediLens does not diagnose conditions, prescribe medicines, or tell users to switch medication.

A lower price or matching active ingredient does not by itself establish that a medicine is appropriate for an individual. Users should verify medication changes with a qualified healthcare professional.

---

## Built With

- **Backend:** Python, FastAPI, Pandas
- **Frontend:** HTML, CSS, JavaScript, Tailwind CSS
- **AWS:** SAM, Lambda runtime, API Gateway, Docker

---

## Run Locally

### Prerequisites

- Python 3.11+
- Docker Desktop
- AWS SAM CLI

### 1. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Build the AWS application

```bash
sam build
```

### 3. Start the local API

Make sure Docker Desktop is running, then:
```bash
sam local start-api --warm-containers EAGER
```
The API will run at:
```bash
http://127.0.0.1:3000
```

### 4. Start the Frontend

Open a new terminal
```bash
cd frontend
python -m http.server 5500
```
Then open:
```bash
http://127.0.0.1:5500
```

---

## Project

Built for **AWS First Commit (BUILD IT)** — September 2026.