# Full Stack Test Automation Framework

### Playwright • Cucumber BDD • Python Behave • PostgreSQL • GitHub Actions • Allure

This project demonstrates a **production-style automation architecture designed by an SDET**, validating **UI, API, and database layers** of a full-stack application with **BDD testing and CI/CD automation**.

The framework integrates **Playwright UI automation, Python Behave API testing, PostgreSQL validation, GitHub Actions CI pipelines, and unified Allure reporting**.

---

# Project Overview

The system under test includes:

• React frontend
• FastAPI backend
• PostgreSQL database

Automation validates the system across **all layers of the application stack**.

---

# Test Architecture

```
UI BDD Tests (Playwright + Cucumber)
            │
            ▼
       React Frontend
            │
            ▼
       FastAPI Backend
            │
            ▼
      PostgreSQL Database
            │
            ▼
      Database Validation
```

The framework verifies application behavior from **user interaction to database state**.

---

# Technologies

## UI Automation

• Playwright
• Cucumber BDD
• TypeScript
• Page Object Model

## API Automation

• Python
• Behave BDD
• Requests library

## Database Testing

• PostgreSQL
• Python validation scripts

## CI/CD

• GitHub Actions
• automated environment setup
• sequential test pipeline

## Reporting

• Allure Reports
• unified dashboard for UI, API, and DB tests

---

# Continuous Integration Pipeline

The project includes an automated CI pipeline that runs the entire test suite.

Pipeline stages:

```
Setup Backend + Frontend
        │
        ▼
API BDD Tests
        │
        ▼
UI BDD Tests
        │
        ▼
DB BDD Tests
        │
        ▼
Unified Allure Report
```

Each stage validates a different layer of the system.

---

# BDD Example

Example scenario validating business functionality.

```
Scenario: Admin uploads inventory Excel file
Given admin logs in
When admin uploads an inventory Excel file
Then cars should be added to inventory
And cars should exist in the database
```

---

# Key Engineering Features

• Layered automation architecture
• BDD test design
• Playwright Page Object Model
• API validation with Behave
• database state verification
• CI/CD automation with GitHub Actions
• environment configuration using .env and GitHub Secrets
• unified reporting using Allure

---

# Reporting

Test results are aggregated into a **single Allure dashboard**.

The report provides:

• scenario results
• step level execution details
• screenshots on failure
• execution timeline
• test statistics

---

# Project Structure

```
app/
   backend/
   frontend/

test/
   API/
   UI/
   DB/
   fixtures/
   reports/

docs/
   portfolio website

screenshots/
   CI pipeline
   Allure dashboard
   architecture diagrams
```

---

# Running Tests Locally

Run API tests

```
behave API/features
```

Run UI tests

```
cd test/UI
npx cucumber-js
```

Run database validation tests

```
behave DB/features
```

---

# Portfolio Purpose

This project demonstrates **real-world SDET skills including automation architecture design, CI/CD integration, and multi-layer testing strategy**.

It serves as a **portfolio project showcasing modern software test engineering practices**.

---
