"""
Secret-detection rules.
Each rule is a dict consumed by static_analyzer.py.

Fields:
    rule_id      – unique identifier
    title        – human-readable name
    description  – what it detects
    severity     – critical / high / medium / low / info
    pattern      – compiled regex
    remediation  – fix advice
"""
import re
from app.models.scan import SeverityEnum, FindingTypeEnum

FINDING_TYPE = FindingTypeEnum.SECRET

SECRET_RULES: list[dict] = [
    {
        "rule_id":     "SEC001",
        "title":       "AWS Access Key ID",
        "description": "Hardcoded AWS Access Key ID detected.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
        "remediation": (
            "Remove the key from source code immediately. "
            "Rotate the key in AWS IAM and use environment variables or "
            "AWS Secrets Manager instead."
        ),
    },
    {
        "rule_id":     "SEC002",
        "title":       "AWS Secret Access Key",
        "description": "Hardcoded AWS Secret Access Key detected.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)aws.{0,20}secret.{0,20}['\"]([A-Za-z0-9/+=]{40})['\"]"
        ),
        "remediation": (
            "Remove immediately and rotate in IAM. Store in AWS Secrets Manager."
        ),
    },
    {
        "rule_id":     "SEC003",
        "title":       "Generic API Key",
        "description": "A variable named api_key / apikey contains a string literal.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]([A-Za-z0-9_\-]{16,})['\"]"
        ),
        "remediation": "Move API keys to environment variables or a secrets vault.",
    },
    {
        "rule_id":     "SEC004",
        "title":       "JWT Secret / Token",
        "description": "Hardcoded JWT secret or bearer token.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(jwt[_-]?secret|jwt[_-]?key|bearer[_-]?token)\s*[=:]\s*['\"]([^'\"]{8,})['\"]"
        ),
        "remediation": "Store JWT secrets in environment variables, never in code.",
    },
    {
        "rule_id":     "SEC005",
        "title":       "Database Connection String with Password",
        "description": "Database URI containing embedded password.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(postgres|mysql|mongodb|mssql)://[^:]+:[^@]{3,}@"
        ),
        "remediation": (
            "Use environment variables for database credentials. "
            "Never embed passwords in connection strings committed to source control."
        ),
    },
    {
        "rule_id":     "SEC006",
        "title":       "GitHub Personal Access Token",
        "description": "GitHub PAT (ghp_ prefix) found in code.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"ghp_[A-Za-z0-9]{36}"),
        "remediation": "Revoke the token immediately on GitHub and remove from code.",
    },
    {
        "rule_id":     "SEC007",
        "title":       "GitHub OAuth App Token",
        "description": "GitHub OAuth token (gho_ prefix) found in code.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"gho_[A-Za-z0-9]{36}"),
        "remediation": "Revoke the OAuth token and store credentials securely.",
    },
    {
        "rule_id":     "SEC008",
        "title":       "Google API Key",
        "description": "Google API key (AIza prefix) hardcoded.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        "remediation": (
            "Restrict the key in Google Cloud Console and move it to "
            "Secret Manager or environment variables."
        ),
    },
    {
        "rule_id":     "SEC009",
        "title":       "Slack Bot / Webhook Token",
        "description": "Slack token (xoxb- / xoxp- / hooks.slack.com) detected.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(xox[bprs]-[0-9A-Za-z\-]{10,}|hooks\.slack\.com/services/[A-Za-z0-9/]+)"
        ),
        "remediation": "Revoke in Slack App settings and store in environment variables.",
    },
    {
        "rule_id":     "SEC010",
        "title":       "Private Key / Certificate",
        "description": "PEM-encoded private key block found.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        ),
        "remediation": (
            "Remove private keys from repositories. "
            "Rotate/revoke affected certificates and store keys in a secrets vault."
        ),
    },
]