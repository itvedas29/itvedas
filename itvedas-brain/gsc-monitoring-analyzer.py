#!/usr/bin/env python3
"""GSC Monitoring & Analysis Tool - Track international SEO performance by country"""
import csv
import json
from datetime import datetime
from pathlib import Path

class GSCMonitor:
    """Monitor and analyze GSC performance data by country"""

    def __init__(self, data_file='gsc-monitoring-template.csv'):
        self.data_file = Path(data_file)
        self.countries = ['IN', 'US', 'GB', 'AU', 'CA']
        self.data = []
        self.load_data()

    def load_data(self):
        """Load CSV monitoring data"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                reader = csv.DictReader(f)
                self.data = list(reader)

    def add_weekly_data(self, week, in_ctr, us_ctr, gb_ctr, au_ctr, ca_ctr,
                       in_clicks, us_clicks, gb_clicks, au_clicks, ca_clicks,
                       in_imp, us_imp, gb_imp, au_imp, ca_imp,
                       in_pos, us_pos, gb_pos, au_pos, ca_pos):
        """Add weekly performance data"""
        date = datetime.now().strftime('%Y-%m-%d')
        countries_data = [
            ('IN', in_ctr, in_clicks, in_imp, in_pos),
            ('US', us_ctr, us_clicks, us_imp, us_pos),
            ('GB', gb_ctr, gb_clicks, gb_imp, gb_pos),
            ('AU', au_ctr, au_clicks, au_imp, au_pos),
            ('CA', ca_ctr, ca_clicks, ca_imp, ca_pos),
        ]

        for country, ctr, clicks, imp, pos in countries_data:
            trend = self._calculate_trend(country, float(ctr))
            row = {
                'Date': date,
                'Week': week,
                'Country': country,
                'CTR (%)': ctr,
                'Clicks': clicks,
                'Impressions': imp,
                'Avg Position': pos,
                'Trend': trend,
                'Notes': f'{country} - Week {week} update'
            }
            self.data.append(row)

        self._save_data()
        return True

    def _calculate_trend(self, country, ctr):
        """Calculate trend based on previous CTR"""
        country_data = [d for d in self.data if d['Country'] == country]
        if not country_data:
            return 'BASELINE'

        last_ctr = float(country_data[-1]['CTR (%)'])
        if ctr > last_ctr:
            return 'UP'
        elif ctr < last_ctr:
            return 'DOWN'
        else:
            return 'FLAT'

    def _save_data(self):
        """Save data to CSV"""
        if not self.data:
            return

        fieldnames = ['Date', 'Week', 'Country', 'CTR (%)', 'Clicks',
                     'Impressions', 'Avg Position', 'Trend', 'Notes']

        with open(self.data_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)

    def get_country_summary(self, country):
        """Get summary for a specific country"""
        country_data = [d for d in self.data if d['Country'] == country]
        if not country_data:
            return None

        latest = country_data[-1]
        first = country_data[0]

        ctr_change = float(latest['CTR (%)']) - float(first['CTR (%)'])
        clicks_change = int(latest['Clicks']) - int(first['Clicks'])
        pos_change = float(latest['Avg Position']) - float(first['Avg Position'])

        return {
            'country': country,
            'current_ctr': float(latest['CTR (%)']),
            'current_clicks': int(latest['Clicks']),
            'current_impressions': int(latest['Impressions']),
            'current_position': float(latest['Avg Position']),
            'ctr_change': ctr_change,
            'ctr_change_pct': (ctr_change / float(first['CTR (%)']) * 100) if float(first['CTR (%)']) > 0 else 0,
            'clicks_change': clicks_change,
            'position_improvement': -pos_change,  # Negative is good (lower position = better)
            'trend': latest['Trend'],
            'weeks': len(country_data)
        }

    def generate_report(self):
        """Generate comprehensive monitoring report"""
        print("\n" + "="*70)
        print("GSC GEO-TARGETING MONITORING REPORT")
        print("="*70)

        for country in self.countries:
            summary = self.get_country_summary(country)
            if not summary:
                continue

            print(f"\n📊 {country} PERFORMANCE")
            print("-" * 70)
            print(f"  Current CTR:        {summary['current_ctr']:.1f}%")
            print(f"  Current Clicks:     {summary['current_clicks']}")
            print(f"  Impressions:        {summary['current_impressions']}")
            print(f"  Avg Position:       {summary['current_position']:.1f}")
            print(f"  Trend:              {summary['trend']}")
            print(f"\n  📈 CHANGES (Over {summary['weeks']} weeks)")
            print(f"  CTR Change:         {summary['ctr_change']:+.1f}% ({summary['ctr_change_pct']:+.0f}%)")
            print(f"  Clicks Change:      {summary['clicks_change']:+d}")
            print(f"  Position Improved:  {summary['position_improvement']:+.1f} (lower is better)")

            if summary['ctr_change'] > 0:
                print(f"  ✓ POSITIVE TREND - Growth on track")
            elif summary['ctr_change'] < -0.5:
                print(f"  ⚠ WARNING - CTR declining, review content")
            else:
                print(f"  ○ FLAT - Monitor for next week")

        print("\n" + "="*70)
        print("ACTION ITEMS")
        print("="*70)

        summaries = [self.get_country_summary(c) for c in self.countries]
        summaries = [s for s in summaries if s]
        summaries.sort(key=lambda x: x['current_ctr'], reverse=True)

        print(f"\n✓ TOP PERFORMER: {summaries[0]['country']} ({summaries[0]['current_ctr']:.1f}% CTR)")
        print(f"  → Consider prioritizing {summaries[0]['country']}-specific content")

        print(f"\n⚠ NEEDS ATTENTION: {summaries[-1]['country']} ({summaries[-1]['current_ctr']:.1f}% CTR)")
        print(f"  → Review top articles, check for technical issues, consider localization")

        print("\n📋 NEXT STEPS:")
        print("  1. Review this week's top performing articles by country")
        print("  2. Identify content gaps per country (what queries are missing?)")
        print("  3. Plan targeted optimizations for underperforming regions")
        print("  4. Schedule follow-up check in 7 days")
        print("\n")

def print_quick_guide():
    """Print quick reference guide"""
    print("\n" + "="*70)
    print("GSC GEO-TARGETING QUICK GUIDE")
    print("="*70)
    print("""
SETUP (Do This Once):
1. Open Google Search Console
2. Go to Settings → Audience → Target audience
3. Set primary target: INDIA (highest current traffic)
4. Go to Performance → Add filter → Country
5. View metrics by: IN, US, GB, AU, CA

WEEKLY MONITORING (Every Monday):
1. Take screenshot of Performance report (all countries)
2. Copy CTR, Clicks, Position for each country
3. Run this script to add data and generate report
4. Review action items

EXPECTED RESULTS (Week-by-week):
  Week 1: Baseline metrics (hreflang just deployed)
  Week 2: Impressions start increasing (+5-10%)
  Week 3: CTR trending up (+10-20%)
  Week 4: Significant improvement visible (+30-50%)

COUNTRIES RANKED BY POTENTIAL:
  1. INDIA (IN)     → Strongest base, 70% current CTR → Target first
  2. USA (US)       → Largest market, 330M people → Target second
  3. UK (GB)        → 70M people, high-intent → Target third
  4. CANADA (CA)    → 40M people → Secondary market
  5. AUSTRALIA (AU) → 25M people → Secondary market

TROUBLESHOOTING:
  • CTR not improving? → Check title tags and meta descriptions
  • Impressions not increasing? → Wait 3-5 days for full hreflang crawl
  • One country dropping? → Review new competitors, check mobile UX
  • Position not improving? → Add more content depth, internal links
""")
    print("="*70 + "\n")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'guide':
        print_quick_guide()
    else:
        monitor = GSCMonitor()
        monitor.generate_report()
        print("\n💡 TIP: Run 'python3 gsc-monitoring-analyzer.py guide' for quick reference")
