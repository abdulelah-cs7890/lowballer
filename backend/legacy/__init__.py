"""Archived Haraj-era code (scraper + ML valuation pipeline).

This package is the original car-mispricing system the project started as, kept for the
pivot story (see ../legacy/README.md and the root README). It is NOT imported by the live
eBay app (`app/`) and is excluded from CI. It targets the original car schema, so it sets
only the columns that survive on the current `Listing` model.
"""
