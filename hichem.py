"""
GitHub Advanced Project Assistant (HICHEM)
Version: 5.0
Author: Hichem
Features: Hybrid Analysis, Advanced Reporting, CI/CD Detection, Async Support
"""

import os
import json
import math
import asyncio
import aiohttp
import datetime
from functools import lru_cache
from textstat import flesch_reading_ease, textstat
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle

# Configuration
CONFIG = {
    "ssh_key": os.path.expanduser("~/.ssh/hichem_key"),
    "repo": "hichem-repo",
    "user": "hichem",
    "api_timeout": 20,
    "max_results": 15,
    "ranking_weights": {
        'activity': 0.35,
        'readability': 0.25,
        'health': 0.20,
        'popularity': 0.15,
        'ci_cd': 0.05
    }
}

class SSHVault:
    """Secure SSH Key Management System"""
    def __init__(self):
        self.key_path = CONFIG['ssh_key']
        self._setup_ssh()

    def _setup_ssh(self):
        if not os.path.exists(self.key_path):
            self.generate_keys()
        os.chmod(self.key_path, 0o600)

    def generate_keys(self):
        """Generate new SSH keys"""
        try:
            cmd = [
                "ssh-keygen", "-t", "ed25519", "-f", self.key_path, "-N", "", "-q"
            ]
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating SSH keys: {e}")

    def test_connection(self):
        """Test GitHub connection"""
        try:
            result = subprocess.run(
                ["ssh", "-T", "-i", self.key_path, "git@github.com"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "successfully authenticated" in result.stderr
        except Exception as e:
            print(f"Connection Error: {str(e)}")
            return False

class ProjectAnalyzer:
    """Advanced Project Analyzer with Async Support"""
    def __init__(self):
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}

    async def fetch(self, session, url):
        """Async HTTP GET request"""
        try:
            async with session.get(url, timeout=CONFIG['api_timeout']) as response:
                return await response.json()
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return {}

    async def analyze_readme(self, repo):
        """Analyze documentation quality"""
        readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"
        async with aiohttp.ClientSession() as session:
            response = await self.fetch(session, readme_url)
            analysis = {'readme_exists': False}
            if response:
                content = response
                analysis.update({
                    'readme_exists': True,
                    'readability': flesch_reading_ease(content),
                    'grade_level': textstat.text_standard(content),
                    'sections': content.count('#')
                })
            return analysis

    def calculate_health(self, repo):
        """Calculate project health metrics"""
        try:
            last_update = datetime.datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
            delta_days = (datetime.datetime.now() - last_update).days

            return {
                'activity_score': max(0, 100 - delta_days),
                'issue_ratio': (repo['closed_issues'] / repo['open_issues']) if repo['open_issues'] > 0 else 1,
                'commit_frequency': repo['commits'] / (repo['age_days'] or 1)
            }
        except KeyError as e:
            print(f"Missing key in repo data: {e}")
            return {}

class HybridRanker:
    """Hybrid Ranking System"""
    def __init__(self):
        self.weights = CONFIG['ranking_weights']

    def calculate_score(self, repo):
        """Enhanced ranking algorithm"""
        try:
            components = {
                'activity': repo['health']['activity_score'] * 0.01,
                'readability': repo['readme']['readability'] * 0.01 if repo['readme']['readme_exists'] else 0.3,
                'health': repo['health']['issue_ratio'] * 0.5 + repo['health']['commit_frequency'] * 0.5,
                'popularity': math.log(repo['stargazers_count'] + 1) * 0.4,
                'ci_cd': 1.0 if repo['metadata']['ci_cd'] else 0.3
            }

            total = sum(components[k] * self.weights[k] for k in components)
            return min(max(total * 100, 0), 100)
        except Exception as e:
            print(f"Error calculating score: {e}")
            return 0

# Main Interface
async def main():
    hichem = HICHEM_Core()
    if not hichem.ssh.test_connection():
        print("Error: Failed to connect to GitHub")
        return

    query = input("Enter search keywords: ")
    filters = {
        'min_stars': int(input("Minimum stars (0 for any): ") or 0),
        'license': input("License type (optional): ")
    }

    results = await hichem.search_projects(query, filters)
    print("\nResults:")
    for i, repo in enumerate(results, 1):
        print(f"{i}. {repo['name']} ({repo['score']:.1f}/100)")
        print(f"   Stars: {repo['stars']} | Health: {repo['health']['activity_score']:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())