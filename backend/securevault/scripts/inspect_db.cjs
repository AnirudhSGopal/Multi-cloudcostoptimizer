const { DatabaseSync } = require('node:sqlite');

const db = new DatabaseSync('instance/securevault.db', { readOnly: true });

const tables = db.prepare(
  "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
).all();

const counts = Object.fromEntries(
  tables.map(({ name }) => [
    name,
    db.prepare(`SELECT COUNT(*) AS count FROM ${name}`).get().count,
  ])
);

const scanResults = db.prepare(
  `SELECT id, job_id, security_score, total_findings, critical_count,
          high_count, medium_count, low_count, info_count, files_scanned,
          lines_scanned, scan_duration_s, created_at
   FROM scan_results ORDER BY id`
).all();

const vulnerabilities = db.prepare(
  `SELECT severity, finding_type, COUNT(*) AS count
   FROM vulnerabilities GROUP BY severity, finding_type ORDER BY severity, finding_type`
).all();

const cloudMetrics = db.prepare(
  `SELECT provider, COUNT(*) AS resources, SUM(cost_usd) AS total_cost
   FROM cloud_metrics GROUP BY provider ORDER BY provider`
).all();

const accounts = db.prepare(
  `SELECT id, provider, account_label, status, last_synced_at
   FROM cloud_accounts ORDER BY id`
).all();

const metricRows = db.prepare(
  `SELECT provider, account_id, region, bucket_name, storage_class, size_bytes,
          object_count, cost_usd, collected_at
   FROM cloud_metrics ORDER BY id`
).all();

console.log(JSON.stringify({
  tables, counts, accounts, scanResults, vulnerabilities, cloudMetrics, metricRows,
}, null, 2));
