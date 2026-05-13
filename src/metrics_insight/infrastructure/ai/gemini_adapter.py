import json
from typing import List, Dict, Any

try:
    from google import genai
except ImportError:
    genai = None

from metrics_insight.domain.repository_interfaces import SentimentAnalyzer, RootCauseAnalyzer, PredictiveAnalyzer


class GeminiAIAdapter(SentimentAnalyzer, RootCauseAnalyzer, PredictiveAnalyzer):
    """Adapter for AI-driven analysis using Google's Gemini API (new google-genai SDK)."""

    def __init__(self, api_key: str):
        if genai is None:
            raise RuntimeError(
                "Gemini support is not available because the 'google-genai' "
                "dependency is not installed."
            )
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-2.0-flash'

    def analyze_sentiment(self, comments: List[str]) -> Dict[str, Any]:
        if not comments:
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "friction_detected": False,
                "summary": "No comments to analyze."
            }

        prompt = f"""
        Analyze the sentiment of the following code review comments from a GitHub Pull Request.
        Identify the overall sentiment (score from -1 to 1), a label (Positive, Neutral, Negative), 
        and whether there is any team friction detected (e.g., aggressive tone, repetitive nitpicking, 
        frustration).
        
        Comments:
        {json.dumps(comments)}
        
        Provide the output ONLY as a JSON object with these keys:
        - sentiment_score: float (-1 to 1)
        - sentiment_label: string (Positive, Neutral, Negative)
        - friction_detected: boolean
        - summary: string (brief explanation of the sentiment and friction)
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            return json.loads(text)
        except Exception as e:
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "Error",
                "friction_detected": False,
                "summary": f"Failed to analyze sentiment: {str(e)}"
            }

    def suggest_root_causes(self, metrics_data: Dict[str, Any], insights: List[Any]) -> str:
        """Suggests root causes based on metrics and findings."""
        insights_str = "\n".join([f"- {i.category}: {i.title} - {i.description}" for i in insights])
        
        prompt = f"""
        As an expert Engineering Manager, analyze these engineering metrics and findings to suggest 
        root causes for performance issues.
        
        Metrics Summary:
        {json.dumps(metrics_data)}
        
        Key Insights Found:
        {insights_str}
        
        Provide a concise but deep analysis. Focus on:
        1. Why specific bottlenecks (like slow reviews or high rework) might be occurring.
        2. The relationship between different metrics (e.g., PR size vs. review time).
        3. Potential organizational or process-level issues.
        
        Keep the response professional, actionable, and less than 300 words.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Failed to generate root cause analysis: {str(e)}"

    def predict_pr_outcomes(self, pr_data: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimates PR duration and rework risk based on historical patterns."""
        
        prompt = f"""
        Predict the outcome for this new Pull Request based on historical team performance.
        
        New PR Data:
        {json.dumps(pr_data)}
        
        Historical Averages:
        {json.dumps(history)}
        
        Predict:
        1. estimated_duration_h: float (hours)
        2. rework_risk_label: string (High, Medium, Low)
        3. risk_factors: list of strings (why is it risky or not)
        
        Provide the output ONLY as a JSON object with those keys.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            return json.loads(text)
        except Exception as e:
            return {
                "estimated_duration_h": 0.0,
                "rework_risk_label": "Unknown",
                "risk_factors": [str(e)]
            }
