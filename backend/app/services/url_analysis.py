"""Deterministic, non-invasive URL security analysis."""

import ipaddress
import re
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qsl, urlsplit

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.analysis import URLAnalysis
from app.schemas.url_analysis import URLAnalysisResponse, URLDetectedIndicator, URLRiskLevel


def _indicator(code: str, label: str, description: str, severity: str) -> URLDetectedIndicator:
    return URLDetectedIndicator(
        code=code,
        label=label,
        description=description,
        severity=severity,  # type: ignore[arg-type]
    )


def _risk_level(score: int) -> URLRiskLevel:
    if score >= 75:
        return "CRITICAL"
    if score >= 45:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "SAFE"


def _recommended_action(level: URLRiskLevel, codes: set[str]) -> str:
    if level in {"HIGH", "CRITICAL"}:
        return "Do not open this URL. Use the organization’s known website, bookmark, or official app and verify the request through a trusted channel."
    if level == "MEDIUM":
        return "Pause before opening it. Verify the hostname independently and do not enter credentials or payment information unless the destination is confirmed."
    if "https_not_used" in codes:
        return "Avoid entering sensitive information over this HTTP URL; verify the destination and use an official HTTPS link instead."
    if level == "LOW":
        return "Proceed only if you expected this link and have independently verified the hostname."
    return "No obvious structural red flags were detected. Open it only if you expected it and continue to verify the destination."


def analyze_url_value(url: str) -> dict[str, object]:
    """Inspect URL text and structure only; never connect to the destination."""

    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    indicators: list[URLDetectedIndicator] = []
    weights: dict[str, int] = {}

    def add(code: str, label: str, description: str, severity: str, weight: int) -> None:
        if code not in weights:
            indicators.append(_indicator(code, label, description, severity))
            weights[code] = weight

    if parsed.scheme.lower() != "https":
        add(
            "https_not_used",
            "HTTPS is not used",
            "The URL uses HTTP rather than HTTPS, so transport encryption cannot be assumed.",
            "medium",
            15,
        )

    try:
        parsed.port
    except ValueError:
        add(
            "invalid_syntax",
            "URL syntax irregularity",
            "The URL contains a malformed port or authority component.",
            "high",
            20,
        )

    if any(character.isspace() for character in url) or url.count("@") > 1:
        add(
            "invalid_syntax",
            "URL syntax irregularity",
            "The URL contains whitespace or repeated authority separators that deserve extra verification.",
            "medium",
            15,
        )

    if parsed.username is not None or parsed.password is not None:
        add(
            "embedded_credentials",
            "Embedded credentials",
            "The URL contains user-information fields before the hostname; do not use links that ask you to authenticate this way.",
            "high",
            30,
        )

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        add(
            "ip_address_host",
            "IP-address-based URL",
            "The destination uses a numeric IP address instead of a recognizable hostname, which makes independent verification harder.",
            "high",
            25,
        )

    labels = [label for label in hostname.split(".") if label]
    if any(label.startswith("xn--") for label in labels) or any(ord(character) > 127 for character in hostname):
        add(
            "idn_or_punycode",
            "Punycode or IDN hostname",
            "The hostname uses internationalized or punycode labels; inspect it carefully for look-alike characters.",
            "medium",
            20,
        )

    suspicious_words = {
        "account",
        "authenticate",
        "auth",
        "confirm",
        "login",
        "secure",
        "signin",
        "support",
        "update",
        "verify",
    }
    brand_words = {
        "amazon",
        "apple",
        "bank",
        "facebook",
        "google",
        "instagram",
        "microsoft",
        "netflix",
        "paypal",
        "university",
        "whatsapp",
    }
    subdomain_labels = labels[:-2] if len(labels) > 2 else []
    if len(labels) >= 5 or (len(labels) >= 4 and suspicious_words.intersection(subdomain_labels)):
        add(
            "suspicious_subdomain",
            "Suspicious subdomain pattern",
            "The hostname has an unusually deep or action-oriented subdomain structure; verify the registrable domain carefully.",
            "medium",
            20,
        )

    host_compact = re.sub(r"[^a-z0-9]", "", hostname)
    if brand_words.intersection(labels) and suspicious_words.intersection(labels):
        add(
            "impersonation_pattern",
            "Obvious impersonation pattern",
            "The hostname combines a recognizable brand or organization with a login, verification, or security action word.",
            "high",
            25,
        )
    elif any(brand in host_compact for brand in brand_words) and any(word in host_compact for word in suspicious_words):
        add(
            "impersonation_pattern",
            "Possible impersonation pattern",
            "The hostname appears to combine brand-like wording with an account or verification action; confirm the actual domain owner.",
            "medium",
            18,
        )

    path_and_query = f"{parsed.path}?{parsed.query}".lower()
    suspicious_keywords = {
        "account",
        "authenticate",
        "auth",
        "billing",
        "confirm",
        "credential",
        "login",
        "password",
        "payment",
        "signin",
        "secure",
        "session",
        "update",
        "verify",
        "wallet",
    }
    if any(re.search(rf"(?:^|[/_.=-]){re.escape(word)}(?:$|[/_.?&=-])", path_and_query) for word in suspicious_keywords):
        add(
            "suspicious_keyword",
            "Suspicious URL keyword",
            "The path or query contains account, login, payment, verification, or credential-related wording.",
            "medium",
            12,
        )

    if len(url) > 500:
        add(
            "excessive_length",
            "Excessive URL length",
            "The URL is unusually long, which can obscure its destination or carry a large amount of tracking or encoded data.",
            "medium",
            20,
        )
    elif len(url) > 200:
        add(
            "long_url",
            "Long URL",
            "The URL is longer than typical links and should be checked carefully before opening.",
            "low",
            10,
        )

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    suspicious_query_keys = {
        "auth",
        "continue",
        "dest",
        "destination",
        "login",
        "next",
        "password",
        "redirect",
        "return",
        "session",
        "target",
        "token",
        "url",
        "verify",
    }
    if len(query_pairs) > 10 or any(key.lower() in suspicious_query_keys for key, _ in query_pairs):
        add(
            "suspicious_query",
            "Suspicious query parameters",
            "The query contains redirect, token, session, login, or other parameters that can obscure where a click leads or carry sensitive values.",
            "medium",
            15,
        )
    if any(re.search(r"%[0-9a-f]{2}", value, re.IGNORECASE) for _, value in query_pairs):
        add(
            "encoded_query_value",
            "Encoded query value",
            "The query contains encoded data; inspect the destination and avoid entering secrets until verified.",
            "low",
            8,
        )

    score = min(100, sum(weights.values()))
    level = _risk_level(score)
    codes = set(weights)
    if indicators:
        explanation = (
            f"This URL contains {len(indicators)} observable structural indicator(s). "
            "The score is based on URL text and parsing only; it does not prove that the destination is malicious, and no connection was made."
        )
    else:
        explanation = (
            "No obvious structural warning indicators were detected in this URL. "
            "This is not proof that the destination is safe; reputation, page content, and context were not checked, and no connection was made."
        )
    return {
        "url": url,
        "risk_score": score,
        "risk_level": level,
        "detected_indicators": indicators,
        "explanation": explanation,
        "recommended_action": _recommended_action(level, codes),
    }


def _to_response(analysis: URLAnalysis) -> URLAnalysisResponse:
    return URLAnalysisResponse(
        id=analysis.id,
        url=analysis.url,
        risk_score=int(analysis.risk_score),
        risk_level=analysis.risk_level.upper(),  # type: ignore[arg-type]
        detected_indicators=[URLDetectedIndicator.model_validate(item) for item in analysis.detected_indicators],
        explanation=analysis.analysis_result,
        recommended_action=analysis.recommended_action,
        created_at=analysis.created_at,
    )


def persist_url_analysis(db: Session, *, user_id: int | None, url: str) -> URLAnalysisResponse:
    result = analyze_url_value(url)
    indicators = result["detected_indicators"]
    assert isinstance(indicators, list)
    score = result["risk_score"]
    level = result["risk_level"]
    assert isinstance(score, int)
    assert isinstance(level, str)
    if user_id is None:
        return URLAnalysisResponse(
            id=None,
            url=url,
            risk_score=score,
            risk_level=level,  # type: ignore[arg-type]
            detected_indicators=[URLDetectedIndicator.model_validate(item) for item in indicators],
            explanation=str(result["explanation"]),
            recommended_action=str(result["recommended_action"]),
            created_at=datetime.now(timezone.utc),
        )

    analysis = URLAnalysis(
        user_id=user_id,
        url=url,
        risk_score=Decimal(score),
        risk_level=level.lower(),
        analysis_result=str(result["explanation"]),
        detected_indicators=[item.model_dump() for item in indicators],
        recommended_action=str(result["recommended_action"]),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _to_response(analysis)


def get_url_history(db: Session, *, user_id: int, limit: int) -> list[URLAnalysisResponse]:
    rows = db.scalars(
        select(URLAnalysis)
        .where(URLAnalysis.user_id == user_id)
        .order_by(desc(URLAnalysis.created_at), desc(URLAnalysis.id))
        .limit(limit)
    ).all()
    return [_to_response(row) for row in rows]
