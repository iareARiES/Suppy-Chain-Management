"""
Enhanced AI Model Integration using Google Gemini API
Analyzes all scraped data and provides comprehensive risk assessments with scores 0.00-1.00
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Any, Tuple
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiSupplyChainAnalyzer:
    """Enhanced AI-powered supply chain risk analyzer using Google Gemini API."""
    
    def __init__(self, data_dir: str = "data/outputs", api_key: str = None):
        self.data_dir = Path(data_dir)
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.analysis_results = {}
        logger.info("Gemini AI Analyzer initialized with API key")
    
    def load_all_data(self) -> Dict[str, Any]:
        """Load all available data from the pipeline."""
        data = {}
        
        # Load nodes
        nodes_path = self.data_dir / "nodes.json"
        if nodes_path.exists():
            with open(nodes_path, 'r') as f:
                nodes = json.load(f)
            data['nodes'] = pd.DataFrame(nodes)
            logger.info(f"Loaded {len(nodes)} nodes")
        
        # Load CSV files
        csv_files = {
            'social_events': 'social_events.csv',
            'news_events': 'news_events.csv', 
            'weather_anomalies': 'weather_anomalies.csv',
            'features_today': 'features_today.csv'
        }
        
        for key, filename in csv_files.items():
            csv_path = self.data_dir / filename
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                data[key] = df
                logger.info(f"Loaded {filename}: {len(df)} records")
            else:
                data[key] = pd.DataFrame()
                logger.warning(f"File not found: {filename}")
        
        # Load parquet files if available
        parquet_files = {
            'social_events_parquet': 'social_events.parquet',
            'news_events_parquet': 'news_events.parquet',
            'weather_anomalies_parquet': 'weather_anomalies.parquet',
            'extracted_events': 'extracted_events.parquet'
        }
        
        for key, filename in parquet_files.items():
            parquet_path = self.data_dir / filename
            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
                data[key] = df
                logger.info(f"Loaded {filename}: {len(df)} records")
        
        return data
    
    def prepare_data_summary(self, data: Dict[str, Any]) -> str:
        """Prepare a comprehensive data summary for Gemini analysis."""
        summary_parts = []
        
        # Nodes summary
        if 'nodes' in data and not data['nodes'].empty:
            nodes_df = data['nodes']
            summary_parts.append(f"SUPPLIERS ({len(nodes_df)} total):")
            summary_parts.append(f"- Countries: {nodes_df['country'].nunique() if 'country' in nodes_df.columns else 'N/A'}")
            summary_parts.append(f"- Categories: {nodes_df['category'].value_counts().to_dict() if 'category' in nodes_df.columns else 'N/A'}")
            summary_parts.append(f"- Tiers: {nodes_df['tier'].value_counts().to_dict() if 'tier' in nodes_df.columns else 'N/A'}")
            summary_parts.append("")
        
        # Social events summary
        if 'social_events' in data and not data['social_events'].empty:
            social_df = data['social_events']
            summary_parts.append(f"SOCIAL MEDIA EVENTS ({len(social_df)} total):")
            if 'platform' in social_df.columns:
                summary_parts.append(f"- Platforms: {social_df['platform'].value_counts().to_dict()}")
            if 'sentiment' in social_df.columns:
                summary_parts.append(f"- Sentiment distribution: {social_df['sentiment'].value_counts().to_dict()}")
            summary_parts.append("")
        
        # News events summary
        if 'news_events' in data and not data['news_events'].empty:
            news_df = data['news_events']
            summary_parts.append(f"NEWS EVENTS ({len(news_df)} total):")
            if 'source' in news_df.columns:
                summary_parts.append(f"- Sources: {news_df['source'].value_counts().head().to_dict()}")
            if 'sentiment_score' in news_df.columns:
                avg_sentiment = news_df['sentiment_score'].mean()
                summary_parts.append(f"- Average sentiment: {avg_sentiment:.2f}")
            summary_parts.append("")
        
        # Weather anomalies summary
        if 'weather_anomalies' in data and not data['weather_anomalies'].empty:
            weather_df = data['weather_anomalies']
            summary_parts.append(f"WEATHER ANOMALIES ({len(weather_df)} total):")
            if 'severity' in weather_df.columns:
                summary_parts.append(f"- Severity distribution: {weather_df['severity'].value_counts().to_dict()}")
            if 'event_type' in weather_df.columns:
                summary_parts.append(f"- Event types: {weather_df['event_type'].value_counts().to_dict()}")
            summary_parts.append("")
        
        # Features summary
        if 'features_today' in data and not data['features_today'].empty:
            features_df = data['features_today']
            summary_parts.append(f"ML FEATURES ({len(features_df)} total):")
            numeric_cols = features_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:5]:  # Show first 5 numeric columns
                avg_val = features_df[col].mean()
                summary_parts.append(f"- {col}: {avg_val:.2f} (avg)")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def analyze_with_gemini(self, data_summary: str, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini API to analyze supplier risk."""
        
        prompt = f"""
You are an expert supply chain risk analyst. Analyze the following data and provide a comprehensive risk assessment.

DATA OVERVIEW:
{data_summary}

SUPPLIER DETAILS:
- Name: {supplier_data.get('name', 'Unknown')}
- Country: {supplier_data.get('country', 'Unknown')}
- City: {supplier_data.get('city', 'Unknown')}
- Category: {supplier_data.get('category', 'Unknown')}
- Tier: {supplier_data.get('tier', 'Unknown')}

SUPPLIER-SPECIFIC DATA:
- Social Events: {supplier_data.get('social_count', 0)} events
- News Events: {supplier_data.get('news_count', 0)} articles
- Weather Anomalies: {supplier_data.get('weather_count', 0)} anomalies
- Recent News Headlines: {supplier_data.get('recent_headlines', 'None')}
- Social Media Activity: {supplier_data.get('social_activity', 'None')}
- Weather Events: {supplier_data.get('weather_events', 'None')}

Please provide a comprehensive risk analysis with the following format:

RISK_SCORE: [Provide a score from 0.00 to 1.00 where 0.00 = no risk, 1.00 = maximum risk]

RISK_CATEGORY: [LOW/MEDIUM/HIGH]

RISK_FACTORS:
- Factor 1: [Description and impact]
- Factor 2: [Description and impact]
- Factor 3: [Description and impact]

CORRELATION_ANALYSIS:
- [Explain correlations between different data sources]
- [Identify patterns and trends]

RECOMMENDATIONS:
- [Specific actionable recommendations]
- [Priority actions to take]

CONFIDENCE_LEVEL: [0.00 to 1.00 - how confident you are in this assessment]

EXPLANATION: [Detailed explanation of the risk assessment reasoning]
"""

        try:
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            logger.debug(f"Gemini response for {supplier_data.get('name', 'Unknown')}: {analysis_text[:200]}...")
            return self._parse_gemini_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_analysis(supplier_data)
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured data."""
        try:
            import re
            
            # Initialize with defaults
            analysis = {
                'risk_score': 0.5,
                'risk_category': 'MEDIUM',
                'confidence': 0.7,
                'risk_factors': 'Analysis in progress',
                'correlation_analysis': 'Correlation analysis pending',
                'recommendations': 'Continue monitoring',
                'explanation': 'Risk assessment completed'
            }
            
            # Try to extract risk score
            score_patterns = [
                r'RISK_SCORE:\s*(\d+\.?\d*)',
                r'risk score[:\s]*(\d+\.?\d*)',
                r'score[:\s]*(\d+\.?\d*)'
            ]
            
            for pattern in score_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    score = float(match.group(1))
                    if score > 1.0:
                        score = score / 100.0
                    analysis['risk_score'] = min(max(score, 0.0), 1.0)
                    break
            
            # Try to extract risk category
            category_patterns = [
                r'RISK_CATEGORY:\s*(LOW|MEDIUM|HIGH)',
                r'risk category[:\s]*(LOW|MEDIUM|HIGH)',
                r'category[:\s]*(LOW|MEDIUM|HIGH)'
            ]
            
            for pattern in category_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    analysis['risk_category'] = match.group(1).upper()
                    break
            
            # Try to extract confidence
            conf_patterns = [
                r'CONFIDENCE_LEVEL:\s*(\d+\.?\d*)',
                r'confidence[:\s]*(\d+\.?\d*)',
                r'confidence level[:\s]*(\d+\.?\d*)'
            ]
            
            for pattern in conf_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    conf = float(match.group(1))
                    if conf > 1.0:
                        conf = conf / 100.0
                    analysis['confidence'] = min(max(conf, 0.0), 1.0)
                    break
            
            # Extract sections using more flexible patterns
            sections = response_text.split('\n\n')
            for section in sections:
                section = section.strip()
                if re.search(r'risk factors?', section, re.IGNORECASE):
                    analysis['risk_factors'] = re.sub(r'risk factors?[:\s]*', '', section, flags=re.IGNORECASE).strip()
                elif re.search(r'correlation', section, re.IGNORECASE):
                    analysis['correlation_analysis'] = re.sub(r'correlation[:\s]*', '', section, flags=re.IGNORECASE).strip()
                elif re.search(r'recommendations?', section, re.IGNORECASE):
                    analysis['recommendations'] = re.sub(r'recommendations?[:\s]*', '', section, flags=re.IGNORECASE).strip()
                elif re.search(r'explanation', section, re.IGNORECASE):
                    analysis['explanation'] = re.sub(r'explanation[:\s]*', '', section, flags=re.IGNORECASE).strip()
            
            # If we couldn't parse much, try to infer from the overall text
            if analysis['risk_score'] == 0.5 and analysis['risk_category'] == 'MEDIUM':
                # Look for risk indicators in the text
                high_risk_words = ['high', 'severe', 'critical', 'urgent', 'dangerous', 'risky']
                low_risk_words = ['low', 'minimal', 'safe', 'stable', 'secure']
                
                text_lower = response_text.lower()
                high_count = sum(1 for word in high_risk_words if word in text_lower)
                low_count = sum(1 for word in low_risk_words if word in text_lower)
                
                if high_count > low_count:
                    analysis['risk_score'] = 0.7
                    analysis['risk_category'] = 'HIGH'
                elif low_count > high_count:
                    analysis['risk_score'] = 0.3
                    analysis['risk_category'] = 'LOW'
            
            logger.debug(f"Parsed analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            return self._fallback_analysis({})
    
    def _fallback_analysis(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when Gemini API fails."""
        logger.warning("Using fallback analysis due to API error")
        
        # Simple heuristic-based analysis
        social_count = supplier_data.get('social_count', 0)
        news_count = supplier_data.get('news_count', 0)
        weather_count = supplier_data.get('weather_count', 0)
        
        # Calculate basic risk score
        risk_score = min((social_count * 0.1 + news_count * 0.15 + weather_count * 0.2), 1.0)
        
        if risk_score >= 0.7:
            category = 'HIGH'
        elif risk_score >= 0.4:
            category = 'MEDIUM'
        else:
            category = 'LOW'
        
        return {
            'risk_score': risk_score,
            'risk_category': category,
            'confidence': 0.6,
            'risk_factors': f'Social events: {social_count}, News: {news_count}, Weather: {weather_count}',
            'correlation_analysis': 'Basic correlation analysis - multiple data sources indicate risk factors',
            'recommendations': 'Monitor supplier closely and prepare contingency plans' if category == 'HIGH' else 'Continue regular monitoring',
            'explanation': f'Risk assessment based on {social_count} social events, {news_count} news articles, and {weather_count} weather anomalies'
        }
    
    def get_supplier_specific_data(self, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract supplier-specific data for analysis."""
        supplier_data = {
            'node_id': node_id,
            'social_count': 0,
            'news_count': 0,
            'weather_count': 0,
            'recent_headlines': [],
            'social_activity': [],
            'weather_events': []
        }
        
        # Get node info
        if 'nodes' in data and not data['nodes'].empty:
            node_info = data['nodes'][data['nodes']['node_id'] == node_id]
            if not node_info.empty:
                supplier_data.update(node_info.iloc[0].to_dict())
        
        # Count social events
        if 'social_events' in data and not data['social_events'].empty:
            social_df = data['social_events']
            if 'node_id' in social_df.columns:
                node_social = social_df[social_df['node_id'] == node_id]
                supplier_data['social_count'] = len(node_social)
                if 'text' in node_social.columns:
                    supplier_data['social_activity'] = node_social['text'].head(3).tolist()
        
        # Count news events (match by supplier name)
        if 'news_events' in data and not data['news_events'].empty:
            news_df = data['news_events']
            supplier_name = supplier_data.get('name', '').lower()
            if supplier_name and 'headline' in news_df.columns:
                name_matches = news_df[news_df['headline'].str.contains(supplier_name, case=False, na=False)]
                supplier_data['news_count'] = len(name_matches)
                supplier_data['recent_headlines'] = name_matches['headline'].head(3).tolist()
        
        # Count weather anomalies
        if 'weather_anomalies' in data and not data['weather_anomalies'].empty:
            weather_df = data['weather_anomalies']
            if 'node_id' in weather_df.columns:
                node_weather = weather_df[weather_df['node_id'] == node_id]
                supplier_data['weather_count'] = len(node_weather)
                if 'event_type' in node_weather.columns:
                    supplier_data['weather_events'] = node_weather['event_type'].tolist()
        
        return supplier_data
    
    def analyze_all_suppliers(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Analyze all suppliers using Gemini AI."""
        logger.info("Starting comprehensive Gemini AI analysis...")
        
        if 'nodes' not in data or data['nodes'].empty:
            logger.error("No nodes data available for analysis")
            return pd.DataFrame()
        
        data_summary = self.prepare_data_summary(data)
        results = []
        
        nodes_df = data['nodes']
        total_suppliers = len(nodes_df)
        
        for idx, (_, node) in enumerate(nodes_df.iterrows()):
            node_id = node['node_id']
            logger.info(f"Analyzing supplier {idx+1}/{total_suppliers}: {node.get('name', node_id)}")
            
            # Get supplier-specific data
            supplier_data = self.get_supplier_specific_data(node_id, data)
            
            # Analyze with Gemini
            analysis = self.analyze_with_gemini(data_summary, supplier_data)
            
            # Combine with node data
            result = {
                'node_id': node_id,
                'name': node.get('name', 'Unknown'),
                'country': node.get('country', 'Unknown'),
                'city': node.get('city', 'Unknown'),
                'category': node.get('category', 'Unknown'),
                'tier': node.get('tier', 'Unknown'),
                'lat': node.get('lat', 0),
                'lon': node.get('lon', 0),
                
                # Gemini analysis results
                'gemini_risk_score': analysis['risk_score'],
                'gemini_risk_category': analysis['risk_category'],
                'gemini_confidence': analysis['confidence'],
                'gemini_risk_factors': analysis['risk_factors'],
                'gemini_correlation_analysis': analysis['correlation_analysis'],
                'gemini_recommendations': analysis['recommendations'],
                'gemini_explanation': analysis['explanation'],
                
                # Data counts
                'social_events_count': supplier_data['social_count'],
                'news_events_count': supplier_data['news_count'],
                'weather_anomalies_count': supplier_data['weather_count'],
                
                # Timestamps
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'gemini_ai'
            }
            
            results.append(result)
        
        return pd.DataFrame(results)
    
    def generate_comprehensive_insights(self, analysis_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive insights from Gemini analysis."""
        if analysis_df.empty:
            return {}
        
        insights = {
            'analysis_summary': {
                'total_suppliers': len(analysis_df),
                'high_risk_suppliers': len(analysis_df[analysis_df['gemini_risk_category'] == 'HIGH']),
                'medium_risk_suppliers': len(analysis_df[analysis_df['gemini_risk_category'] == 'MEDIUM']),
                'low_risk_suppliers': len(analysis_df[analysis_df['gemini_risk_category'] == 'LOW']),
                'average_risk_score': analysis_df['gemini_risk_score'].mean(),
                'average_confidence': analysis_df['gemini_confidence'].mean(),
                'highest_risk_supplier': analysis_df.loc[analysis_df['gemini_risk_score'].idxmax(), 'name'] if not analysis_df.empty else None,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'risk_distribution': {
                'high_risk_count': len(analysis_df[analysis_df['gemini_risk_category'] == 'HIGH']),
                'medium_risk_count': len(analysis_df[analysis_df['gemini_risk_category'] == 'MEDIUM']),
                'low_risk_count': len(analysis_df[analysis_df['gemini_risk_category'] == 'LOW'])
            },
            'top_risks': analysis_df.nlargest(5, 'gemini_risk_score')[['name', 'gemini_risk_score', 'gemini_risk_category', 'gemini_confidence']].to_dict('records') if not analysis_df.empty else [],
            'recommendations': {
                'immediate_actions': analysis_df[analysis_df['gemini_risk_category'] == 'HIGH']['name'].tolist(),
                'monitoring_priority': analysis_df[analysis_df['gemini_risk_category'] == 'MEDIUM']['name'].tolist(),
                'stable_suppliers': analysis_df[analysis_df['gemini_risk_category'] == 'LOW']['name'].tolist()
            },
            'data_quality': {
                'suppliers_with_social_data': len(analysis_df[analysis_df['social_events_count'] > 0]),
                'suppliers_with_news_data': len(analysis_df[analysis_df['news_events_count'] > 0]),
                'suppliers_with_weather_data': len(analysis_df[analysis_df['weather_anomalies_count'] > 0])
            }
        }
        
        return insights
    
    def save_results(self, analysis_df: pd.DataFrame, insights: Dict[str, Any]):
        """Save Gemini analysis results."""
        # Save detailed analysis CSV
        analysis_path = self.data_dir / "gemini_risk_analysis.csv"
        analysis_df.to_csv(analysis_path, index=False)
        logger.info(f"Saved Gemini analysis to {analysis_path}")
        
        # Save insights JSON
        insights_path = self.data_dir / "gemini_insights.json"
        with open(insights_path, 'w') as f:
            json.dump(insights, f, indent=2)
        logger.info(f"Saved Gemini insights to {insights_path}")
        
        # Save summary report
        summary_path = self.data_dir / "gemini_summary_report.txt"
        with open(summary_path, 'w') as f:
            f.write("GEMINI AI SUPPLY CHAIN RISK ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis Date: {insights['analysis_summary']['analysis_timestamp']}\n")
            f.write(f"Total Suppliers Analyzed: {insights['analysis_summary']['total_suppliers']}\n")
            f.write(f"Average Risk Score: {insights['analysis_summary']['average_risk_score']:.3f}/1.00\n")
            f.write(f"Average Confidence: {insights['analysis_summary']['average_confidence']:.3f}/1.00\n\n")
            
            f.write("RISK DISTRIBUTION:\n")
            f.write(f"High Risk: {insights['risk_distribution']['high_risk_count']} suppliers\n")
            f.write(f"Medium Risk: {insights['risk_distribution']['medium_risk_count']} suppliers\n")
            f.write(f"Low Risk: {insights['risk_distribution']['low_risk_count']} suppliers\n\n")
            
            f.write("TOP RISK SUPPLIERS:\n")
            for supplier in insights['top_risks']:
                f.write(f"- {supplier['name']}: {supplier['gemini_risk_score']:.3f} ({supplier['gemini_risk_category']}) [Confidence: {supplier['gemini_confidence']:.3f}]\n")
            
            f.write("\nIMMEDIATE ACTIONS REQUIRED:\n")
            for supplier in insights['recommendations']['immediate_actions']:
                f.write(f"- {supplier}\n")
            
            f.write("\nDATA QUALITY METRICS:\n")
            f.write(f"- Suppliers with social data: {insights['data_quality']['suppliers_with_social_data']}\n")
            f.write(f"- Suppliers with news data: {insights['data_quality']['suppliers_with_news_data']}\n")
            f.write(f"- Suppliers with weather data: {insights['data_quality']['suppliers_with_weather_data']}\n")
        
        logger.info(f"Saved Gemini summary report to {summary_path}")
    
    def run_complete_analysis(self):
        """Run complete Gemini AI analysis."""
        logger.info("🚀 Starting Gemini AI-powered supply chain risk analysis...")
        
        # Load all data
        data = self.load_all_data()
        
        # Analyze all suppliers
        analysis_df = self.analyze_all_suppliers(data)
        
        # Generate insights
        insights = self.generate_comprehensive_insights(analysis_df)
        
        # Save results
        self.save_results(analysis_df, insights)
        
        logger.info("✅ Gemini AI analysis completed!")
        return analysis_df, insights

if __name__ == "__main__":
    analyzer = GeminiSupplyChainAnalyzer()
    analysis_df, insights = analyzer.run_complete_analysis()
    
    print("\n" + "="*70)
    print("GEMINI AI SUPPLY CHAIN RISK ANALYSIS RESULTS")
    print("="*70)
    print(f"Total Suppliers: {insights['analysis_summary']['total_suppliers']}")
    print(f"Average Risk Score: {insights['analysis_summary']['average_risk_score']:.3f}/1.00")
    print(f"Average Confidence: {insights['analysis_summary']['average_confidence']:.3f}/1.00")
    print(f"High Risk: {insights['risk_distribution']['high_risk_count']}")
    print(f"Medium Risk: {insights['risk_distribution']['medium_risk_count']}")
    print(f"Low Risk: {insights['risk_distribution']['low_risk_count']}")
    print("\nTop Risk Suppliers:")
    for supplier in insights['top_risks']:
        print(f"  - {supplier['name']}: {supplier['gemini_risk_score']:.3f} ({supplier['gemini_risk_category']}) [Confidence: {supplier['gemini_confidence']:.3f}]")
    print("\nFiles saved:")
    print("  - gemini_risk_analysis.csv")
    print("  - gemini_insights.json") 
    print("  - gemini_summary_report.txt")
