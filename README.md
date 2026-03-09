# CloudTasker

A simple task management API built with FastAPI and Google Cloud Firestore, deployed on Cloud Run.

## Features
- Create, read, update, delete tasks per user
- Firestore as NoSQL database
- CI/CD with GitHub Actions
- Dockerized for Cloud Run

## Local Development

### Prerequisites
- Python 3.12+
- Google Cloud SDK (for Firestore emulator or real project)
- (Optional) Firestore emulator for local testing

### Setup
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows