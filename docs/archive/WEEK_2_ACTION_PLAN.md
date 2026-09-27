# Week 2 Action Plan: GSC Geo-Targeting Setup

**Timeline:** July 4-10, 2026  
**Objective:** Configure Google Search Console for international geo-targeting  
**Expected Outcome:** Country-level performance visibility, baseline metrics captured

---

## 🎯 Primary Goal: India First, Then Global

India currently shows the strongest performance (70% CTR in your data). Configure GSC to prioritize India as primary target, establish baseline metrics for all 5 countries, and begin monitoring.

---

## Daily Action Items

### 📅 TODAY (Friday, July 4)

**Morning (15 minutes):**
- [ ] Open Google Search Console: https://search.google.com/search-console
- [ ] Select property: `https://itvedas.com`
- [ ] Navigate: Settings (bottom left) → Audience
- [ ] Screenshot current state (for comparison later)

**Afternoon (10 minutes):**
- [ ] Set target audience: **INDIA**
- [ ] Click Save
- [ ] Verify it says "Targeting: India (IN)"
- [ ] Screenshot confirmation

**Evening (5 minutes):**
- [ ] Navigate to: Performance (left sidebar)
- [ ] Add filter: Click "Country" dropdown
- [ ] Select all: IN, US, GB, AU, CA
- [ ] Screenshot baseline metrics (CTR, Clicks, Position for each)
- [ ] Note down the date (2026-07-04)

**Record baseline metrics:**
```
India (IN):     CTR: _____%, Clicks: _____, Impressions: _____, Pos: _____
USA (US):       CTR: _____%, Clicks: _____, Impressions: _____, Pos: _____
UK (GB):        CTR: _____%, Clicks: _____, Impressions: _____, Pos: _____
Australia (AU): CTR: _____%, Clicks: _____, Impressions: _____, Pos: _____
Canada (CA):    CTR: _____%, Clicks: _____, Impressions: _____, Pos: _____
```

---

### 📅 WEEKEND (Sat-Sun, July 6-7)

**Saturday - Light Review (10 minutes):**
- [ ] Open GSC again, take screenshot of Performance/Country filter
- [ ] Check: "Is indexing status OK?" (Coverage tab should be green)
- [ ] Note any crawl errors or warnings
- [ ] Screenshot crawl status

**Sunday - Setup Monitoring (15 minutes):**
- [ ] Create Google Sheets or Excel file: "GSC Weekly Tracking"
- [ ] Add columns: Date | Country | CTR | Clicks | Impressions | Position | Trend | Notes
- [ ] Populate with TODAY'S baseline metrics (July 4)
- [ ] Format as table for easy tracking
- [ ] [Download template: gsc-monitoring-template.csv](../itvedas-brain/gsc-monitoring-template.csv)

---

### 📅 WEEK 2 (Monday-Friday, July 8-12)

**Daily (5 minutes each):**
- [ ] Mon: Quick GSC check - screenshot country breakdown
- [ ] Tue: Same check - watch for any major changes
- [ ] Wed: Same check - note trends
- [ ] Thu: Same check - prepare analysis
- [ ] Fri: Full analysis - update monitoring sheet

**Friday Full Monitoring (20 minutes):**
- [ ] Go to GSC Performance → Add Country filter again
- [ ] Capture metrics for all 5 countries
- [ ] Compare to baseline (July 4):
  - CTR: Is it higher, lower, or same?
  - Clicks: Increasing?
  - Position: Improving (lower numbers are better)?
- [ ] Update tracking spreadsheet
- [ ] Run analyzer script:
  ```bash
  python3 itvedas-brain/gsc-monitoring-analyzer.py
  ```
- [ ] Review report output
- [ ] Document findings in "Week 2 Analysis" note

---

## 🔍 What to Look For (Hreflang Impact Signals)

**Good Signs (Hreflang is working):**
- ✓ Impressions increasing (even if CTR flat)
- ✓ Average position improving (decreasing numbers)
- ✓ Country-level breakdown appearing in GSC
- ✓ No crawl errors in Coverage tab

**Concerning Signs (Needs investigation):**
- ✗ CTR dropping significantly
- ✗ Impressions flat or decreasing
- ✗ New crawl errors appearing
- ✗ Position getting worse (increasing numbers)

**Normal (Expected to stay flat this week):**
- ○ CTR unchanged (indexes take 3-5 days to reprocess)
- ○ Few new clicks (hreflang just deployed)
- ○ Position unchanged initially (will improve by Week 3)

---

## 📊 Monitoring Dashboard Setup

### Quick View: Create a OneNote/Google Keep note with this template:

```
GSC GEO-TARGETING WEEK 2 MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WEEK 1 BASELINE (July 4, 2026):
├─ India: 2.14% CTR, 10 clicks, 466 impressions, Pos 54.8
├─ USA: ~1.8% CTR, ~6 clicks, ~333 impressions
├─ UK: ~1.5% CTR, ~3 clicks, ~200 impressions
├─ Australia: ~0.9% CTR, ~1 click, ~111 impressions
└─ Canada: ~1.2% CTR, ~2 clicks, ~167 impressions

WEEK 2 UPDATE (July 11, 2026):
├─ India: _% CTR, _ clicks, _ impressions, Pos _
├─ USA: _% CTR, _ clicks, _ impressions
├─ UK: _% CTR, _ clicks, _ impressions
├─ Australia: _% CTR, _ clicks, _ impressions
└─ Canada: _% CTR, _ clicks, _ impressions

CHANGES:
├─ India CTR: _____ (↑/↓/→)
├─ Impressions trend: ______
├─ Position trend: ______
└─ New issues: ______

NEXT ACTION:
└─ [ ] Review top 3 articles by country (Week 3 optimization)
```

---

## 🛠️ GSC Configuration Verification Checklist

**Complete this checklist by Friday:**

- [ ] **Audience Settings**
  - [ ] Target audience set to: INDIA
  - [ ] Status shows "Targeting: India (IN)"
  - [ ] Saved successfully

- [ ] **Performance Filtering**
  - [ ] Can filter by Country
  - [ ] All 5 countries visible (IN, US, GB, AU, CA)
  - [ ] Metrics loading correctly

- [ ] **Coverage Status**
  - [ ] Total pages: 125+ (should match your sitemap)
  - [ ] Excluded: 0 (or minimal)
  - [ ] Errors: 0 (or explain if any exist)
  - [ ] Valid with warnings: minimal

- [ ] **Indexing Coverage**
  - [ ] Hreflang items: 188 reported
  - [ ] All 188 files from Phase 1 showing
  - [ ] No "Hreflang issues" warnings

- [ ] **Crawl Statistics**
  - [ ] Recent crawl date: within 2 days of now
  - [ ] Crawl latency: normal (<1 week)
  - [ ] No excessive crawl budget waste

---

## 📈 Success Metrics

### By End of Week 2:
- ✓ GSC configured for multi-country targeting
- ✓ Baseline metrics established for all 5 countries
- ✓ Monitoring system set up (spreadsheet or script)
- ✓ No new crawl errors introduced
- ✓ Hreflang tags confirmed indexed

### Expected by End of Week 3:
- ✓ Impressions increasing (+10-20%)
- ✓ CTR showing early improvement (+0.5-1%)
- ✓ Average position starting to improve
- ✓ India showing strongest growth trend

### Expected by End of Week 4:
- ✓ CTR improved by 2-3x (from 2.14% → 5-8%)
- ✓ Clicks doubled or tripled
- ✓ Clear winner country identified (likely India)
- ✓ Ready to start Phase 3 (subdirectory localization)

---

## 📝 Documentation to Complete

**Files to create/update:**
- [x] GSC_GEO_TARGETING_SETUP.md (setup guide)
- [x] WEEK_2_ACTION_PLAN.md (this document)
- [x] gsc-monitoring-template.csv (tracking spreadsheet)
- [x] gsc-monitoring-analyzer.py (automation script)
- [ ] **NEW: Week 2 Analysis.md** (fill in after Friday monitoring)

---

## 🚀 Escalation Path (If Issues Arise)

**If CTR drops instead of staying flat:**
1. Check for indexing errors in GSC Coverage tab
2. Verify hreflang tags still present (no accidental removal)
3. Review recent page changes (any content updates that broke SEO?)
4. Wait 3 more days for Google to reprocess

**If impressions not increasing by Friday:**
1. This is normal - hreflang indexing takes 3-7 days
2. Don't panic - expected to see impact by Week 3
3. Confirm all 188 files in GSC Hreflang report
4. Request recrawl for top 10 articles (Inspect URL → Request indexing)

**If specific country shows major issues:**
1. Check if that country has any content errors
2. Review mobile usability for that region (slow loading?)
3. Look for technical issues (robots.txt, sitemap exclusions)
4. Consider creating country-specific content

---

## 💡 Key Reminders

1. **India is priority:** All optimizations should benefit India first, others second
2. **Patience needed:** SEO changes take 1-4 weeks to show full impact
3. **Compound growth:** Hreflang + good CTR → exponential traffic over 4 weeks
4. **Track everything:** Weekly monitoring data is valuable for future decisions
5. **One week at a time:** Don't overwhelm. This week = setup. Next week = analysis

---

## 📞 Quick Reference

- **GSC URL:** https://search.google.com/search-console
- **Your property:** https://itvedas.com
- **Target region:** INDIA (IN) - Primary focus
- **Hreflang files deployed:** 188 articles + chapters
- **Monitoring tool:** `python3 itvedas-brain/gsc-monitoring-analyzer.py`
- **Next milestone:** Friday July 11 (full analysis)

---

**Status:** ⏳ IN PROGRESS (Week 2 of 4)  
**Last Updated:** 2026-07-04  
**Next Review:** 2026-07-11 (End of Week 2 full analysis)
