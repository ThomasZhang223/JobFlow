"""Test the scraper service"""

from scraper_service import scrape_with_preferences
import json

print("=" * 60)
print("Testing Scraper Service")
print("=" * 60)

# Test 1: Basic scrape
print("\n[Test 1] Basic scrape - 3 jobs")
print("-" * 60)
result = scrape_with_preferences({
    'query': 'python developer',
    'location': 'New York',
    'max_results': 3
})

print(f"\n✓ Success: {result['success']}")
print(f"✓ Jobs found: {result['jobs_found']}")
print(f"✓ Time: {result.get('time_elapsed', 0):.1f}s")

if not result['success']:
    print(f"❌ Error: {result['error']}")
elif result['jobs']:
    print(f"\nSample jobs:")
    for i, job in enumerate(result['jobs'][:3], 1):
        print(f"\n  Job {i}:")
        print(f"    Title: {job['title']}")
        print(f"    Company: {job['company_name']}")
        print(f"    Location: {job['location']}")
        if job.get('salary_text'):
            print(f"    Salary: {job['salary_text']}")

# Test 2: With filters
print("\n" + "=" * 60)
print("[Test 2] With experience level filter")
print("-" * 60)
result2 = scrape_with_preferences({
    'query': 'software engineer',
    'location': 'NYC',
    'experience_level': 'entry',
    'max_results': 2
})

print(f"\n✓ Success: {result2['success']}")
print(f"✓ Jobs found: {result2['jobs_found']}")

if result2['success'] and result2['jobs']:
    print(f"\nEntry-level jobs:")
    for job in result2['jobs']:
        print(f"  - {job['title']} at {job['company_name']}")

print("\n" + "=" * 60)
print("Tests complete!")
print("=" * 60)