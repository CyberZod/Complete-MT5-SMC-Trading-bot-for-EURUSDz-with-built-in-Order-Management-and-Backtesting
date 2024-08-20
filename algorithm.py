import MetaTrader5 as mt5
import time
import pandas as pd
import schedule
from datetime import datetime, timezone, timedelta

# Account credentials
login = 81555550 #insert login here
server = 'Exness-MT5Trial10' #insert actual server name here
password = 'xyriehsje' #insert actual pwd here

symbols_to_trade = ["EURUSDz", "GBPUSDz"] 

# Initialize MetaTrader 5
if not mt5.initialize(login=login, server=server, password=password):
    print("initialize() failed, error code =", mt5.last_error())
    quit()

def find_bullish_wick_candle(df):
    latest_candle = len(df) - 2
    for i in range(latest_candle - 1, -1, -1):
        if df['low'][latest_candle] < df['low'][i] and df['close'][latest_candle] >= df['low'][i]:

            # Check if candle i is a bullish outside bar
            outside_bar = df['high'][i] > df['high'][i + 1] and df['low'][i] < df['low'][i + 1]
            # Check if candle i is a bullish double wick
            double_wick = df['low'][i] < df['low'][i - 1] and df['close'][i] > df['low'][i - 1]
            if outside_bar or double_wick:
                if all(df['low'][k] > df['low'][latest_candle] and df['close'][k] >= df['low'][i] for k in range(i + 1, latest_candle)):
                    return latest_candle, None, i
                
            # Check if candle i is a bullish order block
            imbalance_found = False
            fvg_found = False
            if i + 1 < latest_candle and df['high'][i - 1] >= df['low'][i + 1] and df['high'][i + 1] > df['high'][i] and df['close'][i + 1] > df['high'][i]:
                imbalance_found = True
                k = i + 1
                ob_high = df['high'][k - 1]
                for l in range(k + 1, len(df)):
                    if df['high'][l] > df['high'][k] and df['low'][l] > df['high'][i]:
                        if all(df['low'][m] > ob_high for m in range(k + 1, l + 1)):
                            fvg_found = True
                            break
            if imbalance_found and fvg_found:
                if all(df['low'][k] > df['low'][latest_candle] and df['close'][k] >= df['low'][i] for k in range(i + 1, latest_candle)):
                    return latest_candle, i, None

    return None, None, None  # Return None if no suitable candle is found

def find_bearish_wick_candle(df):
    latest_candle = len(df) - 2
    for i in range(latest_candle - 1, -1, -1):
        if df['high'][latest_candle] > df['high'][i] and df['close'][latest_candle] <= df['high'][i]:

            # Check if candle i is a bearish outside bar
            outside_bar = df['high'][i] > df['high'][i + 1] and df['low'][i] < df['low'][i + 1]
            # Check if candle i is a bearish double wick
            double_wick = df['high'][i] > df['high'][i - 1] and df['close'][i] < df['high'][i - 1]
            if outside_bar or double_wick:
                if all(df['high'][k] < df['high'][latest_candle] and df['close'][k] <= df['high'][i] for k in range(i + 1, latest_candle)):
                    return latest_candle, None, i
                
            # Check if candle i is a bearish order block
            imbalance_found = False
            fvg_found = False
            if i + 1 < latest_candle and df['low'][i - 1] <= df['high'][i + 1] and df['low'][i + 1] < df['low'][i] and df['close'][i + 1] < df['low'][i]:
                imbalance_found = True
                k = i + 1
                ob_low = df['low'][k - 1]
                for l in range(k + 1, len(df)):
                    if df['low'][l] < df['low'][k] and df['high'][l] < df['low'][i]:
                        if all(df['high'][m] < ob_low for m in range(k + 1, l + 1)):
                            fvg_found = True
                            break
            if imbalance_found and fvg_found:
                if all(df['close'][k] <= df['high'][i] and df['high'][k] < df['high'][latest_candle] for k in range(i + 1, latest_candle)):
                    return latest_candle, i, None

    return None, None, None  # Return None if no suitable candle is found

def find_bullish_pullback(df, wick_index):
    
    if wick_index <= 0 or wick_index >= len(df):
        return None, None
    pivot_indices = []
    pullback_indices = []

    for i in range(wick_index - 1, -1, -1):
        first_closing_candle = None
        second_closing_candle = None

        for j in range(i + 1, wick_index):
            if first_closing_candle is None:
                if df['close'][j] < df['low'][i]:
                    if all(df['low'][k] > df['close'][j] for k in range(i + 1, j)) and all(df['high'][k] <= df['high'][i] for k in range(i + 1, j + 1)):
                        first_closing_candle = j
            elif second_closing_candle is None:
                if df['close'][j] < df['low'][first_closing_candle]:
                    if all(df['low'][k] > df['close'][j] for k in range(first_closing_candle + 1, j)) and all(df['high'][k] <= df['high'][i] for k in range(first_closing_candle + 1, j + 1)):
                        second_closing_candle = j
                        break

        if first_closing_candle is not None and second_closing_candle is not None:
            pivot_index = i
            pullback_index = second_closing_candle

            # Validate the pivot
            if (pivot_index > 0 and pivot_index < len(df) - 1 and
                df['high'][pivot_index] > df['high'][pivot_index - 1] and 
                df['high'][pivot_index] >= df['high'][pivot_index + 1] and 
                df['high'][pivot_index + 1] <= df['high'][pivot_index]):
                pivot_indices.append(pivot_index)
                pullback_indices.append(pullback_index)
    
    if not pivot_indices or not pullback_indices:
        return None, None
    else:
        return pivot_indices, pullback_indices


def find_bearish_pullback(df, wick_index):
    if wick_index <= 0 or wick_index >= len(df):
        return None, None
    
    pivot_indices = []
    pullback_indices = []


    for i in range(wick_index - 1, -1, -1):
        first_closing_candle = None
        second_closing_candle = None

        for j in range(i + 1, wick_index):
            if first_closing_candle is None:
                if df['close'][j] > df['high'][i]:
                    if all(df['high'][k] < df['close'][j] for k in range(i + 1, j)) and all(df['low'][k] >= df['low'][i] for k in range(i + 1, j + 1)):
                        first_closing_candle = j
            elif second_closing_candle is None:
                if df['close'][j] > df['high'][first_closing_candle]:
                    if all(df['high'][k] < df['close'][j] for k in range(first_closing_candle + 1, j)) and all(df['low'][k] >= df['low'][i] for k in range(first_closing_candle + 1, j + 1)):
                        second_closing_candle = j
                        break

        if first_closing_candle is not None and second_closing_candle is not None:
            pivot_index = i
            pullback_index = second_closing_candle

            # Validate the pivot
            if (pivot_index > 0 and pivot_index < len(df) - 1 and
                df['low'][pivot_index] < df['low'][pivot_index - 1] and 
                df['low'][pivot_index] <= df['low'][pivot_index + 1] and 
                df['low'][pivot_index + 1] >= df['low'][pivot_index]):
                pivot_indices.append(pivot_index)
                pullback_indices.append(pullback_index)

    if not pivot_indices or not pullback_indices:
        return None, None
    else:
        return pivot_indices, pullback_indices

def validate_bullish_break(df, wick_index, pullback_indices, pivot_indices):
    break_list = []
    final_pullback_low_list = []
    final_pullback_low_index_list = []

    for pullback_index, pivot_index in zip(pullback_indices, pivot_indices):
        pullback_low = df['low'][pullback_index]
        valid_break_attempted = False
        final_pullback_low = pullback_low
        break_candle = None
        final_pullback_low_index = None
        
        for i in range(pullback_index + 1, wick_index):
            if df['high'][i] > df['high'][pivot_index]:
                final_pullback_low = min(df['low'][pullback_index:i])
                final_pullback_low_index = df['low'][pullback_index:i].idxmin()
                if df['close'][i] > df['high'][pivot_index]:
                    break_candle = i 
                    # Store the index of the valid break
                    break
                else:
                    valid_break_attempted = True  # Mark that a break attempt has been made
                    pivot_index = i  # Update the pivot_index to the current candle

            if valid_break_attempted and df['low'][i] < final_pullback_low:
                break_candle = None  # Invalidate if a candle goes below the pullback low after an invalid break attempt
                final_pullback_low_index = None
                break
        
        if break_candle is not None:
            if check_opposite_bear(df, pivot_index, final_pullback_low_index) is None:
                break_list.append(break_candle)
                final_pullback_low_list.append(final_pullback_low)
                final_pullback_low_index_list.append(final_pullback_low_index)
        else:
            break_list.append(None)
            final_pullback_low_list.append(None)
            final_pullback_low_index_list.append(None)
    
    return break_list, final_pullback_low_index_list

        
def validate_bearish_break(df, wick_index, pullback_indices, pivot_indices):
    break_list = []
    final_pullback_high_list = []
    final_pullback_high_index_list = []

    for pullback_index, pivot_index in zip(pullback_indices, pivot_indices):
        pullback_high = df['high'][pullback_index]
        valid_break_attempted = False
        final_pullback_high = pullback_high
        break_candle = None
        final_pullback_high_index = None

        for i in range(pullback_index + 1, wick_index):
            if df['low'][i] < df['low'][pivot_index]:
                final_pullback_high = max(df['high'][pullback_index:i])
                final_pullback_high_index = df['high'][pullback_index:i].idxmax()
                if df['close'][i] < df['low'][pivot_index]:
                    break_candle = i  # Store the index of the valid break
                    break
                else:
                    valid_break_attempted = True  # Mark that a break attempt has been made
                    pivot_index = i  # Update the pivot_index to the current candle

            if valid_break_attempted and df['high'][i] > final_pullback_high:
                break_candle = None  # Invalidate if a candle goes above the pullback high after an invalid break attempt
                final_pullback_high_index = None
                break

        if break_candle is not None:
            if check_opposite_bull(df, pivot_index, final_pullback_high_index) is None:
                break_list.append(break_candle)
                final_pullback_high_list.append(final_pullback_high)
                final_pullback_high_index_list.append(final_pullback_high_index)
        else:
            break_list.append(None)
            final_pullback_high_list.append(None)
            final_pullback_high_index_list.append(None)
    
    return break_list, final_pullback_high_index_list

def find_bullish_impulse(df, pivot_indices, pullback_indices):
    bullish_impulse_list = []

    for pivot_index, pullback_index in zip(pivot_indices, pullback_indices):
      if pullback_index is not None:   
        pivot_high = df['high'][pivot_index]
        impulse_found = None

        for i in range(pivot_index - 1, -1, -1):
            if df['low'][i] < df['low'][pullback_index]:
                if check_opposite_bull(df, i, pivot_index) is None:
                    impulse_found = i
                    break
            if df['high'][i] >= pivot_high:
                impulse_found = None  # Invalidate the impulse if any high is >= pivot high
                break

        bullish_impulse_list.append(impulse_found)
      else:
        bullish_impulse_list.append(None)

    return bullish_impulse_list


def find_bearish_impulse(df, pivot_indices, pullback_indices):
    bearish_impulse_list = []

    for pivot_index, pullback_index in zip(pivot_indices, pullback_indices):
        if pullback_index is not None:
            pivot_low = df['low'][pivot_index]
            impulse_found = None

            for i in range(pivot_index - 1, -1, -1):
                if df['high'][i] > df['high'][pullback_index]:
                    if check_opposite_bear(df, i, pivot_index) is None:
                        impulse_found = i
                        break
                if df['low'][i] <= pivot_low:
                    impulse_found = None  # Invalidate the impulse if any low is <= pivot low
                    break

            bearish_impulse_list.append(impulse_found)
        else:
            bearish_impulse_list.append(None)

    return bearish_impulse_list

def determine_bullish_range(df, impulse_indices, current_pivot_highs):

    impulse_indices = impulse_indices[::-1]
    current_pivot_highs = current_pivot_highs[::-1]
    
    if impulse_indices is None or current_pivot_highs is None:
        raise ValueError("impulse_indices and current_pivot_highs cannot be None")

    if len(impulse_indices) != len(current_pivot_highs):
        raise ValueError("Length of impulse_indices and current_pivot_highs must be the same")

    for impulse_index, current_pivot_high in zip(impulse_indices, current_pivot_highs):
        if impulse_index is None or current_pivot_high is None:
            continue  # Skip any None values

        lower_boundary = None
        upper_boundary = current_pivot_high

        for i in range(impulse_index - 1, -1, -1):
            first_closing_candle = None
            second_closing_candle = None 

            # Valid break method
            valid_break_found = False
            for j in range(i + 1, impulse_index + 2):
                if first_closing_candle is None:
                    if df['close'][j] < df['low'][i]:
                        if all(df['low'][k] > df['close'][j] for k in range(i, j)):
                            if df['high'][i - 1] > df['high'][i] and df['low'][i - 1] < df['low'][i]:
                                continue
                            first_closing_candle = j
                if first_closing_candle is not None and second_closing_candle is None:
                    if df['close'][j] < df['low'][first_closing_candle]:
                        if all(df['low'][k] > df['close'][j] for k in range(first_closing_candle, j)):
                            second_closing_candle = j
                            valid_break_found = True
                            break
            
            if valid_break_found:
                temp_range_low_index = df['low'][i:impulse_index + 1].idxmin()
                lower_boundary = temp_range_low_index
                break

            # Sequence method
            if df['high'][i] > df['high'][current_pivot_high]:
                temp_range_low_index = df['low'][i:current_pivot_high + 1].idxmin()
                lower_boundary = temp_range_low_index
                break

        if lower_boundary is None:
            # Default to the impulse low if no valid range is found
            lower_boundary = impulse_index

    return lower_boundary, upper_boundary

def determine_bearish_range(df, impulse_indices, current_pivot_lows):

    impulse_indices = impulse_indices[::-1]
    current_pivot_lows = current_pivot_lows[::-1]

    if impulse_indices is None or current_pivot_lows is None:
        raise ValueError("impulse_indices and current_pivot_highs cannot be None")

    if len(impulse_indices) != len(current_pivot_lows):
        raise ValueError("Length of impulse_indices and current_pivot_highs must be the same")

    for impulse_index, current_pivot_low in zip(impulse_indices, current_pivot_lows):
    
        if impulse_index is None or current_pivot_low is None:
            continue  # Skip any None values

        upper_boundary = None
        lower_boundary = current_pivot_low

        for i in range(impulse_index - 1, -1, -1):
            first_closing_candle = None
            second_closing_candle = None

            # Valid break method
            valid_break_found = False
            for j in range(i + 1, impulse_index + 2):
                if first_closing_candle is None:
                    if df['close'][j] > df['high'][i]:
                        if all(df['high'][k] < df['close'][j] for k in range(i, j)):
                            if df['high'][i - 1] > df['high'][i] and df['low'][i - 1] < df['low'][i]:
                                continue
                            first_closing_candle = j
                if first_closing_candle is not None and second_closing_candle is None:
                    if df['close'][j] > df['high'][first_closing_candle]:
                        if all(df['high'][k] < df['close'][j] for k in range(first_closing_candle + 1, j)):
                            second_closing_candle = j
                            valid_break_found = True
                            break

            if valid_break_found:
                temp_range_high_index = df['high'][i:impulse_index + 1].idxmax()
                upper_boundary = temp_range_high_index
                break

            # Sequence method
            if df['low'][i] < df['low'][current_pivot_low]:
                temp_range_high_index = df['high'][i:current_pivot_low + 1].idxmax()
                upper_boundary = temp_range_high_index
                break

        if upper_boundary is None:
            # Default to the impulse high if no valid range is found
            upper_boundary = impulse_index


    return upper_boundary, lower_boundary

def find_bullish_entry_candle(df, ob_index, formation_index, wick_index, lower_boundary, symbol):
    pipette_value = mt5.symbol_info(symbol).point * 2
    
    entry_candle = None
    upper_boundary = None

    # Process for ob_index
    if ob_index is not None:
        new_upper_boundary = df['high'][lower_boundary:wick_index].idxmax()
        new_current_pivot_high = df['high'][new_upper_boundary]

        if ob_index <= new_upper_boundary and df['low'][wick_index] >= df['low'][lower_boundary]:
            if df['high'][wick_index] < new_current_pivot_high - pipette_value:
                if all(df['low'][k] > df['low'][wick_index] for k in range(new_upper_boundary, wick_index)):
                    if check_opposite_bear(df, new_upper_boundary, wick_index) is None:
                        entry_candle = wick_index
                        upper_boundary = new_upper_boundary
                        return entry_candle, upper_boundary

    # Process for formation_index
    if formation_index is not None:
        new_upper_boundary = df['high'][lower_boundary:wick_index].idxmax()
        new_current_pivot_high = df['high'][new_upper_boundary]

        # Ensure high of wick_index is lower than our new pivot high
        if df['high'][wick_index] < new_current_pivot_high - pipette_value and df['low'][wick_index] >= df['low'][lower_boundary]:
            # Ensure wick_index is lower than every candle between the new upper boundary and wick_index
            if all(df['low'][k] > df['low'][wick_index] for k in range(new_upper_boundary, wick_index)):
                if check_opposite_bear(df, new_upper_boundary, wick_index) is None:
                    entry_candle = wick_index
                    upper_boundary = new_upper_boundary
                    return entry_candle, upper_boundary

    return entry_candle, upper_boundary


def find_bearish_entry_candle(df, ob_index, formation_index, wick_index, upper_boundary, symbol):
    pipette_value = mt5.symbol_info(symbol).point * 2
    
    entry_candle = None
    lower_boundary = None

    # Process for ob_index
    if ob_index is not None:
        new_lower_boundary = df['low'][upper_boundary:wick_index].idxmin()
        new_current_pivot_low = df['low'][new_lower_boundary]

        if ob_index <= new_lower_boundary and df['high'][wick_index] <= df['high'][upper_boundary]:
            if df['low'][wick_index] > new_current_pivot_low + pipette_value:
                if all(df['high'][k] < df['high'][wick_index] for k in range(new_lower_boundary, wick_index)):
                    if check_opposite_bull(df, new_lower_boundary, wick_index) is None:
                        entry_candle = wick_index
                        lower_boundary = new_lower_boundary
                        return entry_candle, lower_boundary

    # Process for formation_index
    if formation_index is not None:
        new_lower_boundary = df['low'][upper_boundary:wick_index].idxmin()
        new_current_pivot_low = df['low'][new_lower_boundary]

        # Ensure low of wick_index is higher than our new pivot low 
        if df['low'][wick_index] > new_current_pivot_low + pipette_value and df['high'][wick_index] <= df['high'][upper_boundary]:
            # Ensure wick_index is higher than every candle between the new lower boundary and wick_index
            if all(df['high'][k] < df['high'][wick_index] for k in range(new_lower_boundary, wick_index)):
                if check_opposite_bull(df, new_lower_boundary, wick_index) is None:
                    entry_candle = wick_index
                    lower_boundary = new_lower_boundary
                    return entry_candle, lower_boundary

    return entry_candle, lower_boundary

def check_opposite_bear(df, max_high, wick_index):
    for i in range(max_high + 1, wick_index):
        first_closing_candle = None
        second_closing_candle = None
        valid_break_found = False  # Initialize this variable outside the inner loop

        for j in range(i + 1, wick_index):
            if first_closing_candle is None:
                if df['close'][j] > df['high'][i]:
                    if all(df['high'][k] < df['close'][j] for k in range(i, j)):
                        if df['high'][i - 1] > df['high'][i] and df['low'][i - 1] < df['low'][i]:
                            continue
                        first_closing_candle = j
            elif second_closing_candle is None:  # Changed to elif for clarity
                if df['close'][j] > df['high'][first_closing_candle]:
                    if all(df['high'][k] < df['close'][j] for k in range(first_closing_candle + 1, j)):
                        second_closing_candle = j
                        valid_break_found = True
                        break  # Exit the inner loop once we've found a valid break

        if valid_break_found:
            for m in range(i + 1, wick_index + 1):
                if (df['close'][m] < df['low'][i] and
                    df['low'][i] < df['low'][i - 1] and 
                    df['low'][i] <= df['low'][i + 1] and 
                    df['low'][i + 1] >= df['low'][i]):
                    return i
    
    return None  # Move this outside the loop to return None if no valid break is found
            

def check_opposite_bull(df, max_low, wick_index):


    for i in range(max_low + 1, wick_index):
        first_closing_candle = None
        second_closing_candle = None
        valid_break_found = False

        for j in range(i + 1, wick_index):
            if first_closing_candle is None:
                if df['close'][j] < df['low'][i]:
                    if all(df['low'][k] > df['close'][j] for k in range(i, j)):
                        if df['low'][i - 1] < df['low'][i] and df['high'][i - 1] > df['high'][i]:
                            continue
                        first_closing_candle = j
            if first_closing_candle is not None and second_closing_candle is None:
                if df['close'][j] < df['low'][first_closing_candle]:
                    if all(df['low'][k] > df['close'][j] for k in range(first_closing_candle + 1, j)):
                        second_closing_candle = j
                        valid_break_found = True
                        break
                    
        if valid_break_found:
            for m in range(i + 1, wick_index + 1):
                if (df['close'][m] > df['high'][i] and
                    df['high'][i] > df['high'][i - 1] and 
                    df['high'][i] >= df['high'][i + 1] and 
                    df['high'][i + 1] <= df['high'][i]):
                    return i

    return None

def place_wick_orders():
    for symbol in symbols_to_trade:
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            if rates is None:
                print(f"Error: Unable to fetch rates for {symbol}")
                continue
            df = pd.DataFrame(rates)
            
            bullish_wick_index, bullish_ob, bullish_formation = find_bullish_wick_candle(df)
            bearish_wick_index, bearish_ob, bearish_formation = find_bearish_wick_candle(df)
            
            # Bullish scenario
            if bullish_wick_index is not None:
                print(f"Bullish wick index found at {bullish_wick_index, bullish_ob, bullish_formation, symbol}")
                try:
                    bullish_pivot_index, bullish_pullback_index = find_bullish_pullback(df, bullish_wick_index)
                    if bullish_pivot_index is not None and bullish_pullback_index is not None:
                        print(f"Bullish pivot index and pullback index found at {bullish_pivot_index, bullish_pullback_index}")
                        bullish_break, final_bullish_pullback = validate_bullish_break(df, bullish_wick_index, bullish_pullback_index, bullish_pivot_index)
                        if bullish_break is not None:
                            print(f"Bullish break index found at {bullish_break}")
                            bullish_impulse_index = find_bullish_impulse(df, bullish_pivot_index, final_bullish_pullback)
                            if bullish_impulse_index is not None:
                                print(f"Bullish impulse index found at {bullish_impulse_index}")
                                lower_boundaries, upper_boundary = determine_bullish_range(df, bullish_impulse_index, bullish_break)
                                if lower_boundaries is not None:
                                    print(f"Bullish lower boundary found at {lower_boundaries}")
                                    entry_signal, bullish_boundary = find_bullish_entry_candle(df, bullish_ob, bullish_formation, bullish_wick_index, lower_boundaries, symbol)
                                    if entry_signal is not None:
                                        print("Bullish entry found")
                                        entry_price = df['high'][entry_signal] + 1 * mt5.symbol_info(symbol).point
                                        stop_loss = df['low'][entry_signal] - 1 * mt5.symbol_info(symbol).point
                                        take_profit = df['high'][bullish_boundary]
                                        lot_size = calculate_lot_size_EU(entry_price, stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(entry_price, stop_loss)
                                        result = send_order_request_new(symbol, entry_price, stop_loss, lot_size, take_profit, "Bullish Wick", 234004, "buy")
                                        if result.retcode != mt5.TRADE_RETCODE_DONE:
                                            print(f"Order send failed with error code: {result.retcode}")
                                    else:
                                        print("No valid bullish entry signal found")
                                else:
                                    print("No valid bullish lower boundaries found")
                            else:
                                print("No valid bullish impulse index found")
                        else:
                            print("No valid bullish break found")
                    else:
                        print("No valid bullish pivot and pullback indices found")
                except Exception as e:
                    print(f"Error in bullish scenario for {symbol}: {str(e)}")
            else:
                print("No bullish wick candle found")
            
            # Bearish scenario
            if bearish_wick_index is not None:
                print(f"Bearish wick index found at {bearish_wick_index, bearish_ob, bearish_formation, symbol}")
                try:
                    bearish_pivot_index, bearish_pullback_index = find_bearish_pullback(df, bearish_wick_index)
                    if bearish_pivot_index is not None and bearish_pullback_index is not None:
                        print(f"Bearish pivot index and pullback index found at {bearish_pivot_index, bearish_pullback_index}")
                        bearish_break, final_bearish_pullback = validate_bearish_break(df, bearish_wick_index, bearish_pullback_index, bearish_pivot_index)
                        if bearish_break is not None:
                            print(f"Bearish break index found at {bearish_break}")
                            bearish_impulse_index = find_bearish_impulse(df, bearish_pivot_index, final_bearish_pullback)
                            if bearish_impulse_index is not None:
                                print(f"Bearish impulse index found at {bearish_impulse_index}")
                                upper_boundaries, lower_boundary = determine_bearish_range(df, bearish_impulse_index, bearish_break)
                                if upper_boundaries is not None:
                                    print(f"Bearish upper boundary found at {upper_boundaries}")
                                    entry_signal, bearish_boundary = find_bearish_entry_candle(df, bearish_ob, bearish_formation, bearish_wick_index, upper_boundaries, symbol)
                                    if entry_signal is not None:
                                        print("Bearish entry found")
                                        entry_price = df['low'][entry_signal] - 1 * mt5.symbol_info(symbol).point
                                        stop_loss = df['high'][entry_signal] + 1 * mt5.symbol_info(symbol).point
                                        take_profit = df['low'][bearish_boundary]
                                        lot_size = calculate_lot_size_EU(entry_price, stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(entry_price, stop_loss)
                                        result = send_order_request_new(symbol, entry_price, stop_loss, lot_size, take_profit, "Bearish Wick", 234004, "sell")
                                        if result.retcode != mt5.TRADE_RETCODE_DONE:
                                            print(f"Order send failed with error code: {result.retcode}")
                                    else:
                                        print("No valid bearish entry signal found")
                                else:
                                    print("No valid bearish upper boundaries found")
                            else:
                                print("No valid bearish impulse index found")
                        else:
                            print("No valid bearish break found")
                    else:
                        print("No valid bearish pivot and pullback indices found")
                except Exception as e:
                    print(f"Error in bearish scenario for {symbol}: {str(e)}")
            else:
                print("No bearish wick candle found")
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
def delete_order(ticket):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": ticket,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order delete failed, retcode={result.retcode}")
    else:
        print(f"Order {ticket} deleted successfully")
        
def calculate_lot_size_EU(entry, stop_loss, risk=10, commission_per_lot=7):
    pips = abs(entry - stop_loss) * 100000
    
    # Calculate the lot size iteratively
    lot_size = risk / pips
    total_loss = risk + (lot_size * commission_per_lot)
    
    while total_loss > risk:
        lot_size -= 0.01  # Decrease lot size by 0.01
        total_loss = (lot_size * pips) + (lot_size * commission_per_lot)
    
    return round(lot_size, 2)

def calculate_lot_size_GU(entry, stop_loss, risk=10, commission_per_lot=9):
    pips = abs(entry - stop_loss) * 100000
    
    # Calculate the lot size iteratively
    lot_size = risk / pips
    total_loss = risk + (lot_size * commission_per_lot)
    
    while total_loss > risk:
        lot_size -= 0.01  # Decrease lot size by 0.01
        total_loss = (lot_size * pips) + (lot_size * commission_per_lot)
    
    return round(lot_size, 2)

def check_existing_orders(symbol, entry_price):
    # Fetch pending orders for the symbol
    pending_orders = mt5.orders_get(symbol=symbol)
    if pending_orders is None:
        print("No pending orders found, error code =", mt5.last_error())
        pending_orders = []

    # Fetch open positions for the symbol
    open_positions = mt5.positions_get(symbol=symbol)
    if open_positions is None:
        print("No open positions found, error code =", mt5.last_error())
        open_positions = []

    # Check pending orders
    for order in pending_orders:
        if abs(order.price_open - entry_price) < mt5.symbol_info(symbol).point:
            return True

    # Check open positions
    for position in open_positions:
        if abs(position.price_open - entry_price) < mt5.symbol_info(symbol).point:
            return True

    return False

def check_existing_orders_new(symbol, stop_loss, entry):
    # Fetch pending orders for the symbol
    pending_orders = mt5.orders_get(symbol=symbol)
    if pending_orders is None:
        print("No pending orders found, error code =", mt5.last_error())
        pending_orders = []

    # Fetch open positions for the symbol
    open_positions = mt5.positions_get(symbol=symbol)
    if open_positions is None:
        print("No open positions found, error code =", mt5.last_error())
        open_positions = []

    # Check pending orders
    for order in pending_orders:
        if abs(order.sl - stop_loss) < mt5.symbol_info(symbol).point or abs(order.price.open - entry) < mt5.symbol_info(symbol).point:
            return True

    # Check open positions
    for position in open_positions:
        if abs(position.sl - stop_loss) < mt5.symbol_info(symbol).point or abs(position.price.open - entry) < mt5.symbol_info(symbol).point:
            return True

    return False

def send_order_request(symbol, entry_price, stop_loss, lot_size, take_profit, order_comment, magic_number, action):
    if check_existing_orders(symbol, entry_price):
        print(f"Order for {symbol} at price {entry_price} already exists. Skipping.")
        return

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY_STOP if action == "buy" else mt5.ORDER_TYPE_SELL_STOP,
        "price": entry_price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 10,
        "magic": magic_number,
        "comment": order_comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={result.retcode}")
    else:
        print(f"Order send successfully: {result}")

def send_order_request_new(symbol, entry_price, stop_loss, lot_size, take_profit, order_comment, magic_number, action):
    if check_existing_orders_new(symbol, stop_loss, entry_price):
        print(f"Order for {symbol} at price {entry_price} already exists. Skipping.")
        return

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY_STOP if action == "buy" else mt5.ORDER_TYPE_SELL_STOP,
        "price": entry_price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 10,
        "magic": magic_number,
        "comment": order_comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={result.retcode}")
    else:
        print(f"Order send successfully: {result}")
win_count = 0
loss_count = 0


def manage_orders():
    global win_count, loss_count
    orders = mt5.orders_get()
    if orders is None:
        print("No orders found, error code =", mt5.last_error())
        return

    for order in orders:
        symbol = order.symbol
        order_type = order.type
        entry_price = order.price_open
        stop_loss = order.sl
        take_profit = order.tp

        # Get the latest two candles
        candles = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 2)
        most_recent_closed_candle = candles[-2]

        if order_type == mt5.ORDER_TYPE_BUY_STOP:
            if (most_recent_closed_candle['low'] <= stop_loss and most_recent_closed_candle['close'] > stop_loss and most_recent_closed_candle['high'] < entry_price) or \
               (most_recent_closed_candle['high'] < entry_price and most_recent_closed_candle['low'] > stop_loss):
                # Set new buy stop order
                new_entry_price = most_recent_closed_candle['high'] + 1 * mt5.symbol_info(symbol).point
                new_stop_loss = most_recent_closed_candle['low'] - 1 * mt5.symbol_info(symbol).point if (most_recent_closed_candle['low'] <= stop_loss and most_recent_closed_candle['close'] > stop_loss and most_recent_closed_candle['high'] < entry_price) else stop_loss
                if symbol == "EURUSDz":
                    lot_size = calculate_lot_size_EU(new_entry_price, new_stop_loss)
                elif symbol == "GBPUSDz":
                    lot_size = calculate_lot_size_GU(new_entry_price, new_stop_loss)

                new_take_profit = take_profit
                if not check_existing_orders(symbol, new_entry_price):
                    send_order_request(symbol, new_entry_price, new_stop_loss, lot_size, new_take_profit, "New Buy stop order", 234002, "buy")
                    delete_order(order.ticket)
                else:
                    print(f"Order for {symbol} at price {new_entry_price} already exists. Skipping modification.")
            elif most_recent_closed_candle['close'] <= stop_loss:
                # Delete the order
                delete_order(order.ticket)
        elif order_type == mt5.ORDER_TYPE_SELL_STOP:
            if (most_recent_closed_candle['high'] >= stop_loss and most_recent_closed_candle['close'] < stop_loss and most_recent_closed_candle['low'] > entry_price) or \
               (most_recent_closed_candle['low'] > entry_price and most_recent_closed_candle['high'] < stop_loss):
                # Set new sell stop order
                new_entry_price = most_recent_closed_candle['low'] - 1 * mt5.symbol_info(symbol).point
                new_stop_loss = most_recent_closed_candle['high'] + 1 * mt5.symbol_info(symbol).point if (most_recent_closed_candle['high'] >= stop_loss and most_recent_closed_candle['close'] < stop_loss and most_recent_closed_candle['low'] > entry_price) else stop_loss
                if symbol == "EURUSDz":
                    lot_size = calculate_lot_size_EU(new_entry_price, new_stop_loss)
                elif symbol == "GBPUSDz":
                    lot_size = calculate_lot_size_GU(new_entry_price, new_stop_loss)

                new_take_profit = take_profit
                if not check_existing_orders(symbol, new_entry_price):
                    send_order_request(symbol, new_entry_price, new_stop_loss, lot_size, new_take_profit, "New Sell stop order", 234003, "sell")
                    delete_order(order.ticket)
                else:
                    print(f"Order for {symbol} at price {new_entry_price} already exists. Skipping modification.")
            elif most_recent_closed_candle['close'] >= stop_loss:
                # Delete the order
                delete_order(order.ticket)
        elif order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]:
            # Check if the order has been closed
            position = mt5.positions_get(ticket=order.ticket)
            if not position:
                # Order has been closed, check if it's a win or loss
                if (order_type == mt5.ORDER_TYPE_BUY and most_recent_closed_candle['close'] > entry_price) or \
                   (order_type == mt5.ORDER_TYPE_SELL and most_recent_closed_candle['close'] < entry_price):
                    win_count += 1
                else:
                    loss_count += 1
                
                if win_count == 2 or loss_count == 2:
                    print(f"Strategy completed with {win_count} wins and {loss_count} losses.")
                    return schedule.CancelJob

    place_wick_orders()

def start_trading():
    global win_count, loss_count
    win_count = 0
    loss_count = 0
    schedule.every(2).seconds.do(manage_orders)
    print(f"Trading started at {datetime.now()} UTC")

# Schedule the task to start at 7am UTC
schedule.every().day.at("07:00").do(start_trading)

# Check if it's already past 7am UTC and start immediately if so
now = datetime.now(timezone.utc)
if now.time() >= datetime.strptime("07:00", "%H:%M").time():
    print("It's already past 7am UTC. Starting trading immediately.")
    start_trading()

# Run the scheduler
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Restarting in 60 seconds...")
        time.sleep(5)
        continue
