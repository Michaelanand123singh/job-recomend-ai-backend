import requests
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class RealJobFetcher:
    def __init__(self):
        # API Keys (get from environment variables)
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
        
        # Indian cities for location-based search
        self.indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 
            'Pune', 'Ahmedabad', 'Jaipur', 'Gurgaon', 'Noida', 'Indore'
        ]
        
        # Skills to job title mapping
        self.skill_to_job_mapping = {
            'python': ['Python Developer', 'Backend Developer', 'Data Scientist'],
            'java': ['Java Developer', 'Backend Developer', 'Full Stack Developer'],
            'javascript': ['Frontend Developer', 'Full Stack Developer', 'Web Developer'],
            'react': ['React Developer', 'Frontend Developer', 'UI Developer'],
            'node.js': ['Node.js Developer', 'Backend Developer', 'Full Stack Developer'],
            'data science': ['Data Scientist', 'Data Analyst', 'ML Engineer'],
            'machine learning': ['ML Engineer', 'Data Scientist', 'AI Engineer'],
            'devops': ['DevOps Engineer', 'Cloud Engineer', 'SRE'],
            'aws': ['Cloud Engineer', 'DevOps Engineer', 'Solutions Architect']
        }
    
    def fetch_jobs(self, limit: int = 50, resume_skills: List[str] = None) -> List[Dict]:
        """
        Fetch real jobs from multiple APIs based on resume skills
        """
        print(f"🔍 Fetching {limit} real jobs from APIs...")
        
        all_jobs = []
        job_titles = self._get_relevant_job_titles(resume_skills or [])
        
        # Try different APIs in order of preference
        apis_to_try = [
            ('google_jobs', self._fetch_google_jobs),
            ('adzuna', self._fetch_adzuna_jobs),
            ('jsearch', self._fetch_jsearch_jobs),
            ('arbeitnow', self._fetch_arbeitnow_jobs)
        ]
        
        for api_name, fetch_function in apis_to_try:
            if len(all_jobs) >= limit:
                break
                
            try:
                print(f"📱 Trying {api_name} API...")
                jobs = fetch_function(job_titles, limit - len(all_jobs))
                if jobs:
                    all_jobs.extend(jobs)
                    print(f"✅ Found {len(jobs)} jobs from {api_name}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"❌ Error with {api_name}: {str(e)}")
                continue
        
        # Format and enhance jobs
        formatted_jobs = self._format_jobs(all_jobs)
        return formatted_jobs[:limit]
    
    def _get_relevant_job_titles(self, skills: List[str]) -> List[str]:
        """Convert resume skills to relevant job titles"""
        job_titles = set()
        
        for skill in skills:
            skill_lower = skill.lower()
            for skill_key, titles in self.skill_to_job_mapping.items():
                if skill_key in skill_lower or skill_lower in skill_key:
                    job_titles.update(titles)
        
        if not job_titles:
            job_titles.update(['Software Developer', 'Software Engineer'])
        
        return list(job_titles)[:3]  # Limit to top 3
    
    def _fetch_google_jobs(self, job_titles: List[str], limit: int) -> List[Dict]:
        """Fetch jobs using Google Jobs API via SerpApi"""
        if not self.serpapi_key:
            print("⚠️  SerpApi key not found")
            return []
        
        jobs = []
        
        for title in job_titles:
            try:
                params = {
                    "engine": "google_jobs",
                    "q": f"{title} jobs in India",
                    "location": "India",
                    "api_key": self.serpapi_key,
                    "num": min(limit // len(job_titles), 10)
                }
                
                response = requests.get("https://serpapi.com/search", params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'jobs_results' in data:
                        for job in data['jobs_results']:
                            parsed_job = self._parse_google_job(job)
                            if parsed_job:
                                jobs.append(parsed_job)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Google Jobs API error: {str(e)}")
                continue
        
        return jobs
    
    def _fetch_adzuna_jobs(self, job_titles: List[str], limit: int) -> List[Dict]:
        """Fetch jobs using Adzuna API"""
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("⚠️  Adzuna API keys not found")
            return []
        
        jobs = []
        
        for title in job_titles:
            try:
                url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
                params = {
                    "app_id": self.adzuna_app_id,
                    "app_key": self.adzuna_app_key,
                    "what": title,
                    "where": "india",
                    "results_per_page": min(limit // len(job_titles), 10)
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for job in data['results']:
                            parsed_job = self._parse_adzuna_job(job)
                            if parsed_job:
                                jobs.append(parsed_job)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Adzuna API error: {str(e)}")
                continue
        
        return jobs
    
    def _fetch_jsearch_jobs(self, job_titles: List[str], limit: int) -> List[Dict]:
        """Fetch jobs using JSearch API via RapidAPI"""
        if not self.rapidapi_key:
            print("⚠️  RapidAPI key not found")
            return []
        
        jobs = []
        
        for title in job_titles:
            try:
                url = "https://jsearch.p.rapidapi.com/search"
                
                querystring = {
                    "query": f"{title} in India",
                    "page": "1",
                    "num_pages": "1",
                    "date_posted": "all"
                }
                
                headers = {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }
                
                response = requests.get(url, headers=headers, params=querystring, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data:
                        for job in data['data'][:limit // len(job_titles)]:
                            parsed_job = self._parse_jsearch_job(job)
                            if parsed_job:
                                jobs.append(parsed_job)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"JSearch API error: {str(e)}")
                continue
        
        return jobs
    
    def _fetch_arbeitnow_jobs(self, job_titles: List[str], limit: int) -> List[Dict]:
        """Fetch jobs using ArbeitsNow API (Free)"""
        jobs = []
        
        try:
            url = "https://www.arbeitnow.com/api/job-board-api"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for job in data['data'][:limit]:
                        parsed_job = self._parse_arbeitnow_job(job)
                        if parsed_job:
                            jobs.append(parsed_job)
            
        except Exception as e:
            print(f"ArbeitsNow API error: {str(e)}")
        
        return jobs
    
    def _parse_google_job(self, job: Dict) -> Optional[Dict]:
        """Parse Google Jobs API response"""
        try:
            return {
                'id': f"google_{hash(job.get('title', '') + job.get('company_name', ''))}",
                'title': job.get('title', 'Not specified'),
                'company': job.get('company_name', 'Not specified'),
                'location': job.get('location', 'India'),
                'salary': job.get('salary', 'Not disclosed'),
                'description': job.get('description', 'No description available')[:500],
                'source': 'Google Jobs',
                'url': job.get('share_link', 'https://www.google.com/search?q=jobs'),
                'posted_date': job.get('posted_at', 'Recent'),
                'job_type': 'Full-time',
                'remote': 'remote' in job.get('description', '').lower(),
                'requirements': self._extract_requirements_from_text(job.get('description', ''))
            }
        except Exception as e:
            return None
    
    def _parse_adzuna_job(self, job: Dict) -> Optional[Dict]:
        """Parse Adzuna API response"""
        try:
            return {
                'id': f"adzuna_{job.get('id', hash(job.get('title', '')))}",
                'title': job.get('title', 'Not specified'),
                'company': job.get('company', {}).get('display_name', 'Not specified'),
                'location': job.get('location', {}).get('display_name', 'India'),
                'salary': f"₹{job.get('salary_min', 0)}-{job.get('salary_max', 0)}" if job.get('salary_min') else 'Not disclosed',
                'description': job.get('description', 'No description available')[:500],
                'source': 'Adzuna',
                'url': job.get('redirect_url', 'https://www.adzuna.co.in/'),
                'posted_date': job.get('created', 'Recent'),
                'job_type': 'Full-time',
                'remote': 'remote' in job.get('description', '').lower(),
                'requirements': self._extract_requirements_from_text(job.get('description', ''))
            }
        except Exception as e:
            return None
    
    def _parse_jsearch_job(self, job: Dict) -> Optional[Dict]:
        """Parse JSearch API response"""
        try:
            return {
                'id': f"jsearch_{job.get('job_id', hash(job.get('job_title', '')))}",
                'title': job.get('job_title', 'Not specified'),
                'company': job.get('employer_name', 'Not specified'),
                'location': job.get('job_city', 'India'),
                'salary': job.get('job_salary', 'Not disclosed'),
                'description': job.get('job_description', 'No description available')[:500],
                'source': 'JSearch',
                'url': job.get('job_apply_link', 'https://www.google.com/search?q=jobs'),
                'posted_date': job.get('job_posted_at_datetime_utc', 'Recent'),
                'job_type': job.get('job_employment_type', 'Full-time'),
                'remote': job.get('job_is_remote', False),
                'requirements': self._extract_requirements_from_text(job.get('job_description', ''))
            }
        except Exception as e:
            return None
    
    def _parse_arbeitnow_job(self, job: Dict) -> Optional[Dict]:
        """Parse ArbeitsNow API response"""
        try:
            return {
                'id': f"arbeitnow_{job.get('slug', hash(job.get('title', '')))}",
                'title': job.get('title', 'Not specified'),
                'company': job.get('company_name', 'Not specified'),
                'location': job.get('location', 'Remote'),
                'salary': 'Not disclosed',
                'description': job.get('description', 'No description available')[:500],
                'source': 'ArbeitsNow',
                'url': job.get('url', 'https://www.arbeitnow.com/'),
                'posted_date': job.get('created_at', 'Recent'),
                'job_type': 'Full-time',
                'remote': True,
                'requirements': self._extract_requirements_from_text(job.get('description', ''))
            }
        except Exception as e:
            return None
    
    def _extract_requirements_from_text(self, text: str) -> List[str]:
        """Extract technical requirements from job description"""
        requirements = []
        text_lower = text.lower()
        
        # Common tech skills
        skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'node.js',
            'sql', 'mysql', 'mongodb', 'aws', 'docker', 'kubernetes',
            'spring boot', 'django', 'flask', 'git', 'html', 'css'
        ]
        
        for skill in skills:
            if skill in text_lower:
                requirements.append(skill.title())
        
        return requirements[:6]
    
    def _format_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Format and enhance job data"""
        formatted_jobs = []
        
        for job in jobs:
            # Add experience level
            job['experience_level'] = self._determine_experience_level(job.get('description', ''))
            
            # Add market insights
            job['market_insights'] = {
                'job_market': 'India',
                'currency': 'INR',
                'notice_period': '30-60 days typical',
                'visa_required': False
            }
            
            formatted_jobs.append(job)
        
        return formatted_jobs
    
    def _determine_experience_level(self, description: str) -> str:
        """Determine experience level"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['fresher', 'entry level', '0-1 year']):
            return 'Fresher'
        elif any(word in description_lower for word in ['senior', 'lead', '5+ years']):
            return 'Senior'
        else:
            return 'Mid-level'
    
    def get_job_market_insights(self) -> Dict:
        """Get insights about job market"""
        return {
            'top_hiring_cities': self.indian_cities,
            'popular_skills': ['Python', 'Java', 'JavaScript', 'React', 'SQL', 'AWS'],
            'salary_ranges': {
                'fresher': '₹2-4 Lakhs',
                'mid_level': '₹4-8 Lakhs',
                'senior': '₹8-15 Lakhs'
            },
            'api_sources': ['Google Jobs', 'Adzuna', 'JSearch', 'ArbeitsNow']
        }