-- Seed data: service catalog, project platforms, default settings.
-- Safe to re-run — every insert is OR IGNORE.

INSERT OR IGNORE INTO service_catalog (slug, name, description, starting_price_usd, sort_order) VALUES
  ('microsoft-365',       'Microsoft 365',       'Email, Outlook, Exchange Online, Teams, licensing and admin.',      40,  1),
  ('google-workspace',    'Google Workspace',    'Gmail, Drive, admin console and user management.',                  40,  2),
  ('endpoint-management', 'Endpoint Management', 'Manage, monitor and secure every device your team uses.',           49,  3),
  ('windows-support',     'Windows Support',     'Troubleshooting, updates, performance and configuration.',          25,  4),
  ('macos-jamf',          'macOS / Jamf',        'Mac fleet management and configuration with Jamf.',                 40,  5),
  ('active-directory',    'Active Directory',    'Users, groups, permissions and identity administration.',           40,  6),
  ('patch-management',    'Patch Management',    'Keep operating systems and software up to date and secure.',        49,  7),
  ('cybersecurity',       'Cybersecurity',       'Practical security hardening for small business environments.',     75,  8),
  ('remote-it-support',   'Remote IT Support',   'On-demand troubleshooting wherever your team works.',               25,  9),
  ('it-migration',        'IT Migration',        'Move platforms, mailboxes and infrastructure without disruption.',  75, 10),
  ('it-asset-management', 'IT Asset Management', 'Track, manage and account for the devices and licenses you own.',   49, 11),
  ('other',               'Other',               'Something not covered by the categories above.',                  NULL, 12);

INSERT OR IGNORE INTO project_platforms (slug, name) VALUES
  ('fiverr', 'Fiverr'),
  ('upwork', 'Upwork'),
  ('other',  'Other');

INSERT OR IGNORE INTO settings (key, value) VALUES
  ('business_name',    'ITVedas Services'),
  ('website_url',      'https://services.itvedas.com'),
  ('contact_email',    'info@itvedas.com'),
  ('fiverr_profile',   ''),
  ('upwork_profile',   ''),
  ('analytics_id',     '');
