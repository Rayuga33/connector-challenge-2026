# EquipIntel

**An AI-powered unified intelligence platform for equipment rental businesses.**

EquipIntel brings business data and communications into one place, helping rental businesses understand operations, monitor performance, and retrieve actionable insights through natural-language queries.

**Live application:** https://connector-challenge-2026.onrender.com/  
**GitHub repository:** https://github.com/Rayuga33/connector-challenge-2026

## Overview

Equipment rental businesses often manage information across multiple systems, including customer records, equipment inventories, rental contracts, invoices, payments, and communications.

EquipIntel aims to unify this information into a queryable intelligence layer.

The current implementation includes:
- Business dashboard with operational KPIs.
- Equipment, customer, rental, quotation, invoice, and payment data.
- Analytics for fleet utilization, revenue, outstanding balances, and overdue invoices.
- Natural-language business queries with supporting source records.
- Gmail OAuth integration using the official Google API.
- Persistent PostgreSQL storage using Supabase.
- A web dashboard deployed on Render.

## Current implementation status

| Component | Status |
|---|---|
| Business dashboard | Implemented |
| Business analytics | Implemented |
| Natural-language query engine | Implemented using rule-based query handling |
| PostgreSQL database | Implemented using Supabase |
| Gmail OAuth connection | Implemented and tested |
| Gmail mailbox profile retrieval | Tested locally and on deployment |
| Gmail message import | Tested locally; production import has resource limitations |
| Gmail classification | Implemented for imported messages |
| WhatsApp Business connector | Not yet implemented |
| Google Drive connector | Not yet implemented |
| Unified cross-connector intelligence | Partially implemented; business data and imported Gmail communications are stored in a common database |

**Important:** Gmail bulk importing is not currently reliable on the free production hosting instance because of memory constraints. The deployed application can verify the Gmail connection and retrieve mailbox profile information, but production bulk import should not be considered fully operational.

WhatsApp and Google Drive are future connector integrations, not completed features.

## Architecture

The application uses:

- **Backend:** Python and Flask
- **Frontend:** HTML, CSS, JavaScript, Bootstrap and dashboard charts
- **Database:** PostgreSQL hosted on Supabase
- **Local development database:** SQLite
- **Email integration:** Gmail API and Google OAuth 2.0
- **Authentication:** Flask session-based application login
- **Deployment:** Render
- **Database connectivity:** Psycopg

### Project structure

```text
connector-challenge-2026/
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── AI_USAGE.md
│
├── src/
│   ├── connectors/
│   │   ├── gmail_auth.py
│   │   ├── gmail_importer.py
│   │   └── gmail_service.py
│   │
│   ├── database/
│   │   └── db.py
│   │
│   └── services/
│       ├── analytics.py
│       └── query_engine.py
│
├── templates/
│   ├── index.html
│   └── login.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── dashboard.js
```

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Rayuga33/connector-challenge-2026.git
cd connector-challenge-2026
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

Add the required database, application authentication, and Google OAuth configuration.

Never commit `.env`, OAuth credentials, access tokens, or database passwords.

### 5. Run the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Gmail integration

EquipIntel uses the official Gmail API with the read-only scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

The integration uses Google OAuth 2.0.

To configure Gmail integration:

1. Create or select a Google Cloud project.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Create an OAuth 2.0 Web Application client.
5. Add the appropriate local and production callback URLs.
6. Configure the Google OAuth environment variables.
7. Connect Gmail through the application.

OAuth tokens are encrypted before being stored in the database.

The integration is designed for read-only access. It does not send, delete, or modify emails.

## Database

The application uses Supabase PostgreSQL for persistent business data and encrypted Gmail OAuth token storage.

Local development and seed data can use SQLite.

The current demo dataset includes customers, equipment, rentals, quotations, invoices, payments, maintenance records, and communications.

## Deployment

The application is deployed on Render.

Production configuration:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Required environment variables must be configured in the hosting provider's environment settings.

The database connection string and OAuth secrets must remain server-side.

## Security considerations

- OAuth credentials and database connection strings are environment variables.
- Gmail access uses a read-only OAuth scope.
- OAuth tokens are encrypted before database storage.
- Sensitive local files and database files are excluded through `.gitignore`.
- The application should be extended with stronger organization-level authorization and tenant isolation before production use with multiple independent customers.
- Only data that the account owner is authorized to access should be connected.

## Limitations and future work

Planned improvements include:

1. Complete Google Drive connector with document extraction and classification.
2. Official WhatsApp Business Platform Cloud API integration, subject to eligibility and authorized access.
3. More robust Gmail ingestion with background jobs and pagination.
4. LLM-powered natural-language retrieval across all connected sources.
5. Improved organization-level access controls and tenant isolation.
6. Production-grade monitoring, error handling, and scalable deployment.

## Hackathon context

Built for the **E9Rental.ai / Equip9 Internet Pvt. Ltd. Connector Challenge 2026**.

This repository represents the current implementation and its actual tested capabilities. Features marked as planned or incomplete should not be interpreted as completed integrations.
