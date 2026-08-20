"""Add structured Learning Hub content and seed the initial lessons."""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op


revision: str = "20260820_0006"
down_revision: Union[str, None] = "20260820_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cybersecurity_lessons", sa.Column("introduction", sa.Text(), nullable=True))
    op.add_column("cybersecurity_lessons", sa.Column("learning_objectives", sa.JSON(), nullable=True))
    op.add_column("cybersecurity_lessons", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column("cybersecurity_lessons", sa.Column("real_world_example", sa.Text(), nullable=True))
    op.add_column("cybersecurity_lessons", sa.Column("safety_tips", sa.JSON(), nullable=True))
    op.add_column("cybersecurity_lessons", sa.Column("key_takeaways", sa.JSON(), nullable=True))
    op.execute(
        "UPDATE cybersecurity_lessons SET "
        "introduction = description, learning_objectives = '[]', explanation = content, "
        "real_world_example = 'Use the safety tips to evaluate an unexpected request.', "
        "safety_tips = '[]', key_takeaways = '[]'"
    )
    op.alter_column(
        "cybersecurity_lessons",
        "introduction",
        nullable=False,
        server_default=sa.text("'A practical introduction to this cybersecurity topic.'"),
    )
    op.alter_column("cybersecurity_lessons", "learning_objectives", nullable=False, server_default=sa.text("'[]'"))
    op.alter_column(
        "cybersecurity_lessons",
        "explanation",
        nullable=False,
        server_default=sa.text("'Review the practical guidance in this lesson.'"),
    )
    op.alter_column(
        "cybersecurity_lessons",
        "real_world_example",
        nullable=False,
        server_default=sa.text("'Use the safety tips to evaluate an unexpected request.'"),
    )
    op.alter_column("cybersecurity_lessons", "safety_tips", nullable=False, server_default=sa.text("'[]'"))
    op.alter_column("cybersecurity_lessons", "key_takeaways", nullable=False, server_default=sa.text("'[]'"))

    lesson_table = sa.table(
        "cybersecurity_lessons",
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("introduction", sa.Text()),
        sa.column("category", sa.String()),
        sa.column("content", sa.Text()),
        sa.column("learning_objectives", sa.JSON()),
        sa.column("explanation", sa.Text()),
        sa.column("real_world_example", sa.Text()),
        sa.column("safety_tips", sa.JSON()),
        sa.column("key_takeaways", sa.JSON()),
        sa.column("difficulty", sa.String()),
    )
    seed_rows = [
            {
                "title": "Build a Strong Password Foundation",
                "description": "Learn how unique, long passwords protect your campus and personal accounts.",
                "introduction": "Passwords are still a major line of defense for email, learning platforms, banking, and social accounts.",
                "category": "password-security",
                "content": "A strong password is long, unique to one service, and difficult to guess. Password managers can create and store unique passwords so you do not need to reuse or memorize every one.",
                "learning_objectives": ["Explain why password reuse is risky.", "Create a strong passphrase.", "Use a password manager safely."],
                "explanation": "Attackers often try credentials exposed in one breach against other services. Unique passwords limit the damage when one service is compromised.",
                "real_world_example": "If a gaming account password is reused for college email and that gaming service is breached, an attacker may try the same password against the email account.",
                "safety_tips": ["Use a different password for every important account.", "Prefer long passphrases over short complex strings.", "Turn on MFA for email, finance, and academic systems.", "Never share passwords in messages or forms reached through unexpected links."],
                "key_takeaways": ["Length and uniqueness matter.", "Password reuse creates a chain reaction.", "A password manager reduces risky reuse."],
                "difficulty": "beginner",
            },
            {
                "title": "Recognize Phishing Before You Click",
                "description": "Spot the language, links, and requests commonly used in phishing messages.",
                "introduction": "Phishing uses convincing messages to make people click, share secrets, or send money.",
                "category": "phishing",
                "content": "Phishing messages often combine urgency, impersonation, suspicious links, and requests for passwords or codes. Check the sender and destination through a trusted channel instead of using the message itself.",
                "learning_objectives": ["Identify common phishing signals.", "Inspect a link without opening it.", "Report a suspicious message safely."],
                "explanation": "A professional logo or familiar name does not prove a message is genuine. The request, timing, destination, and sender context matter together.",
                "real_world_example": "A message appearing to come from campus IT says your account will be closed today and asks you to sign in through a shortened link.",
                "safety_tips": ["Pause when a message creates pressure.", "Open official apps or type known addresses yourself.", "Never share passwords or one-time codes by message.", "Use your campus reporting process and preserve the original message."],
                "key_takeaways": ["Urgency is a signal, not a reason to rush.", "Verify using a separate trusted channel.", "Reporting helps protect others."],
                "difficulty": "beginner",
            },
            {
                "title": "Understand Malware and Its Delivery Paths",
                "description": "Learn what malware is and how everyday actions can expose a device.",
                "introduction": "Malware is software designed to disrupt, damage, spy on, or gain unauthorized access to systems.",
                "category": "malware",
                "content": "Malware can arrive through attachments, unsafe downloads, compromised websites, removable media, or vulnerable software. Safe habits and timely updates reduce exposure.",
                "learning_objectives": ["Describe common malware delivery paths.", "Recognize risky downloads and attachments.", "Know what to do after a suspected infection."],
                "explanation": "Malware is a broad category that includes spyware, trojans, worms, and other unwanted software. A familiar file name or icon is not enough to trust a file.",
                "real_world_example": "A fake course-material download asks a student to disable security protections before opening it.",
                "safety_tips": ["Download software from official sources.", "Keep operating systems and apps updated.", "Do not disable security protections to open unexpected files.", "Disconnect from networks and contact IT if you suspect infection."],
                "key_takeaways": ["Malware uses both technical weaknesses and human trust.", "Updates close known gaps.", "Early reporting limits impact."],
                "difficulty": "beginner",
            },
            {
                "title": "Prepare for Ransomware",
                "description": "Understand ransomware impact and the habits that improve recovery.",
                "introduction": "Ransomware can make files unavailable and demand payment, but paying does not guarantee recovery.",
                "category": "ransomware",
                "content": "Ransomware commonly enters through phishing, exposed services, unsafe downloads, or stolen credentials. Backups, MFA, updates, and a practiced response plan improve resilience.",
                "learning_objectives": ["Explain how ransomware affects availability.", "Identify preventive controls.", "Describe the first safe response steps."],
                "explanation": "A resilient organization limits access, separates backups, monitors unusual activity, and knows how to report an incident without spreading it.",
                "real_world_example": "A shared drive becomes unreadable after a user opens a malicious attachment that runs with excessive permissions.",
                "safety_tips": ["Keep tested backups separate from everyday access.", "Use MFA and least privilege.", "Do not reconnect infected devices to shared drives.", "Contact security staff instead of negotiating alone."],
                "key_takeaways": ["Recovery planning matters before an incident.", "Backups must be tested.", "Fast reporting can contain spread."],
                "difficulty": "intermediate",
            },
            {
                "title": "Defend Against Social Engineering",
                "description": "Recognize manipulation tactics that target attention, trust, and emotion.",
                "introduction": "Social engineering manipulates people into taking actions that weaken security or disclose information.",
                "category": "social-engineering",
                "content": "Attackers may use authority, fear, urgency, helpfulness, secrecy, or familiarity. A respectful request can still be unsafe if it asks you to bypass normal verification.",
                "learning_objectives": ["Recognize common manipulation tactics.", "Use verification scripts confidently.", "Set boundaries around sensitive requests."],
                "explanation": "Security procedures exist to protect people from pressure. It is reasonable to pause, verify identity, and use an approved process even when a request appears urgent.",
                "real_world_example": "Someone claiming to be a supervisor asks a staff member to purchase gift cards and keep the request confidential.",
                "safety_tips": ["Verify unusual requests independently.", "Do not let authority or urgency override policy.", "Avoid sharing internal details publicly.", "Ask a trusted colleague or security team for a second opinion."],
                "key_takeaways": ["Pressure is information.", "Verification is a security skill, not disrespect.", "Normal processes protect everyone."],
                "difficulty": "beginner",
            },
            {
                "title": "Practice Safer Web Browsing",
                "description": "Build habits for navigating websites, downloads, and browser permissions safely.",
                "introduction": "Safe browsing means checking where you are, what a site asks for, and whether the action is expected.",
                "category": "safe-browsing",
                "content": "HTTPS protects data in transit but does not prove a site is trustworthy. Check the domain, avoid unexpected downloads, and review permissions before granting them.",
                "learning_objectives": ["Read a domain name carefully.", "Understand what HTTPS does and does not guarantee.", "Manage browser permissions and downloads."],
                "explanation": "A malicious site can use HTTPS. Trust comes from the full context: how you reached the site, the domain, the request, and the organization’s known channels.",
                "real_world_example": "A search result uses a look-alike domain and asks for browser notifications before showing a fake delivery update.",
                "safety_tips": ["Use bookmarks for important services.", "Do not install extensions from unexpected prompts.", "Review notification, camera, and microphone permissions.", "Keep the browser updated."],
                "key_takeaways": ["HTTPS is encryption, not a trust certificate.", "Domains deserve careful attention.", "Permissions can be revoked."],
                "difficulty": "beginner",
            },
            {
                "title": "Secure Your Mobile Device",
                "description": "Protect phones and tablets that carry accounts, messages, photos, and location data.",
                "introduction": "Mobile devices are valuable targets because they combine identity, communication, payments, and personal data.",
                "category": "mobile-security",
                "content": "A screen lock, timely updates, trusted apps, and device recovery settings provide a strong baseline. Treat mobile notifications and QR codes as untrusted input too.",
                "learning_objectives": ["Configure a secure device baseline.", "Evaluate mobile app permissions.", "Plan for loss or theft."],
                "explanation": "App stores reduce risk but do not eliminate it. Review the developer, permissions, reviews, and whether the app is actually needed.",
                "real_world_example": "A fake campus app requests access to contacts, messages, and accessibility features even though it only claims to show a timetable.",
                "safety_tips": ["Use a strong screen lock and automatic updates.", "Install apps from official stores and review permissions.", "Enable remote find and erase features.", "Avoid sensitive activity on unknown public Wi-Fi."],
                "key_takeaways": ["Your phone is an identity device.", "Permissions should match the app’s purpose.", "Prepare before a device is lost."],
                "difficulty": "beginner",
            },
            {
                "title": "Make Online Payments More Secure",
                "description": "Learn how to reduce risk when shopping, paying fees, or using digital wallets.",
                "introduction": "Payment security depends on the account, device, merchant, network, and the message that brought you there.",
                "category": "online-payment-security",
                "content": "Use official payment apps or sites, confirm the recipient and amount, and avoid acting on unexpected payment instructions. Banks and payment providers have different recovery processes, so report quickly.",
                "learning_objectives": ["Verify payment destinations.", "Recognize payment scams.", "Know safe response steps after an error."],
                "explanation": "Scammers create fake refunds, fees, delivery charges, and urgent payment requests. A familiar logo or caller ID is not independent verification.",
                "real_world_example": "A fake scholarship message requests a processing fee through a personal wallet before releasing an award.",
                "safety_tips": ["Type known payment addresses yourself.", "Confirm account names and amounts before sending.", "Never share card PINs, OTPs, or recovery codes.", "Contact the provider immediately if you sent money by mistake."],
                "key_takeaways": ["Slow down financial decisions.", "Verify recipient details out of band.", "Fast reporting improves recovery options."],
                "difficulty": "beginner",
            },
            {
                "title": "Protect Your Data Privacy",
                "description": "Understand what personal data reveals and how to share less by default.",
                "introduction": "Data privacy is about making informed choices about what information is collected, used, and shared.",
                "category": "data-privacy",
                "content": "Personal data includes direct identifiers, location, activity, education records, and combinations of ordinary details. Minimize collection, review settings, and consider who may receive a post or file.",
                "learning_objectives": ["Identify sensitive and linkable data.", "Apply data minimization.", "Review sharing and privacy settings."],
                "explanation": "Small details can become sensitive when combined. Privacy controls reduce exposure but cannot guarantee that shared content will never be copied.",
                "real_world_example": "A public post combines a campus badge photo, travel dates, and a routine, giving strangers useful information about when a room is empty.",
                "safety_tips": ["Share the minimum needed for the purpose.", "Review app and social privacy settings regularly.", "Remove unnecessary metadata from shared files when possible.", "Do not post IDs, access codes, or detailed schedules publicly."],
                "key_takeaways": ["Privacy is a set of choices.", "Context can make ordinary data sensitive.", "Once shared, content can be copied."],
                "difficulty": "beginner",
            },
            {
                "title": "Use Two-Factor Authentication",
                "description": "Add a second proof of identity and understand how to use it safely.",
                "introduction": "Two-factor authentication combines something you know, have, or are so a stolen password is not enough by itself.",
                "category": "two-factor-authentication",
                "content": "Authenticator apps, hardware keys, and approved passkeys can provide stronger protection than passwords alone. One-time codes are still secrets and must not be shared.",
                "learning_objectives": ["Explain the factors in MFA.", "Choose a suitable second factor.", "Respond safely to unexpected prompts."],
                "explanation": "MFA reduces account takeover risk, but attackers may still try to trick users into approving a login or sharing a code. Unexpected prompts should be denied and reported.",
                "real_world_example": "A student receives repeated login prompts after a phishing attempt and approves one to make the notifications stop.",
                "safety_tips": ["Enable MFA on email and financial accounts first.", "Prefer passkeys, security keys, or authenticator apps when supported.", "Deny unexpected prompts and change the password if they continue.", "Store recovery codes securely and never send them in chat."],
                "key_takeaways": ["MFA is stronger than a password alone.", "Approval fatigue is a real risk.", "Codes and recovery options are sensitive."],
                "difficulty": "beginner",
            },
            {
                "title": "Understand Network Security Basics",
                "description": "Learn how devices, Wi-Fi, and network boundaries affect everyday security.",
                "introduction": "Networks connect devices and services, but each connection creates choices about trust and exposure.",
                "category": "network-security",
                "content": "Use trusted networks, secure home Wi-Fi, and avoid treating public connectivity as private. Encryption protects some traffic, while device updates and firewall controls reduce other risks.",
                "learning_objectives": ["Distinguish trusted and untrusted networks.", "Secure a home Wi-Fi baseline.", "Recognize risky network behavior."],
                "explanation": "A network name alone does not prove who operates it. HTTPS and app encryption help, but sensitive activity still benefits from a trusted connection and updated device.",
                "real_world_example": "A look-alike public Wi-Fi network uses a campus name and asks users to sign in through an unfamiliar portal.",
                "safety_tips": ["Use a strong unique Wi-Fi password.", "Update router firmware and change default admin credentials.", "Avoid sensitive work on unknown networks.", "Turn off auto-join for networks you do not trust."],
                "key_takeaways": ["Network names can be copied.", "Home routers need maintenance.", "Use layered protections."],
                "difficulty": "intermediate",
            },
            {
                "title": "Use Cloud Services Responsibly",
                "description": "Protect files and accounts stored in cloud drives, collaboration tools, and hosted platforms.",
                "introduction": "Cloud security is shared between the provider and the people who configure and use the service.",
                "category": "cloud-security",
                "content": "Strong identity controls, careful sharing, and least privilege prevent many cloud data exposures. A link that works is not necessarily a link that should be public.",
                "learning_objectives": ["Explain shared responsibility in cloud services.", "Review sharing permissions.", "Respond to suspicious cloud activity."],
                "explanation": "Cloud providers secure their infrastructure, while users remain responsible for account access, permissions, data classification, and safe sharing.",
                "real_world_example": "A project folder is shared with anyone who has the link, allowing an old document to be downloaded outside the team.",
                "safety_tips": ["Share with named people or groups instead of public links.", "Remove access when a project ends.", "Use MFA and review sign-in alerts.", "Report unexpected sharing notifications or file changes."],
                "key_takeaways": ["Convenience can widen access.", "Permissions should be reviewed over time.", "Cloud security is shared responsibility."],
                "difficulty": "intermediate",
            },
        ]
    if context.is_offline_mode():
        columns = (
            "title",
            "description",
            "introduction",
            "category",
            "content",
            "learning_objectives",
            "explanation",
            "real_world_example",
            "safety_tips",
            "key_takeaways",
            "difficulty",
        )

        def sql_string(value: str) -> str:
            return "'" + value.replace("'", "''") + "'"

        value_rows = []
        for row in seed_rows:
            values = []
            for column in columns:
                if column in {"learning_objectives", "safety_tips", "key_takeaways"}:
                    values.append(f"{sql_string(json.dumps(row[column]))}::json")
                else:
                    values.append(sql_string(row[column]))
            value_rows.append("(" + ", ".join(values) + ")")

        op.execute(
            sa.text(
                "INSERT INTO cybersecurity_lessons ("
                + ", ".join(columns)
                + ") VALUES "
                + ", ".join(value_rows)
                + ";"
            )
        )
    else:
        op.bulk_insert(lesson_table, seed_rows)


def downgrade() -> None:
    op.drop_column("cybersecurity_lessons", "key_takeaways")
    op.drop_column("cybersecurity_lessons", "safety_tips")
    op.drop_column("cybersecurity_lessons", "real_world_example")
    op.drop_column("cybersecurity_lessons", "explanation")
    op.drop_column("cybersecurity_lessons", "learning_objectives")
    op.drop_column("cybersecurity_lessons", "introduction")
