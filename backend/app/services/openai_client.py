<file>
      <absolute_file_name>/app/backend/app/services/openai_client.py</absolute_file_name>
      <content">from openai import OpenAI
from typing import Dict, List, Optional
from app.config import settings

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def summarize_standup(self, issues_text: str) -> str:
        """Generate AI standup summary from Jira issues"""
        prompt = f"""
You are an AI Scrum Master assistant. Summarize the following Jira issues into a concise standup update format.

Issues from the last 24 hours:
{issues_text}

Please format your response as:
- **Yesterday**: [Key accomplishments and completed work]
- **Today/Next**: [Planned work and priorities]  
- **Blockers**: [Any impediments or issues that need attention]

Keep it concise and focus on the most important updates. If no significant work is shown, mention that activity was light.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def identify_blockers(self, issues_text: str) -> str:
        """Identify and summarize potential blockers from Jira issues"""
        prompt = f"""
You are an AI Scrum Master. Analyze the following Jira issues and identify potential blockers or impediments.

Issues to analyze:
{issues_text}

Look for:
- Issues marked as blocked or with blocking statuses
- Issues with no recent activity that should be progressing
- Dependencies that might be causing delays
- Issues assigned but not being worked on

Provide a summary of potential blockers and recommendations for the Scrum Master.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_retrospective(self, sprint_data: str) -> str:
        """Generate retrospective insights from sprint data"""
        prompt = f"""
You are an AI Scrum Master facilitating a sprint retrospective. Based on the following sprint data, provide insights and suggestions.

Sprint Data:
{sprint_data}

Please provide:
1. **What Went Well**: Positive highlights from the sprint
2. **What Could Be Improved**: Areas needing attention  
3. **Action Items**: Specific, actionable recommendations for the next sprint
4. **Team Performance**: Brief assessment of velocity and delivery

Keep insights constructive and actionable.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()

# Global instance
openai_service = OpenAIService()

def summarize_list(markdown_list: str) -> str:
    """Legacy function for backward compatibility"""
    return openai_service.summarize_standup(markdown_list)

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
    
    def summarize_standup(self, issues_text: str) -> str:
        """Generate AI standup summary from Jira issues"""
        prompt = f"""
You are an AI Scrum Master assistant. Summarize the following Jira issues into a concise standup update format.

Issues from the last 24 hours:
{issues_text}

Please format your response as:
- **Yesterday**: [Key accomplishments and completed work]
- **Today/Next**: [Planned work and priorities]  
- **Blockers**: [Any impediments or issues that need attention]

Keep it concise and focus on the most important updates. If no significant work is shown, mention that activity was light.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def identify_blockers(self, issues_text: str) -> str:
        """Identify and summarize potential blockers from Jira issues"""
        prompt = f"""
You are an AI Scrum Master. Analyze the following Jira issues and identify potential blockers or impediments.

Issues to analyze:
{issues_text}

Look for:
- Issues marked as blocked or with blocking statuses
- Issues with no recent activity that should be progressing
- Dependencies that might be causing delays
- Issues assigned but not being worked on

Provide a summary of potential blockers and recommendations for the Scrum Master.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_retrospective(self, sprint_data: str) -> str:
        """Generate retrospective insights from sprint data"""
        prompt = f"""
You are an AI Scrum Master facilitating a sprint retrospective. Based on the following sprint data, provide insights and suggestions.

Sprint Data:
{sprint_data}

Please provide:
1. **What Went Well**: Positive highlights from the sprint
2. **What Could Be Improved**: Areas needing attention  
3. **Action Items**: Specific, actionable recommendations for the next sprint
4. **Team Performance**: Brief assessment of velocity and delivery

Keep insights constructive and actionable.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()

# Global instance
openai_service = OpenAIService()

def summarize_list(markdown_list: str) -> str:
    """Legacy function for backward compatibility"""
    return openai_service.summarize_standup(markdown_list)
</content>
    </file>