"""
Agent 7: Export and Report Generation
Export final features and generate comprehensive reports.
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from core.io import read_parquet, write_csv, write_json, write_text
from core.utils import now_utc

logger = logging.getLogger(__name__)


class ExportAgent:
    """Agent for exporting data and generating reports."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def run(self, features_df: pd.DataFrame) -> str:
        """
        Export features and generate reports.
        
        Args:
            features_df: DataFrame with computed features
            
        Returns:
            Path to the exported CSV file
        """
        logger.info("Starting export agent...")
        
        # Export features CSV
        csv_path = self._export_features_csv(features_df)
        
        # Generate summary report
        self._generate_summary_report(features_df)
        
        # Export metadata
        self._export_metadata(features_df)
        
        logger.info(f"Export agent completed. Exported to {csv_path}")
        return csv_path
    
    def _export_features_csv(self, features_df: pd.DataFrame) -> str:
        """Export features to CSV file."""
        # Ensure proper column order and formatting
        export_df = self._prepare_features_for_export(features_df)
        
        # Generate filename with timestamp
        timestamp = now_utc().strftime("%Y%m%d_%H%M%S")
        filename = f"features_{timestamp}.csv"
        output_path = self.data_dir / "outputs" / filename
        
        # Also create a "today" version for easy access
        today_path = self.data_dir / "outputs" / "features_today.csv"
        
        # Export both files
        write_csv(export_df, str(output_path))
        write_csv(export_df, str(today_path))
        
        logger.info(f"Exported features to {output_path} and {today_path}")
        return str(output_path)
    
    def _prepare_features_for_export(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features DataFrame for export."""
        # Create a copy to avoid modifying original
        export_df = features_df.copy()
        
        # Ensure all required columns exist
        required_columns = [
            'node_id', 'node_type', 'name', 'country', 'lat', 'lon', 'tier',
            'news_count_1d', 'news_count_7d', 'neg_tone_frac_3d',
            'weather_anomaly_7d', 'strike_flag_7d', 'avg_lead_time_days',
            'inventory_days', 'single_sourced', 'past_delay_days',
            'news_velocity', 'disruption_within_7d', 'days_to_disruption'
        ]
        
        # Add missing columns with default values
        for col in required_columns:
            if col not in export_df.columns:
                if col in ['news_count_1d', 'news_count_7d', 'weather_anomaly_7d', 
                          'strike_flag_7d', 'single_sourced', 'past_delay_days',
                          'disruption_within_7d', 'days_to_disruption']:
                    export_df[col] = 0
                elif col in ['neg_tone_frac_3d', 'news_velocity']:
                    export_df[col] = 0.0
                elif col in ['avg_lead_time_days', 'inventory_days']:
                    export_df[col] = None
                else:
                    export_df[col] = ''
        
        # Reorder columns
        export_df = export_df[required_columns]
        
        # Clean data
        export_df = self._clean_export_data(export_df)
        
        return export_df
    
    def _clean_export_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data for export."""
        # Handle NaN values
        df = df.fillna({
            'news_count_1d': 0,
            'news_count_7d': 0,
            'neg_tone_frac_3d': 0.0,
            'weather_anomaly_7d': 0,
            'strike_flag_7d': 0,
            'single_sourced': 0,
            'past_delay_days': 0,
            'news_velocity': 0.0,
            'disruption_within_7d': 0,
            'days_to_disruption': 0
        })
        
        # Ensure numeric columns are properly typed
        numeric_columns = [
            'lat', 'lon', 'tier', 'news_count_1d', 'news_count_7d',
            'neg_tone_frac_3d', 'weather_anomaly_7d', 'strike_flag_7d',
            'single_sourced', 'past_delay_days', 'news_velocity',
            'disruption_within_7d', 'days_to_disruption'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Ensure binary flags are 0 or 1
        binary_flags = ['weather_anomaly_7d', 'strike_flag_7d', 'single_sourced', 'disruption_within_7d']
        for flag in binary_flags:
            if flag in df.columns:
                df[flag] = df[flag].clip(0, 1).astype(int)
        
        # Ensure negative tone fraction is between 0 and 1
        if 'neg_tone_frac_3d' in df.columns:
            df['neg_tone_frac_3d'] = df['neg_tone_frac_3d'].clip(0, 1)
        
        return df
    
    def _generate_summary_report(self, features_df: pd.DataFrame) -> None:
        """Generate a summary report of the features."""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("SUPPLY CHAIN RISK ANALYSIS - FEATURE SUMMARY REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {now_utc().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report_lines.append("")
        
        # Dataset overview
        report_lines.append("DATASET OVERVIEW")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Suppliers: {len(features_df)}")
        report_lines.append(f"Countries: {features_df['country'].nunique() if 'country' in features_df.columns else 'N/A'}")
        report_lines.append(f"Node Types: {features_df['node_type'].nunique() if 'node_type' in features_df.columns else 'N/A'}")
        report_lines.append("")
        
        # Risk indicators
        if not features_df.empty:
            report_lines.append("RISK INDICATORS")
            report_lines.append("-" * 40)
            
            # News activity
            if 'news_count_7d' in features_df.columns:
                avg_news = features_df['news_count_7d'].mean()
                high_news = (features_df['news_count_7d'] > avg_news * 2).sum()
                report_lines.append(f"Average News Events (7d): {avg_news:.1f}")
                report_lines.append(f"Suppliers with High News Activity: {high_news}")
            
            # Negative sentiment
            if 'neg_tone_frac_3d' in features_df.columns:
                avg_neg_sentiment = features_df['neg_tone_frac_3d'].mean()
                high_neg_sentiment = (features_df['neg_tone_frac_3d'] > 0.5).sum()
                report_lines.append(f"Average Negative Sentiment: {avg_neg_sentiment:.2f}")
                report_lines.append(f"Suppliers with High Negative Sentiment: {high_neg_sentiment}")
            
            # Weather anomalies
            if 'weather_anomaly_7d' in features_df.columns:
                weather_affected = features_df['weather_anomaly_7d'].sum()
                report_lines.append(f"Suppliers Affected by Weather: {weather_affected}")
            
            # Strike flags
            if 'strike_flag_7d' in features_df.columns:
                strike_affected = features_df['strike_flag_7d'].sum()
                report_lines.append(f"Suppliers with Strike Activity: {strike_affected}")
            
            # News velocity
            if 'news_velocity' in features_df.columns:
                avg_velocity = features_df['news_velocity'].mean()
                high_velocity = (features_df['news_velocity'] > avg_velocity * 2).sum()
                report_lines.append(f"Average News Velocity: {avg_velocity:.2f}")
                report_lines.append(f"Suppliers with High News Velocity: {high_velocity}")
            
            report_lines.append("")
        
        # Top risk suppliers
        if not features_df.empty and 'news_velocity' in features_df.columns:
            report_lines.append("TOP RISK SUPPLIERS (by News Velocity)")
            report_lines.append("-" * 40)
            
            top_risks = features_df.nlargest(5, 'news_velocity')
            for i, (_, row) in enumerate(top_risks.iterrows(), 1):
                name = row.get('name', 'Unknown')
                velocity = row.get('news_velocity', 0)
                country = row.get('country', 'Unknown')
                report_lines.append(f"{i}. {name} ({country}) - Velocity: {velocity:.2f}")
            
            report_lines.append("")
        
        # Data quality metrics
        report_lines.append("DATA QUALITY METRICS")
        report_lines.append("-" * 40)
        
        if not features_df.empty:
            total_cells = len(features_df) * len(features_df.columns)
            missing_cells = features_df.isnull().sum().sum()
            completeness = ((total_cells - missing_cells) / total_cells) * 100
            
            report_lines.append(f"Data Completeness: {completeness:.1f}%")
            report_lines.append(f"Missing Values: {missing_cells}")
            
            # Column completeness
            report_lines.append("\nColumn Completeness:")
            for col in features_df.columns:
                missing = features_df[col].isnull().sum()
                completeness_pct = ((len(features_df) - missing) / len(features_df)) * 100
                report_lines.append(f"  {col}: {completeness_pct:.1f}%")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        # Write report
        report_content = "\n".join(report_lines)
        report_path = self.data_dir / "outputs" / "feature_summary_report.txt"
        write_text(report_content, str(report_path))
        
        logger.info(f"Generated summary report: {report_path}")
    
    def _export_metadata(self, features_df: pd.DataFrame) -> None:
        """Export metadata about the features."""
        metadata = {
            "export_timestamp": now_utc().isoformat(),
            "total_suppliers": len(features_df),
            "columns": list(features_df.columns),
            "data_types": features_df.dtypes.to_dict(),
            "feature_statistics": self._calculate_feature_statistics(features_df),
            "data_sources": [
                "supplier_registry",
                "news_events",
                "social_events", 
                "extracted_events",
                "weather_anomalies"
            ],
            "pipeline_version": "1.0.0"
        }
        
        metadata_path = self.data_dir / "outputs" / "features_metadata.json"
        write_json(metadata, str(metadata_path))
        
        logger.info(f"Exported metadata: {metadata_path}")
    
    def _calculate_feature_statistics(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistics for numeric features."""
        stats = {}
        
        numeric_columns = features_df.select_dtypes(include=['number']).columns
        
        for col in numeric_columns:
            if col in features_df.columns:
                stats[col] = {
                    "mean": float(features_df[col].mean()) if not features_df[col].isnull().all() else None,
                    "std": float(features_df[col].std()) if not features_df[col].isnull().all() else None,
                    "min": float(features_df[col].min()) if not features_df[col].isnull().all() else None,
                    "max": float(features_df[col].max()) if not features_df[col].isnull().all() else None,
                    "missing_count": int(features_df[col].isnull().sum())
                }
        
        return stats


def main():
    """Main function for running the export agent."""
    # Load features from parquet file
    features_path = Path("data/outputs/features_today.csv")
    
    if not features_path.exists():
        print("No features file found. Run the feature agent first.")
        return
    
    try:
        features_df = pd.read_csv(features_path)
        agent = ExportAgent()
        output_path = agent.run(features_df)
        print(f"Export agent completed. Exported to {output_path}")
    except Exception as e:
        print(f"Export failed: {e}")


if __name__ == "__main__":
    main()
