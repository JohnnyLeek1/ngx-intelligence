# ngx-intelligence User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Account Setup](#account-setup)
4. [Dashboard Overview](#dashboard-overview)
5. [Processing Documents](#processing-documents)
6. [Viewing History](#viewing-history)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

**ngx-intelligence** is an AI-powered document processing companion for Paperless-NGX that automatically enhances your documents through:
- Intelligent document classification
- Automatic tagging
- Correspondent identification
- Smart document renaming
- Date extraction

Using local AI models via Ollama, ngx-intelligence learns from your feedback to improve accuracy over time.

---

## Getting Started

### Prerequisites
- A running Paperless-NGX instance
- Paperless-NGX API token
- Ollama installed and running (local or remote)

### First-Time Setup

1. **Access the Application**
   - Navigate to `http://localhost:3000` (or your configured URL)
   - You'll be greeted with the login page

2. **Create Your Account**
   - Click "Register" on the login page
   - Fill in the registration form:
     - **Username**: Your desired username for ngx-intelligence
     - **Password**: Strong password (min 8 characters)
     - **Paperless-NGX URL**: URL of your Paperless instance (e.g., `http://paperless.local:8000`)
     - **Paperless Username**: Your Paperless-NGX username
     - **Paperless Auth Token**: Your Paperless API token

3. **Getting Your Paperless API Token**
   - Log into Paperless-NGX
   - Go to Settings → User Accounts
   - Click your username
   - Copy your API token
   - If no token exists, click "Generate Token"

---

## Account Setup

### Paperless Integration Validation

When you register, ngx-intelligence:
1. Validates your Paperless URL is reachable
2. Verifies your API token is valid
3. Confirms your username matches
4. Tests basic API access

If validation fails, check:
- Paperless-NGX is running and accessible
- URL is correct (include http:// or https://)
- API token is current and not expired
- Username matches exactly (case-sensitive)

### User Roles

- **Admin**: Full access to configuration, AI settings, and all features
- **Standard User**: Can process documents and view their own history

The first user created automatically becomes an admin.

---

## Dashboard Overview

### Statistics Cards

The dashboard displays key metrics:

1. **Total Processed**
   - Documents processed today
   - Weekly totals
   - All-time count
   - Percentage changes

2. **Processing Queue**
   - Current queue depth
   - In-progress documents
   - Failed documents requiring attention

3. **Success Rate**
   - 7-day success rate graph
   - Trending indicators
   - Average confidence scores

4. **Processing Time**
   - Average time per document
   - Performance trends

### Current Jobs

Real-time view of documents being processed:
- Document name
- Current processing step
- Progress indicator
- Estimated time remaining

### Recent Activity

Last 10 processed documents with:
- Document title
- Processing timestamp
- Status (success/pending/failed)
- Confidence score
- Quick action buttons

### Alerts

Important notifications:
- Failed processing jobs
- Low confidence warnings (< 70%)
- Configuration issues
- Paperless connection problems

---

## Processing Documents

### Processing Modes

#### Real-time Processing (Default)
- Continuously polls Paperless for new documents
- Processes documents as they arrive
- Default interval: 30 seconds
- Fully automatic

#### Batch Processing
- Processes documents on schedule
- Configurable thresholds:
  - Document count (e.g., every 100 documents)
  - Time interval (e.g., every hour)
  - Combined (whichever comes first)

#### Manual Processing
- On-demand processing
- Reprocess specific documents
- Process filtered sets
- Useful after configuration changes

### What Gets Processed

For each document, ngx-intelligence:

1. **Identifies Correspondent**
   - Extracts sender/recipient from content
   - Matches against existing correspondents
   - Creates new correspondent if enabled

2. **Classifies Document Type**
   - Analyzes content to determine type
   - Matches to existing document types
   - Suggests new types if enabled

3. **Suggests Tags**
   - Applies relevant tags based on content
   - Follows configured tag rules
   - Respects min/max tag limits

4. **Extracts Date**
   - Finds most relevant date in document
   - Priority: Invoice date > Letter date > Event date
   - Validates date format

5. **Generates Title**
   - Creates descriptive filename
   - Follows your naming template
   - Removes redundant information

### Approval Workflow (Optional)

When approval mode is enabled:
1. AI processes document and generates suggestions
2. Document tagged as "approval-pending" in Paperless
3. Review suggestions in Approval Queue
4. Approve, reject, or edit suggestions
5. Provide feedback for rejected suggestions

### Confidence Scores

Each suggestion includes a confidence score (0-100%):
- **90-100%**: Very high confidence, likely accurate
- **70-89%**: Good confidence, review recommended
- **50-69%**: Medium confidence, review required
- **<50%**: Low confidence, manual review necessary

Default threshold: 70% (configurable)

---

## Viewing History

### History Page Features

#### Document Table
- **Columns**: Document, Processed Date, Status, Confidence, Actions
- **Sorting**: Click column headers to sort
- **Filtering**: Filter by status, date range, document type
- **Search**: Find documents by title or ID
- **Pagination**: Navigate through results

#### Status Indicators
- ✅ **Success**: Processed and applied successfully
- ⏳ **Pending Approval**: Awaiting your review
- ❌ **Failed**: Processing error occurred
- 🔄 **Rejected**: Rejected after review

#### Document Details

Click any document to view:
- **Original Values**: Before processing
- **Suggested Values**: AI recommendations
- **Applied Values**: Final values (if approved)
- **Confidence Scores**: Per-field confidence
- **Processing Log**: Step-by-step details
- **User Feedback**: Any notes you provided

#### Actions

From history page you can:
- **Reprocess**: Run document through pipeline again
- **View in Paperless**: Open document in Paperless-NGX
- **Export**: Download processing history (CSV/JSON)
- **Bulk Reprocess**: Reprocess multiple documents

---

## Configuration

### General Settings

**User Profile**:
- Change password
- Update email
- Update Paperless credentials
- View account statistics

**Preferences**:
- Default dashboard view
- Notification settings
- Date/time format

### AI Configuration (Admin Only)

**Model Selection**:
- Choose Ollama model (e.g., llama3.2, mistral)
- View model details (size, parameters)
- Pull new models from Ollama library

**Parameters**:
- **Temperature** (0.0-1.0): Creativity vs consistency
  - 0.2-0.3: Conservative, consistent (recommended for classification)
  - 0.5-0.7: Balanced
  - 0.8-1.0: Creative, varied
- **Top P**: Nucleus sampling threshold
- **Max Tokens**: Maximum response length

**Prompts**:
- **System Prompt**: Base AI instructions
- **Task Prompts**: Per-task instructions (classification, tagging, etc.)
- **Variables**: Available template variables
- **Preview**: Test prompts with sample documents

### Processing Configuration (Admin Only)

**Mode**:
- Real-time polling
- Batch processing
- Manual only

**Real-time Settings**:
- Polling interval (seconds)
- Concurrent workers (1-10)
- Retry attempts (1-5)

**Batch Settings**:
- Cron schedule (e.g., `0 2 * * *` for 2 AM daily)
- Document threshold
- Time threshold
- Combined rule logic

**Retry Logic**:
- Max retry attempts
- Backoff strategy (exponential)
- Retry delay

### Tag Rules (Admin Only)

Configure how tags are applied:

**Quantity Rules**:
- Minimum tags per document (default: 0)
- Maximum tags per document (default: 10)

**Confidence**:
- Minimum confidence threshold (default: 70%)
- Per-tag confidence tracking

**Naming Conventions**:
- Tag prefix for auto-generated tags
- Case convention (lowercase, Title Case)
- Excluded tags (never auto-apply)

**Auto-Creation**:
- Allow AI to create new tags
- Require admin approval for new tags

### Naming Templates (Per-User)

Customize how documents are renamed:

**Available Variables**:
- `{date}` - Document date (YYYY-MM-DD)
- `{type}` - Document type
- `{correspondent}` - Correspondent name
- `{title}` - AI-generated title
- `{original}` - Original filename

**Example Templates**:
- `{date}_{correspondent}_{type}_{title}` (default)
- `{correspondent}/{date}_{title}`
- `{type}/{date}_{correspondent}`

**Date Formats**:
- YYYY-MM-DD (2024-03-15)
- MM-DD-YYYY (03-15-2024)
- DD-MM-YYYY (15-03-2024)
- YYYY/MM/DD (2024/03/15)

**Tips**:
- Use preview to see generated names
- Keep templates concise
- Avoid special characters (/, \, :, *)
- Test with different document types

---

## Troubleshooting

### Common Issues

#### Documents Not Processing

**Symptoms**: Queue stays at 0, no new documents detected

**Solutions**:
1. Check Paperless connection: Settings → Check Status
2. Verify polling is enabled: Settings → Processing → Mode
3. Check Paperless has new documents
4. Review logs for errors
5. Restart queue manager: Settings → Restart Processing

#### Low Confidence Scores

**Symptoms**: All documents have confidence < 50%

**Solutions**:
1. Use larger, more capable model (llama3.2 vs mistral-7b)
2. Improve system prompt with examples
3. Reduce temperature (0.2-0.3)
4. Train with example library (approve correct suggestions)
5. Check document OCR quality in Paperless

#### Ollama Connection Failed

**Symptoms**: "Ollama connection error" in logs

**Solutions**:
1. Verify Ollama is running: `ollama list`
2. Check Ollama URL: Settings → AI → Ollama URL
3. Test connection: `curl http://localhost:11434/api/tags`
4. If using Docker: Use `http://host.docker.internal:11434`
5. Check firewall settings

#### Incorrect Classifications

**Symptoms**: Documents consistently misclassified

**Solutions**:
1. Provide feedback on incorrect suggestions
2. Add examples to prompt (Settings → AI → Prompts)
3. Increase confidence threshold (reject low-confidence)
4. Use approval workflow to review before applying
5. Adjust AI temperature (lower = more consistent)

#### Slow Processing

**Symptoms**: Processing takes minutes per document

**Solutions**:
1. Use smaller, faster model (mistral-7b vs llama3-70b)
2. Reduce max tokens in AI settings
3. Increase concurrent workers (if multi-core)
4. Enable GPU acceleration for Ollama
5. Use batch mode instead of real-time

### Getting Help

If issues persist:

1. **Check Logs**:
   - Backend: `docker-compose logs backend`
   - Frontend: Browser console (F12)
   - Processing: Settings → View Processing Logs

2. **Review Documentation**:
   - This user guide
   - Deployment guide (DEPLOYMENT.md)
   - API documentation (/api/docs)

3. **GitHub Issues**:
   - Search existing issues
   - Create new issue with logs and reproduction steps

4. **Community**:
   - GitHub Discussions
   - Discord/Slack (if available)

---

## Tips & Best Practices

### Optimize Accuracy

1. **Start with Approval Workflow**: Review first 50-100 documents to build example library
2. **Provide Feedback**: Reject incorrect suggestions with detailed feedback
3. **Use Consistent Naming**: Establish naming conventions in Paperless first
4. **Tag Strategically**: Don't over-tag; focus on 3-5 meaningful tags per document
5. **Monitor Confidence**: Track trends; declining confidence indicates model drift

### Performance Optimization

1. **Model Selection**: Balance speed vs accuracy
   - Fast: mistral-7b, llama3.2-8b
   - Balanced: llama3.2-70b
   - Accurate: mixtral-8x7b
2. **Concurrent Workers**: 1-2 for CPU, 3-5 for GPU
3. **Batch Processing**: Use for large backlogs (off-peak hours)
4. **Polling Interval**: 30s default, increase to 60s+ for lower load

### Security Best Practices

1. **Strong Passwords**: Min 12 characters, mixed case, numbers, symbols
2. **Rotate API Tokens**: Change Paperless tokens periodically
3. **HTTPS**: Use reverse proxy (nginx, Caddy) for SSL/TLS
4. **Network Isolation**: Keep services on isolated Docker network
5. **Regular Backups**: Backup database and configuration

### Maintenance

1. **Weekly**: Review failed documents, check queue health
2. **Monthly**: Update models, review examples, backup database
3. **Quarterly**: Update ngx-intelligence, Ollama, dependencies
4. **Yearly**: Review and optimize configuration, prune old logs

---

**End of User Guide**

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
For API documentation, visit `/api/docs` when application is running
