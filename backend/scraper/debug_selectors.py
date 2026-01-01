#!/usr/bin/env python3
"""
Debug script to test CSS selectors against Indeed HTML
"""

import sys
import os
import json
from pathlib import Path

# Add the scraper directory to Python path
script_dir = Path(__file__).parent
scraper_dir = script_dir / 'indeed_scraper'
sys.path.insert(0, str(scraper_dir))

from scrapy.http import HtmlResponse
import scrapy

def test_preference_matching(job_data, preferences):
    """Test preference matching logic like the spider does"""

    job_title = job_data.get('title', '').lower()
    job_location = job_data.get('location', '').lower()
    job_type = (job_data.get('job_type') or '').lower()
    job_description = (job_data.get('description') or '').lower()
    job_salary = (job_data.get('salary') or '').lower()

    print(f"     Job data normalized:")
    print(f"       title: {repr(job_title)}")
    print(f"       location: {repr(job_location)}")
    print(f"       job_type: {repr(job_type)}")
    print(f"       description: {repr(job_description)}")
    print(f"       salary: {repr(job_salary)}")

    # Check title preferences
    if preferences.get('title'):
        preferred_titles = [t.strip().lower() for t in preferences['title'].split(',')]
        title_match = any(pref_title in job_title for pref_title in preferred_titles)
        print(f"     Title check: {preferred_titles} -> {title_match}")
        if not title_match:
            return False

    # Check location preferences
    if preferences.get('location'):
        preferred_locations = [l.strip().lower() for l in preferences['location'].split(',')]
        location_match = any(pref_loc in job_location for pref_loc in preferred_locations)
        print(f"     Location check: {preferred_locations} -> {location_match}")
        if not location_match:
            return False

    # Check job type preferences
    if preferences.get('job_type'):
        preferred_job_types = [j.strip().lower() for j in preferences['job_type'].split(',')]
        job_type_match = any(pref_type in job_type for pref_type in preferred_job_types)
        print(f"     Job type check: {preferred_job_types} -> {job_type_match}")
        if not job_type_match:
            return False

    # Check description keywords
    if preferences.get('description'):
        preferred_descriptions = [d.strip().lower() for d in preferences['description'].split(',')]
        desc_match = any(keyword in job_description or keyword in job_title for keyword in preferred_descriptions)
        print(f"     Description check: {preferred_descriptions} -> {desc_match}")
        if not desc_match:
            return False

    # Check salary preferences
    if preferences.get('salary'):
        preferred_salaries = [s.strip().lower() for s in preferences['salary'].split(',')]
        salary_match = any(pref_salary in job_salary for pref_salary in preferred_salaries)
        print(f"     Salary check: {preferred_salaries} -> {salary_match}")
        if not salary_match:
            return False

    return True

def test_selectors():
    """Test CSS selectors against sample Indeed HTML"""

    # Sample HTML based on what user shared
    sample_html = '''
    <html>
    <body>
    <div class="cardOutline tapItem dd-privacy-allow result_ee96ed2f56441769 maybeSponsored job resultWithShelf sponTapItem desktop css-oc">
        <div class="slider_container css-we0834 eu4oa1w0" data-testid="slider_container">
            <div class="slider_list css-1bej024 eu4oa1w0">
                <div data-testid="slider_item" class="slider_item css-17bghu4 eu4oa1w0">
                    <div data-testid="fade-in-wrapper" class="css-u74ql7 eu4oa1w0">
                        <div class="job_seen_beacon">
                            <table class="mainContentTable css-131ju4w eu4oa1w0" cellpadding="0" cellspacing="0" role="presentation">
                                <tbody>
                                <tr>
                                    <td class="resultContent css-1o6lhvs eu4oa1w0">
                                        <div class="css-pt3vth e37uo190">
                                            <h2 class="jobTitle css-1o1rn9 eu4oa1w0" tabindex="-1">
                                                <a id="sj_ee96ed2f56441769" data-mobtk="1jdrf2c55j0d7805" data-jk="ee96ed2f56441769" data-ci="451321085" href="/viewjob?jk=ee96ed2f56441769">
                                                    <span title="Google Apps Script Developer & Automation Specialist" class="css-1baag51 eu4oa1w0">Google Apps Script Developer & Automation Specialist</span>
                                                </a>
                                            </h2>
                                            <span class="companyName css-1o6lhvs eu4oa1w0">
                                                <a data-testid="company-name" href="/cmp/Smartshape">Smartshape</a>
                                            </span>
                                            <div data-testid="text-location" class="css-1o6lhvs eu4oa1w0">New York, NY</div>
                                            <div class="job-snippet">
                                                <span>Experience with Google Apps Script, JavaScript, and automation tools</span>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    '''

    # Create a mock response
    response = HtmlResponse(url="https://indeed.com/test", body=sample_html, encoding='utf-8')

    print("=== DEBUGGING CSS SELECTORS ===\n")

    # Test job card selectors
    print("1. Job Card Detection:")
    job_cards_beacon = response.css('div.job_seen_beacon')
    job_cards_result = response.css('td.resultContent')
    job_cards_outline = response.css('div.cardOutline')

    print(f"   div.job_seen_beacon: {len(job_cards_beacon)} found")
    print(f"   td.resultContent: {len(job_cards_result)} found")
    print(f"   div.cardOutline: {len(job_cards_outline)} found")

    # Use the first working selector
    if job_cards_beacon:
        cards = job_cards_beacon
        print("   → Using div.job_seen_beacon")
    elif job_cards_result:
        cards = job_cards_result
        print("   → Using td.resultContent")
    else:
        cards = job_cards_outline
        print("   → Using div.cardOutline")

    if not cards:
        print("   ❌ NO JOB CARDS FOUND!")
        return

    print(f"\n2. Processing {len(cards)} job card(s):\n")

    for i, card in enumerate(cards):
        print(f"Card {i+1}:")

        # Test job_id selectors
        job_id_selectors = [
            '::attr(data-jk)',
            'a::attr(data-jk)',
            'h2 a::attr(data-jk)'
        ]

        job_id = None
        for selector in job_id_selectors:
            result = card.css(selector).get()
            print(f"   Job ID '{selector}': {repr(result)}")
            if result and not job_id:
                job_id = result

        # Test title selectors
        title_selectors = [
            'h2.jobTitle span[title]::attr(title)',
            'h2.jobTitle span::text',
            'a[data-jk] span[title]::attr(title)',
            'h2.jobTitle a span::text',  # New selector
            'h2 a span[title]::attr(title)'  # More flexible
        ]

        title = None
        for selector in title_selectors:
            result = card.css(selector).get()
            print(f"   Title '{selector}': {repr(result)}")
            if result and not title:
                title = result

        # Test company selectors (updated order to match spider)
        company_selectors = [
            'a[data-testid="company-name"]::text',
            'span.companyName a::text',
            'span[data-testid="company-name"]::text',
            'span.companyName::text'
        ]

        company = None
        for selector in company_selectors:
            result = card.css(selector).get()
            print(f"   Company '{selector}': {repr(result)}")
            if result and not company:
                company = result

        # Test location selectors
        location_selectors = [
            'div[data-testid="text-location"]::text',
            'div.companyLocation::text'
        ]

        location = None
        for selector in location_selectors:
            result = card.css(selector).get()
            print(f"   Location '{selector}': {repr(result)}")
            if result and not location:
                location = result

        print(f"\n   EXTRACTED DATA:")
        print(f"   Job ID: {repr(job_id)}")
        print(f"   Title: {repr(title)}")
        print(f"   Company: {repr(company)}")
        print(f"   Location: {repr(location)}")

        # Test validation logic
        print(f"\n   VALIDATION:")
        if not job_id or not title or not company:
            print(f"   ❌ WOULD BE SKIPPED: job_id={bool(job_id)}, title={bool(title)}, company={bool(company)}")
        else:
            print(f"   ✅ WOULD BE INCLUDED")

        # Test preference filtering
        print(f"\n   PREFERENCE FILTERING TEST:")
        test_preferences_with_salary = {
            'title': 'developer, python',
            'location': 'new york, remote',
            'job_type': 'full-time',
            'description': 'javascript, automation',
            'salary': '$80k'
        }

        test_preferences_no_salary = {
            'title': 'developer, python',
            'location': 'new york, remote',
            'job_type': 'full-time',
            'description': 'javascript, automation'
        }

        job_data = {
            'title': title or '',
            'location': location or '',
            'job_type': 'Full-time',  # Default
            'description': 'Experience with Google Apps Script, JavaScript, and automation tools',
            'salary': None
        }

        print(f"   Test 1 - WITH salary requirement:")
        print(f"   Preferences: {test_preferences_with_salary}")
        matches1 = test_preference_matching(job_data, test_preferences_with_salary)
        print(f"   Result: {matches1}")

        print(f"\n   Test 2 - WITHOUT salary requirement:")
        print(f"   Preferences: {test_preferences_no_salary}")
        matches2 = test_preference_matching(job_data, test_preferences_no_salary)
        print(f"   Result: {matches2}")
        print()

if __name__ == '__main__':
    test_selectors()