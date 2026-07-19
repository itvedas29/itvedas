# Changelog

All notable changes to ITVedas will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive test suite infrastructure
- HTML sanitization library for XSS prevention
- Accessibility enhancements (auto ARIA fixes)
- Canonical URL support (800+ pages)
- Subresource Integrity (SRI) for external resources
- API documentation
- Comprehensive changelog

### Changed
- Enhanced error handling with generic messages
- Improved origin validation for API endpoints
- Updated deployment and testing documentation

### Fixed
- Origin validation bypass in career-advice.js
- Error message information disclosure
- Session ID generation using secure random
- Exception handling in scripts
- Missing Content-Security-Policy header
- Missing HSTS header

### Security
- Added CSP header to prevent XSS
- Added HSTS for HTTPS enforcement
- Implemented secure session ID generation
- Added HTML sanitization utility
- Added SRI for CDN resource protection
- Fixed CORS origin validation

---

## [1.0.0] - 2026-07-17 (Phase 1 & 2)

### Security Audit & Fixes
- Complete repository security audit
- Fixed 4 critical security vulnerabilities
- Added comprehensive audit reports

### Phase 1: Security Foundation
- Secure session ID generation (crypto.getRandomValues)
- Content-Security-Policy header implementation
- HSTS header for HTTPS enforcement
- API error message sanitization
- CORS origin validation fixes
- Exception handler improvements
- Configuration cleanup

### Phase 2: Testing, Accessibility, SEO
- Testing framework setup (pytest)
- HTML sanitization library
- Accessibility enhancements (auto ARIA)
- Canonical URLs added (800+ files)
- Subresource Integrity (100+ files)
- Comprehensive documentation

### Initial Release Features
- 866 HTML pages indexed
- 584 news posts with archive
- 5,445+ CVE database entries
- Dynamic search functionality
- Responsive design
- Performance optimizations
- SEO optimization

---

## Previous Releases

### 2026-07-16
- Audit fixes: CVE payload split
- News archive implementation
- Orphaned page resolution
- Dead script archival
- CSS/JS minification

### 2026-07-15
- Initial launch with core IT content
- News feed integration
- Search functionality
- Responsive layout

---

## Security Releases

### [1.0.1] - 2026-07-17 (Security Patch)
**Critical Security Fixes**

#### Fixed
- Session ID generation vulnerability (CVE-XXXX-XXXXX)
  - Changed from `Math.random()` to `crypto.getRandomValues()`
  - Prevents session prediction attacks

- Missing CSP header (CVE-XXXX-XXXXX)
  - Added comprehensive Content-Security-Policy
  - Prevents XSS and injection attacks

- CORS bypass vulnerability (CVE-XXXX-XXXXX)
  - Fixed origin validation using exact matching
  - Changed from `string.includes()` to whitelist comparison

- Information disclosure (CVE-XXXX-XXXXX)
  - API now returns generic errors instead of exposing internals
  - Prevents attacker reconnaissance

---

## Versioning Policy

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes and security updates

### Security Policy

Security fixes are released as patches (Z in X.Y.Z) and may be released out of normal version cycle. Critical vulnerabilities trigger immediate patch releases.

---

## Roadmap

### Next Release (2026-08-01)
- [ ] Complete test coverage (60%+ critical paths)
- [ ] Inline event handler refactoring
- [ ] Schema markup for articles/news
- [ ] Performance optimizations
- [ ] Cache strategy refinement

### Future (2026-09-01)
- [ ] Advanced search features
- [ ] User authentication
- [ ] Community contributions
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Offline support (service worker)

---

## Contributing

See CONTRIBUTING.md for guidelines on reporting bugs, suggesting features, and submitting pull requests.

## License

See LICENSE file for details.

---

**Last Updated**: 2026-07-17  
**Maintainers**: ITVedas Team  
**Repository**: https://github.com/itvedas29/itvedas
