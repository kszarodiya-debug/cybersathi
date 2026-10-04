"""Deterministic defensive analysis for suspicious message content."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.analysis import EmailAnalysis
from app.schemas.analysis import (
    DetectedIndicator,
    MessageAnalysisResponse,
    MessageContentType,
    RiskLevel,
)


@dataclass(frozen=True)
class AnalysisRule:
    code: str
    label: str
    description: str
    severity: str
    weight: int
    pattern: str


RULES = (
    AnalysisRule(
        "urgency",
        "Suspicious urgency",
        "The message pressures you to act immediately or threatens a deadline or account consequence.",
        "medium",
        15,
        r"\b(?:urgent|immediately|act\s+now|within\s+(?:\d+|24)\s*(?:minutes?|hours?|h)|last\s+warning|final\s+notice|failure\s+to\s+act|account\s+(?:will\s+be|has\s+been)\s+(?:closed|suspended|locked))\b",
    ),
    AnalysisRule(
        "impersonation",
        "Possible impersonation",
        "The message refers to a trusted organization, authority, or familiar role in a way that may be used to build trust.",
        "medium",
        12,
        r"\b(?:it\s+support|help\s*desk|administrator|admin\s+team|bank|university|college|professor|faculty|human\s+resources|\bhr\b|ceo|principal|security\s+team|microsoft|google|paypal|netflix|tax\s+(?:office|department))\b",
    ),
    AnalysisRule(
        "credential_request",
        "Credential or login request",
        "The message appears to request, confirm, or enter account credentials or a login.",
        "high",
        20,
        r"(?:(?:click|visit|use|confirm|verify|send|share|provide|enter|reply).{0,50}(?:password|username|credentials?|login|log[\s-]?in)|(?:password|credentials?|username).{0,50}(?:needed|required|confirm|send|share|provide|enter))",
    ),
    AnalysisRule(
        "suspicious_link",
        "Suspicious link or link bait",
        "The message includes a link or urges you to click one. A link’s presence alone does not prove it is malicious.",
        "medium",
        15,
        r"(?:https?://|www\.|\b(?:bit\.ly|tinyurl\.com|t\.co|is\.gd)/|\bclick\s+(?:here|this|the\s+link)\b)",
    ),
    AnalysisRule(
        "financial_scam",
        "Financial scam language",
        "The message uses payment, transfer, refund, fee, gift-card, or money-related language that can signal a scam.",
        "high",
        18,
        r"\b(?:gift\s+cards?|wire\s+transfer|bank\s+transfer|payment|invoice|refund|crypto(?:currency)?|bitcoin|cash|fee|prize|lottery|money)\b",
    ),
    AnalysisRule(
        "social_engineering",
        "Social engineering pressure",
        "The message uses secrecy, authority, emotion, or a request to bypass normal verification.",
        "medium",
        15,
        r"(?:keep\s+(?:this|it)\s+(?:secret|confidential)|don['’]?t\s+tell|do\s+not\s+tell|bypass\s+(?:the\s+)?(?:process|policy|approval)|trust\s+me|emergency|need\s+your\s+help)",
    ),
    AnalysisRule(
        "suspicious_attachment",
        "Suspicious attachment reference",
        "The message refers to an attachment or a file type commonly abused to deliver malware or credential theft.",
        "medium",
        10,
        r"(?:attached|attachment|open\s+the\s+file|enable\s+(?:macros?|content)|\.(?:zip|exe|scr|js|html?|docm|xlsm|iso)\b)",
    ),
    AnalysisRule(
        "otp_request",
        "One-time code request",
        "The message appears to request an OTP, MFA code, verification code, or security code.",
        "high",
        25,
        r"(?:(?:send|share|tell|read|forward|provide|enter|confirm).{0,45}(?:otp|one[-\s]?time\s+(?:pass)?code|mfa\s+code|verification\s+code|security\s+code)|(?:otp|one[-\s]?time\s+(?:pass)?code|mfa\s+code).{0,45}(?:send|share|tell|forward|provide|enter|confirm))",
    ),
    AnalysisRule(
        "password_request",
        "Password request",
        "The message appears to ask for a password or to send a password by message.",
        "high",
        25,
        r"(?:(?:send|share|tell|provide|reply\s+with|confirm).{0,35}password|password.{0,35}(?:send|share|tell|provide|reply))",
    ),
    AnalysisRule(
        "payment_request",
        "Payment request",
        "The message asks you to make a payment, transfer funds, buy gift cards, or pay an unexpected fee.",
        "high",
        22,
        r"(?:(?:send|make|complete|process|pay|purchase|buy).{0,45}(?:payment|transfer|gift\s+cards?|fee|invoice)|(?:payment|transfer|gift\s+cards?|fee|invoice).{0,45}(?:send|make|complete|process|pay|purchase|buy))",
    ),
)

_EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PUBLIC_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me"}


def _indicator(rule: AnalysisRule) -> DetectedIndicator:
    return DetectedIndicator(
        code=rule.code,
        label=rule.label,
        description=rule.description,
        severity=rule.severity,  # type: ignore[arg-type]
    )


def _sender_indicator(text: str) -> DetectedIndicator | None:
    sender_match = re.search(r"(?:from|sender)\s*:?[^\n<]*<?(" + _EMAIL_PATTERN.pattern + r")", text, re.IGNORECASE)
    reply_match = re.search(r"reply[- ]?to\s*:?[^\n<]*<?(" + _EMAIL_PATTERN.pattern + r")", text, re.IGNORECASE)
    if sender_match and reply_match:
        sender_domain = sender_match.group(1).split("@", 1)[1].lower()
        reply_domain = reply_match.group(1).split("@", 1)[1].lower()
        if sender_domain != reply_domain:
            return DetectedIndicator(
                code="unusual_sender",
                label="Unusual sender information",
                description="The From and Reply-To domains do not match; verify the sender through a trusted channel.",
                severity="high",
            )
    if sender_match:
        sender_line = sender_match.group(0).lower()
        domain = sender_match.group(1).split("@", 1)[1].lower()
        trusted_claim = re.search(r"\b(?:bank|university|college|it\s+support|security|admin|paypal|microsoft|google)\b", sender_line)
        if trusted_claim and domain in _PUBLIC_EMAIL_DOMAINS:
            return DetectedIndicator(
                code="unusual_sender",
                label="Unusual sender information",
                description="A trusted organization or role appears to use a public email domain; independently verify the sender.",
                severity="medium",
            )
    return None


def _risk_level(score: int) -> RiskLevel:
    if score >= 85:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def _recommendations(codes: set[str]) -> list[str]:
    actions = [
        "Pause and verify the request using a trusted phone number, official website, or known contact.",
        "Do not click links, open unexpected attachments, or reply until the message is independently verified.",
    ]
    if codes & {"credential_request", "otp_request", "password_request"}:
        actions.append("Never share a password, OTP, MFA code, recovery code, or login details by message.")
    if codes & {"financial_scam", "payment_request"}:
        actions.append("Do not send money, buy gift cards, or change payment details based only on this message.")
    if codes & {"suspicious_link", "suspicious_attachment"}:
        actions.append("Report the message through your campus or platform reporting channel and preserve the original content.")
    return actions


def _safe_handling_advice(codes: set[str]) -> str:
    if codes:
        return "Do not interact with the message while checking it. Keep it available for reporting, and contact campus IT/security through a trusted channel if you already clicked, replied, opened a file, or shared information."
    return "No common high-risk indicators were detected by these rules. This does not prove the message is safe; verify unexpected requests through a trusted channel before acting."


def analyze_message_content(content: str, content_type: MessageContentType) -> dict[str, object]:
    """Return a deterministic, explainable result without making certainty claims."""

    normalized = content.lower()
    indicators = [_indicator(rule) for rule in RULES if re.search(rule.pattern, normalized, re.IGNORECASE)]
    sender_indicator = _sender_indicator(content)
    if sender_indicator:
        indicators.append(sender_indicator)
    weights = {rule.code: rule.weight for rule in RULES}
    weights["unusual_sender"] = 15
    score = min(100, sum(weights.get(indicator.code, 0) for indicator in indicators))
    codes = {indicator.code for indicator in indicators}
    if indicators:
        explanation = (
            f"The {content_type.replace('_', ' ')} contains {len(indicators)} defensive warning indicator(s). "
            "The score reflects observable language or message structure, not proof that the sender or content is malicious. "
            "Verify the request independently before taking action."
        )
    else:
        explanation = (
            f"The {content_type.replace('_', ' ')} did not match the common warning patterns used by this analyzer. "
            "This is not proof that the message is safe; context and sender verification still matter."
        )
    return {
        "content_type": content_type,
        "risk_score": score,
        "risk_level": _risk_level(score),
        "detected_indicators": indicators,
        "explanation": explanation,
        "recommended_actions": _recommendations(codes),
        "safe_handling_advice": _safe_handling_advice(codes),
    }


def persist_message_analysis(
    db: Session,
    *,
    user_id: int | None,
    content: str,
    content_type: MessageContentType,
) -> MessageAnalysisResponse:
    result = analyze_message_content(content, content_type)
    indicators = result["detected_indicators"]
    assert isinstance(indicators, list)
    risk_score = result["risk_score"]
    risk_level = result["risk_level"]
    assert isinstance(risk_score, int)
    assert isinstance(risk_level, str)
    if user_id is None:
        return MessageAnalysisResponse(
            id=None,
            content_type=content_type,
            risk_score=risk_score,
            risk_level=risk_level.upper(),  # type: ignore[arg-type]
            detected_indicators=[DetectedIndicator.model_validate(item) for item in indicators],
            explanation=str(result["explanation"]),
            recommended_actions=list(result["recommended_actions"]),  # type: ignore[arg-type]
            safe_handling_advice=str(result["safe_handling_advice"]),
            created_at=datetime.now(timezone.utc),
        )

    analysis = EmailAnalysis(
        user_id=user_id,
        content_type=content_type,
        email_content=content,
        risk_score=Decimal(risk_score),
        risk_level=risk_level.lower(),
        analysis_result=str(result["explanation"]),
        detected_indicators=[item.model_dump() for item in indicators],
        recommended_actions=result["recommended_actions"],
        safe_handling_advice=str(result["safe_handling_advice"]),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return MessageAnalysisResponse(
        id=analysis.id,
        content_type=content_type,
        risk_score=int(analysis.risk_score),
        risk_level=analysis.risk_level.upper(),  # type: ignore[arg-type]
        detected_indicators=[DetectedIndicator.model_validate(item) for item in analysis.detected_indicators],
        explanation=analysis.analysis_result,
        recommended_actions=analysis.recommended_actions,
        safe_handling_advice=analysis.safe_handling_advice,
        created_at=analysis.created_at,
    )
