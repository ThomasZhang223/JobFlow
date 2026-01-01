#!/usr/bin/env python3
"""
Test preference filtering logic comprehensively
"""

def test_preference_matching(job_data, preferences, preferred_titles, preferred_locations, preferred_job_types, preferred_descriptions, preferred_salaries):
    """Test preference matching logic exactly like the spider"""

    job_title = job_data.get('title', '').lower()
    job_location = job_data.get('location', '').lower()
    job_type = (job_data.get('job_type') or '').lower()
    job_description = (job_data.get('description') or '').lower()
    job_salary = (job_data.get('salary') or '').lower()

    print(f"Job Data:")
    print(f"  title: '{job_title}'")
    print(f"  location: '{job_location}'")
    print(f"  job_type: '{job_type}'")
    print(f"  description: '{job_description}'")
    print(f"  salary: '{job_salary}'")
    print()

    print(f"Preferences:")
    print(f"  preferred_titles: {preferred_titles}")
    print(f"  preferred_locations: {preferred_locations}")
    print(f"  preferred_job_types: {preferred_job_types}")
    print(f"  preferred_descriptions: {preferred_descriptions}")
    print(f"  preferred_salaries: {preferred_salaries}")
    print()

    # Check if job matches ANY of the title preferences
    if preferred_titles:
        title_match = any(pref_title in job_title for pref_title in preferred_titles)
        print(f"Title check: {title_match} (required: {preferred_titles})")
        if not title_match:
            return False
    else:
        print("Title check: SKIPPED (no preferences set)")

    # Check if job matches ANY of the location preferences
    if preferred_locations:
        location_match = any(pref_loc in job_location for pref_loc in preferred_locations)
        print(f"Location check: {location_match} (required: {preferred_locations})")
        if not location_match:
            return False
    else:
        print("Location check: SKIPPED (no preferences set)")

    # Check if job matches ANY of the job type preferences
    if preferred_job_types:
        job_type_match = any(pref_type in job_type for pref_type in preferred_job_types)
        print(f"Job type check: {job_type_match} (required: {preferred_job_types})")
        if not job_type_match:
            return False
    else:
        print("Job type check: SKIPPED (no preferences set)")

    # Check if job matches ANY of the description keywords
    if preferred_descriptions:
        desc_match = any(keyword in job_description or keyword in job_title for keyword in preferred_descriptions)
        print(f"Description check: {desc_match} (required: {preferred_descriptions})")
        if not desc_match:
            return False
    else:
        print("Description check: SKIPPED (no preferences set)")

    # Check if job matches ANY of the salary preferences
    if preferred_salaries:
        salary_match = any(pref_salary in job_salary for pref_salary in preferred_salaries)
        print(f"Salary check: {salary_match} (required: {preferred_salaries})")
        if not salary_match:
            return False
    else:
        print("Salary check: SKIPPED (no preferences set)")

    return True

def run_tests():
    """Run comprehensive preference filtering tests"""

    sample_job = {
        'title': 'Senior Python Developer',
        'location': 'New York, NY',
        'job_type': 'Full-time',
        'description': 'Looking for an experienced Python developer with Django experience',
        'salary': None  # Common case - no salary data
    }

    test_cases = [
        {
            'name': 'Test 1: Only title and location preferences (typical case)',
            'preferences': {'title': 'python, developer', 'location': 'new york'},
            'expected': True
        },
        {
            'name': 'Test 2: Multiple location options - should match NY',
            'preferences': {'title': 'python', 'location': 'san francisco, new york, london'},
            'expected': True
        },
        {
            'name': 'Test 3: No salary preference - should pass despite missing salary data',
            'preferences': {'title': 'python', 'location': 'new york', 'description': 'django'},
            'expected': True
        },
        {
            'name': 'Test 4: With salary preference - should fail due to missing salary data',
            'preferences': {'title': 'python', 'location': 'new york', 'salary': '$100k, $120k'},
            'expected': False
        },
        {
            'name': 'Test 5: Only required fields (title, location) - all others skipped',
            'preferences': {'title': 'developer', 'location': 'york'},
            'expected': True
        },
        {
            'name': 'Test 6: Multiple title options - python should match',
            'preferences': {'title': 'javascript, python, java', 'location': 'new york'},
            'expected': True
        },
        {
            'name': 'Test 7: No matches - wrong location',
            'preferences': {'title': 'python', 'location': 'los angeles'},
            'expected': False
        }
    ]

    print("=== PREFERENCE FILTERING TESTS ===\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"{test_case['name']}:")
        preferences = test_case['preferences']

        # Parse preferences like the spider does
        preferred_titles = [t.strip().lower() for t in preferences['title'].split(',')] if preferences.get('title') else None
        preferred_locations = [l.strip().lower() for l in preferences['location'].split(',')] if preferences.get('location') else None
        preferred_job_types = [j.strip().lower() for j in preferences['job_type'].split(',')] if preferences.get('job_type') else None
        preferred_descriptions = [d.strip().lower() for d in preferences['description'].split(',')] if preferences.get('description') else None
        preferred_salaries = [s.strip().lower() for s in preferences['salary'].split(',')] if preferences.get('salary') else None

        result = test_preference_matching(
            sample_job, preferences, preferred_titles, preferred_locations,
            preferred_job_types, preferred_descriptions, preferred_salaries
        )

        expected = test_case['expected']
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"Expected: {expected}, Got: {result} - {status}")
        print("-" * 80)
        print()

if __name__ == '__main__':
    run_tests()