# Product Maintenance Plan

## Smart Complaint Management System

Two companion formats are stored here:

- **Editable Markdown reference:** [Product_Maintenance_Plan_Smart_Complaint_Management_System.md](Product_Maintenance_Plan_Smart_Complaint_Management_System.md)
- **Formatted Word document:** [SCMS_Product_Maintenance_Plan.docx](SCMS_Product_Maintenance_Plan.docx)

Both formats cover maintenance ownership, change/release steps, routine checks, backup and recovery, monitoring, security/privacy upkeep, incident severity, maintenance records, and review/approval. The Markdown is the preferred editable reference for future changes; compare/regenerate the formatted Word version whenever material content changes so the submitted copies remain aligned.

## Version and Operating Constraints

Both copies are Version 1.0, prepared on 10 October 2026. This is a proposed student-project maintenance baseline, not evidence of a managed production support service.

- Backup/restore commands are manual operating procedures; an automated backup schedule was not verified.
- Dedicated production monitoring/alerting is not configured in the repository.
- Real email/SMS/WhatsApp delivery is not operational until a provider is configured and delivery is verified end to end.
- The Jenkinsfile includes machine-specific paths; verify those assumptions before moving Jenkins to another host.
- Do not use local fallback secrets or demo passwords in an untrusted/shared deployment.

Review the plan against the final environment before the development freeze.

See the [Final Submission Readiness Checklist](../FINAL_SUBMISSION_READINESS.md).
