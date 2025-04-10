"""
GitHub Advanced Project Assistant (HICHEM)
Version: 4.2
Author: Hichem
Features: Hybrid Analysis, Advanced Reporting, CI/CD Detection
"""

import os
import json
import math
import requests
import datetime
import subprocess
from textstat import flesch_reading_ease, textstat
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from git import Repo
from functools import lru_cache

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
        cmd = [
            "ssh-keygen",
            "-t", "ed25519",
            "-f", self.key_path,
            "-N", "",
            "-q"
        ]
        subprocess.run(cmd, check=True)

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
    """Advanced Project Analyzer"""
    def __init__(self):
        self.base_url = "https://api.github.com/search/repositories"
        self.headers = {'Accept': 'application/vnd.github.v3+json'}

    def _get_repo_details(self, repo_url):
        """Get complete project details"""
        return requests.get(repo_url, headers=self.headers).json()

    def analyze_readme(self, repo):
        """Analyze documentation quality"""
        readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"
        response = requests.get(readme_url)
        
        analysis = {'readme_exists': False}
        if response.status_code == 200:
            content = response.text
            analysis.update({
                'readme_exists': True,
                'readability': flesch_reading_ease(content),
                'grade_level': textstat.text_standard(content),
                'sections': content.count('#')
            })
        return analysis

    def calculate_health(self, repo):
        """Calculate project health metrics"""
        last_update = datetime.datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
        delta_days = (datetime.datetime.now() - last_update).days
        
        return {
            'activity_score': max(0, 100 - delta_days),
            'issue_ratio': (repo['closed_issues'] / repo['open_issues']) if repo['open_issues'] > 0 else 1,
            'commit_frequency': repo['commits'] / (repo['age_days'] or 1)
        }

class HybridRanker:
    """Hybrid Ranking System"""
    def __init__(self):
        self.weights = CONFIG['ranking_weights']
        
    def calculate_score(self, repo):
        """Enhanced ranking algorithm"""
        components = {
            'activity': repo['health']['activity_score'] * 0.01,
            'readability': repo['readme']['readability'] * 0.01 if repo['readme']['readme_exists'] else 0.3,
            'health': repo['health']['issue_ratio'] * 0.5 + repo['health']['commit_frequency'] * 0.5,
            'popularity': math.log(repo['stargazers_count'] + 1) * 0.4,
            'ci_cd': 1.0 if repo['metadata']['ci_cd'] else 0.3
        }
        
        total = sum(components[k] * self.weights[k] for k in components)
        return min(max(total * 100, 0), 100)

class HICHEM_Core:
    """Core Application System"""
    def __init__(self):
        self.ssh = SSHVault()
        self.analyzer = ProjectAnalyzer()
        self.ranker = HybridRanker()
        self.report_style = ParagraphStyle(
            'HichemStyle',
            fontSize=11,
            leading=13,
            fontName='Helvetica'
        )

    def search_projects(self, query, filters=None):
        """Advanced search with filters"""
        search_url = self._build_search_url(query, filters)
        results = requests.get(search_url, timeout=CONFIG['api_timeout']).json()
        
        processed = []
        for item in results.get('items', [])[:CONFIG['max_results']]:
            repo = self._process_repo(item)
            processed.append(repo)
            
        return sorted(processed, key=lambda x: x['score'], reverse=True)

    def _build_search_url(self, query, filters):
        """Construct search URL"""
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': CONFIG['max_results']
        }
        
        if filters:
            if 'min_stars' in filters:
                params['q'] += f" stars:>={filters['min_stars']}"
            if 'license' in filters:
                params['q'] += f" license:{filters['license']}"
                
        return f"{self.analyzer.base_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"

    def _process_repo(self, item):
        """Process repository data"""
        full_data = self.analyzer._get_repo_details(item['url'])
        
        return {
            'name': item['name'],
            'description': item['description'],
            'stars': item['stargazers_count'],
            'forks': item['forks_count'],
            'readme': self.analyzer.analyze_readme(item),
            'health': self.analyzer.calculate_health(full_data),
            'metadata': {
                'license': full_data.get('license', {}).get('name'),
                'ci_cd': full_data['has_workflows'],
                'tests': full_data['has_tests']
            },
            'score': self.ranker.calculate_score(full_data)
        }

    def generate_report(self, repo, filename=None):
        """Generate advanced report"""
        filename = filename or f"HICHEM_{repo['name']}_Report.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        
        # Main Title
        c.setFont('Helvetica-Bold', 16)
        c.drawString(50, 800, f"Project Report: {repo['name']}")
        
        # Basic Information
        info_lines = [
            f"Description: {repo['description'] or 'No description'}",
            f"Stars: {repo['stars']} | Forks: {repo['forks']}",
            f"Last Updated: {repo['pushed_at'][:10]}",
            f"License: {repo['metadata']['license'] or 'Unknown'}"
        ]
        
        y_pos = 750
        for line in info_lines:
            c.setFont('Helvetica', 12)
            c.drawString(50, y_pos, line)
            y_pos -= 25
            
        # Health Metrics
        self._draw_health_metrics(c, repo, y_pos-30)
        c.save()
        return filename

    def _draw_health_metrics(self, c, repo, y_pos):
        """Draw health metrics visualization"""
        c.setFont('Helvetica-Bold', 14)
        c.drawString(50, y_pos, "Project Health Metrics:")
        
        metrics = [
            ("Activity", repo['health']['activity_score']),
            ("Issue Management", repo['health']['issue_ratio'] * 100),
            ("Commit Frequency", repo['health']['commit_frequency'])
        ]
        
        y_pos -= 40
        for name, value in metrics:
            c.setFont('Helvetica', 12)
            c.drawString(70, y_pos, f"{name}: {value:.1f}%")
            y_pos -= 25

# Main Interface
if __name__ == "__main__":
    hichem = HICHEM_Core()
    
    if not hichem.ssh.test_connection():
        print("Error: Failed to connect to GitHub")
        exit(1)
        
    query = input("Enter search keywords: ")
    filters = {
        'min_stars': int(input("Minimum stars (0 for any): ") or 0),
        'license': input("License type (optional): ")
    }
    
    results = hichem.search_projects(query, filters)
    
    print("\nResults:")
    for i, repo in enumerate(results, 1):
        print(f"{i}. {repo['name']} ({repo['score']:.1f}/100)")
        print(f"   Stars: {repo['stars']} | Health: {repo['health']['activity_score']:.1f}%")
        
    if results:
        hichem.generate_report(results[0])
        print("Report generated successfully!")
