"""
Insecure code-pattern detection rules.
15 rules covering: eval/exec, SQL injection, XSS, shell injection,
deserialization, weak crypto, path traversal, and more.
"""
import re
from app.models.scan import SeverityEnum, FindingTypeEnum

FINDING_TYPE = FindingTypeEnum.CODE_PATTERN

CODE_RULES: list[dict] = [
    # ── Code execution ────────────────────────────────────────────────────
    {
        "rule_id":     "CODE001",
        "title":       "Use of eval()",
        "description": "eval() executes arbitrary code and is almost always dangerous.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\beval\s*\("),
        "remediation": (
            "Replace eval() with safer alternatives such as ast.literal_eval() "
            "for data parsing or a proper parser for structured input."
        ),
    },
    {
        "rule_id":     "CODE002",
        "title":       "Use of exec()",
        "description": "exec() can execute arbitrary Python code at runtime.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\bexec\s*\("),
        "remediation": "Avoid exec(). Refactor to use functions or modules instead.",
    },
    # ── SQL injection ─────────────────────────────────────────────────────
    {
        "rule_id":     "CODE003",
        "title":       "SQL Injection — String Formatting",
        "description": "SQL query built with % or .format() string interpolation.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(execute|cursor\.execute)\s*\(\s*['\"].*?(SELECT|INSERT|UPDATE|DELETE|DROP)"
            r".*?(%s|%d|\{[^}]*\}|f['\"])"
        ),
        "remediation": "Use parameterised queries (cursor.execute(sql, params)) instead.",
    },
    {
        "rule_id":     "CODE004",
        "title":       "SQL Injection — f-string Query",
        "description": "SQL query constructed with an f-string, enabling injection.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)f['\"].*?(SELECT|INSERT|UPDATE|DELETE|DROP|WHERE).*?\{.*?\}"
        ),
        "remediation": "Never build SQL with f-strings. Use ORM or parameterised statements.",
    },
    # ── Shell injection ───────────────────────────────────────────────────
    {
        "rule_id":     "CODE005",
        "title":       "Shell Injection — os.system()",
        "description": "os.system() called with potentially tainted input.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\bos\.system\s*\("),
        "remediation": (
            "Use subprocess.run() with a list argument and shell=False. "
            "Validate and sanitise all input before constructing commands."
        ),
    },
    {
        "rule_id":     "CODE006",
        "title":       "Shell Injection — subprocess with shell=True",
        "description": "subprocess called with shell=True allows shell meta-character injection.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"subprocess\.(run|call|Popen|check_output).*shell\s*=\s*True"),
        "remediation": "Set shell=False and pass arguments as a list.",
    },
    # ── XSS ───────────────────────────────────────────────────────────────
    {
        "rule_id":     "CODE007",
        "title":       "XSS — Jinja2 mark_safe / Markup()",
        "description": "Marking user-supplied content as safe disables auto-escaping.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"(mark_safe|Markup)\s*\("),
        "remediation": "Never pass untrusted data to mark_safe/Markup. Use escaping.",
    },
    {
        "rule_id":     "CODE008",
        "title":       "XSS — innerHTML Assignment (JavaScript)",
        "description": "Direct assignment to innerHTML with dynamic content.",
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\.innerHTML\s*=\s*(?!(['\"`]<))"),
        "remediation": "Use textContent or DOM methods; sanitise HTML with DOMPurify.",
    },
    # ── Insecure deserialization ──────────────────────────────────────────
    {
        "rule_id":     "CODE009",
        "title":       "Insecure Deserialization — pickle.loads()",
        "description": "pickle.loads() on untrusted data allows arbitrary code execution.",
        "severity":    SeverityEnum.CRITICAL,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\bpickle\.loads?\s*\("),
        "remediation": "Use JSON or a schema-validated format for untrusted data.",
    },
    {
        "rule_id":     "CODE010",
        "title":       "Insecure YAML Loading — yaml.load()",
        "description": "yaml.load() without Loader=yaml.SafeLoader allows code execution.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\byaml\.load\s*\((?!.*SafeLoader)"),
        "remediation": "Replace yaml.load() with yaml.safe_load().",
    },
    # ── Weak cryptography ─────────────────────────────────────────────────
    {
        "rule_id":     "CODE011",
        "title":       "Weak Hash Algorithm — MD5",
        "description": "MD5 is cryptographically broken and unsuitable for security use.",
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"(?i)hashlib\.md5\s*\(|md5\s*\("),
        "remediation": "Use SHA-256 or SHA-3 for hashing. For passwords, use bcrypt/argon2.",
    },
    {
        "rule_id":     "CODE012",
        "title":       "Weak Hash Algorithm — SHA-1",
        "description": "SHA-1 is deprecated for cryptographic use.",
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"(?i)hashlib\.sha1\s*\("),
        "remediation": "Migrate to SHA-256 or SHA-3.",
    },
    # ── Path traversal ────────────────────────────────────────────────────
    {
        "rule_id":     "CODE013",
        "title":       "Path Traversal — open() with User Input",
        "description": "open() called with a variable that may contain path traversal sequences.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(r"\bopen\s*\(\s*(request\.|input\()"),
        "remediation": (
            "Validate file paths with os.path.realpath() and ensure they are "
            "within an expected base directory."
        ),
    },
    # ── Weak authentication ───────────────────────────────────────────────
    {
        "rule_id":     "CODE014",
        "title":       "Hardcoded Password",
        "description": "A variable named password/passwd/pwd holds a string literal.",
        "severity":    SeverityEnum.HIGH,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"](?!.*environ)([^'\"]{4,})['\"]"
        ),
        "remediation": "Store passwords in environment variables or a secrets vault.",
    },
    {
        "rule_id":     "CODE015",
        "title":       "Debug Mode Enabled in Production Code",
        "description": "DEBUG=True or app.run(debug=True) found in application code.",
        "severity":    SeverityEnum.MEDIUM,
        "finding_type": FINDING_TYPE,
        "pattern":     re.compile(
            r"(?i)(DEBUG\s*=\s*True|app\.run\s*\(.*debug\s*=\s*True)"
        ),
        "remediation": (
            "Disable debug mode in production. "
            "Control via environment variable: DEBUG=os.getenv('DEBUG', 'False') == 'True'."
        ),
    },
]