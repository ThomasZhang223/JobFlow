"""
Singleton Scraper Service
Works with subprocess to run the Indeed spider
"""

import subprocess
import json
import os
import tempfile
from datetime import datetime
from typing import Dict
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class ScraperService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.scraper_path = os.path.join(os.path.dirname(__file__), 'indeed_scraper')
        self.scraper_parent = os.path.dirname(__file__)  # backend/scraper
        
        import shutil
        self.scrapy_path = shutil.which('scrapy')
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def scrape_with_preferences(self, preferences: Dict) -> Dict:
        """
        Run scraper with preferences dict
        
        Args:
            preferences: {
                'query': 'python developer',
                'location': 'NYC',
                'experience_level': 'entry',  # optional
                'required_keywords': 'django,react',  # optional
                'excluded_keywords': 'senior',  # optional
                'max_results': 20
            }
        
        Returns:
            {
                'success': True/False,
                'jobs_found': 10,
                'jobs': [...],
                'time_elapsed': 45.2,
                'error': 'error msg' (if failed)
            }
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate required fields
            if not preferences.get('query'):
                return {
                    'success': False,
                    'jobs_found': 0,
                    'jobs': [],
                    'error': 'Missing required field: query'
                }
            
            if not preferences.get('location'):
                return {
                    'success': False,
                    'jobs_found': 0,
                    'jobs': [],
                    'error': 'Missing required field: location'
                }
            
            # Create temp output file
            output_file = tempfile.mktemp(suffix='.json')
            
            # Build scrapy command
            cmd = [
                self.scrapy_path or 'scrapy',
                'crawl', 'indeed',
                '-a', f"query={preferences['query']}",
                '-a', f"location={preferences['location']}",
                '-a', f"max_results={preferences.get('max_results', 50)}",
                '-o', output_file
            ]
            
            # Add optional filters
            if preferences.get('experience_level'):
                cmd.extend(['-a', f"experience_level={preferences['experience_level']}"])
            
            if preferences.get('required_keywords'):
                cmd.extend(['-a', f"required_keywords={preferences['required_keywords']}"])
            
            if preferences.get('excluded_keywords'):
                cmd.extend(['-a', f"excluded_keywords={preferences['excluded_keywords']}"])
            
            # CRITICAL: Set environment variables (same as manual test)
            env = os.environ.copy()
            
            # Set PYTHONPATH to scraper parent directory
            env['PYTHONPATH'] = self.scraper_parent
            
            # Tell Scrapy where settings module is
            env['SCRAPY_SETTINGS_MODULE'] = 'indeed_scraper.settings'
            
            print(f"\n{'='*60}")
            print(f"Running Scraper")
            print(f"{'='*60}")
            print(f"Query: {preferences['query']}")
            print(f"Location: {preferences['location']}")
            print(f"Max Results: {preferences.get('max_results', 50)}")
            print(f"Working dir: {self.scraper_path}")
            print(f"{'='*60}\n")
            
            # Run scraper from indeed_scraper directory
            result = subprocess.run(
                cmd,
                cwd=self.scraper_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )
            
            # Check if scraper failed
            if result.returncode != 0:
                print(f"\n❌ SCRAPER FAILED")
                print(f"Return code: {result.returncode}")
                print(f"\nStderr (last 1000 chars):")
                print(result.stderr[-1000:] if result.stderr else "None")
                
                return {
                    'success': False,
                    'jobs_found': 0,
                    'jobs': [],
                    'error': f"Scraper failed: {result.stderr[-500:] if result.stderr else 'Unknown error'}"
                }
            
            # Read results
            jobs = []
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        content = f.read()
                        if content.strip():
                            jobs = json.loads(content)
                        else:
                            print("Warning: Output file is empty")
                    os.unlink(output_file)  # Clean up temp file
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    return {
                        'success': False,
                        'jobs_found': 0,
                        'jobs': [],
                        'error': f"Failed to parse results: {str(e)}"
                    }
                except Exception as e:
                    print(f"Error reading file: {e}")
                    return {
                        'success': False,
                        'jobs_found': 0,
                        'jobs': [],
                        'error': f"Failed to read results: {str(e)}"
                    }
            else:
                print(f"Warning: Output file not found: {output_file}")
            
            time_elapsed = (datetime.utcnow() - start_time).total_seconds()
            
            print(f"\n✅ Scraping complete!")
            print(f"Jobs found: {len(jobs)}")
            print(f"Time elapsed: {time_elapsed:.1f}s\n")
            
            return {
                'success': True,
                'jobs_found': len(jobs),
                'jobs': jobs,
                'time_elapsed': time_elapsed,
                'preferences_used': preferences
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'jobs_found': 0,
                'jobs': [],
                'error': 'Scraper timeout after 5 minutes'
            }
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'jobs_found': 0,
                'jobs': [],
                'error': str(e)
            }
    
    def scrape_for_user(self, user_id: str) -> Dict:
        """
        Run scraper using user's saved preferences from database
        
        Args:
            user_id: User ID to fetch preferences
        
        Returns:
            Same as scrape_with_preferences()
        """
        try:
            from app.database import db
            
            # Fetch user preferences from database
            preferences = db.get_user_preferences(user_id)
            
            if not preferences:
                return {
                    'success': False,
                    'jobs_found': 0,
                    'jobs': [],
                    'error': f'No preferences found for user: {user_id}'
                }
            
            # Convert database model to dict
            prefs_dict = {
                'query': preferences.query,
                'location': preferences.location,
                'experience_level': preferences.experience_level,
                'required_keywords': preferences.required_keywords,
                'excluded_keywords': preferences.excluded_keywords,
                'max_results': preferences.max_results or 50
            }
            
            # Run scraper with these preferences
            return self.scrape_with_preferences(prefs_dict)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'jobs_found': 0,
                'jobs': [],
                'error': f'Database error: {str(e)}'
            }


# Convenience functions for easy import
def scrape_with_preferences(preferences: Dict) -> Dict:
    """Run scraper with preferences dict"""
    scraper = ScraperService.get_instance()
    return scraper.scrape_with_preferences(preferences)


def scrape_for_user(user_id: str) -> Dict:
    """Run scraper with user's saved preferences"""
    scraper = ScraperService.get_instance()
    return scraper.scrape_for_user(user_id)


# For testing
if __name__ == '__main__':
    print("=" * 60)
    print("Testing Scraper Service")
    print("=" * 60)
    
    test_prefs = {
        'query': 'python developer',
        'location': 'New York',
        'max_results': 3
    }
    
    print(f"\nTest preferences: {test_prefs}\n")
    result = scrape_with_preferences(test_prefs)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"✓ Success: {result['success']}")
    print(f"✓ Jobs found: {result['jobs_found']}")
    print(f"✓ Time: {result.get('time_elapsed', 0):.1f}s")
    
    if result['success'] and result['jobs']:
        print(f"\n📋 Sample Jobs:")
        for i, job in enumerate(result['jobs'][:3], 1):
            print(f"\n  Job {i}:")
            print(f"    Title: {job['title']}")
            print(f"    Company: {job['company_name']}")
            print(f"    Location: {job['location']}")
            if job.get('salary_text'):
                print(f"    Salary: {job['salary_text']}")
    elif not result['success']:
        print(f"\n❌ Error: {result['error']}")
    
    print(f"\n{'='*60}\n")