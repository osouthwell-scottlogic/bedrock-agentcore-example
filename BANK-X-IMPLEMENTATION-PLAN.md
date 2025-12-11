# Bank X Financial Product Marketing System - Implementation Plan

## Overview
Transform the current utility billing agent into a financial product marketing system where users can request "email interesting customers" to send tailored IPO/bond offers.

## Architecture
- **MCP Tools**: Assess customer preferences, research products, manage emails
- **Approval Flow**: Via chat interface with indefinite wait
- **Email Storage**: Plain text files in date-based folders
- **Multi-Agent**: Use Strands built-in capabilities where available

## Implementation Steps

### 1. Replace Data Schema and Files
Create new data files:
- `bank-x-customers.json` - Array of 5-8 customers with:
  - `customerId`, `name`, `email`, `interestedInBonds`, `portfolioValue`
- `government-bond-y.json` - Product with:
  - `productId`, `name`, `yield`, `maturity`, `minInvestment`, `description`
- Copy both to `cdk/assets/` for production

### 2. Implement New MCP Tools
Add tools in both `strands_agent.py` and `strands_agent_local.py`:
- `list_customers()` - Returns customer summary list
- `get_customer_profile(customer_id)` - Returns full customer profile
- `get_product_details(product_name)` - Returns product JSON
- `search_market_data(product_type)` - Returns mock comparable bonds + description
- `send_email(customer_email, subject, body)` - Writes to `sent_emails/YYYY-MM-DD/{ISO8601-timestamp}_{email}_{subject-slug}.txt`
  - Skip individual failures with try/except
- `get_recent_emails(limit)` - Parses filenames for metadata

### 3. Update Lambda Functions and S3 Structure
Modify `mcp-stack.ts`:
- Add `SendEmailFunction` and `GetRecentEmailsFunction`
- Grant S3 `PutObject` and `ListObjects` for `sent-emails/*` prefix
- Pass Lambda ARNs to `runtime-stack.ts` environment variables

### 4. Configure Multi-Agent
In agent files:
- Research Strands native multi-agent support
- Implement if available, or use single comprehensive agent
- Update system prompt workflow:
  1. Research product
  2. Filter customers (`interestedInBonds == true` and `portfolioValue >= minInvestment`)
  3. Generate personalized draft emails
  4. Present all drafts for approval
  5. Wait indefinitely for "yes" confirmation
  6. Send emails and report successes/failures
- Leverage AgentCore memory for session state

### 5. Customize Frontend for Bank X
Update `App.tsx`:
- Bank X branding and title "Bank X Financial Assistant"
- Support prompts:
  - "Email customers about Government Bond Y"
  - "Show recently sent emails"
  - "Research bond market trends"

### 6. Test Locally and Deploy
- Run `dev-local.ps1` to validate:
  - Customer matching logic
  - Approval flow with memory
  - Emails to `agent/local_data/sent_emails/2025-12-11/`
  - Error skipping
- Deploy with `deploy-all.ps1`

## Design Decisions

### Customer Matching
- Basic filter: `interestedInBonds == true` AND `portfolioValue >= minInvestment`

### Email Format
- Plain text with personalization
- Filename: `{ISO8601-timestamp}_{email}_{subject-slug}.txt` (subject truncated at 50 chars)
- Storage: Date-based folders `sent_emails/YYYY-MM-DD/`

### Market Data
- Mock JSON with 3-5 comparable bonds
- Includes `description` field summarizing market trends

### Approval Mechanism
- Via chat interface
- Wait indefinitely without re-prompting
- Use AgentCore memory for state persistence

### Error Handling
- Skip individual email send failures
- Report summary of successes/failures to user

## Date
Implementation plan created: December 11, 2025
