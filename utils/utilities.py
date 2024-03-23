from pandas_market_calendars import get_calendar
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import warnings

class Utilities:
    """
    Utility class
    """
    
    @staticmethod
    def create_rebalancing_calendar(start_date: datetime, end_date: datetime):
        """
        Create a rebalancing calendar with business days between the start and end date.
    
        Parameters:
        - start_date (datetime): The start date of the calendar.
        - end_date (datetime): The end date of the calendar.
      
        Returns:
        list[datetime]: A list of rebalancing dates from start_date to end_date
        Raises:
        ValueError: If start_date is after end_date.
        """
      
        # Création d'un calendrier de trading pour la bourse US
        nyse = mcal.get_calendar('NYSE')

        # Générer les dates de rebalancement à la fin de chaque mois
        rebalance_dates = nyse.valid_days(start_date=start_date, end_date=end_date)
        rebalance_dates = [date.to_pydatetime().date() for i, date in enumerate(rebalance_dates[:-1]) if rebalance_dates[i + 1].month != date.month]

        return rebalance_dates


    

    @staticmethod
    def get_rebalancing_date(date, step):
        """
        Calculate the rebalancing date by adding a specified number of months to the given date.
    
        Parameters:
        - date (datetime): The starting date for calculating the rebalancing date.
        - step (int): The number of months to add to the given date.
    
        Returns:
        datetime.date: The calculated rebalancing date.
        """
        # Ajoute ou soustrait le nombre de mois à la date de départ
        rebalancing_date = date + pd.DateOffset(months=step)
    
        # Récupère le dernier jour du mois pour la date calculée
        rebalancing_date = rebalancing_date + pd.offsets.MonthEnd(0)
        
        # # Convertir la date en datetime avec un fuseau horaire
        # rebalancing_datetime = datetime.combine(rebalancing_date, datetime.min.time())
        rebalancing_date=rebalancing_date.date()
        # Création d'un calendrier de trading pour la bourse US
        nyse = get_calendar('XNYS')
        valid_days_index = nyse.valid_days(start_date=(rebalancing_date-pd.Timedelta(days=3)), end_date=rebalancing_date)
        valid_days_list = [date.to_pydatetime().date() for date in valid_days_index]
        if not valid_days_list:
            return rebalancing_date
        
        while rebalancing_date not in valid_days_list:
            # Si la date calculée n'est pas un jour ouvré, ajustez-la jusqu'à obtenir un jour ouvré
            rebalancing_date -= pd.Timedelta(days=1)
        
        return rebalancing_date

    
    @staticmethod
    def check_universe(universe, market_data, date, next_date):
        """
        Check if the market data for each ticker in the universe is available between the given dates.
    
        Parameters:
        - universe (List[str]): List of ticker symbols representing the universe of assets.
        - market_data (Dict[str, pd.DataFrame]): Dictionary containing market data for each ticker.
        - date (datetime): The start date for checking market data availability.
        - next_date (datetime): The end date for checking market data availability.
    
        Returns:
        List[str]: List of ticker symbols for which market data is available between the given dates.
        """        
        return [ticker for ticker in universe if Utilities.check_data_between_dates(market_data[ticker], date, next_date)]
    
    @staticmethod
    def check_data_between_dates(df, start_date, end_date):
        """
        Check if there is non-NaN data between two dates in a DataFrame.
        
        Args:
        df (pd.DataFrame): DataFrame with dates as index.
        start_date (str): Start date (inclusive).
        end_date (str): End date (inclusive).
        
        Returns:
        bool: True if there is non-NaN data between the specified dates, False otherwise.
        """
        # Vérification si les dates existent dans l'index
        if start_date not in df.index or end_date not in df.index:
            return False
        
        # Vérification si des données existent entre les deux dates
        data_subset = df.loc[(df.index > start_date) & (df.index < end_date)]
        if not data_subset.empty:
            return True
        return False
            
    @staticmethod
    def calculate_past_vol(price_history : pd.DataFrame, date : datetime,previous_date)->float:
        """
        Calculate the past 6 months volatility based on the provided price history dataframe.
    
        Parameters:
        - price_history (pd.DataFrame): DataFrame containing historical prices.
        - date (datetime): The date for which volatility is calculated.
    
        Returns:
        float: The calculated volatility over the past 6 months.
        """       
        
        price_history = price_history.loc[previous_date:date]
        
        # Convertir les prix historiques en rendements quotidiens
        returns = price_history.iloc[:,0].pct_change().dropna()

        # Calculer la volatilité à partir des rendements
        volatility = np.std(returns)

        return volatility
    
    @staticmethod
    def get_data_from_pickle(file_name: str):
        """
        Load data from a pickle file located in the 'data' directory.

        Parameters:
        - file_name (str): Name of the pickle file to load, without the extension.

        Returns:
        Any: The data loaded from the pickle file.
        """
        # Construit le chemin du fichier en incluant le dossier 'data'
        # Assurez-vous que le dossier 'data' est au même niveau que ce script,
        # sinon ajustez le chemin d'accès selon votre structure de dossiers.
        file_path = f"data/{file_name}.pkl"

        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        return data
