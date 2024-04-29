from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime
from estimation_and_robustness import Estimation
from utils.utilities import Utilities
import utils.config
import numpy as np

class Strategy(ABC):


    @abstractmethod
    def generate_signals(self, market_data, compositions, date):

    
        previous_date = Utilities.get_rebalancing_date(date, step = config.STEP_VOL)
        
        # Calculer la volatilité de chaque actif financier
        volatilities = {ticker: Utilities.calculate_past_vol(market_data[ticker], date,previous_date) for ticker in compositions}

        # Trier les actifs financiers par volatilité décroissante
        sorted_assets = sorted(volatilities.keys(), key=lambda x: volatilities[x], reverse=False)

        # Diviser les actifs financiers en déciles
        deciles = [decile.tolist() for decile in np.array_split(sorted_assets, 10)]
        if date == config.END_DATE:
            next_date=date
        else:
            next_date = Utilities.get_rebalancing_date(date, step=1)
            
        return deciles, next_date, volatilities



    def generate_weights(self, decile, volatilities):
        
        if config.WEGHTS_TYPE.lower() == "equally weighted":
            return {ticker : 1/len(decile) for ticker in decile}


class LowVolatilityDecileStrategy(Strategy):


    def generate_signals(self, market_data: dict[str, pd.DataFrame], compositions : list(str), date : datetime) -> dict[str, float]:
        """
        Generate trading signals based on the low volatility decile strategy.

        Parameters:
        - financial_assets: A list of FinancialAsset objects.

        Returns:
        - A dictionary with FinancialAsset objects as keys and weights as values.
        """
        
        deciles, next_date, volatilities = super().generate_signals(market_data, compositions, date)
       
        
        # Sélectionner le décile avec la volatilité la plus faible
        low_volatility_decile = deciles[0]
        low_volatility_decile = Utilities.check_universe(low_volatility_decile, market_data, date, next_date)
        low_volatility_decile = super().generate_weights(low_volatility_decile, volatilities)
        
        
        return low_volatility_decile, next_date
    
    
class HighVolatilityDecileStrategy(Strategy):

    def generate_signals(self, market_data: dict[str, pd.DataFrame], compositions: list[str], date: datetime) -> dict[str, float]:
        """
        Generate trading signals based on the high volatility decile strategy.

        Parameters:
        - market_data: A dictionary of DataFrame containing market data for each financial asset.
        - compositions: A list of tickers representing the financial assets to consider.
        - date: The date for which to generate the signals.

        Returns:
        - A dictionary with tickers as keys and weights as values.
        """

        deciles, next_date, volatilities = super().generate_signals(market_data, compositions, date)
       
        # Sélectionner le décile avec la volatilité la plus élevée
        high_volatility_decile = deciles[-1]
        high_volatility_decile = Utilities.check_universe(high_volatility_decile, market_data, date, next_date)
        high_volatility_decile = super().generate_weights(high_volatility_decile, volatilities)
        return high_volatility_decile, next_date
    
    
class MidVolatilityDecileStrategy(Strategy):

    def generate_signals(self, market_data: dict[str, pd.DataFrame], compositions: list[str], date: datetime) -> dict[str, float]:
        """
        Generate trading signals based on the high volatility decile strategy.

        Parameters:
        - market_data: A dictionary of DataFrame containing market data for each financial asset.
        - compositions: A list of tickers representing the financial assets to consider.
        - date: The date for which to generate the signals.

        Returns:
        - A dictionary with tickers as keys and weights as values.
        """

        deciles, next_date, volatilities = super().generate_signals(market_data, compositions, date)
       
        # Sélectionner le décile avec la volatilité la plus élevée
        mid_volatility_decile = deciles[4]
        mid_volatility_decile = Utilities.check_universe(mid_volatility_decile, market_data, date, next_date)
        mid_volatility_decile = super().generate_weights(mid_volatility_decile, volatilities)
        return mid_volatility_decile, next_date


class VolatilityTimingStrategy(Strategy):  
    
    def __init__(self):
        self.switch = {config.START_DATE : False} 
    
          
    def generate_signals(self, market_data: dict[str, pd.DataFrame], compositions: list[str], date: datetime) -> dict[str, float]:
         
        low_decile, next_date = LowVolatilityDecileStrategy().generate_signals(market_data,compositions,date) 
        high_decile, next_date = HighVolatilityDecileStrategy().generate_signals(market_data,compositions,date)
        
        slope = self.__build_slope(market_data, low_decile, high_decile, date)
        
        if date!= config.END_DATE:
            self.switch.update({next_date : Estimation.is_slope_significantly_positive(slope,alpha=config.SLOPE_ALPHA)})
        
        
        if self.switch[date] == True :
            return high_decile, next_date
        return low_decile, next_date 
        
        
    @staticmethod
    def __build_slope(market_data, low_decile, high_decile, date):
        
        previous_date = Utilities.get_rebalancing_date(date, step = config.STEP_SLOPE)
        low_decile_returns = Utilities.get_ptf_returns(market_data, low_decile, previous_date, date)
        high_decile_returns = Utilities.get_ptf_returns(market_data, high_decile, previous_date, date)
        return high_decile_returns - low_decile_returns
        
        
        
if __name__ == "__main__":
    
    date = config.START_DATE
    previous_date = Utilities.get_rebalancing_date(date, step = config.STEP_VOL)
    compositions = Utilities.get_data_from_pickle("composition_par_date")
    global_market_data = Utilities.get_data_from_pickle("global_market_data")
    VolatilityTimingStrategy.generate_signals(global_market_data, compositions[date], date, previous_date)
    
    
    
    