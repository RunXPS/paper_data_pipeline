# Paper Data Pipeline

Daily quant-research pipeline: fetches arXiv papers, screens with Groq, deep-analyzes with Gemini, accumulates results in Supabase, and sends a weekly email summary on Sunday.

## Local Development

- **Conda env:** `paper_pipeline`
- **Groq API key:** [console.groq.com/keys](https://console.groq.com/keys)

```bash
conda activate paper_pipeline
pip install -r requirements.txt
cd src && python main.py
```

Set environment variables in a `.env` file or export them:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq abstract screening |
| `GEMINI_API_KEY` | Gemini PDF analysis |
| `DATABASE_URL` | Supabase Postgres connection string |
| `SENDER_EMAIL` | Gmail address for weekly summary |
| `SENDER_PASSWORD` | Gmail app password |
| `RECEIVER_EMAIL` | Recipient for weekly summary |

---

## GitHub Actions Setup

### Step 1 — Create the Supabase table

1. Open your [Supabase dashboard](https://supabase.com/dashboard) and select your project.
2. Go to **SQL Editor** → **New query**.
3. Run:

```sql
create table accumulated_papers (
  id              uuid primary key default gen_random_uuid(),
  week_key        text not null,
  title           text not null,
  published       text,
  summary         text,
  link            text,
  screener_reason text,
  deep_analysis   jsonb,
  created_at      timestamptz default now()
);

create index idx_accumulated_papers_week_key on accumulated_papers (week_key);
```

4. Confirm the table appears under **Table Editor** → `accumulated_papers`.

### Step 2 — Get Supabase database URL

1. In Supabase, go to **Project Settings** → **Database**.
2. Under **Connection string**, select **URI** and copy the connection string.
3. Use the **Transaction pooler** URI (port `6543`) for short-lived connections like this pipeline.
4. Replace `[YOUR-PASSWORD]` with your database password — this becomes `DATABASE_URL`.

### Step 3 — Prepare Gmail app password

1. Enable 2FA on your Google account.
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords).
3. Generate an app password for "Mail" — use this as `SENDER_PASSWORD`.

### Step 4 — Add GitHub repository secrets

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**.
2. Add each secret:

| Secret name | Value |
|-------------|-------|
| `GROQ_API_KEY` | [Groq console](https://console.groq.com/keys) |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `DATABASE_URL` | Supabase Postgres connection string (transaction pooler URI) |
| `SENDER_EMAIL` | Gmail address used to send |
| `SENDER_PASSWORD` | Gmail app password |
| `RECEIVER_EMAIL` | Email address to receive the weekly summary |

### Step 5 — Push and test manually

1. Push the code to `master` (the default branch).
2. Go to **Actions** → **Daily Quant Pipeline** → **Run workflow**.
3. Check the job log for arXiv fetch, Groq screening, Gemini analysis, and Supabase inserts.
4. Verify rows appear in Supabase **Table Editor** → `accumulated_papers`.

### Step 6 — Confirm the schedule

- The workflow runs daily at **12:00 UTC** (`0 12 * * *`).
- Scheduled workflows only run on the default branch (`master`).
- GitHub may disable scheduled workflows on inactive repos after 60 days.

### Step 7 — Test Sunday email (optional)

To test email without waiting for Sunday, temporarily change `EMAIL_DAY` in `src/main.py` to today's weekday, run via **Run workflow**, then revert.

---

## Notes

- **Gmail SMTP from GHA:** Google may block SMTP from cloud IPs. Check the Actions log if email fails.
- **Runtime:** PDF + Gemini calls can be slow. The workflow timeout is 120 minutes.
- **Timezone:** The runner uses UTC. "Yesterday" for arXiv queries is computed in UTC.
