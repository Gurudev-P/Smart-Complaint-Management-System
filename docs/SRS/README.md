# Software Requirements Specification

## Smart Complaint Management System

This folder contains the Software Requirements Specification (SRS) for the Smart Complaint Management System, Project ID 67.

The SRS defines the functional requirements, non-functional requirements, business rules, data requirements, use cases, interfaces, constraints, and requirement traceability for the system.

## Document

**File:** `SRS_Smart_Complaint_Management_System.docx`

## Purpose

The SRS establishes the approved requirements baseline for the project.

It defines what the system must provide before architecture, detailed design, implementation, and testing begin.

## Scope

The system is a web-based complaint management platform that supports:

- User registration and authentication
- Complaint submission
- Complaint categorization and priority assignment
- Complaint assignment to staff or departments
- Complaint status tracking
- SLA monitoring and escalation
- Notifications
- Administrative dashboards and reporting
- Complaint history and resolution records

## User Roles

| Role             | Main Responsibilities                                                                                      |
|------------------|------------------------------------------------------------------------------------------------------------|
| User             | Register/login, submit complaints, view complaints, and track complaint status                             |
| Staff / Resolver | View assigned complaints, update status, and record resolution details                                     |
| Administrator    | Manage users and categories, assign complaints, configure SLA-related rules, and access dashboards/reports |

## Functional Requirements

The SRS defines functional requirements from **FR-01 to FR-24**, covering:

- Authentication and account management
- Complaint submission and tracking
- Categorization and priority management
- Assignment and resolution
- SLA monitoring and escalation
- Notifications
- Dashboard and reporting

## Non-Functional Requirements

The SRS defines requirements related to:

- Performance
- Safety
- Security
- Usability
- Reliability
- Maintainability
- Software quality attributes

Security requirements include authentication, role-based authorization, password protection, and input validation.

## Data Requirements

The SRS identifies the major logical data entities required by the system:

- User
- Complaint
- Category
- Assignment
- Status History
- SLA
- Notification
- Resolution

## Business Rules

The SRS defines rules governing:

- Authenticated complaint submission
- Valid category and priority
- Authorized assignment
- Authorized status updates
- Resolution requirements
- SLA calculation
- Escalation
- Complaint access
- Administrative access
- Status-history retention

## Analysis Models

The SRS includes:

- Use case model
- High-level complaint workflow
- Requirement Traceability Matrix
- Glossary
- Field layouts

## Relationship With Other Documents

The SRS is the requirements baseline for the project.

The project documentation flow is:

`SRS → High-Level Architecture → Software Design → Implementation → Testing`

Architecture and design decisions should remain traceable to the requirements defined here.

## Status

**Status:** Requirements Baseline

**Next Related Phase:** High-Level Architecture
