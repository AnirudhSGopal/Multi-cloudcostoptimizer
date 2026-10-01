"""
Java-specific security rules.

Covers patterns that are common Java security issues and do not map to
the generic Python/JS rules in code_patterns.py:

  - SQL injection via JDBC string concatenation
  - Runtime.exec() / ProcessBuilder — shell injection
  - Hardcoded passwords / credentials in Java code
  - Weak crypto: MD5, SHA-1, DES, ECB mode
  - Insecure random: java.util.Random for security purposes
  - XML External Entity (XXE) — unsafe DocumentBuilder / SAXParser
  - Java object deserialization (ObjectInputStream.readObject)
  - Outdated/vulnerable dependency versions detected in pom.xml / build.gradle
"""
import re
from app.models.scan import SeverityEnum, FindingTypeEnum

_CODE   = FindingTypeEnum.CODE_PATTERN
_SECRET = FindingTypeEnum.SECRET
_DEP    = FindingTypeEnum.DEPENDENCY

JAVA_RULES: list[dict] = [
    # ── SQL Injection (JDBC) ────────────────────────────────────────────────
    {
        "rule_id":     "JAVA001",
        "title":       "SQL Injection — JDBC String Concatenation",
        "description": (
            "SQL query built by string concatenation allows injection. "
            "Detected createStatement() without PreparedStatement."
        ),
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": _CODE,
        "pattern":     re.compile(
            r"(?i)(createStatement\s*\(\s*\)|Statement\s+\w+\s*=).*?(\"|\+)\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)"
        ),
        "remediation": (
            "Replace Statement with PreparedStatement and use parameterised queries. "
            "Never concatenate user input into SQL strings."
        ),
    },
    {
        "rule_id":     "JAVA002",
        "title":       "SQL Injection — executeQuery / executeUpdate with Concatenation",
        "description": "SQL executed via executeQuery/executeUpdate with string literal + variable.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": _CODE,
        "pattern":     re.compile(
            r"(?i)(executeQuery|executeUpdate|execute)\s*\(\s*\"[^\"]*\"\s*\+"
        ),
        "remediation": "Use PreparedStatement with ? placeholders instead of concatenation.",
    },

    # ── Shell Injection ─────────────────────────────────────────────────────
    {
        "rule_id":     "JAVA003",
        "title":       "Shell Injection — Runtime.exec()",
        "description": (
            "Runtime.exec() called with a string argument may allow command injection "
            "if the argument contains unsanitised user input."
        ),
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bRuntime\b.*\bexec\s*\("),
        "remediation": (
            "Pass arguments as a String[] array to avoid shell interpretation. "
            "Validate and whitelist all external input before use in commands."
        ),
    },
    {
        "rule_id":     "JAVA004",
        "title":       "Shell Injection — ProcessBuilder with Concatenated String",
        "description": "ProcessBuilder constructed with a dynamic/concatenated command string.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bProcessBuilder\s*\(.*\+"),
        "remediation": "Pass arguments as a fixed String[] list; never concatenate user input.",
    },

    # ── Hardcoded Credentials ───────────────────────────────────────────────
    {
        "rule_id":     "JAVA005",
        "title":       "Hardcoded Password in Java Code",
        "description": 'String literal assigned to a variable named password/passwd/pwd/secret.',
        "severity":    SeverityEnum.HIGH,
        "finding_type": _SECRET,
        "pattern":     re.compile(
            r'(?i)(password|passwd|pwd|secret)\s*=\s*"[^"]{4,}"'
        ),
        "remediation": (
            "Move credentials to environment variables or a secrets manager "
            "(e.g. AWS Secrets Manager, HashiCorp Vault)."
        ),
    },
    {
        "rule_id":     "JAVA006",
        "title":       "Hardcoded Database Credentials",
        "description": "JDBC URL with embedded username or password.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": _SECRET,
        "pattern":     re.compile(
            r'(?i)jdbc:[a-z]+://[^"]*:(password|[A-Za-z0-9@#$%^&*!]{6,})@'
        ),
        "remediation": "Use environment variables or a connection pool with externalised config.",
    },

    # ── Weak Cryptography ───────────────────────────────────────────────────
    {
        "rule_id":     "JAVA007",
        "title":       "Weak Hash — MD5 in Java",
        "description": 'MessageDigest.getInstance("MD5") — MD5 is cryptographically broken.',
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": _CODE,
        "pattern":     re.compile(r'(?i)MessageDigest\.getInstance\s*\(\s*"MD5"'),
        "remediation": 'Use SHA-256: MessageDigest.getInstance("SHA-256").',
    },
    {
        "rule_id":     "JAVA008",
        "title":       "Weak Hash — SHA-1 in Java",
        "description": 'MessageDigest.getInstance("SHA-1") — SHA-1 is deprecated for security use.',
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": _CODE,
        "pattern":     re.compile(r'(?i)MessageDigest\.getInstance\s*\(\s*"SHA-?1"'),
        "remediation": 'Use SHA-256 or SHA-3 instead.',
    },
    {
        "rule_id":     "JAVA009",
        "title":       "Weak Cipher — DES / DESede",
        "description": 'Cipher.getInstance("DES") or "DESede" uses broken encryption.',
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r'(?i)Cipher\.getInstance\s*\(\s*"DES'),
        "remediation": 'Use AES/GCM/NoPadding: Cipher.getInstance("AES/GCM/NoPadding").',
    },
    {
        "rule_id":     "JAVA010",
        "title":       "Insecure Cipher Mode — ECB",
        "description": 'AES/ECB mode leaks data patterns. Found Cipher.getInstance("AES/ECB").',
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r'(?i)Cipher\.getInstance\s*\(\s*"AES/ECB'),
        "remediation": 'Use AES/GCM/NoPadding for authenticated encryption.',
    },

    # ── Insecure Randomness ─────────────────────────────────────────────────
    {
        "rule_id":     "JAVA011",
        "title":       "Insecure Random — java.util.Random",
        "description": (
            "java.util.Random is not cryptographically secure. "
            "Using it for tokens, passwords, or session IDs is unsafe."
        ),
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bnew\s+Random\s*\(\s*\)"),
        "remediation": "Use java.security.SecureRandom for any security-sensitive randomness.",
    },

    # ── XXE ─────────────────────────────────────────────────────────────────
    {
        "rule_id":     "JAVA012",
        "title":       "XML External Entity (XXE) — Unsafe DocumentBuilder",
        "description": (
            "DocumentBuilderFactory without disabling external entity processing "
            "is vulnerable to XXE attacks."
        ),
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bDocumentBuilderFactory\.newInstance\s*\(\s*\)"),
        "remediation": (
            'Call dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true) '
            "immediately after creation to prevent XXE."
        ),
    },
    {
        "rule_id":     "JAVA013",
        "title":       "XML External Entity (XXE) — Unsafe SAXParser",
        "description": "SAXParserFactory without XXE protection may allow entity expansion attacks.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bSAXParserFactory\.newInstance\s*\(\s*\)"),
        "remediation": (
            'Set spf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true).'
        ),
    },

    # ── Insecure Deserialization ─────────────────────────────────────────────
    {
        "rule_id":     "JAVA014",
        "title":       "Insecure Deserialization — ObjectInputStream.readObject()",
        "description": (
            "Java object deserialization via readObject() on untrusted data can lead "
            "to remote code execution."
        ),
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": _CODE,
        "pattern":     re.compile(r"\bnew\s+ObjectInputStream\b"),
        "remediation": (
            "Avoid native Java serialization for data from untrusted sources. "
            "Use JSON (Jackson, Gson) or validate with a whitelist-based ObjectInputFilter."
        ),
    },

    # ── Maven pom.xml: Vulnerable / Outdated Dependencies ───────────────────
    {
        "rule_id":     "JAVA015",
        "title":       "Outdated JUnit 4.x Dependency (pom.xml)",
        "description": (
            "junit:junit versions before 4.13.2 contain a known vulnerability "
            "(CVE-2020-15250 — temp directory info disclosure)."
        ),
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": _DEP,
        "pattern":     re.compile(
            r"<artifactId>junit</artifactId>\s*(?:<[^/].*?>\s*)*"
            r"<version>4\.((?:[0-9]|1[0-2])(\.[0-9]+)?)</version>",
            re.DOTALL,
        ),
        "remediation": "Upgrade to junit:junit:4.13.2 or migrate to JUnit 5 (junit-jupiter).",
    },
    {
        "rule_id":     "JAVA016",
        "title":       "Spring Framework < 5.3.x Detected (pom.xml)",
        "description": (
            "Old Spring Framework versions (< 5.3) lack patches for multiple CVEs "
            "including Spring4Shell (CVE-2022-22965)."
        ),
        "severity":    SeverityEnum.HIGH,
        "finding_type": _DEP,
        "pattern":     re.compile(
            r"<artifactId>spring-(?:core|webmvc|context|beans)</artifactId>\s*"
            r"(?:<[^/].*?>\s*)*<version>([0-4]\.|5\.[0-2]\.)",
            re.DOTALL,
        ),
        "remediation": "Upgrade to Spring Framework 5.3.39+ or 6.1.x.",
    },
    {
        "rule_id":     "JAVA017",
        "title":       "Log4j 2.x Vulnerable Version Detected (pom.xml)",
        "description": (
            "log4j-core versions prior to 2.17.1 are vulnerable to Log4Shell "
            "(CVE-2021-44228) — critical remote code execution."
        ),
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": _DEP,
        "pattern":     re.compile(
            r"<artifactId>log4j-core</artifactId>\s*(?:<[^/].*?>\s*)*"
            r"<version>2\.((?:[0-9]|1[0-6])(\.[0-9]+)?)</version>",
            re.DOTALL,
        ),
        "remediation": (
            "Upgrade log4j-core to 2.17.1 or later immediately. "
            "This is a critical RCE (Log4Shell / CVE-2021-44228)."
        ),
    },
    {
        "rule_id":     "JAVA018",
        "title":       "Jackson Databind Vulnerable Version (pom.xml)",
        "description": (
            "jackson-databind versions prior to 2.13.4.2 have known RCE vulnerabilities "
            "(CVE-2022-42004 and others)."
        ),
        "severity":    SeverityEnum.HIGH,
        "finding_type": _DEP,
        "pattern":     re.compile(
            r"<artifactId>jackson-databind</artifactId>\s*(?:<[^/].*?>\s*)*"
            r"<version>(1\.|2\.(0|1|2|3|4|5|6|7|8|9|10|11|12)\.|2\.13\.[0-3])",
            re.DOTALL,
        ),
        "remediation": "Upgrade jackson-databind to 2.15.x or later.",
    },
    {
        "rule_id":     "JAVA019",
        "title":       "Java Source Compiled to Java 8 or Earlier",
        "description": (
            "Maven compiler plugin targeting Java 8 or earlier (source/target 1.8) "
            "misses modern security APIs and is approaching EOL."
        ),
        "severity":    SeverityEnum.LOW,
        "finding_type": _CODE,
        "pattern":     re.compile(
            r"<(?:source|target)>1\.[0-8]</(?:source|target)>"
        ),
        "remediation": "Migrate to Java 17 LTS or Java 21 LTS for long-term security support.",
    },
    {
        "rule_id":     "JAVA020",
        "title":       "Gradle Dependency — Vulnerable JUnit 4.x",
        "description": (
            "build.gradle references junit:junit versions before 4.13.2 "
            "(CVE-2020-15250)."
        ),
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": _DEP,
        "pattern":     re.compile(
            r"['\"]junit:junit:4\.(?:[0-9]|1[0-2])(?:\.[0-9]+)?['\"]"
        ),
        "remediation": "Upgrade to junit:junit:4.13.2 or migrate to JUnit 5.",
    },
]
