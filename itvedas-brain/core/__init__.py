"""Shared core library for the ITVedas brain (content + ops pipelines).

This package is intentionally dependency-free (standard library only) so
every brain script - whether run on GitHub Actions, the VPS via PM2/cron,
or interactively - can import it without extra installs.
"""
