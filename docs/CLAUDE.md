# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based REST API backend for an electrical/power systems management application. It manages Single Line Diagrams (SLDs), electrical components as nodes/edges, tasks, forms, photos, infrared sessions, and issues/quotes.

## Technology Stack

- **Python 3.11** with Flask 2.0+
- **Flask-SQLAlchemy** for PostgreSQL ORM
- **PostgreSQL** database (AWS RDS)
- **Gunicorn** WSGI server (4 workers in production)
- **Docker** for containerization
- **AWS ECR/EC2** for deployment

## Common Development Commands

### Local Development
```bash
# Run the Flask application locally
python app.py  # Runs on http://localhost:5000

# Install dependencies
pip install -r requirements.txt
```

### Docker Operations
```bash
# Build Docker image
docker build -t project-z-backend .

# Run locally with Docker
./build.sh  # Builds and runs container locally

# Deploy to AWS
./deploy.sh  # Builds, pushes to ECR, and deploys to EC2
```

## High-Level Architecture

### Core Domain Model Structure

The application centers around **SLD (Single Line Diagram)** entities, which organize all other components:

1. **Graph-based Component Model**: Electrical components are represented as nodes and edges with class definitions (NodeClass, EdgeClass) that define their types and behaviors.

2. **Task & Workflow System**: Tasks can be one-time or recurring, with automatic scheduling based on `recur_interval_months`. Forms collect structured data for tasks.

3. **Multi-Entity Mapping**: The system uses numerous mapping tables to create relationships between entities (e.g., sld_to_node, task_to_form, node_to_edge).

4. **Attribute Flexibility**: Most entities include JSONB `attributes` fields for extensible data storage without schema changes.

### Key API Patterns

- **Standard CRUD**: All entities follow `/entity/create` and `/entity/update/<id>` patterns
- **Bulk Retrieval**: `/sld/<id>` returns complete SLD with all related data in a single response
- **UUID Primary Keys**: All entities use UUIDs for primary keys
- **Soft Deletion**: Entities have `is_deleted` flags rather than hard deletes
- **Comprehensive Timestamps**: All entities track `created_at` and `modified_at`

### Database Considerations

- **Connection String**: Hardcoded in app.py - connects to AWS RDS PostgreSQL
- **Session Management**: Uses Flask-SQLAlchemy's session management
- **Transaction Handling**: Each request gets its own database session

### Important Implementation Details

1. **Task Scheduling**: When creating recurring tasks, the system automatically calculates `next_run_date` based on `recur_interval_months`.

2. **Photo Management**: Photos and IR photos are stored with S3 URLs, with metadata in the database.

3. **Issue Tracking**: Issues link to nodes/edges and can have associated quotes with line items.

4. **Form System**: Forms are versioned and can be linked to multiple tasks for data collection.

5. **IR Sessions**: Infrared inspection sessions track multiple IR photos with temperature data.

## Deployment Configuration

- **AWS ECR Repository**: `637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz`
- **Region**: us-east-2
- **Platform**: linux/amd64
- **Port**: 5000 (both local and production)

## Development Notes

- No formal test suite exists - consider adding pytest for testing
- No linting/formatting tools configured - consider adding black and flake8
- Database connection string is hardcoded - consider using environment variables
- No API documentation/OpenAPI spec - consider adding Flask-RESTX or similar