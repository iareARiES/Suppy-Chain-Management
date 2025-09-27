#!/usr/bin/env python3
"""
Complete end-to-end supply chain risk analysis pipeline.
From data collection to ML model output.
"""
import os
import sys
import logging
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set environment variables (fallback if not in .env)
# Note: These are example keys - replace with your actual API keys
os.environ['SERP_API_KEY'] = os.getenv('SERP_API_KEY', '')
os.environ['WEATHER_API_KEY'] = os.getenv('WEATHER_API_KEY', '')
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', '')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_complete_pipeline():
    """Run the complete end-to-end pipeline."""
    logger.info("🚀 STARTING COMPLETE SUPPLY CHAIN RISK ANALYSIS PIPELINE")
    logger.info("=" * 70)
    
    try:
        # Step 1: Data Collection Pipeline
        logger.info("📋 STEP 1: DATA COLLECTION PIPELINE")
        logger.info("-" * 50)
        
        from agents.agent0_registry import RegistryAgent
        from agents.agent2_news import NewsAgent
        from agents.agent5_weather import WeatherAgent
        from core.io import read_yaml
        
        # Build registry with enhanced geocoding
        logger.info("🗺️ Building supplier registry with Google Maps geocoding...")
        registry_agent = RegistryAgent()
        nodes = registry_agent.run()
        logger.info(f"✅ Registry: {len(nodes)} suppliers geocoded")
        
        # Fetch news data
        logger.info("📰 Fetching news data with SERP API...")
        allowlist = read_yaml("data/inputs/allowlist_regions.yaml")
        news_agent = NewsAgent()
        news_df = news_agent.run(nodes, allowlist)
        logger.info(f"✅ News: {len(news_df)} articles collected")
        
        # Fetch weather data
        logger.info("🌤️ Fetching weather data with WeatherAPI.com...")
        weather_agent = WeatherAgent()
        weather_df = weather_agent.run(nodes)
        logger.info(f"✅ Weather: {len(weather_df)} anomalies detected")
        
        # Step 2: Feature Engineering
        logger.info("\n🔧 STEP 2: FEATURE ENGINEERING")
        logger.info("-" * 50)
        
        from agents.agent6_features import FeatureAgent
        feature_agent = FeatureAgent()
        features_df = feature_agent.run(nodes)
        logger.info(f"✅ Features: {len(features_df)} ML-ready feature rows")
        
        # Step 3: Gemini AI Analysis
        logger.info("\n🤖 STEP 3: GEMINI AI RISK ANALYSIS")
        logger.info("-" * 50)
        
        from gemini_ai_analyzer import GeminiSupplyChainAnalyzer
        gemini_analyzer = GeminiSupplyChainAnalyzer()
        gemini_results = gemini_analyzer.run_complete_analysis()
        logger.info("✅ Gemini AI Analysis: Advanced risk assessment completed")
        
        # Step 3b: Legacy AI Analysis (backup)
        logger.info("\n🤖 STEP 3b: LEGACY AI ANALYSIS (BACKUP)")
        logger.info("-" * 50)
        
        from ai_model_analysis import SupplyChainAIAnalyzer
        ai_analyzer = SupplyChainAIAnalyzer()
        ai_results = ai_analyzer.run_analysis()
        logger.info("✅ Legacy AI Analysis: Backup risk assessment completed")
        
        # Step 4: ML Pipeline
        logger.info("\n🧠 STEP 4: ML PIPELINE EXECUTION")
        logger.info("-" * 50)
        
        # Change to parent directory to run ML pipeline
        parent_dir = Path(__file__).parent.parent
        ml_pipeline_path = parent_dir / "supplychain_ml_pipeline.py"
        features_path = Path("data/outputs/features_today.csv")
        
        if ml_pipeline_path.exists() and features_path.exists():
            logger.info("🔬 Running ML pipeline with generated features...")
            try:
                # Run ML pipeline inference
                result = subprocess.run([
                    sys.executable, str(ml_pipeline_path),
                    "--infer",
                    "--model_path", str(parent_dir / "supplychain_model.pth"),
                    "--live_data", str(features_path.absolute())
                ], capture_output=True, text=True, cwd=str(parent_dir))
                
                if result.returncode == 0:
                    logger.info("✅ ML Pipeline: Inference completed successfully")
                    logger.info("ML Output:")
                    print(result.stdout)
                else:
                    logger.warning(f"⚠️ ML Pipeline warning: {result.stderr}")
                    logger.info("ML Output (partial):")
                    print(result.stdout)
            except Exception as e:
                logger.warning(f"⚠️ ML Pipeline error: {e}")
                logger.info("Continuing with AI analysis results...")
        else:
            logger.info("ℹ️ ML pipeline files not found, using AI analysis results")
        
        # Step 5: Final Report Generation
        logger.info("\n📊 STEP 5: FINAL REPORT GENERATION")
        logger.info("-" * 50)
        
        # Display final results
        logger.info("🎯 FINAL RESULTS SUMMARY")
        logger.info("=" * 50)
        
        # Load and display results
        import pandas as pd
        
        # Try to load Gemini results first
        gemini_risk_df = None
        legacy_risk_df = None
        
        try:
            gemini_risk_df = pd.read_csv("data/outputs/gemini_risk_analysis.csv")
            print(f"\n🤖 GEMINI AI SUPPLY CHAIN RISK ANALYSIS RESULTS")
            print(f"Total Suppliers: {len(gemini_risk_df)}")
            print(f"Average Risk Score: {gemini_risk_df['gemini_risk_score'].mean():.3f}/1.00")
            print(f"Average Confidence: {gemini_risk_df['gemini_confidence'].mean():.3f}/1.00")
            
            # Risk distribution
            risk_counts = gemini_risk_df['gemini_risk_category'].value_counts()
            print(f"\n🔍 GEMINI RISK DISTRIBUTION:")
            for category, count in risk_counts.items():
                print(f"   {category}: {count} suppliers")
            
            # Top risks
            print(f"\n🔴 TOP RISK SUPPLIERS (GEMINI):")
            top_risks = gemini_risk_df.nlargest(5, 'gemini_risk_score')
            for _, row in top_risks.iterrows():
                print(f"   {row['name']}: {row['gemini_risk_score']:.3f} ({row['gemini_risk_category']}) [Confidence: {row['gemini_confidence']:.3f}]")
        except FileNotFoundError:
            print("\n⚠️ Gemini analysis results not found")
        
        # Load legacy results as backup
        try:
            legacy_risk_df = pd.read_csv("data/outputs/ai_risk_analysis.csv")
            print(f"\n📈 LEGACY AI SUPPLY CHAIN RISK ANALYSIS RESULTS")
            print(f"Total Suppliers: {len(legacy_risk_df)}")
            print(f"Average Risk Score: {legacy_risk_df['overall_risk_score'].mean():.1f}/100")
            
            # Risk distribution
            risk_counts = legacy_risk_df['risk_category'].value_counts()
            print(f"\n🔍 LEGACY RISK DISTRIBUTION:")
            for category, count in risk_counts.items():
                print(f"   {category}: {count} suppliers")
            
            # Top risks
            print(f"\n🔴 TOP RISK SUPPLIERS (LEGACY):")
            top_risks = legacy_risk_df.nlargest(5, 'overall_risk_score')
            for _, row in top_risks.iterrows():
                print(f"   {row['name']}: {row['overall_risk_score']:.1f} ({row['risk_category']})")
        except FileNotFoundError:
            print("\n⚠️ Legacy analysis results not found")
        
        # File outputs
        print(f"\n📁 OUTPUT FILES GENERATED:")
        output_files = [
            "data/outputs/gemini_risk_analysis.csv",
            "data/outputs/gemini_insights.json", 
            "data/outputs/gemini_summary_report.txt",
            "data/outputs/ai_risk_analysis.csv",
            "data/outputs/ai_insights.json", 
            "data/outputs/ai_summary_report.txt",
            "data/outputs/features_today.csv",
            "data/outputs/nodes.json",
            "data/outputs/news_events.parquet",
            "data/outputs/weather_anomalies.parquet"
        ]
        
        for file_path in output_files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")
        
        logger.info("\n🎉 COMPLETE PIPELINE EXECUTION FINISHED!")
        logger.info("=" * 70)
        
        # Prepare return data
        result_data = {
            "success": True,
            "gemini_analysis": None,
            "legacy_analysis": None
        }
        
        if gemini_risk_df is not None:
            result_data["gemini_analysis"] = {
                "suppliers": len(gemini_risk_df),
                "avg_risk": gemini_risk_df['gemini_risk_score'].mean(),
                "avg_confidence": gemini_risk_df['gemini_confidence'].mean(),
                "risk_distribution": gemini_risk_df['gemini_risk_category'].value_counts().to_dict(),
                "top_risks": gemini_risk_df.nlargest(5, 'gemini_risk_score')[['name', 'gemini_risk_score', 'gemini_risk_category', 'gemini_confidence']].to_dict('records')
            }
        
        if legacy_risk_df is not None:
            result_data["legacy_analysis"] = {
                "suppliers": len(legacy_risk_df),
                "avg_risk": legacy_risk_df['overall_risk_score'].mean(),
                "risk_distribution": legacy_risk_df['risk_category'].value_counts().to_dict(),
                "top_risks": legacy_risk_df.nlargest(5, 'overall_risk_score')[['name', 'overall_risk_score', 'risk_category']].to_dict('records')
            }
        
        return result_data
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = run_complete_pipeline()
    
    if result["success"]:
        print(f"\n✅ COMPLETE PIPELINE SUCCESS!")
        print(f"📊 Final Results:")
        
        if result.get('gemini_analysis'):
            gemini = result['gemini_analysis']
            print(f"🤖 Gemini AI Analysis:")
            print(f"   - Suppliers: {gemini['suppliers']}")
            print(f"   - Average Risk: {gemini['avg_risk']:.3f}/1.00")
            print(f"   - Average Confidence: {gemini['avg_confidence']:.3f}/1.00")
            print(f"   - Risk Distribution: {gemini['risk_distribution']}")
        
        if result.get('legacy_analysis'):
            legacy = result['legacy_analysis']
            print(f"📈 Legacy AI Analysis:")
            print(f"   - Suppliers: {legacy['suppliers']}")
            print(f"   - Average Risk: {legacy['avg_risk']:.1f}/100")
            print(f"   - Risk Distribution: {legacy['risk_distribution']}")
    else:
        print(f"\n❌ Pipeline failed: {result['error']}")
