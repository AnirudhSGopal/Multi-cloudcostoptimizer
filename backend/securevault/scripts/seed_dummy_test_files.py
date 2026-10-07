"""
Seed full dummy data of test files, scan jobs, scan results, and vulnerabilities
for demo user anirudhsgopal18@gmail.com into the Supabase database.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core.factory import create_app
from app.core.extensions import db
from app.models.user import User, RoleEnum
from app.models.cloud_account import CloudAccount, AccountStatusEnum
from app.models.cloud import CloudProviderEnum, CloudMetric
from app.models.scan import ScanJob, ScanResult, Vulnerability, ScanStatusEnum, SeverityEnum, FindingTypeEnum
from app.services.cloud.demo_dataset import get_demo_service_costs


def seed_dummy_data():
    app = create_app("development")
    with app.app_context():
        email = "anirudhsgopal18@gmail.com"
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                username="anirudhsgopal18",
                email=email,
                role=RoleEnum.ADMIN,
                is_active=True,
            )
            user.password = "anirudh@123"
            db.session.add(user)
            db.session.commit()
            print(f"[+] Created user {email}")
        else:
            user.password = "anirudh@123"
            user.role = RoleEnum.ADMIN
            user.is_active = True
            db.session.commit()
            print(f"[+] Verified user {email} (id={user.id})")

        # ── 1. Cloud Accounts & Metrics ───────────────────────────────────────
        providers = [
            (CloudProviderEnum.AWS, "AWS Production Primary (us-east-1)", {"access_key_id": "AKIA9DEMOEXAMPLE9982", "region": "us-east-1"}),
            (CloudProviderEnum.GCP, "GCP Analytics & Data Platform", {"project_id": "cloudopt-enterprise-prod-01", "bigquery_dataset": "billing_export_prod"}),
            (CloudProviderEnum.AZURE, "Azure Corporate Workloads", {"subscription_id": "sub-8841-92fa-azure-prod", "tenant_id": "tenant-0041-99af"}),
        ]

        for provider_enum, label, creds in providers:
            account = CloudAccount.query.filter_by(user_id=user.id, provider=provider_enum).first()
            if not account:
                account = CloudAccount(
                    user_id=user.id,
                    provider=provider_enum,
                    account_label=label,
                    status=AccountStatusEnum.CONNECTED
                )
                account.set_credentials(creds)
                db.session.add(account)
                db.session.flush()
            else:
                account.account_label = label
                account.status = AccountStatusEnum.CONNECTED
                account.set_credentials(creds)

            # Refresh CloudMetrics
            CloudMetric.query.filter_by(cloud_account_id=account.id).delete()
            cost_items = get_demo_service_costs(provider_enum.value)
            for item in cost_items:
                m = CloudMetric(
                    user_id=user.id,
                    cloud_account_id=account.id,
                    provider=provider_enum,
                    account_id=label,
                    region="global",
                    bucket_name=item.get("service"),
                    storage_class="COST_SUMMARY",
                    cost_usd=item.get("monthly_cost", 0.0),
                )
                db.session.add(m)

        db.session.commit()
        print("[+] Seeded AWS, GCP, and Azure accounts & metrics")

        # ── 2. Remove old scan jobs for user to cleanly insert full dummy dataset
        existing_jobs = ScanJob.query.filter_by(requested_by=user.id).all()
        for j in existing_jobs:
            db.session.delete(j)
        db.session.commit()

        now = datetime.now(timezone.utc)

        # ── 3. Scan Job 1: workspace://test-files (Uploaded Test Files) ────────
        job_test_files = ScanJob(
            repo_url="workspace://test-files",
            branch="main",
            status=ScanStatusEnum.COMPLETED,
            requested_by=user.id,
            created_at=now - timedelta(hours=2),
            started_at=now - timedelta(hours=2),
            finished_at=now - timedelta(hours=1, minutes=58),
        )
        db.session.add(job_test_files)
        db.session.flush()

        res_test_files = ScanResult(
            job_id=job_test_files.id,
            security_score=58.0,
            coverage={"python": "complete", "npm": "not_present", "maven": "not_present", "gradle": "not_present"},
            total_findings=11,
            critical_count=4,
            high_count=4,
            medium_count=2,
            low_count=1,
            info_count=0,
            files_scanned=8,
            lines_scanned=1420,
            scan_duration_s=3.8,
            created_at=now - timedelta(hours=1, minutes=58),
        )
        db.session.add(res_test_files)

        vulns_test_files = [
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.SECRET,
                severity=SeverityEnum.CRITICAL,
                rule_id="SEC001",
                title="AWS Access Key ID",
                description="Hardcoded AWS Access Key ID detected in application configuration.",
                file_path="app/auth_service.py",
                line_number=6,
                matched_text="AKIA1234567890ABCDEF",
                remediation="Remove key from source code and use AWS Secrets Manager or IAM instance profiles.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.SECRET,
                severity=SeverityEnum.CRITICAL,
                rule_id="SEC002",
                title="AWS Secret Access Key",
                description="Hardcoded AWS Secret Access Key detected.",
                file_path="app/auth_service.py",
                line_number=7,
                matched_text="aws_secret_key = 'abcdefghijklmnopqrstuvwxyz0123456789ABCD'",
                remediation="Remove immediately and rotate key in AWS IAM console.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.CRITICAL,
                rule_id="CODE003",
                title="SQL Injection — String Formatting",
                description="SQL query constructed with % string interpolation allows arbitrary SQL injection.",
                file_path="app/db_service.py",
                line_number=14,
                matched_text="cursor.execute(\"SELECT * FROM users WHERE id = '%s'\" % user_id)",
                remediation="Use parameterised queries (cursor.execute(sql, (user_id,))).",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.CRITICAL,
                rule_id="CODE004",
                title="SQL Injection — f-string Query",
                description="SQL query dynamically interpolated using Python f-string.",
                file_path="app/db_service.py",
                line_number=16,
                matched_text="cursor.execute(f\"SELECT * FROM accounts WHERE user_id = '{user_id}'\")",
                remediation="Never interpolate parameters directly into SQL statements.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.SECRET,
                severity=SeverityEnum.HIGH,
                rule_id="SEC004",
                title="Hardcoded JWT Secret / Token",
                description="Hardcoded JWT secret token in code.",
                file_path="app/auth_service.py",
                line_number=10,
                matched_text="jwt_secret = 'super_secret_jwt_signing_key_123456'",
                remediation="Store JWT_SECRET_KEY in secure environment variable.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.HIGH,
                rule_id="CODE014",
                title="Hardcoded Database Password",
                description="Literal database password embedded in Python source.",
                file_path="app/auth_service.py",
                line_number=11,
                matched_text="db_password = 'SuperAdminPassword2026!'",
                remediation="Inject database credentials via environment variables.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.HIGH,
                rule_id="CODE001",
                title="Use of eval()",
                description="eval() executes arbitrary code and allows remote code execution.",
                file_path="app/api_routes.py",
                line_number=13,
                matched_text="result = eval(script_str)",
                remediation="Replace eval() with safe parsers like ast.literal_eval().",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.HIGH,
                rule_id="CODE005",
                title="Shell Injection — os.system()",
                description="os.system() called with concatenated user input allows shell injection.",
                file_path="app/api_routes.py",
                line_number=16,
                matched_text="os.system(\"echo \" + command_str)",
                remediation="Use subprocess.run with arguments array and shell=False.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.MEDIUM,
                rule_id="CODE011",
                title="Weak Hash Algorithm — MD5",
                description="MD5 is cryptographically broken and prone to collision attacks.",
                file_path="app/auth_service.py",
                line_number=15,
                matched_text="hashlib.md5(pwd.encode()).hexdigest()",
                remediation="Use SHA-256 for integrity hashing or bcrypt/argon2 for passwords.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.MEDIUM,
                rule_id="CODE015",
                title="Debug Mode Enabled in Production Code",
                description="DEBUG=True hardcoded in application startup code.",
                file_path="app/api_routes.py",
                line_number=9,
                matched_text="DEBUG = True",
                remediation="Disable debug mode in production via environment flag.",
            ),
            Vulnerability(
                job_id=job_test_files.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.LOW,
                rule_id="CODE012",
                title="Deprecated SHA-1 Hashing",
                description="SHA-1 algorithm detected for data signature.",
                file_path="app/web_views.py",
                line_number=28,
                matched_text="hashlib.sha1(data.encode())",
                remediation="Upgrade to SHA-256 or SHA-512.",
            ),
        ]
        db.session.add_all(vulns_test_files)

        # ── 4. Scan Job 2: https://github.com/AnirudhSGopal/maven-project ─────
        job_maven = ScanJob(
            repo_url="https://github.com/AnirudhSGopal/maven-project",
            branch="main",
            status=ScanStatusEnum.COMPLETED,
            requested_by=user.id,
            created_at=now - timedelta(hours=5),
            started_at=now - timedelta(hours=5),
            finished_at=now - timedelta(hours=4, minutes=58),
        )
        db.session.add(job_maven)
        db.session.flush()

        res_maven = ScanResult(
            job_id=job_maven.id,
            security_score=78.0,
            coverage={"python": "not_present", "npm": "not_present", "maven": "complete", "gradle": "complete"},
            total_findings=4,
            critical_count=0,
            high_count=1,
            medium_count=2,
            low_count=1,
            info_count=0,
            files_scanned=6,
            lines_scanned=310,
            scan_duration_s=2.4,
            created_at=now - timedelta(hours=4, minutes=58),
        )
        db.session.add(res_maven)

        vulns_maven = [
            Vulnerability(
                job_id=job_maven.id,
                finding_type=FindingTypeEnum.DEPENDENCY,
                severity=SeverityEnum.MEDIUM,
                rule_id="JAVA015",
                title="Outdated JUnit 4.12 Dependency",
                description="junit:junit version 4.12 contains known vulnerability CVE-2020-15250 (temporary folder permission bypass).",
                file_path="pom.xml",
                line_number=17,
                cve_id="CVE-2020-15250",
                package_name="junit:junit",
                package_version="4.12",
                fix_version="4.13.2",
                matched_text="<artifactId>junit</artifactId>\n            <version>4.12</version>",
                remediation="Upgrade to junit:junit:4.13.2 or migrate to JUnit 5 (org.junit.jupiter).",
            ),
            Vulnerability(
                job_id=job_maven.id,
                finding_type=FindingTypeEnum.DEPENDENCY,
                severity=SeverityEnum.MEDIUM,
                rule_id="JAVA020",
                title="Gradle Dependency — Vulnerable JUnit 4.x",
                description="build.gradle references vulnerable JUnit 4.x dependency before patch version 4.13.2.",
                file_path="build.gradle",
                line_number=14,
                cve_id="CVE-2020-15250",
                package_name="junit:junit",
                package_version="4.12",
                fix_version="4.13.2",
                matched_text="testImplementation 'junit:junit:4.12'",
                remediation="Update build.gradle dependency to 'junit:junit:4.13.2'.",
            ),
            Vulnerability(
                job_id=job_maven.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.HIGH,
                rule_id="JAVA001",
                title="SQL Injection — JDBC String Concatenation",
                description="SQL query built by string concatenation in Java JDBC layer allows SQL injection.",
                file_path="src/main/java/com/example/App.java",
                line_number=18,
                matched_text="statement.executeQuery(\"SELECT * FROM items WHERE name = '\" + input + \"'\")",
                remediation="Use PreparedStatement with parameter placeholders (?) rather than string concatenation.",
            ),
            Vulnerability(
                job_id=job_maven.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.LOW,
                rule_id="JAVA019",
                title="Java Source Compiled to Java 8 (EOL)",
                description="Maven compiler plugin targets Java 1.8 which misses modern security features and is nearing EOL.",
                file_path="pom.xml",
                line_number=29,
                matched_text="<source>1.8</source>\n                    <target>1.8</target>",
                remediation="Migrate source/target compilation to Java 17 LTS or Java 21 LTS.",
            ),
        ]
        db.session.add_all(vulns_maven)

        # ── 5. Scan Job 3: https://github.com/AnirudhSGopal/myintern ──────────
        job_myintern = ScanJob(
            repo_url="https://github.com/AnirudhSGopal/myintern",
            branch="main",
            status=ScanStatusEnum.COMPLETED,
            requested_by=user.id,
            created_at=now - timedelta(days=1),
            started_at=now - timedelta(days=1),
            finished_at=now - timedelta(days=1) + timedelta(minutes=4),
        )
        db.session.add(job_myintern)
        db.session.flush()

        res_myintern = ScanResult(
            job_id=job_myintern.id,
            security_score=85.0,
            coverage={"python": "complete", "npm": "clean", "maven": "not_present", "gradle": "not_present"},
            total_findings=3,
            critical_count=0,
            high_count=1,
            medium_count=1,
            low_count=1,
            info_count=0,
            files_scanned=24,
            lines_scanned=2150,
            scan_duration_s=4.1,
            created_at=now - timedelta(days=1) + timedelta(minutes=4),
        )
        db.session.add(res_myintern)

        vulns_myintern = [
            Vulnerability(
                job_id=job_myintern.id,
                finding_type=FindingTypeEnum.SECRET,
                severity=SeverityEnum.HIGH,
                rule_id="SEC003",
                title="Generic API Key in Frontend Config",
                description="Client-side configuration file contains plain-text API key literal.",
                file_path="src/config/api.json",
                line_number=12,
                matched_text="api_key: 'AIzaSyD9876543210ZYXWVUTSRQPONMLKJIHGF'",
                remediation="Move API key to backend proxy or inject via environment build parameters.",
            ),
            Vulnerability(
                job_id=job_myintern.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.MEDIUM,
                rule_id="CODE008",
                title="DOM XSS — innerHTML Assignment",
                description="Direct assignment to element.innerHTML with dynamic content.",
                file_path="src/components/DashboardView.js",
                line_number=45,
                matched_text="container.innerHTML = userContent",
                remediation="Use textContent or sanitize HTML with DOMPurify.",
            ),
            Vulnerability(
                job_id=job_myintern.id,
                finding_type=FindingTypeEnum.CODE_PATTERN,
                severity=SeverityEnum.LOW,
                rule_id="CODE015",
                title="Debug Mode Flag in Development Module",
                description="app.run(debug=True) present in entry point file.",
                file_path="server.py",
                line_number=62,
                matched_text="app.run(debug=True, port=8000)",
                remediation="Conditionally gate debug flag with os.getenv('DEBUG') == 'true'.",
            ),
        ]
        db.session.add_all(vulns_myintern)

        db.session.commit()
        print(f"[SUCCESS] Fully seeded dummy scan jobs, results & vulnerabilities for {email}!")


if __name__ == "__main__":
    seed_dummy_data()
