"""
AI Model Integration for Supply Chain Risk Analysis
Analyzes the scraped data and provides risk assessments and recommendations.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupplyChainAIAnalyzer:
    """AI-powered supply chain risk analyzer."""
    
    def __init__(self, data_dir: str = "data/outputs"):
        self.data_dir = Path(data_dir)
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.analysis_results = {}
    
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV data files."""
        data = {}
        
        # Load nodes
        nodes_path = self.data_dir / "nodes.json"
        if nodes_path.exists():
            with open(nodes_path, 'r') as f:
                nodes = json.load(f)
            data['nodes'] = pd.DataFrame(nodes)
        
        # Load CSV files
        csv_files = [
            'social_events.csv',
            'news_events.csv', 
            'weather_anomalies.csv',
            'features_today.csv'
        ]
        
        for csv_file in csv_files:
            csv_path = self.data_dir / csv_file
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                data[csv_file.replace('.csv', '')] = df
                logger.info(f"Loaded {csv_file}: {len(df)} records")
        
        return data
    
    def calculate_risk_scores(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate comprehensive risk scores for each supplier."""
        nodes_df = data.get('nodes', pd.DataFrame())
        social_df = data.get('social_events', pd.DataFrame())
        news_df = data.get('news_events', pd.DataFrame())
        weather_df = data.get('weather_anomalies', pd.DataFrame())
        features_df = data.get('features_today', pd.DataFrame())
        
        risk_analysis = []
        
        for _, node in nodes_df.iterrows():
            node_id = node['node_id']
            
            # Get data for this node
            node_social = social_df[social_df['node_id'] == node_id] if not social_df.empty and 'node_id' in social_df.columns else pd.DataFrame()
            
            # News data doesn't have node_id, so we'll match by supplier name or use all news
            if not news_df.empty:
                # Try to match news by supplier name in headline/snippet
                supplier_name = node['name'].lower()
                if 'headline' in news_df.columns:
                    name_matches = news_df[news_df['headline'].str.contains(supplier_name, case=False, na=False)]
                elif 'snippet' in news_df.columns:
                    name_matches = news_df[news_df['snippet'].str.contains(supplier_name, case=False, na=False)]
                else:
                    name_matches = pd.DataFrame()
                node_news = name_matches
            else:
                node_news = pd.DataFrame()
            
            node_weather = weather_df[weather_df['node_id'] == node_id] if not weather_df.empty and 'node_id' in weather_df.columns else pd.DataFrame()
            node_features = features_df[features_df['node_id'] == node_id] if not features_df.empty and 'node_id' in features_df.columns else pd.DataFrame()
            
            # Calculate risk components
            social_risk = self._calculate_social_risk(node_social)
            news_risk = self._calculate_news_risk(node_news)
            weather_risk = self._calculate_weather_risk(node_weather)
            operational_risk = self._calculate_operational_risk(node_features)
            
            # Calculate overall risk score (0-100)
            overall_risk = (
                social_risk * 0.2 +
                news_risk * 0.3 +
                weather_risk * 0.2 +
                operational_risk * 0.3
            )
            
            # Determine risk category
            if overall_risk >= 70:
                risk_category = "HIGH"
            elif overall_risk >= 40:
                risk_category = "MEDIUM"
            else:
                risk_category = "LOW"
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                social_risk, news_risk, weather_risk, operational_risk, overall_risk
            )
            
            risk_record = {
                'node_id': node_id,
                'name': node['name'],
                'country': node['country'],
                'city': node['city'],
                'category': node['category'],
                'lat': node['lat'],
                'lon': node['lon'],
                'tier': node['tier'],
                
                # Risk scores
                'social_risk_score': social_risk,
                'news_risk_score': news_risk,
                'weather_risk_score': weather_risk,
                'operational_risk_score': operational_risk,
                'overall_risk_score': overall_risk,
                'risk_category': risk_category,
                
                # Data counts
                'social_events_count': len(node_social),
                'news_events_count': len(node_news),
                'weather_anomalies_count': len(node_weather),
                
                # Recommendations
                'recommendations': recommendations,
                'priority_actions': self._get_priority_actions(risk_category, overall_risk),
                
                # Timestamps
                'analysis_timestamp': datetime.now().isoformat(),
                'data_freshness': self._calculate_data_freshness(node_social, node_news, node_weather)
            }
            
            risk_analysis.append(risk_record)
        
        return pd.DataFrame(risk_analysis)
    
    def _calculate_social_risk(self, social_df: pd.DataFrame) -> float:
        """Calculate social media risk score."""
        if social_df.empty:
            return 0.0
        
        # Factors: engagement, negative sentiment, activity volume
        engagement_risk = 0.0
        if 'engagement_count' in social_df.columns:
            engagement_risk = min(social_df['engagement_count'].sum() / 1000, 50)  # Cap at 50
        
        volume_risk = min(len(social_df) * 2, 30)  # Cap at 30
        
        # Check for negative keywords in social content
        negative_keywords = ['disruption', 'delay', 'shortage', 'strike', 'shutdown', 'problem', 'issue']
        negative_content = 0
        if 'text' in social_df.columns:
            for text in social_df['text']:
                if any(keyword in str(text).lower() for keyword in negative_keywords):
                    negative_content += 1
        
        negative_risk = min(negative_content * 10, 20)  # Cap at 20
        
        return min(engagement_risk + volume_risk + negative_risk, 100)
    
    def _calculate_news_risk(self, news_df: pd.DataFrame) -> float:
        """Calculate news-based risk score."""
        if news_df.empty:
            return 0.0
        
        # Use sentiment score if available
        if 'sentiment_score' in news_df.columns:
            negative_sentiment = news_df[news_df['sentiment_score'] < -0.5]
            sentiment_risk = len(negative_sentiment) * 15
        else:
            sentiment_risk = 0
        
        # Volume risk
        volume_risk = min(len(news_df) * 3, 40)
        
        # Check for risk-related keywords
        risk_keywords = ['disruption', 'shortage', 'delay', 'strike', 'flood', 'fire', 'cyberattack']
        risk_content = 0
        if 'headline' in news_df.columns:
            for headline in news_df['headline']:
                if any(keyword in str(headline).lower() for keyword in risk_keywords):
                    risk_content += 1
        
        content_risk = min(risk_content * 20, 40)
        
        return min(sentiment_risk + volume_risk + content_risk, 100)
    
    def _calculate_weather_risk(self, weather_df: pd.DataFrame) -> float:
        """Calculate weather-based risk score."""
        if weather_df.empty:
            return 0.0
        
        # Severity-based scoring
        high_severity = len(weather_df[weather_df.get('severity', '') == 'high'])
        medium_severity = len(weather_df[weather_df.get('severity', '') == 'medium'])
        low_severity = len(weather_df[weather_df.get('severity', '') == 'low'])
        
        weather_risk = (
            high_severity * 30 +
            medium_severity * 15 +
            low_severity * 5
        )
        
        return min(weather_risk, 100)
    
    def _calculate_operational_risk(self, features_df: pd.DataFrame) -> float:
        """Calculate operational risk score."""
        if features_df.empty:
            return 25.0  # Default moderate risk if no data
        
        # Use existing features if available
        operational_risk = 25.0  # Base risk
        
        # Add risk based on available features
        if 'news_count_7d' in features_df.columns:
            news_risk = min(features_df['news_count_7d'].iloc[0] * 2, 30)
            operational_risk += news_risk
        
        if 'weather_anomaly_7d' in features_df.columns:
            weather_risk = features_df['weather_anomaly_7d'].iloc[0] * 10
            operational_risk += weather_risk
        
        return min(operational_risk, 100)
    
    def _generate_recommendations(self, social_risk: float, news_risk: float, 
                                weather_risk: float, operational_risk: float, 
                                overall_risk: float) -> str:
        """Generate AI-powered recommendations."""
        recommendations = []
        
        if social_risk > 50:
            recommendations.append("Monitor social media channels closely for negative sentiment")
        
        if news_risk > 60:
            recommendations.append("Investigate recent news coverage for potential supply chain impacts")
        
        if weather_risk > 40:
            recommendations.append("Assess weather-related risks and develop contingency plans")
        
        if operational_risk > 50:
            recommendations.append("Review operational processes and identify potential bottlenecks")
        
        if overall_risk > 70:
            recommendations.append("URGENT: Implement immediate risk mitigation strategies")
            recommendations.append("Consider alternative suppliers or backup plans")
        elif overall_risk > 40:
            recommendations.append("Increase monitoring frequency and prepare contingency plans")
        else:
            recommendations.append("Continue regular monitoring - risk levels are acceptable")
        
        return "; ".join(recommendations)
    
    def _get_priority_actions(self, risk_category: str, overall_risk: float) -> str:
        """Get priority actions based on risk level."""
        if risk_category == "HIGH":
            return "Immediate action required - contact supplier, assess alternatives, activate contingency plans"
        elif risk_category == "MEDIUM":
            return "Increased monitoring - schedule supplier check-ins, review backup options"
        else:
            return "Standard monitoring - continue regular supplier communications"
    
    def _calculate_data_freshness(self, social_df: pd.DataFrame, news_df: pd.DataFrame, 
                                weather_df: pd.DataFrame) -> str:
        """Calculate how fresh the data is."""
        now = datetime.now()
        latest_timestamp = None
        
        for df in [social_df, news_df, weather_df]:
            if not df.empty and 'ts' in df.columns:
                try:
                    df_timestamps = pd.to_datetime(df['ts'])
                    if not df_timestamps.empty:
                        latest = df_timestamps.max()
                        if latest_timestamp is None or latest > latest_timestamp:
                            latest_timestamp = latest
                except:
                    continue
        
        if latest_timestamp:
            hours_old = (now - latest_timestamp).total_seconds() / 3600
            if hours_old < 1:
                return "Very Fresh (< 1 hour)"
            elif hours_old < 24:
                return f"Fresh ({hours_old:.1f} hours old)"
            elif hours_old < 168:  # 1 week
                return f"Moderate ({hours_old/24:.1f} days old)"
            else:
                return f"Stale ({hours_old/24:.1f} days old)"
        
        return "No recent data"
    
    def generate_ai_insights(self, risk_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate AI-powered insights and summary."""
        insights = {
            'analysis_summary': {
                'total_suppliers': len(risk_df),
                'high_risk_suppliers': len(risk_df[risk_df['risk_category'] == 'HIGH']),
                'medium_risk_suppliers': len(risk_df[risk_df['risk_category'] == 'MEDIUM']),
                'low_risk_suppliers': len(risk_df[risk_df['risk_category'] == 'LOW']),
                'average_risk_score': risk_df['overall_risk_score'].mean(),
                'highest_risk_supplier': risk_df.loc[risk_df['overall_risk_score'].idxmax(), 'name'] if not risk_df.empty else None,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'risk_distribution': {
                'high_risk_count': len(risk_df[risk_df['risk_category'] == 'HIGH']),
                'medium_risk_count': len(risk_df[risk_df['risk_category'] == 'MEDIUM']),
                'low_risk_count': len(risk_df[risk_df['risk_category'] == 'LOW'])
            },
            'top_risks': risk_df.nlargest(3, 'overall_risk_score')[['name', 'overall_risk_score', 'risk_category']].to_dict('records') if not risk_df.empty else [],
            'recommendations': {
                'immediate_actions': risk_df[risk_df['risk_category'] == 'HIGH']['name'].tolist(),
                'monitoring_priority': risk_df[risk_df['risk_category'] == 'MEDIUM']['name'].tolist(),
                'stable_suppliers': risk_df[risk_df['risk_category'] == 'LOW']['name'].tolist()
            }
        }
        
        return insights
    
    def save_results(self, risk_df: pd.DataFrame, insights: Dict[str, Any]):
        """Save analysis results to files."""
        # Save risk analysis CSV
        risk_path = self.data_dir / "ai_risk_analysis.csv"
        risk_df.to_csv(risk_path, index=False)
        logger.info(f"Saved risk analysis to {risk_path}")
        
        # Save insights JSON
        insights_path = self.data_dir / "ai_insights.json"
        with open(insights_path, 'w') as f:
            json.dump(insights, f, indent=2)
        logger.info(f"Saved AI insights to {insights_path}")
        
        # Save summary report
        summary_path = self.data_dir / "ai_summary_report.txt"
        with open(summary_path, 'w') as f:
            f.write("SUPPLY CHAIN RISK ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {insights['analysis_summary']['analysis_timestamp']}\n")
            f.write(f"Total Suppliers Analyzed: {insights['analysis_summary']['total_suppliers']}\n")
            f.write(f"Average Risk Score: {insights['analysis_summary']['average_risk_score']:.1f}/100\n\n")
            
            f.write("RISK DISTRIBUTION:\n")
            f.write(f"High Risk: {insights['risk_distribution']['high_risk_count']} suppliers\n")
            f.write(f"Medium Risk: {insights['risk_distribution']['medium_risk_count']} suppliers\n")
            f.write(f"Low Risk: {insights['risk_distribution']['low_risk_count']} suppliers\n\n")
            
            f.write("TOP RISK SUPPLIERS:\n")
            for supplier in insights['top_risks']:
                f.write(f"- {supplier['name']}: {supplier['overall_risk_score']:.1f} ({supplier['risk_category']})\n")
            
            f.write("\nIMMEDIATE ACTIONS REQUIRED:\n")
            for supplier in insights['recommendations']['immediate_actions']:
                f.write(f"- {supplier}\n")
        
        logger.info(f"Saved summary report to {summary_path}")
    
    def run_analysis(self):
        """Run complete AI analysis."""
        logger.info("Starting AI-powered supply chain risk analysis...")
        
        # Load data
        data = self.load_data()
        
        # Calculate risk scores
        risk_df = self.calculate_risk_scores(data)
        
        # Generate insights
        insights = self.generate_ai_insights(risk_df)
        
        # Save results
        self.save_results(risk_df, insights)
        
        logger.info("AI analysis completed!")
        return risk_df, insights

if __name__ == "__main__":
    analyzer = SupplyChainAIAnalyzer()
    risk_df, insights = analyzer.run_analysis()
    
    print("\n" + "="*60)
    print("AI SUPPLY CHAIN RISK ANALYSIS RESULTS")
    print("="*60)
    print(f"Total Suppliers: {insights['analysis_summary']['total_suppliers']}")
    print(f"Average Risk Score: {insights['analysis_summary']['average_risk_score']:.1f}/100")
    print(f"High Risk: {insights['risk_distribution']['high_risk_count']}")
    print(f"Medium Risk: {insights['risk_distribution']['medium_risk_count']}")
    print(f"Low Risk: {insights['risk_distribution']['low_risk_count']}")
    print("\nTop Risk Suppliers:")
    for supplier in insights['top_risks']:
        print(f"  - {supplier['name']}: {supplier['overall_risk_score']:.1f} ({supplier['risk_category']})")
    print("\nFiles saved:")
    print("  - ai_risk_analysis.csv")
    print("  - ai_insights.json") 
    print("  - ai_summary_report.txt")
