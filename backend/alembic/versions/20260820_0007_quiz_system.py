"""Add quiz metadata, secure attempt lifecycle, scoring data, and seed quizzes."""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260820_0007"
down_revision: str | None = "20260820_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    op.add_column("quizzes", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("quizzes", sa.Column("difficulty", sa.String(length=20), nullable=True))
    op.execute(
        sa.text(
            "UPDATE quizzes AS q "
            "SET category = l.category, difficulty = l.difficulty "
            "FROM cybersecurity_lessons AS l WHERE q.lesson_id = l.id"
        )
    )
    op.execute(sa.text("UPDATE quizzes SET category = 'general' WHERE category IS NULL"))
    op.execute(sa.text("UPDATE quizzes SET difficulty = 'beginner' WHERE difficulty IS NULL"))
    op.alter_column("quizzes", "category", nullable=False, server_default=sa.text("'general'"))
    op.alter_column("quizzes", "difficulty", nullable=False, server_default=sa.text("'beginner'"))
    op.create_check_constraint(
        "ck_quizzes_difficulty",
        "quizzes",
        "difficulty IN ('beginner', 'intermediate', 'advanced')",
    )
    op.create_index("ix_quizzes_category", "quizzes", ["category"], unique=False)
    op.create_index(
        "ix_quizzes_category_difficulty",
        "quizzes",
        ["category", "difficulty"],
        unique=False,
    )

    op.add_column("quiz_attempts", sa.Column("status", sa.String(length=20), nullable=True))
    op.add_column("quiz_attempts", sa.Column("answers", sa.JSON(), nullable=True))
    op.add_column(
        "quiz_attempts",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "quiz_attempts",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE quiz_attempts SET status = 'submitted', "
            "answers = '{}'::json, started_at = COALESCE(completed_at, now()), "
            "submitted_at = completed_at"
        )
    )
    op.alter_column("quiz_attempts", "status", nullable=False, server_default=sa.text("'submitted'"))
    op.alter_column("quiz_attempts", "answers", nullable=False, server_default=sa.text("'{}'"))
    op.alter_column("quiz_attempts", "started_at", nullable=False, server_default=sa.text("now()"))
    op.alter_column("quiz_attempts", "completed_at", nullable=True)
    op.create_check_constraint(
        "ck_quiz_attempts_status",
        "quiz_attempts",
        "status IN ('in_progress', 'submitted')",
    )
    op.create_index("ix_quiz_attempts_user_status", "quiz_attempts", ["user_id", "status"], unique=False)

    op.add_column("awareness_scores", sa.Column("mobile_score", sa.Numeric(5, 2), nullable=True))
    op.execute(sa.text("UPDATE awareness_scores SET mobile_score = 0 WHERE mobile_score IS NULL"))
    op.alter_column("awareness_scores", "mobile_score", nullable=False, server_default=sa.text("0"))
    op.create_check_constraint(
        "ck_awareness_scores_mobile_range",
        "awareness_scores",
        "mobile_score >= 0 AND mobile_score <= 100",
    )

    quiz_seeds = [
        {
            "title": "Password Security Check",
            "description": "Practice safer password and account habits.",
            "category": "password-security",
            "difficulty": "beginner",
            "questions": [
                ("Which password is the safest choice?", ["Campus2026!", "correct-horse-battery-river", "Password123!", "qwerty-uiop"], "correct-horse-battery-river", "A long, unique passphrase is harder to guess and avoids predictable reuse."),
                ("What should you do after a service reports a data breach?", ["Reuse the same password elsewhere", "Ignore it", "Change the reused password and enable MFA", "Post the password publicly"], "Change the reused password and enable MFA", "Changing reused credentials and adding MFA reduces account-takeover risk."),
            ],
        },
        {
            "title": "Phishing Awareness Check",
            "description": "Identify pressure, impersonation, and unsafe requests.",
            "category": "phishing",
            "difficulty": "beginner",
            "questions": [
                ("A message says your campus account closes in ten minutes and includes a login link. What is the safest next step?", ["Click immediately", "Reply with your password", "Open the official campus portal separately and verify", "Forward it to everyone"], "Open the official campus portal separately and verify", "Urgency and a login link are warning signs. Verify through a trusted channel."),
                ("Which request is a strong phishing indicator?", ["A public event announcement", "An unexpected request for an OTP", "A known lecturer sharing a syllabus", "A routine library reminder"], "An unexpected request for an OTP", "One-time codes are secrets and should never be shared in response to an unexpected request."),
            ],
        },
        {
            "title": "Malware Safety Check",
            "description": "Recognize risky downloads and basic response steps.",
            "category": "malware",
            "difficulty": "beginner",
            "questions": [
                ("Where should you download a needed application?", ["An unexpected pop-up", "An official vendor source", "A random file-sharing link", "A message attachment"], "An official vendor source", "Official sources reduce the chance of downloading tampered or unwanted software."),
                ("What is a safe first step after suspecting malware?", ["Disable all protections", "Keep using shared drives", "Disconnect if appropriate and contact IT", "Delete all evidence"], "Disconnect if appropriate and contact IT", "Early isolation and reporting can limit spread and help responders investigate."),
            ],
        },
        {
            "title": "Ransomware Resilience Check",
            "description": "Practice habits that reduce ransomware impact.",
            "category": "ransomware",
            "difficulty": "intermediate",
            "questions": [
                ("Which control most improves recovery from ransomware?", ["Untested backups connected to every device", "Tested backups separated from everyday access", "One shared administrator password", "Disabling updates"], "Tested backups separated from everyday access", "Separated and tested backups improve recovery when production files are unavailable."),
                ("What should you avoid when a device may be infected?", ["Contacting security staff", "Preserving useful details", "Reconnecting it to shared drives", "Following the response plan"], "Reconnecting it to shared drives", "Reconnection can spread an infection to shared systems and files."),
            ],
        },
        {
            "title": "Social Engineering Check",
            "description": "Spot manipulation based on authority, secrecy, or pressure.",
            "category": "social-engineering",
            "difficulty": "beginner",
            "questions": [
                ("A caller claiming to be a supervisor asks for gift cards and secrecy. What should you do?", ["Follow the request", "Verify independently using a trusted channel", "Share internal details first", "Keep it secret"], "Verify independently using a trusted channel", "Unusual payment and secrecy requests need independent verification."),
                ("Which behavior is a useful security boundary?", ["Rushing because of authority", "Skipping normal process", "Pausing and asking for verification", "Sharing a recovery code"], "Pausing and asking for verification", "Verification protects people and is appropriate even when a request sounds urgent."),
            ],
        },
        {
            "title": "Safe Browsing Check",
            "description": "Evaluate domains, downloads, and browser permissions.",
            "category": "safe-browsing",
            "difficulty": "beginner",
            "questions": [
                ("What does HTTPS tell you?", ["The site is guaranteed legitimate", "The connection is encrypted in transit", "The file is safe", "The sender is verified"], "The connection is encrypted in transit", "HTTPS helps protect data in transit but does not guarantee that the site itself is trustworthy."),
                ("A site unexpectedly asks for notifications and a browser extension. What is safest?", ["Allow both", "Install immediately", "Decline and verify the site and request", "Enter your password first"], "Decline and verify the site and request", "Unexpected permissions and extensions can create unnecessary exposure."),
            ],
        },
        {
            "title": "Mobile Security Check",
            "description": "Protect mobile devices, apps, and recovery options.",
            "category": "mobile-security",
            "difficulty": "beginner",
            "questions": [
                ("Which mobile baseline is strongest?", ["No screen lock", "Automatic updates and a strong screen lock", "Install every QR code app", "Share the unlock code"], "Automatic updates and a strong screen lock", "Updates and a strong lock protect the device and the accounts it carries."),
                ("What should you review before installing an app?", ["Only its icon", "Requested permissions and the developer", "A message urging installation", "Whether it asks for every permission"], "Requested permissions and the developer", "Permissions should match the app's purpose and the source should be credible."),
            ],
        },
        {
            "title": "Online Payment Security Check",
            "description": "Practice safer payment and digital wallet decisions.",
            "category": "online-payment-security",
            "difficulty": "beginner",
            "questions": [
                ("Before sending a payment, what should you confirm?", ["Only the logo", "The recipient and amount through a trusted flow", "The sender's urgency", "A random payment link"], "The recipient and amount through a trusted flow", "Confirming the destination and amount helps prevent payment redirection scams."),
                ("Which secret should never be shared in a message?", ["A public event time", "An OTP or payment PIN", "A product name", "A campus building name"], "An OTP or payment PIN", "Payment and authentication secrets must remain private."),
            ],
        },
        {
            "title": "Data Privacy Check",
            "description": "Apply data minimization and safer sharing choices.",
            "category": "data-privacy",
            "difficulty": "beginner",
            "questions": [
                ("What is data minimization?", ["Collecting everything", "Sharing the minimum needed for a purpose", "Posting data publicly", "Keeping all settings unchanged"], "Sharing the minimum needed for a purpose", "Minimization reduces unnecessary exposure and limits the impact of mistakes."),
                ("Which post may reveal more than intended?", ["A generic greeting", "A badge photo with travel dates and routine", "A public event poster", "A weather update"], "A badge photo with travel dates and routine", "Details can become sensitive when combined and may reveal identity or absence patterns."),
            ],
        },
        {
            "title": "Two-Factor Authentication Check",
            "description": "Use MFA safely and respond to unexpected prompts.",
            "category": "two-factor-authentication",
            "difficulty": "beginner",
            "questions": [
                ("What does MFA add to a password?", ["A second proof of identity", "A public username", "A longer email", "A faster connection"], "A second proof of identity", "MFA combines different factors so a stolen password is not enough by itself."),
                ("What should you do with an unexpected login prompt?", ["Approve it to stop alerts", "Deny it and investigate", "Share the code", "Ignore repeated prompts forever"], "Deny it and investigate", "Unexpected prompts can indicate attempted account takeover or approval fatigue."),
            ],
        },
        {
            "title": "Network Security Check",
            "description": "Use safer Wi-Fi and network habits.",
            "category": "network-security",
            "difficulty": "intermediate",
            "questions": [
                ("What does a Wi-Fi network name prove?", ["Who operates it", "Nothing by itself", "That it is encrypted", "That it is campus-owned"], "Nothing by itself", "Network names can be copied, so use context and trusted connections."),
                ("Which home router practice is safest?", ["Keep default admin credentials", "Use a strong unique admin password and update firmware", "Enable auto-join everywhere", "Share the admin password"], "Use a strong unique admin password and update firmware", "Router credentials and updates are important parts of the home security baseline."),
            ],
        },
        {
            "title": "Cloud Security Check",
            "description": "Manage sharing, identity, and permissions in cloud services.",
            "category": "cloud-security",
            "difficulty": "intermediate",
            "questions": [
                ("Who is responsible for cloud security?", ["Only the provider", "Only the user", "The provider and the people using the service", "Nobody"], "The provider and the people using the service", "Cloud security is shared: providers secure infrastructure while users manage access and data."),
                ("Which sharing choice is safest for a private project?", ["Anyone with the link", "Named people or approved groups", "A public social post", "No access review"], "Named people or approved groups", "Specific sharing limits exposure and makes access easier to review."),
            ],
        },
    ]

    for quiz in quiz_seeds:
        title = _sql_string(quiz["title"])
        category = _sql_string(quiz["category"])
        description = _sql_string(quiz["description"])
        difficulty = _sql_string(quiz["difficulty"])
        op.execute(
            sa.text(
                "INSERT INTO quizzes (lesson_id, title, description, category, difficulty) "
                "SELECT l.id, "
                + title
                + ", "
                + description
                + ", "
                + category
                + ", "
                + difficulty
                + " FROM cybersecurity_lessons AS l "
                "WHERE l.category = "
                + category
                + " AND NOT EXISTS (SELECT 1 FROM quizzes WHERE title = "
                + title
                + ")"
            )
        )
        for question, options, correct_answer, explanation in quiz["questions"]:
            options_json = _sql_string(json.dumps(options)) + "::jsonb"
            op.execute(
                sa.text(
                    "INSERT INTO quiz_questions (quiz_id, question, options, correct_answer, explanation) "
                    "SELECT q.id, "
                    + _sql_string(question)
                    + ", "
                    + options_json
                    + ", "
                    + _sql_string(correct_answer)
                    + ", "
                    + _sql_string(explanation)
                    + " FROM quizzes AS q WHERE q.title = "
                    + title
                    + " AND q.category = "
                    + category
                    + " AND NOT EXISTS (SELECT 1 FROM quiz_questions WHERE quiz_id = q.id AND question = "
                    + _sql_string(question)
                    + ")"
                )
            )


def downgrade() -> None:
    op.drop_constraint("ck_awareness_scores_mobile_range", "awareness_scores", type_="check")
    op.drop_column("awareness_scores", "mobile_score")

    op.drop_index("ix_quiz_attempts_user_status", table_name="quiz_attempts")
    op.drop_constraint("ck_quiz_attempts_status", "quiz_attempts", type_="check")
    op.drop_column("quiz_attempts", "submitted_at")
    op.drop_column("quiz_attempts", "started_at")
    op.drop_column("quiz_attempts", "answers")
    op.drop_column("quiz_attempts", "status")

    op.drop_index("ix_quizzes_category_difficulty", table_name="quizzes")
    op.drop_index("ix_quizzes_category", table_name="quizzes")
    op.drop_constraint("ck_quizzes_difficulty", "quizzes", type_="check")
    op.drop_column("quizzes", "difficulty")
    op.drop_column("quizzes", "category")
