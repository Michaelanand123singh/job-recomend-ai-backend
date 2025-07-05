import google.generativeai as genai
import os
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class GeminiMatcher:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        # Updated model name from 'gemini-pro' to 'gemini-1.5-flash'
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def match_resume_to_jobs(self, resume_data: Dict, jobs: List[Dict]) -> List[Dict]:
        """
        Use Gemini AI to match resume with job listings and return ranked results
        """
        try:
            # Prepare the prompt for Gemini
            prompt = self._create_matching_prompt(resume_data, jobs)
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            matches = self._parse_gemini_response(response.text, jobs)
            
            return matches
            
        except Exception as e:
            print(f"Error in Gemini matching: {str(e)}")
            # Fallback to simple matching if Gemini fails
            return self._fallback_matching(resume_data, jobs)
    
    def _create_matching_prompt(self, resume_data: Dict, jobs: List[Dict]) -> str:
        """
        Create a comprehensive prompt for Gemini to analyze resume-job matches
        """
        resume_summary = f"""
        RESUME ANALYSIS:
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Experience: {resume_data.get('experience_years', 0)} years
        - Education: {', '.join(resume_data.get('education', []))}
        - Summary: {resume_data.get('summary', 'No summary available')}
        """
        
        jobs_summary = "JOB LISTINGS:\n"
        for i, job in enumerate(jobs[:10]):  # Limit to first 10 jobs to avoid token limits
            jobs_summary += f"""
            Job {i+1}:
            - Title: {job['title']}
            - Company: {job['company']}
            - Requirements: {', '.join(job.get('requirements', []))}
            - Description: {job['description'][:200]}...
            - Salary: {job.get('salary', 'Not specified')}
            - Remote: {job.get('remote', False)}
            """
        
        prompt = f"""
        You are a professional career counselor and job matching expert. Analyze the following resume and job listings to provide the best job matches.

        {resume_summary}

        {jobs_summary}

        TASK: Analyze each job and provide a match score (0-100) based on:
        1. Skills alignment (40% weight)
        2. Experience level match (25% weight)
        3. Industry/role compatibility (20% weight)
        4. Career growth potential (15% weight)

        For each job, also provide:
        - Match percentage (0-100)
        - Matching skills found
        - Missing skills that candidate should develop
        - Brief explanation (2-3 sentences) of why this is a good/poor match

        RESPONSE FORMAT (JSON):
        {{
            "matches": [
                {{
                    "job_index": 0,
                    "match_percentage": 85,
                    "matching_skills": ["React", "JavaScript", "Node.js"],
                    "missing_skills": ["MongoDB", "Docker"],
                    "explanation": "Strong match due to frontend skills alignment. Candidate's React experience directly matches job requirements.",
                    "recommendation": "Apply immediately - excellent fit"
                }}
            ]
        }}

        Return only valid JSON. Analyze ALL jobs provided and rank them by match percentage.
        """
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str, jobs: List[Dict]) -> List[Dict]:
        """
        Parse Gemini's response and create formatted job matches
        """
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                parsed_response = json.loads(json_text)
                
                matches = []
                for match in parsed_response.get('matches', []):
                    job_index = match.get('job_index', 0)
                    if job_index < len(jobs):
                        job = jobs[job_index].copy()
                        job.update({
                            'match_percentage': match.get('match_percentage', 0),
                            'matching_skills': match.get('matching_skills', []),
                            'missing_skills': match.get('missing_skills', []),
                            'explanation': match.get('explanation', ''),
                            'recommendation': match.get('recommendation', '')
                        })
                        matches.append(job)
                
                # Sort by match percentage (descending)
                matches.sort(key=lambda x: x.get('match_percentage', 0), reverse=True)
                return matches[:10]  # Return top 10 matches
            
        except Exception as e:
            print(f"Error parsing Gemini response: {str(e)}")
        
        # Fallback if parsing fails
        return self._fallback_matching({"skills": [], "experience_years": 0}, jobs)
    
    def _fallback_matching(self, resume_data: Dict, jobs: List[Dict]) -> List[Dict]:
        """
        Simple fallback matching algorithm if Gemini fails
        """
        resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
        matches = []
        
        for job in jobs:
            job_requirements = set(req.lower() for req in job.get('requirements', []))
            
            # Calculate simple skill match percentage
            if job_requirements:
                matching_skills = resume_skills.intersection(job_requirements)
                match_percentage = int((len(matching_skills) / len(job_requirements)) * 100)
            else:
                match_percentage = 50  # Default if no requirements listed
            
            job_copy = job.copy()
            job_copy.update({
                'match_percentage': match_percentage,
                'matching_skills': list(matching_skills) if 'matching_skills' in locals() else [],
                'missing_skills': list(job_requirements - resume_skills) if 'job_requirements' in locals() else [],
                'explanation': f"Basic skill match analysis. {len(matching_skills) if 'matching_skills' in locals() else 0} skills match job requirements.",
                'recommendation': 'Consider applying' if match_percentage > 60 else 'Develop missing skills first'
            })
            matches.append(job_copy)
        
        # Sort by match percentage
        matches.sort(key=lambda x: x.get('match_percentage', 0), reverse=True)
        return matches[:10]
    
    def generate_cover_letter_tips(self, resume_data: Dict, job: Dict) -> str:
        """
        Generate personalized cover letter tips using Gemini
        """
        try:
            prompt = f"""
            Generate 3-4 personalized cover letter tips for this job application:
            
            CANDIDATE PROFILE:
            - Skills: {', '.join(resume_data.get('skills', []))}
            - Experience: {resume_data.get('experience_years', 0)} years
            
            JOB DETAILS:
            - Title: {job['title']}
            - Company: {job['company']}
            - Requirements: {', '.join(job.get('requirements', []))}
            
            Provide specific, actionable tips for highlighting relevant experience and skills.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Unable to generate cover letter tips: {str(e)}"
    
    def analyze_skill_gaps(self, resume_data: Dict, target_jobs: List[Dict]) -> Dict:
        """
        Analyze skill gaps across target jobs using Gemini
        """
        try:
            all_requirements = set()
            for job in target_jobs:
                all_requirements.update(job.get('requirements', []))
            
            resume_skills = set(resume_data.get('skills', []))
            missing_skills = all_requirements - resume_skills
            
            prompt = f"""
            Analyze skill gaps and provide learning recommendations:
            
            CURRENT SKILLS: {', '.join(resume_skills)}
            MISSING SKILLS: {', '.join(missing_skills)}
            
            Provide:
            1. Top 5 priority skills to learn
            2. Learning path recommendations
            3. Estimated time to acquire each skill
            
            Focus on skills that appear in multiple job listings.
            """
            
            response = self.model.generate_content(prompt)
            
            return {
                'missing_skills': list(missing_skills),
                'recommendations': response.text,
                'priority_skills': list(missing_skills)[:5]
            }
            
        except Exception as e:
            return {
                'missing_skills': [],
                'recommendations': f"Unable to analyze skill gaps: {str(e)}",
                'priority_skills': []
            }