"""
Data export utilities - CSV, JSON, Excel
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JobExporter:
    """Export job data to various formats"""
    
    def __init__(self, export_dir: str = 'exports'):
        """
        Initialize exporter
        
        Args:
            export_dir: Directory to save exports
        """
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_csv(self, jobs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export jobs to CSV
        
        Args:
            jobs: List of job dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'jobs_export_{timestamp}.csv'
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(jobs)
            
            # Handle JSONB skills column
            if 'skills' in df.columns:
                df['skills'] = df['skills'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else x
                )
            
            # Select relevant columns
            columns_order = [
                'id', 'title', 'company', 'location', 'city', 
                'salary_min', 'salary_max', 'salary_text',
                'description', 'skills', 'experience_level', 
                'job_type', 'is_remote', 'posted_date', 
                'source_url', 'site_source'
            ]
            
            # Only include columns that exist
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]
            
            # Export
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(jobs)} jobs to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def export_to_json(self, jobs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export jobs to JSON
        
        Args:
            jobs: List of job dictionaries
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'jobs_export_{timestamp}.json'
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            # Clean data for JSON serialization
            clean_jobs = []
            for job in jobs:
                clean_job = {}
                for key, value in job.items():
                    # Convert datetime/date to string
                    if isinstance(value, (datetime, pd.Timestamp)):
                        clean_job[key] = value.isoformat()
                    elif pd.isna(value):
                        clean_job[key] = None
                    else:
                        clean_job[key] = value
                clean_jobs.append(clean_job)
            
            # Export with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'total_jobs': len(clean_jobs),
                    'jobs': clean_jobs
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(jobs)} jobs to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise
    
    def export_to_excel(self, jobs: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Export jobs to Excel (XLSX)
        
        Args:
            jobs: List of job dictionaries
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'jobs_export_{timestamp}.xlsx'
        
        filepath = os.path.join(self.export_dir, filename)
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(jobs)
            
            # Handle JSONB skills
            if 'skills' in df.columns:
                df['skills'] = df['skills'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else x
                )
            
            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main jobs sheet
                df.to_excel(writer, sheet_name='Jobs', index=False)
                
                # Summary statistics sheet
                summary = {
                    'Total Jobs': len(df),
                    'Unique Companies': df['company'].nunique() if 'company' in df.columns else 0,
                    'Unique Cities': df['city'].nunique() if 'city' in df.columns else 0,
                    'Remote Jobs': df['is_remote'].sum() if 'is_remote' in df.columns else 0,
                    'Avg Salary Min': df['salary_min'].mean() if 'salary_min' in df.columns else 0,
                    'Avg Salary Max': df['salary_max'].mean() if 'salary_max' in df.columns else 0,
                }
                
                summary_df = pd.DataFrame(list(summary.items()), columns=['Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Exported {len(jobs)} jobs to Excel: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise
    
    def generate_summary_report(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from job data
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not jobs:
            return {}
        
        df = pd.DataFrame(jobs)
        
        summary = {
            'total_jobs': len(df),
            'date_range': {
                'earliest': df['posted_date'].min() if 'posted_date' in df.columns else None,
                'latest': df['posted_date'].max() if 'posted_date' in df.columns else None,
            },
            'by_site': df.groupby('site_source').size().to_dict() if 'site_source' in df.columns else {},
            'by_city': df.groupby('city').size().nlargest(10).to_dict() if 'city' in df.columns else {},
            'by_company': df.groupby('company').size().nlargest(10).to_dict() if 'company' in df.columns else {},
            'remote_stats': {
                'remote': int(df['is_remote'].sum()) if 'is_remote' in df.columns else 0,
                'hybrid': int(df['is_hybrid'].sum()) if 'is_hybrid' in df.columns else 0,
                'onsite': int(df['is_onsite'].sum()) if 'is_onsite' in df.columns else 0,
            },
            'salary_stats': {
                'avg_min': float(df['salary_min'].mean()) if 'salary_min' in df.columns else 0,
                'avg_max': float(df['salary_max'].mean()) if 'salary_max' in df.columns else 0,
                'median_min': float(df['salary_min'].median()) if 'salary_min' in df.columns else 0,
                'median_max': float(df['salary_max'].median()) if 'salary_max' in df.columns else 0,
            }
        }
        
        return summary
