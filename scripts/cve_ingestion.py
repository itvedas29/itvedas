#!/usr/bin/env python3
"""
CVE Database Ingestion Script
Fetches new CVEs from NVD and updates the local database

Usage:
    python3 scripts/cve_ingestion.py --sync
    python3 scripts/cve_ingestion.py --report
"""

import json
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'NVD_API_URL': 'https://services.nvd.nist.gov/rest/json/cves/2.0',
    'NVD_API_KEY': None,  # Set via environment variable or config
    'DATABASE_FILE': 'cve-database-full.json',
    'LAST_SYNC_FILE': '.cve_last_sync',
    'REPORT_FILE': 'cve-ingestion-report.json',
}

class CVEIngester:
    def __init__(self):
        self.db_path = Path(CONFIG['DATABASE_FILE'])
        self.sync_file = Path(CONFIG['LAST_SYNC_FILE'])
        self.report_file = Path(CONFIG['REPORT_FILE'])
        self.existing_cves = self._load_database()
        self.existing_ids = {cve['id'] for cve in self.existing_cves}
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'new_cves': [],
            'updated_cves': [],
            'skipped_duplicates': [],
            'errors': [],
            'summary': {}
        }

    def _load_database(self):
        """Load existing CVE database"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading database: {e}")
        return []

    def _get_last_sync_time(self):
        """Get timestamp of last successful sync"""
        if self.sync_file.exists():
            try:
                with open(self.sync_file, 'r') as f:
                    return datetime.fromisoformat(f.read().strip())
            except Exception as e:
                logger.warning(f"Error reading sync file: {e}")

        # Default: look back 7 days if no sync record
        return datetime.now() - timedelta(days=7)

    def _normalize_cve(self, nvd_cve):
        """Convert NVD CVE data to our schema"""
        try:
            cve_id = nvd_cve.get('id', '')

            # Extract basic info
            descriptions = nvd_cve.get('descriptions', [])
            description = next((d.get('value', '') for d in descriptions if d.get('lang') == 'en'), '')

            # Extract published date
            published = nvd_cve.get('published', '')
            if published:
                published_date = published.split('T')[0]
            else:
                published_date = datetime.now().strftime('%Y-%m-%d')

            # Extract year from CVE ID (CVE-YYYY-NNNN)
            year = int(cve_id.split('-')[1]) if len(cve_id.split('-')) > 1 else datetime.now().year

            # Extract CVSS score (NVD API v2.0 format)
            metrics = nvd_cve.get('metrics', {})
            cvss_score = 0.0
            # Try cvssMetricV31 first, then fall back to cvssMetricV30
            for metric_key in ['cvssMetricV31', 'cvssMetricV30']:
                cvss_metrics = metrics.get(metric_key, [])
                if cvss_metrics:
                    cvss_data = cvss_metrics[0].get('cvssData', {})
                    cvss_score = cvss_data.get('baseScore', 0.0)
                    if cvss_score > 0:
                        break

            # Extract CWE
            weaknesses = nvd_cve.get('weaknesses', [])
            cwe_list = []
            for weakness in weaknesses:
                for cwe in weakness.get('cweIds', []):
                    cwe_list.append(cwe)

            # Determine severity
            if cvss_score >= 9.0:
                severity = 'Critical'
            elif cvss_score >= 7.0:
                severity = 'High'
            elif cvss_score >= 4.0:
                severity = 'Medium'
            else:
                severity = 'Low'

            # Extract affected products
            configs = nvd_cve.get('configurations', [])
            affected_products = set()
            affected_vendor = ''

            for config in configs:
                for node in config.get('nodes', []):
                    for cpe_match in node.get('cpeMatch', []):
                        cpe = cpe_match.get('criteria', '')
                        # Parse CPE to extract vendor/product
                        if 'cpe:2.3:' in cpe:
                            parts = cpe.split(':')
                            if len(parts) >= 4:
                                vendor = parts[3]
                                product = parts[4]
                                if not affected_vendor:
                                    affected_vendor = vendor.title()
                                affected_products.add(product.title())

            affected_str = ', '.join(sorted(list(affected_products))[:3]) if affected_products else affected_vendor

            # Extract vulnerability type
            vuln_type = 'Remote Code Execution'
            if 'buffer' in description.lower():
                vuln_type = 'Buffer Overflow'
            elif 'privilege' in description.lower():
                vuln_type = 'Privilege Escalation'
            elif 'denial' in description.lower():
                vuln_type = 'Denial of Service'
            elif 'information' in description.lower():
                vuln_type = 'Information Disclosure'

            # Check exploitation status
            references = nvd_cve.get('references', [])
            known_exploited = any('exploit' in ref.get('url', '').lower() for ref in references)

            # Create normalized CVE
            normalized = {
                'id': cve_id,
                'name': description[:100] if description else cve_id,
                'affected': affected_vendor if affected_vendor else 'Unknown',
                'year': year,
                'severity': severity,
                'cvss': round(cvss_score, 1),
                'type': vuln_type,
                'description': description[:500] if description else 'No description available',
                'remediation': 'Apply security updates from vendor. Follow CVE mitigation guidance.',
                'published_date': published_date,
                'cwe': cwe_list,
                'known_exploited': known_exploited,
                'source': 'nvd'
            }

            return normalized
        except Exception as e:
            logger.error(f"Error normalizing CVE {nvd_cve.get('id', 'unknown')}: {e}")
            return None

    def fetch_from_nvd(self, start_index=0):
        """Fetch CVEs from NVD API"""
        try:
            logger.info(f"Fetching CVEs from NVD (index: {start_index})...")

            headers = {}
            if CONFIG['NVD_API_KEY']:
                headers['apiKey'] = CONFIG['NVD_API_KEY']

            params = {
                'resultsPerPage': 100,
                'startIndex': start_index
            }

            # Add filter for recently published CVEs
            last_sync = self._get_last_sync_time()
            if last_sync:
                # NVD API uses pubStartDate and pubEndDate parameters
                pub_start_date = last_sync.strftime('%Y-%m-%dT00:00:00')
                pub_end_date = datetime.now().strftime('%Y-%m-%dT23:59:59')
                params['pubStartDate'] = pub_start_date
                params['pubEndDate'] = pub_end_date

            response = requests.get(
                CONFIG['NVD_API_URL'],
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])

                logger.info(f"Fetched {len(vulnerabilities)} CVEs from NVD")
                return vulnerabilities, data.get('totalResults', 0)
            elif response.status_code == 403:
                logger.error("NVD API rate limit exceeded or API key invalid")
                return [], 0
            else:
                logger.error(f"NVD API error: {response.status_code}")
                return [], 0

        except Exception as e:
            logger.error(f"Error fetching from NVD: {e}")
            return [], 0

    def ingest_cves(self, cves_data):
        """Ingest and process CVEs"""
        new_count = 0
        updated_count = 0
        duplicate_count = 0

        for cve_wrapper in cves_data:
            if 'cve' not in cve_wrapper:
                continue

            nvd_cve = cve_wrapper['cve']
            cve_id = nvd_cve.get('id', '')

            # Normalize CVE data
            normalized = self._normalize_cve(nvd_cve)
            if not normalized:
                self.report['errors'].append(f"Failed to normalize {cve_id}")
                continue

            # Check for duplicates
            if cve_id in self.existing_ids:
                duplicate_count += 1
                self.report['skipped_duplicates'].append(cve_id)
                logger.info(f"Skipping duplicate: {cve_id}")
                continue

            # Add new CVE
            self.existing_cves.append(normalized)
            self.existing_ids.add(cve_id)
            new_count += 1
            self.report['new_cves'].append({
                'id': cve_id,
                'severity': normalized['severity'],
                'cvss': normalized['cvss']
            })

            logger.info(f"Added new CVE: {cve_id} ({normalized['severity']})")

        return new_count, updated_count, duplicate_count

    def sort_database(self):
        """Sort CVEs by year (descending) then by ID"""
        self.existing_cves.sort(
            key=lambda x: (-x.get('year', 0), x.get('id', ''))
        )
        logger.info(f"Database sorted: {len(self.existing_cves)} CVEs total")

    def save_database(self):
        """Save CVE database to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.existing_cves, f, indent=2)
            logger.info(f"Saved {len(self.existing_cves)} CVEs to {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            self.report['errors'].append(f"Failed to save database: {e}")
            return False

    def update_sync_time(self):
        """Update last sync timestamp"""
        try:
            with open(self.sync_file, 'w') as f:
                f.write(datetime.now().isoformat())
            logger.info("Sync time updated")
        except Exception as e:
            logger.error(f"Error updating sync time: {e}")

    def save_report(self):
        """Save ingestion report"""
        # Add summary
        self.report['summary'] = {
            'total_cves': len(self.existing_cves),
            'new_cves_count': len(self.report['new_cves']),
            'duplicates_skipped': len(self.report['skipped_duplicates']),
            'errors': len(self.report['errors']),
            'critical_cves': sum(1 for c in self.existing_cves if c.get('severity') == 'Critical'),
            'high_cves': sum(1 for c in self.existing_cves if c.get('severity') == 'High'),
            'by_year': {}
        }

        # Count by year
        for cve in self.existing_cves:
            year = cve.get('year', 'unknown')
            self.report['summary']['by_year'][year] = self.report['summary']['by_year'].get(year, 0) + 1

        try:
            with open(self.report_file, 'w') as f:
                json.dump(self.report, f, indent=2)
            logger.info(f"Report saved to {self.report_file}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def sync(self):
        """Execute full sync"""
        logger.info("Starting CVE ingestion sync...")

        total_results = 0
        start_index = 0
        all_new = 0
        all_updated = 0
        all_duplicates = 0

        # Fetch in batches
        while True:
            cves_data, total_results = self.fetch_from_nvd(start_index)

            if not cves_data:
                break

            new, updated, duplicates = self.ingest_cves(cves_data)
            all_new += new
            all_updated += updated
            all_duplicates += duplicates

            start_index += 100

            # Stop if we've fetched all results
            if start_index >= total_results:
                break

        # Sort database
        self.sort_database()

        # Save updated database
        if self.save_database():
            self.update_sync_time()

        # Save report
        self.save_report()

        logger.info(f"Sync complete: +{all_new} new, ~{all_updated} updated, {all_duplicates} duplicates")
        return True

    def print_report(self):
        """Print ingestion report"""
        try:
            with open(self.report_file, 'r') as f:
                report = json.load(f)

            print("\n" + "="*60)
            print("CVE INGESTION REPORT")
            print("="*60)
            print(f"Timestamp: {report['timestamp']}")
            print(f"\nSummary:")
            print(f"  Total CVEs: {report['summary']['total_cves']}")
            print(f"  New CVEs: {report['summary']['new_cves_count']}")
            print(f"  Duplicates Skipped: {report['summary']['duplicates_skipped']}")
            print(f"  Critical: {report['summary']['critical_cves']}")
            print(f"  High: {report['summary']['high_cves']}")

            if report['summary']['by_year']:
                print(f"\nBreakdown by Year:")
                for year in sorted(report['summary']['by_year'].keys(), reverse=True)[:10]:
                    count = report['summary']['by_year'][year]
                    print(f"  {year}: {count} CVEs")

            if report['errors']:
                print(f"\nErrors ({len(report['errors'])}):")
                for error in report['errors'][:5]:
                    print(f"  - {error}")

            print("="*60 + "\n")
        except Exception as e:
            logger.error(f"Error printing report: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cve_ingestion.py --sync|--report")
        sys.exit(1)

    ingester = CVEIngester()

    if sys.argv[1] == '--sync':
        ingester.sync()
    elif sys.argv[1] == '--report':
        ingester.print_report()
    else:
        print("Invalid argument. Use --sync or --report")
        sys.exit(1)

if __name__ == '__main__':
    main()
