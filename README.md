# TerraFlow — Complete Runnable MVP

TerraFlow is a responsive business workflow SaaS MVP for freelancers and small businesses.
It includes authentication, isolated workspaces, clients, quotations, invoices, expenses,
approvals, dashboard summaries, and CSV reporting.

## Important scope statement
This is a complete runnable MVP/reference implementation, not a production-certified financial,
tax, legal or security product. Production launch still requires HTTPS deployment, email verification,
password recovery, database backups, monitoring, penetration testing, POPIA/legal review,
payment-provider onboarding, signed payment webhooks, and operational support.

## Stack
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- Database: SQLite by default for local setup; PostgreSQL supported through `DATABASE_URL`
- Authentication: JWT access tokens + bcrypt password hashing
- UI: TerraFlow bright green/white design system

## Requirements
- Python 3.11+
- Node.js 20+

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
uvicorn app.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

## Run frontend
In another terminal:
```bash
cd frontend
npm install
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
npm run dev
```
Open http://localhost:5173

## Default behaviour
Register your own account from the application. The first account creates a personal workspace.
There are no hardcoded production credentials.

## Database
- Local default: `sqlite:///./terraflow.db`
- PostgreSQL: set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`
- Tables are created automatically at backend startup for this MVP.
- For production, replace auto-create with Alembic migrations.

## Implemented
- Registration, login, current-user session and logout
- Personal workspace bootstrap
- Workspace isolation at API query level
- Client CRUD
- Quotation CRUD and line items
- Quote approval/rejection by workspace owner (guest token workflow is not yet production-ready)
- Convert approved quote to invoice
- Invoice CRUD and payment recording
- Expense CRUD
- Dashboard metrics
- CSV report export
- Responsive dashboard and module screens
- ZAR formatting and configurable workspace VAT registration/rate

## Not included / required before commercial production
- PayFast or international payment gateway integration
- Email delivery and scheduled reminders
- Secure public guest approval links
- Registered external client portal
- PDF generation (documents are currently printable from browser)
- File upload scanning and private object storage
- Full accounting/tax compliance certification
- Admin operations console
- Automated backup/restore and monitoring

## Security
Use a long random `JWT_SECRET` in production. Do not expose it in frontend code.
Do not deploy the default SQLite database for multi-instance production.
Use PostgreSQL, HTTPS, secure reverse proxy settings, backups, rate limiting and security review.
This MVP uses workspace ownership; team invitations and granular member roles are planned extensions.

## v1.1 additions
- Company profile (`PUT /api/workspace`): address, phone, email, VAT number, bank details, shown on PDFs
- Edit draft quotations/invoices (`PUT /api/quotes/{id}`, `PUT /api/invoices/{id}`) and clients; void instead of delete
- Invoice line items (stored, copied when converting a quote) and per-payment dates
- PDF download for every quotation/invoice (jsPDF, client-side)
- Excel export (Report + VAT & P&L sheets)
- Dashboard: cashflow chart, statistic donut, collection-rate gauge, receivables ageing
- Existing databases: new columns are added automatically at startup (`ensure_columns`); new table `invoice_items` is created.
See DEPLOY.md for going live.
