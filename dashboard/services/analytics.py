import pandas as pd
import numpy as np
from scipy import stats

class AnalyticsService:
    """Data analytics and statistical analysis service"""
    
    @staticmethod
    def calculate_correlation_matrix(df):
        """Calculate price correlation between coins"""
        try:
            if df.empty:
                print("DEBUG: DataFrame is empty")
                return None
            
            if df['symbol'].nunique() < 2:
                print(f"DEBUG: Only {df['symbol'].nunique()} unique symbol(s)")
                return None
            
            print(f"DEBUG: Input shape: {df.shape}")
            print(f"DEBUG: Unique symbols: {df['symbol'].unique()}")
            
            # Pivot the data
            pivot_df = df.pivot_table(
                index='processed_at', 
                columns='symbol', 
                values='current_price',
                aggfunc='first'
            )
            
            print(f"DEBUG: Pivot shape: {pivot_df.shape}")
            print(f"DEBUG: Pivot columns: {pivot_df.columns.tolist()}")
            
            # Drop columns with too many NaN (keep if > 50% data)
            pivot_df = pivot_df.dropna(axis=1, thresh=len(pivot_df) * 0.5)
            
            print(f"DEBUG: After dropna shape: {pivot_df.shape}")
            
            if pivot_df.shape[1] < 2:
                print(f"DEBUG: Less than 2 columns after dropna")
                return None
            
            # Calculate percentage changes
            returns = pivot_df.pct_change().dropna()
            
            print(f"DEBUG: Returns shape: {returns.shape}")
            
            if returns.empty:
                print("DEBUG: Returns is empty")
                return None
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            print(f"DEBUG: Correlation matrix:\n{corr_matrix}")
            
            return corr_matrix.fillna(0)
            
        except Exception as e:
            print(f"ERROR in calculate_correlation_matrix: {e}")
            import traceback
            traceback.print_exc()
            return None
        
@staticmethod
def calculate_volatility_metrics(df):
    """Calculate volatility and risk metrics"""
    metrics = []
    
    for symbol in df['symbol'].unique():
        coin_df = df[df['symbol'] == symbol].copy()
        
        if len(coin_df) < 10:
            continue
        
        # Calculate daily returns (in percentage)
        returns = coin_df['current_price'].pct_change().dropna() * 100
        
        if len(returns) < 5:
            continue
        
        # Annualize (assuming hourly data, 24*365 = 8760 hours/year)
        annual_factor = np.sqrt(8760)  # For hourly data
        
        avg_return = returns.mean()
        volatility = returns.std()
        
        # Sharpe ratio (annualized, assuming risk-free rate = 0)
        sharpe = (avg_return / volatility * annual_factor) if volatility != 0 else 0
        
        # Max drawdown
        cummax = coin_df['current_price'].cummax()
        drawdown = (cummax - coin_df['current_price']) / cummax
        max_dd = drawdown.max() * 100  # Convert to percentage
        
        metrics.append({
            'symbol': symbol,
            'avg_return': avg_return,  # Already in percentage
            'volatility': volatility,  # Already in percentage
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd
        })
    
    return pd.DataFrame(metrics)
@staticmethod
def detect_anomalies(df, threshold=3.5):
    """Detect anomalies using daily aggregated data"""
    anomalies = []
    
    # Aggregate by date and symbol
    daily_data = df.groupby([
        df['processed_at'].dt.date, 
        'symbol'
    ]).agg({
        'price_change_percent': ['mean', 'std', 'count']
    }).reset_index()
    
    daily_data.columns = ['date', 'symbol', 'avg_change', 'std_change', 'count']
    
    # Filter out days with too little data
    daily_data = daily_data[daily_data['count'] > 10]
    
    # Calculate z-scores per symbol
    for symbol in daily_data['symbol'].unique():
        symbol_data = daily_data[daily_data['symbol'] == symbol].copy()
        
        if len(symbol_data) < 10:
            continue
        
        # Calculate z-score
        mean = symbol_data['avg_change'].mean()
        std = symbol_data['avg_change'].std()
        
        if std == 0:
            continue
        
        symbol_data['z_score'] = np.abs((symbol_data['avg_change'] - mean) / std)
        
        # Filter anomalies
        anomalies_df = symbol_data[symbol_data['z_score'] > threshold]
        
        for _, row in anomalies_df.iterrows():
            anomalies.append({
                'symbol': symbol,
                'date': row['date'],
                'z_score': row['z_score']
            })
    
    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()