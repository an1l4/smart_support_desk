"""Generate sample product documentation PDFs for upload testing."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fpdf import FPDF

from config import SAMPLE_PDFS_DIR

DOCUMENTS: dict[str, list[str]] = {
    "01-getting-started.pdf": [
        "Getting Started Guide",
        "",
        "Welcome to SmartDesk, a SaaS platform for API-driven workflows.",
        "",
        "Create an account at app.smartdesk.example/signup. Verify your email within 24 hours.",
        "",
        "After login, complete onboarding: choose a plan, create your first project, and generate an API key under Settings > API > Keys.",
        "",
        "Free plan includes 1 project and 100 API requests per minute. Upgrade anytime from Settings > Billing > Plans.",
    ],
    "02-api-rate-limits.pdf": [
        "API Rate Limits",
        "",
        "Rate limits protect platform stability. Limits apply per API key.",
        "",
        "Free plan: 100 requests per minute, burst up to 150.",
        "Pro plan: 1,000 requests per minute, burst up to 1,500.",
        "Enterprise plan: custom limits negotiated in your contract.",
        "",
        "Monitor usage at Settings > API > Usage. Charts update every 5 minutes.",
        "",
        "When you exceed your limit, the API returns HTTP 429 Too Many Requests. Wait 60 seconds or upgrade your plan.",
        "",
        "Contact sales for temporary limit increases during product launches.",
    ],
    "03-api-keys.pdf": [
        "API Keys - Management and Security",
        "",
        "Generate keys at Settings > API > Keys. Each project can have up to 10 active keys.",
        "",
        "Reset your API key:",
        "1. Log in to the dashboard.",
        "2. Go to Settings > API > Keys.",
        "3. Click Regenerate next to the key.",
        "4. Copy the new key immediately - it is shown only once.",
        "5. Update your applications with the new key.",
        "",
        "The old key stops working within 5 minutes.",
        "",
        "Security best practices: never commit keys to source control; use environment variables; rotate keys every 90 days; revoke unused keys promptly.",
    ],
    "04-plans-and-pricing.pdf": [
        "Plans and Pricing",
        "",
        "Free - $0/month: 1 project, 100 req/min, community support, 7-day log retention.",
        "",
        "Pro - $29.99/month: 10 projects, 1,000 req/min, email support, 30-day log retention, webhooks.",
        "",
        "Enterprise - custom pricing: unlimited projects, custom rate limits, SSO, dedicated support, 1-year log retention, SLA.",
        "",
        "Annual billing saves 20%. Change plans at Settings > Billing > Plans. Downgrades take effect at the next billing cycle.",
        "",
        "All plans include HTTPS, audit logs, and role-based access control.",
    ],
    "05-refunds-policy.pdf": [
        "Refund Policy (Product Documentation)",
        "",
        "Monthly subscriptions: full refund within 14 days of charge if API usage is under 1,000 calls.",
        "",
        "Annual plans: prorated refund within 30 days of purchase.",
        "",
        "Duplicate charges verified by our billing team are refunded within 3 to 5 business days.",
        "",
        "To request a refund, email support with your account email and invoice ID (example: INV-101). Reviews complete within 2 business days.",
        "",
        "Refunds are issued to the original payment method. Usage-based overage charges are non-refundable.",
    ],
    "06-login-troubleshooting.pdf": [
        "Login Troubleshooting",
        "",
        "Forgot password: use Forgot password on the login page. Reset links expire after 1 hour.",
        "",
        "SSO login fails: confirm your organization admin enabled SSO for your email domain. Supported providers: Okta, Azure AD, Google Workspace.",
        "",
        "Session expired: clear browser cookies for our domain and sign in again. Sessions last 12 hours by default.",
        "",
        "Two-factor authentication: if you lost your device, use backup codes from Settings > Security. Contact support if codes are unavailable.",
        "",
        "If login still fails, contact support with browser version, operating system, and any on-screen error message.",
    ],
    "07-webhooks-and-integrations.pdf": [
        "Webhooks and Integrations",
        "",
        "Webhooks notify your server when events occur. Available on Pro and Enterprise plans.",
        "",
        "Configure webhooks at Settings > Integrations > Webhooks. Supported events: job.completed, job.failed, user.invited, invoice.paid.",
        "",
        "Each webhook includes an HMAC-SHA256 signature in the X-SmartDesk-Signature header. Verify signatures before processing.",
        "",
        "Retry policy: failed deliveries retry at 1 min, 5 min, 30 min, 2 hours, then stop. View delivery logs in the dashboard.",
        "",
        "Native integrations: Slack notifications, Zapier, and Segment. Enterprise customers can request custom integrations.",
    ],
    "08-data-export-and-backup.pdf": [
        "Data Export and Backup",
        "",
        "Export project data as JSON or CSV from Settings > Data > Export. Exports include jobs, users, and configuration.",
        "",
        "Free plan: manual export only. Pro plan: scheduled weekly exports to S3-compatible storage. Enterprise: daily exports and point-in-time recovery.",
        "",
        "Large exports over 1 GB are delivered as a download link valid for 7 days.",
        "",
        "Backups are encrypted at rest. Request a data deletion certificate after account closure under Settings > Privacy.",
    ],
    "09-team-and-roles.pdf": [
        "Team Management and Roles",
        "",
        "Invite teammates at Settings > Team > Invite. Invitations expire after 7 days.",
        "",
        "Roles:",
        "Owner - full access including billing and deletion.",
        "Admin - manage projects, API keys, and team members.",
        "Developer - create and run jobs, view logs, no billing access.",
        "Viewer - read-only access to dashboards and logs.",
        "",
        "Pro plan supports up to 5 team members. Enterprise supports unlimited members with SCIM provisioning.",
        "",
        "Remove a member at Settings > Team. Their API keys are revoked immediately.",
    ],
}


def _write_pdf(filename: str, paragraphs: list[str], output_dir: Path) -> Path:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for i, paragraph in enumerate(paragraphs):
        if i == 0:
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 8, paragraph)
            pdf.ln(4)
            pdf.set_font("Helvetica", size=11)
            continue
        if not paragraph:
            pdf.ln(3)
            continue
        pdf.multi_cell(0, 6, paragraph)
        pdf.ln(2)

    output_path = output_dir / filename
    pdf.output(str(output_path))
    return output_path


def generate_all(output_dir: Path | None = None) -> list[Path]:
    target = output_dir or SAMPLE_PDFS_DIR
    target.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for filename, paragraphs in DOCUMENTS.items():
        created.append(_write_pdf(filename, paragraphs, target))
    return created


if __name__ == "__main__":
    paths = generate_all()
    print(f"Generated {len(paths)} PDFs in {SAMPLE_PDFS_DIR}:")
    for path in paths:
        print(f"  - {path.name}")
