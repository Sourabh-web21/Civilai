# Features

## Project Management
- Create and manage construction projects with details like location, contractor, cost, timeline, and progress.
- Track project status across planning, ongoing, on hold, and completed states.
- Monitor physical and financial progress from project records and dashboard summaries.
- Support milestones, EOTs, revised-cost entries, and related project tracking data.

## Task Management
- Create tasks linked to projects or managed as standalone work items.
- Assign tasks to users, set priorities, due dates, and status.
- Filter tasks by status and view them across the full workspace.
- Store task notes, file attachments, and progress updates.

## Team and User Management
- Manage users with roles such as admin, manager, and client.
- Support profile editing, password change, and password reset workflows.
- View team members with assigned task counts and contact details.

## Dashboard and Analytics
- Show a central dashboard with project and task counts by status.
- Visualize project/task distribution using charts and progress indicators.
- Give users a quick view of overall delivery health and activity.

## Email Intelligence
- Sync inbox activity through IMAP with safe, rate-limited checks.
- Save email attachments and make them available to the RAG pipeline.
- Detect meeting links and track recent mailbox activity.
- Review and send compose, reply, or forward emails through SMTP.

## Meeting Assistant
- Start meeting bots for Google Meet, Zoom, or Microsoft Teams links.
- Poll meeting transcripts and generate Minutes of Meeting output.
- Turn meeting activity into structured follow-up content.

## CivilAI Chat Assistant
- Ask questions in natural language about project documents.
- Return document-grounded answers instead of generic responses.
- Show source references and cache-hit indicators in the chat UI.
- Handle greetings and off-topic queries gracefully.

## RAG and Document Search
- Ingest PDF, TXT, and Markdown documents from the documents folder.
- Use cluster-based retrieval for faster search over larger document sets.
- Reuse similar queries through semantic caching.
- Switch between offline and external embeddings/LLM backends.

## Notifications and Workflow Automation
- Notify assigned users when tasks are created or updated.
- Support automatic email sync and document reload workflows.
- Keep mailbox sync separate from the RAG document pipeline for cleaner operation.

## Security and Reliability
- Use JWT-based authentication for secure API access.
- Apply throttling and cooldowns for email and AI-related actions.
- Configure external services through environment-based settings.
