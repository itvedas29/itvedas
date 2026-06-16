- name: Run News Agent
        if: |
          github.event_name == 'workflow_dispatch' && (inputs.run_type == 'both' || inputs.run_type == 'news_only') ||
          github.event_name == 'schedule' && (github.event.schedule != '30 3 * * 1,3,5')
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python3 scripts/news_agent_v2.py
