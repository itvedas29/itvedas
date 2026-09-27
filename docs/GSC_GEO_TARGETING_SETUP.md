# Google Search Console Geo-Targeting Setup Guide

**Objective:** Configure GSC to optimize your content for multiple English-speaking countries (US, UK, Australia, Canada, India)

**Status:** Week 2 of Global Expansion Strategy  
**Date:** 2026-07-04  
**Expected Impact:** Improved impressions & CTR per country, better ranking visibility in target regions

---

## Part 1: Access GSC Settings

### Step 1: Open Google Search Console
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property: `https://itvedas.com`
3. Navigate to **Settings** (left sidebar, bottom)

### Step 2: Find Audience Settings
1. In Settings, click **Audience** (or "Target Audience" depending on GSC version)
2. You should see: "Search Console treats your site as serving users worldwide by default"

---

## Part 2: Configure Primary Target Country

### Option A: Single Primary Country (Recommended for Phase 1)
**If you want to prioritize ONE country first:**

1. In Audience settings, select **Target audience**
2. Choose: **India** (highest organic traffic potential based on your data)
3. Click **Save**
4. **Rationale:** Your GSC data showed India performing strongest (70%+ CTR). Prioritizing India signals Google to rank you higher in Indian search results first, then secondary in other regions via hreflang.

### Option B: Multi-Country Primary (Advanced)
**If you want equal priority across all regions:**

1. Leave target audience as **Worldwide**
2. Use **hreflang tags** (already implemented) to signal regional content preference
3. Monitor performance in GSC to identify which countries respond best
4. Consider shifting to Option A after 2-3 weeks of data

**Recommendation:** Start with Option A (India), observe for 7 days, then evaluate secondary markets.

---

## Part 3: Monitor Performance by Country

### Weekly Monitoring Checklist

**Every Monday, check:**

1. **GSC Performance Report → International Traffic**
   - Menu: Performance → Click "Filter" → Add filter "Country"
   - View metrics by: US, GB (UK), AU (Australia), CA (Canada), IN (India)
   - Watch for:
     - CTR trending up/down per country
     - Impressions growing
     - Average position improving

2. **Key Metrics to Track**
   - **CTR by Country:** Target 8-12% per country (up from current 2.14%)
   - **Clicks by Country:** Monitor absolute volume
   - **Impressions by Country:** Should increase as hreflang is indexed
   - **Avg Position by Country:** Track improvement toward top 10-20

3. **Create a Monitoring Spreadsheet**
   ```
   Country | Week 1 CTR | Week 2 CTR | Week 3 CTR | Trend | Clicks | Position
   --------|-----------|-----------|-----------|-------|--------|----------
   IN      | 2.5%      | 3.2%      | 4.1%      | ↑     | 12     | 52.1
   US      | 1.8%      | 2.4%      | 3.0%      | ↑     | 8      | 61.2
   GB      | 1.5%      | 2.0%      | 2.6%      | ↑     | 5      | 65.4
   AU      | 0.9%      | 1.3%      | 1.8%      | ↑     | 2      | 72.5
   CA      | 1.2%      | 1.7%      | 2.2%      | ↑     | 3      | 68.3
   ```

---

## Part 4: Regional Performance Analysis

### Expected Timeline

| Week | Milestone | Action |
|------|-----------|--------|
| Week 2 (Now) | Hreflang indexed | Configure GSC, start monitoring |
| Week 3 | First data appears | Country-level impressions increase |
| Week 4 | CTR improves | See trending up across all countries |
| Week 5 | Dominant market emerges | Decide secondary priority markets |

### Country-Specific Opportunities

#### 1. **India (IN)** — Highest Priority
- **Current Status:** 70% CTR in your data (strongest)
- **Action:** Set as primary target audience in GSC
- **Content Optimization:** Add India-specific examples (Vodafone, Jio, Indian government regulations, RBI)
- **Expected Growth:** 3-5x organic traffic within 4 weeks
- **Top Keywords:** "VPN India legal", "how to use VPN in India", "cloud computing explained Hindi context"

#### 2. **United States (US)** — Second Priority
- **Current Status:** 2-3% CTR
- **Market Size:** 330M people, massive search volume
- **Action:** After hreflang stabilizes (1 week), consider US-specific content
- **Content Opportunities:** "VPN for streaming in USA", "cloud certifications for US tech jobs"
- **Expected Growth:** 2-3x organic traffic

#### 3. **United Kingdom (GB)** — Third Priority
- **Current Status:** Minimal traffic
- **Market Size:** 70M people, high-intent tech audience
- **Action:** Monitor for 2 weeks, then consider `/uk/` subdirectory
- **Content Differences:** British spellings, GDPR emphasis, UK privacy laws
- **Expected Growth:** 1.5-2x organic traffic

#### 4. **Australia (AU)** & **Canada (CA)** — Tertiary
- **Market Size:** 25M + 40M respectively (smaller but growing)
- **Action:** Monitor but don't optimize until primary markets stabilized
- **Expected Growth:** 0.5-1.5x each

---

## Part 5: Advanced GSC Configuration (Optional)

### Set Up Country-Specific Sitemaps (For Later)
**Do this in Week 3-4 if you want fine-grained control:**

1. Create separate sitemaps:
   - `sitemap-us.xml` (US-targeted articles)
   - `sitemap-gb.xml` (UK-targeted articles)
   - `sitemap-in.xml` (India-targeted articles)

2. In GSC, under Sitemaps, submit:
   - Primary sitemap.xml (global)
   - sitemap-us.xml with target US
   - sitemap-gb.xml with target GB
   - sitemap-in.xml with target IN

3. GSC will prioritize crawling country-specific content

**Note:** Not required now. The hreflang tags you added are sufficient for Phase 2.

---

## Part 6: Integration with SEO Monitoring

### Combined Monitoring Dashboard

Track these 4 metrics together:

1. **GSC by Country** (weekly)
   - CTR, Clicks, Position per country
   
2. **Hreflang Coverage** (weekly)
   - Verify all 188 files still have hreflang tags
   - Check for any crawl errors in GSC
   
3. **Organic Traffic** (daily via Google Analytics)
   - Sessions by country/region
   - Bounce rate by country
   - Average session duration by country
   
4. **Content Performance** (weekly)
   - Which articles getting most clicks per country
   - Which topics converting best in each region

### Dashboard Template (Copy to your spreadsheet)

```
=== WEEK 2 MONITORING (2026-07-07) ===

GSC PERFORMANCE:
├─ India (IN): 2.5% CTR, 15 clicks, 600 impressions, Pos 52.1
├─ USA (US): 1.8% CTR, 10 clicks, 556 impressions, Pos 61.2  
├─ UK (GB): 1.5% CTR, 5 clicks, 333 impressions, Pos 65.4
├─ Australia (AU): 0.9% CTR, 2 clicks, 222 impressions, Pos 72.5
└─ Canada (CA): 1.2% CTR, 3 clicks, 250 impressions, Pos 68.3

HREFLANG STATUS:
├─ 188 files with hreflang tags ✓
├─ Avg crawl latency: 2-3 days
├─ Coverage: 100% of /articles/ + /chapters/
└─ Next update: 2026-07-11

ANALYTICS (Google Analytics 4):
├─ Organic sessions (India): 45
├─ Organic sessions (USA): 28
├─ Organic sessions (UK): 12
├─ Organic sessions (Total): 95
└─ Avg session duration: 2:34

TOP PERFORMING ARTICLES (Last 7 days):
├─ VPN article: 25 clicks (expected, recent optimization)
├─ DNS article: 8 clicks
├─ Cloud guide: 6 clicks
├─ CVE database: 4 clicks
└─ Security article: 3 clicks

ACTION ITEMS THIS WEEK:
├─ [ ] Submit hreflang sitemap to GSC (verify 188 files indexed)
├─ [ ] Review top 3 articles for India-specific content gaps
├─ [ ] Schedule daily GSC monitoring (5 min check)
├─ [ ] Compare US CTR vs India CTR (identify optimization opportunities)
└─ [ ] Plan Week 3: Potential US-specific content creation
```

---

## Part 7: Troubleshooting

### Q: Hreflang tags aren't working. How do I verify?
**A:** In GSC:
1. Go to **Enhancements** → **International targeting** (if available)
2. Should show 188 pages with hreflang configuration
3. If not showing, wait 3-5 days for re-crawl
4. Force re-index: Use "Inspect URL" for top 5 articles, request indexing

### Q: One country's CTR is dropping. What should I do?
**A:**
1. Check if any technical issues in that country's GSC report
2. Review top 5 ranking articles for that country
3. Look for new competitors ranking above you
4. Check for mobile vs desktop CTR difference (mobile might need improvement)

### Q: Should I change my primary target country after 1 week?
**A:** Only if:
- Current target (India) shows negative trend (CTR dropping, clicks falling)
- Another country shows 3x better performance
- Otherwise, wait 2-3 weeks for stabilization

---

## Part 8: Next Phase Preparation (Month 2+)

**Once you have 3-4 weeks of country data:**

1. **Identify secondary market:** Which country has highest CTR after primary?
2. **Plan localization:** Create `/uk/` or `/us/` versions for top 20 articles
3. **Hire translator/editor:** For country-specific content adaptation
4. **Schedule content:** Plan 2-3 country-specific articles per month

---

## Quick Start Checklist

**Do this TODAY (Week 2 start):**

- [ ] Open GSC → Settings → Audience
- [ ] Set target country to **India** (or Worldwide if testing)
- [ ] Click Save
- [ ] Go to Performance → Add filter for "Country"
- [ ] Take screenshot of baseline metrics (July 4, 2026)
- [ ] Set calendar reminder: "GSC Monitoring - Every Monday at 9 AM"
- [ ] Create spreadsheet (use template above)

**Do this by end of Week 2:**

- [ ] Analyze country breakdown: which country has highest CTR?
- [ ] Review top 5 articles by country
- [ ] Identify content gaps per country (what keywords missing?)
- [ ] Plan Week 3 content optimization

**Expected by Week 3:**

- [ ] Hreflang tags fully crawled and indexed
- [ ] Country-level impressions visible in GSC
- [ ] CTR trending upward across all countries
- [ ] 2-3 actionable insights per country

---

## Support & Resources

- [GSC Audience Targeting Help](https://support.google.com/webmasters/answer/189077)
- [Hreflang Implementation Guide](https://support.google.com/webmasters/answer/189077)
- [International SEO Best Practices](https://developers.google.com/search/docs/beginner/international-sites)

---

**Last Updated:** 2026-07-04  
**Next Review:** 2026-07-11 (Week 3 check-in)
