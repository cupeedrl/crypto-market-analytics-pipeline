import psycopg2
import pandas as pd
from src.utils.config import Config
from datetime import datetime

class DatabaseService:
    """Database connection and query service"""
    
    @staticmethod
    def get_connection():
        return psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DB
        )
    
    @staticmethod
    def get_latest_prices():
        """Get latest prices for all coins"""
        conn = DatabaseService.get_connection()
        query = """
            SELECT DISTINCT ON (symbol) 
                symbol, current_price, price_change_percent, volume, processed_at
            FROM real_time_prices
            ORDER BY symbol, processed_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    @staticmethod
    def get_price_history(days=30):
        """Get historical price data"""
        conn = DatabaseService.get_connection()
        query = f"""
            SELECT symbol, processed_at, current_price, volume, price_change_percent
            FROM real_time_prices
            WHERE processed_at >= NOW() - INTERVAL '{days} days'
            ORDER BY symbol, processed_at
        """
        df = pd.read_sql_query(query, conn)
        df['processed_at'] = pd.to_datetime(df['processed_at'])
        conn.close()
        return df
    
    @staticmethod
    def get_pipeline_stats():
        """Get pipeline monitoring stats"""
        conn = DatabaseService.get_connection()
        
        query_records = """
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT symbol) as unique_symbols,
                   MAX(processed_at) as last_update
            FROM real_time_prices
            WHERE DATE(processed_at) = CURRENT_DATE
        """
        stats_df = pd.read_sql_query(query_records, conn)
        
        query_volume = """
            SELECT SUM(volume) as total_volume
            FROM real_time_prices
            WHERE processed_at >= NOW() - INTERVAL '24 hours'
        """
        volume_df = pd.read_sql_query(query_volume, conn)
        
        conn.close()
        
        return {
            'total_records': stats_df['total_records'].iloc[0] or 0,
            'unique_symbols': stats_df['unique_symbols'].iloc[0] or 0,
            'last_update': stats_df['last_update'].iloc[0],
            'total_volume': volume_df['total_volume'].iloc[0] or 0
        }