import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, time

def find_bullish_wick_candle(df):

    latest_candle = len(df) - 1
    for i in range(latest_candle - 1, -1, -1):
        if df['low'].iloc[latest_candle] < df['low'].iloc[i] and df['close'].iloc[latest_candle] >= df['low'].iloc[i]:
            # Check if candle i is a bullish outside bar
            outside_bar = df['high'].iloc[i] > df['high'].iloc[i + 1] and df['low'].iloc[i] < df['low'].iloc[i + 1]
            # Check if candle i is a bullish double wick
            double_wick = df['low'].iloc[i] < df['low'].iloc[i - 1] and df['close'].iloc[i] > df['low'].iloc[i - 1]
            if outside_bar or double_wick:
                latest_candle_time = pd.to_datetime(df['time'].iloc[latest_candle], unit='s')
                if latest_candle_time.hour >= 8 and latest_candle_time.hour < 16:
                    if all(df['low'].iloc[k] > df['low'].iloc[latest_candle] and df['close'].iloc[k] >= df['low'].iloc[i] for k in range(i + 1, latest_candle)):
                        return latest_candle, None, i
                
            # Check if candle i is a bullish order block
            imbalance_found = False
            fvg_found = False
            if i + 1 < latest_candle and df['high'].iloc[i - 1] >= df['low'].iloc[i + 1] and df['high'].iloc[i + 1] > df['high'].iloc[i] and df['close'].iloc[i + 1] > df['high'].iloc[i]:
                imbalance_found = True
                k = i + 1
                ob_high = df['high'].iloc[k - 1]
                for l in range(k + 1, len(df)):
                    if df['high'].iloc[l] > df['high'].iloc[k] and df['low'].iloc[l] > df['high'].iloc[i]:
                        if all(df['low'].iloc[m] > ob_high for m in range(k + 1, l + 1)):
                            fvg_found = True
                            break
            if imbalance_found and fvg_found:
                latest_candle_time = pd.to_datetime(df['time'].iloc[latest_candle], unit='s')
                if latest_candle_time.hour >= 8 and latest_candle_time.hour < 10:
                    if all(df['low'].iloc[k] > df['low'].iloc[latest_candle] and df['close'].iloc[k] >= df['low'].iloc[i] for k in range(i + 1, latest_candle)):
                        return latest_candle, i, None

    return None, None, None  # Return None if no suitable candle is found

def find_bearish_wick_candle(df):
    latest_candle = len(df) - 1
    for i in range(latest_candle - 1, -1, -1):
        if df['high'].iloc[latest_candle] > df['high'].iloc[i] and df['close'].iloc[latest_candle] <= df['high'].iloc[i]:
            
            # Check if candle i is a bearish outside bar
            outside_bar = df['high'].iloc[i] > df['high'].iloc[i + 1] and df['low'].iloc[i] < df['low'].iloc[i + 1]
            # Check if candle i is a bearish double wick
            double_wick = df['high'].iloc[i] > df['high'].iloc[i - 1] and df['close'].iloc[i] < df['high'].iloc[i - 1]
            if outside_bar or double_wick:
                latest_candle_time = pd.to_datetime(df['time'].iloc[latest_candle], unit='s')
                if latest_candle_time.hour >= 8 and latest_candle_time.hour < 10:
                    if all(df['high'].iloc[k] < df['high'].iloc[latest_candle] and df['close'].iloc[k] <= df['high'].iloc[i] for k in range(i + 1, latest_candle)):
                        return latest_candle, None, i
                
            # Check if candle i is a bearish order block
            imbalance_found = False
            fvg_found = False
            if i + 1 < latest_candle and df['low'].iloc[i - 1] <= df['high'].iloc[i + 1] and df['low'].iloc[i + 1] < df['low'].iloc[i] and df['close'].iloc[i + 1] < df['low'].iloc[i]:
                imbalance_found = True
                k = i + 1
                ob_low = df['low'].iloc[k - 1]
                for l in range(k + 1, len(df)):
                    if df['low'].iloc[l] < df['low'].iloc[k] and df['high'].iloc[l] < df['low'].iloc[i]:
                        if all(df['high'].iloc[m] < ob_low for m in range(k + 1, l + 1)):
                            fvg_found = True
                            break
            if imbalance_found and fvg_found:
                latest_candle_time = pd.to_datetime(df['time'].iloc[latest_candle], unit='s')
                if latest_candle_time.hour >= 8 and latest_candle_time.hour < 10:
                    if all(df['close'].iloc[k] <= df['high'].iloc[i] and df['high'].iloc[k] < df['high'].iloc[latest_candle] for k in range(i + 1, latest_candle)):
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
                if df['close'].iloc[j] < df['low'].iloc[i]:
                    if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(i + 1, j)) and all(df['high'].iloc[k] <= df['high'].iloc[i] for k in range(i + 1, j + 1)):
                        first_closing_candle = j
            elif second_closing_candle is None:
                if df['close'].iloc[j] < df['low'].iloc[first_closing_candle]:
                    if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(first_closing_candle + 1, j)) and all(df['high'].iloc[k] <= df['high'].iloc[i] for k in range(first_closing_candle + 1, j + 1)):
                        second_closing_candle = j
                        break

        if first_closing_candle is not None and second_closing_candle is not None:
            pivot_index = i
            pullback_index = second_closing_candle

            # Validate the pivot
            if (pivot_index > 0 and pivot_index < len(df) - 1 and
                df['high'].iloc[pivot_index] > df['high'].iloc[pivot_index - 1] and 
                df['high'].iloc[pivot_index] >= df['high'].iloc[pivot_index + 1] and 
                df['high'].iloc[pivot_index + 1] <= df['high'].iloc[pivot_index]):
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
                if df['close'].iloc[j] > df['high'].iloc[i]:
                    if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(i + 1, j)) and all(df['low'].iloc[k] >= df['low'].iloc[i] for k in range(i + 1, j + 1)):
                        first_closing_candle = j
            elif second_closing_candle is None:
                if df['close'].iloc[j] > df['high'].iloc[first_closing_candle]:
                    if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(first_closing_candle + 1, j)) and all(df['low'].iloc[k] >= df['low'].iloc[i] for k in range(first_closing_candle + 1, j + 1)):
                        second_closing_candle = j
                        break

        if first_closing_candle is not None and second_closing_candle is not None:
            pivot_index = i
            pullback_index = second_closing_candle

            # Validate the pivot
            if (pivot_index > 0 and pivot_index < len(df) - 1 and
                df['low'].iloc[pivot_index] < df['low'].iloc[pivot_index - 1] and 
                df['low'].iloc[pivot_index] <= df['low'].iloc[pivot_index + 1] and 
                df['low'].iloc[pivot_index + 1] >= df['low'].iloc[pivot_index]):
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
        pullback_low = df['low'].iloc[pullback_index]
        valid_break_attempted = False
        final_pullback_low = pullback_low
        break_candle = None
        final_pullback_low_index = None
        
        for i in range(pullback_index + 1, wick_index):
            if df['high'].iloc[i] > df['high'].iloc[pivot_index]:
                final_pullback_low = min(df['low'].iloc[pullback_index:i])
                final_pullback_low_index = df['low'].iloc[pullback_index:i].idxmin()
                if df['close'].iloc[i] > df['high'].iloc[pivot_index]:
                    break_candle = i 
                    # Store the index of the valid break
                    break
                else:
                    valid_break_attempted = True  # Mark that a break attempt has been made
                    pivot_index = i  # Update the pivot_index to the current candle

            if valid_break_attempted and df['low'].iloc[i] < final_pullback_low:
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
        pullback_high = df['high'].iloc[pullback_index]
        valid_break_attempted = False
        final_pullback_high = pullback_high
        break_candle = None
        final_pullback_high_index = None

        for i in range(pullback_index + 1, wick_index):
            if df['low'].iloc[i] < df['low'].iloc[pivot_index]:
                final_pullback_high = max(df['high'].iloc[pullback_index:i])
                final_pullback_high_index = df['high'].iloc[pullback_index:i].idxmax()
                if df['close'].iloc[i] < df['low'].iloc[pivot_index]:
                    break_candle = i  # Store the index of the valid break
                    break
                else:
                    valid_break_attempted = True  # Mark that a break attempt has been made
                    pivot_index = i  # Update the pivot_index to the current candle

            if valid_break_attempted and df['high'].iloc[i] > final_pullback_high:
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
        pivot_high = df['high'].iloc[pivot_index]
        impulse_found = None

        for i in range(pivot_index - 1, -1, -1):
            if df['low'].iloc[i] < df['low'].iloc[pullback_index]:
                if check_opposite_bull(df, i, pivot_index) is None:
                    impulse_found = i
                    break
            if df['high'].iloc[i] >= pivot_high:
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
            pivot_low = df['low'].iloc[pivot_index]
            impulse_found = None

            for i in range(pivot_index - 1, -1, -1):
                if df['high'].iloc[i] > df['high'].iloc[pullback_index]:
                    if check_opposite_bear(df, i, pivot_index) is None:
                        impulse_found = i
                        break
                if df['low'].iloc[i] <= pivot_low:
                    impulse_found = None  # Invalidate the impulse if any low is <= pivot low
                    break

            bearish_impulse_list.append(impulse_found)
        else:
            bearish_impulse_list.append(None)

    return bearish_impulse_list

def determine_bullish_range(df, impulse_indices, current_pivot_highs):
    if impulse_indices is None or current_pivot_highs is None:
        return None, None

    # Reverse the lists to start from the rightmost (most recent) values
    # impulse_indices = impulse_indices[::-1]
    # current_pivot_highs = current_pivot_highs[::-1]

    # Find the first non-None value in impulse_indices
    for idx, impulse_index in enumerate(impulse_indices):
        if impulse_index is not None:
            # Get the corresponding value in current_pivot_highs
            current_pivot_high = current_pivot_highs[idx]

            if current_pivot_high is None:
                continue  # Skip if the corresponding pivot high is None

            lower_boundary = None
            upper_boundary = current_pivot_high

            # Perform the logic to determine the boundaries
            for i in range(impulse_index - 1, -1, -1):
                first_closing_candle = None
                second_closing_candle = None 

                # Valid break method
                valid_break_found = False
                for j in range(i + 1, impulse_index + 2):
                    if first_closing_candle is None:
                        if df['close'].iloc[j] < df['low'].iloc[i]:
                            if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(i, j)):
                                if df['high'].iloc[i - 1] > df['high'].iloc[i] and df['low'].iloc[i - 1] < df['low'].iloc[i]:
                                    continue
                                first_closing_candle = j
                    elif second_closing_candle is None:
                        if df['close'].iloc[j] < df['low'].iloc[first_closing_candle]:
                            if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(first_closing_candle + 1, j)):
                                second_closing_candle = j
                                valid_break_found = True
                                break

                if valid_break_found:
                    temp_range_low_index = df['low'].iloc[i:impulse_index + 1].idxmin()
                    lower_boundary = temp_range_low_index
                    return lower_boundary, upper_boundary

                # Sequence method
                if df['high'].iloc[i] > df['high'].iloc[current_pivot_high]:
                    temp_range_low_index = df['low'].iloc[i:current_pivot_high + 1].idxmin()
                    lower_boundary = temp_range_low_index
                    return lower_boundary, upper_boundary

            if lower_boundary is None:
                # Default to the impulse low if no valid range is found
                lower_boundary = impulse_index

            return lower_boundary, upper_boundary

    return None, None  # Return None if no valid boundaries are found

def determine_bearish_range(df, impulse_indices, current_pivot_lows):
    if impulse_indices is None or current_pivot_lows is None:
        return None, None

    # Reverse the lists to start from the rightmost (most recent) values
    # impulse_indices = impulse_indices[::-1]
    # current_pivot_lows = current_pivot_lows[::-1]

    # Find the first non-None value in impulse_indices
    for idx, impulse_index in enumerate(impulse_indices):
        if impulse_index is not None:
            # Get the corresponding value in current_pivot_lows
            current_pivot_low = current_pivot_lows[idx]

            if current_pivot_low is None:
                continue  # Skip if the corresponding pivot low is None

            upper_boundary = None  # Initialize upper_boundary
            lower_boundary = current_pivot_low

            # Perform the logic to determine the boundaries
            for i in range(impulse_index - 1, -1, -1):
                first_closing_candle = None
                second_closing_candle = None

                # Valid break method
                valid_break_found = False
                for j in range(i + 1, impulse_index + 2):
                    if first_closing_candle is None:
                        if df['close'].iloc[j] > df['high'].iloc[i]:
                            if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(i, j)):
                                if df['high'].iloc[i - 1] > df['high'].iloc[i] and df['low'].iloc[i - 1] < df['low'].iloc[i]:
                                    continue
                                first_closing_candle = j
                    elif second_closing_candle is None:
                        if df['close'].iloc[j] > df['high'].iloc[first_closing_candle]:
                            if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(first_closing_candle + 1, j)):
                                second_closing_candle = j
                                valid_break_found = True
                                break

                if valid_break_found:
                    temp_range_high_index = df['high'].iloc[i:impulse_index + 1].idxmax()
                    upper_boundary = temp_range_high_index
                    return upper_boundary, lower_boundary

                # Sequence method
                if df['low'].iloc[i] < df['low'].iloc[current_pivot_low]:
                    temp_range_high_index = df['high'].iloc[i:current_pivot_low + 1].idxmax()
                    upper_boundary = temp_range_high_index
                    return upper_boundary, lower_boundary

            if upper_boundary is None:
                # Default to the impulse high if no valid range is found
                upper_boundary = impulse_index

            return upper_boundary, lower_boundary

    return None, None  # Return None if no valid boundaries are found

def find_bullish_entry_candle(df, ob_index, formation_index, wick_index, lower_boundary, symbol):
    pipette_value = mt5.symbol_info(symbol).point * 2
    
    entry_candle = None
    upper_boundary = None

    # Process for ob_index
    if ob_index is not None:
        new_upper_boundary = df['high'].iloc[lower_boundary:wick_index].idxmax()
        new_current_pivot_high = df['high'].iloc[new_upper_boundary]

        if ob_index <= new_upper_boundary and df['low'].iloc[wick_index] >= df['low'].iloc[lower_boundary]:
            if df['high'].iloc[wick_index] < new_current_pivot_high - pipette_value:
                if all(df['low'].iloc[k] > df['low'].iloc[wick_index] for k in range(new_upper_boundary, wick_index)):
                    if check_opposite_bear(df, new_upper_boundary, wick_index) is None and bullish_momentum_check(df, new_upper_boundary, wick_index) is not None:
                        potential_entry = df['high'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                        potential_stop = df['low'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                        entry_to_total_pips = calculate_pip_distance(potential_entry, new_current_pivot_high)
                        entry_to_sl_pips = calculate_pip_distance(potential_entry, potential_stop)
                        if entry_to_total_pips >= 1.3 * entry_to_sl_pips:
                            entry_candle = wick_index
                            upper_boundary = new_upper_boundary
                            return entry_candle, upper_boundary
    # Process for formation_index
    if formation_index is not None:
        new_upper_boundary = df['high'].iloc[lower_boundary:wick_index].idxmax()
        new_current_pivot_high = df['high'].iloc[new_upper_boundary]

        # Ensure high of wick_index is lower than our new pivot high
        if df['high'].iloc[wick_index] < new_current_pivot_high - pipette_value and df['low'].iloc[wick_index] >= df['low'].iloc[lower_boundary]:
            # Ensure wick_index is lower than every candle between the new upper boundary and wick_index
            if all(df['low'].iloc[k] > df['low'].iloc[wick_index] for k in range(new_upper_boundary, wick_index)):
                if check_opposite_bear(df, new_upper_boundary, wick_index) is None and bullish_momentum_check(df, new_upper_boundary, wick_index) is not None:
                    potential_entry = df['high'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                    potential_stop = df['low'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                    entry_to_total_pips = calculate_pip_distance(potential_entry, new_current_pivot_high)
                    entry_to_sl_pips = calculate_pip_distance(potential_entry, potential_stop)
                    if entry_to_total_pips >= 1.3 * entry_to_sl_pips:
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
        new_lower_boundary = df['low'].iloc[upper_boundary:wick_index].idxmin()
        new_current_pivot_low = df['low'].iloc[new_lower_boundary]

        if ob_index <= new_lower_boundary and df['high'].iloc[wick_index] <= df['high'].iloc[upper_boundary]:
            if df['low'].iloc[wick_index] > new_current_pivot_low + pipette_value:
                if all(df['high'].iloc[k] < df['high'].iloc[wick_index] for k in range(new_lower_boundary, wick_index)):
                    if check_opposite_bull(df, new_lower_boundary, wick_index) is None and bearish_momentum_check(df, new_lower_boundary, wick_index) is not None:
                        potential_entry = df['low'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                        potential_stop = df['high'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                        entry_to_total_pips = calculate_pip_distance(potential_entry, new_current_pivot_low)
                        entry_to_sl_pips = calculate_pip_distance(potential_entry, potential_stop)
                        if entry_to_total_pips >= 1.3 * entry_to_sl_pips:
                            entry_candle = wick_index
                            lower_boundary = new_lower_boundary
                            return entry_candle, lower_boundary

    # Process for formation_index
    if formation_index is not None:
        new_lower_boundary = df['low'].iloc[upper_boundary:wick_index].idxmin()
        new_current_pivot_low = df['low'].iloc[new_lower_boundary]

        # Ensure low of wick_index is higher than our new pivot low 
        if df['low'].iloc[wick_index] > new_current_pivot_low + pipette_value and df['high'].iloc[wick_index] <= df['high'].iloc[upper_boundary]:
            # Ensure wick_index is higher than every candle between the new lower boundary and wick_index
            if all(df['high'].iloc[k] < df['high'].iloc[wick_index] for k in range(new_lower_boundary, wick_index)):
                if check_opposite_bull(df, new_lower_boundary, wick_index) is None and bearish_momentum_check(df, new_lower_boundary, wick_index) is not None:
                    potential_entry = df['low'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                    potential_stop = df['high'].iloc[wick_index] + 1 * mt5.symbol_info(symbol).point
                    entry_to_total_pips = calculate_pip_distance(potential_entry, new_current_pivot_low)
                    entry_to_sl_pips = calculate_pip_distance(potential_entry, potential_stop)
                    if entry_to_total_pips >= 1.3 * entry_to_sl_pips:
                        entry_candle = wick_index
                        lower_boundary = new_lower_boundary
                        return entry_candle, lower_boundary

    return entry_candle, lower_boundary

def check_opposite_bear(df, max_high, wick_index):
    for i in range(max_high + 1, wick_index):
        first_closing_candle = None
        second_closing_candle = None
        valid_break_found = False  # Initialize this variable outside the inner loop

        for j in range(i + 1, wick_index + 1):
            if first_closing_candle is None:
                if df['close'].iloc[j] > df['high'].iloc[i]:
                    if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(i, j)):
                        if df['high'].iloc[i - 1] > df['high'].iloc[i] and df['low'].iloc[i - 1] < df['low'].iloc[i]:
                            continue
                        first_closing_candle = j
            elif second_closing_candle is None:  # Changed to elif for clarity
                if df['close'].iloc[j] > df['high'].iloc[first_closing_candle]:
                    if all(df['high'].iloc[k] < df['close'].iloc[j] for k in range(first_closing_candle + 1, j)):
                        second_closing_candle = j
                        valid_break_found = True
                        break  # Exit the inner loop once we've found a valid break

        if valid_break_found:
            for m in range(i + 1, wick_index + 1):
                if (df['close'].iloc[m] < df['low'].iloc[i] and
                    df['low'].iloc[i] < df['low'].iloc[i - 1] and 
                    df['low'].iloc[i] <= df['low'].iloc[i + 1] and 
                    df['low'].iloc[i + 1] >= df['low'].iloc[i]):
                    return i
    
    return None  # Move this outside the loop to return None if no valid break is found

def bullish_momentum_check(df, max_high, wick_index):
    # Get the number of candles from max_high to wick_index, including both
    candles_to_wick = wick_index - max_high + 1
    
    found_candle = None
    
    # Iterate backwards from max_high
    for i in range(max_high, -1, -1):
        if df['low'].iloc[i] < df['low'].iloc[wick_index]:
            found_candle = i
            break  # Exit the loop once we find the first suitable candle
    
    if found_candle is not None:
        # Count candles from this candle to max_high, including both
        candles_to_max_high = max_high - found_candle + 1
        
        # Compare the counts
        if candles_to_max_high <= candles_to_wick:
            return found_candle  # Return the index of the found candle
    
    return None  # Return None if no suitable candle is found or if the count check fails

def bearish_momentum_check(df, max_low, wick_index):
    # Get the number of candles from max_low to wick_index, including both
    candles_to_wick = wick_index - max_low + 1
    
    found_candle = None
    
    # Iterate backwards from max_low
    for i in range(max_low, -1, -1):
        if df['high'].iloc[i] > df['high'].iloc[wick_index]:
            found_candle = i
            break  # Exit the loop once we find the first suitable candle
    
    if found_candle is not None:
        # Count candles from this candle to max_low, including both
        candles_to_max_low = max_low - found_candle + 1
        
        # Compare the counts
        if candles_to_max_low <= candles_to_wick:
            return found_candle  # Return the index of the found candle
    
    return None  # Return None if no suitable candle is found or if the count check fails

def calculate_pip_distance(price1, price2):
    return abs(price1 - price2) * 100000

def check_opposite_bull(df, max_low, wick_index):


    for i in range(max_low + 1, wick_index):
        first_closing_candle = None
        second_closing_candle = None
        valid_break_found = False

        for j in range(i + 1, wick_index + 1):
            if first_closing_candle is None:
                if df['close'].iloc[j] < df['low'].iloc[i]:
                    if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(i, j)):
                        if df['low'].iloc[i - 1] < df['low'].iloc[i] and df['high'].iloc[i - 1] > df['high'].iloc[i]:
                            continue
                        first_closing_candle = j
            if first_closing_candle is not None and second_closing_candle is None:
                if df['close'].iloc[j] < df['low'].iloc[first_closing_candle]:
                    if all(df['low'].iloc[k] > df['close'].iloc[j] for k in range(first_closing_candle + 1, j)):
                        second_closing_candle = j
                        valid_break_found = True
                        break
                    
        if valid_break_found:
            for m in range(i + 1, wick_index + 1):
                if (df['close'].iloc[m] > df['high'].iloc[i] and
                    df['high'].iloc[i] > df['high'].iloc[i - 1] and 
                    df['high'].iloc[i] >= df['high'].iloc[i + 1] and 
                    df['high'].iloc[i + 1] <= df['high'].iloc[i]):
                    return i

    return None

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

def backtest(start_date, end_date, symbols):
    # Initialize MT5
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return

    for symbol in symbols:
        # Fetch historical data
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)
        df = pd.DataFrame(rates)
        print(f"Total data points for {symbol}: {len(df)}")

        for i in range(100, len(df)):
            if i % 1000 == 0:
                print(f"Processing candle {i} for {symbol}")

        # Initialize variables for tracking performance
        trades = []
        pending_orders = []
        balance = 500  # Starting balance   
        equity = balance
        total_trades_counter = 0
        profits = 0
        losses = 0
        profit_amount = 0
        loss_amount = 0
        commission = 0

        # Iterate through historical data
        for i in range(100, len(df)):
            current_data = df.iloc[i-100:i]
            current_data = current_data.reset_index(drop=True)
            current_candle = current_data.iloc[-1]
            
            # Your trading logic here
            bullish_wick_index, bullish_ob, bullish_formation = find_bullish_wick_candle(current_data)
            bearish_wick_index, bearish_ob, bearish_formation = find_bearish_wick_candle(current_data)
            
            # Check for entry conditions and simulate order placement
            if bullish_wick_index is not None:
                bullish_pivot_index, bullish_pullback_index = find_bullish_pullback(current_data, bullish_wick_index)
                if bullish_pivot_index is not None and bullish_pullback_index is not None:
                        bullish_break, final_bullish_pullback = validate_bullish_break(current_data, bullish_wick_index, bullish_pullback_index, bullish_pivot_index)
                        if bullish_break is not None:
                            bullish_impulse_index = find_bullish_impulse(current_data, bullish_pivot_index, final_bullish_pullback)
                            if bullish_impulse_index is not None:
                                lower_boundaries, upper_boundary = determine_bullish_range(current_data, bullish_impulse_index, bullish_break)
                                if lower_boundaries is not None:
                                    entry_signal, bullish_boundary = find_bullish_entry_candle(current_data, bullish_ob, bullish_formation, bullish_wick_index, lower_boundaries, symbol)
                                    if entry_signal is not None:
                                        entry_price = current_data['high'][entry_signal] + 1 * mt5.symbol_info(symbol).point
                                        stop_loss = current_data['low'][entry_signal] - 1 * mt5.symbol_info(symbol).point
                                        take_profit = current_data['high'][bullish_boundary]
                                        lot_size = calculate_lot_size_EU(entry_price, stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(entry_price, stop_loss)
                
                                        pending_orders.append({
                                            'type': 'buy_stop',
                                            'entry_time': current_data.index[-1],
                                            'entry_price': entry_price,
                                            'stop_loss': stop_loss,
                                            'take_profit': take_profit,
                                            'lot_size': lot_size,
                                            'time': current_candle.name
                                         })
                                        # Get the time associated with the bearish_wick_index
                                        bullish_wick_time = current_data.iloc[bullish_wick_index]['time']

                                        # Convert the time to a human-readable format
                                        bullish_wick_datetime = pd.to_datetime(bullish_wick_time, unit='s')

                                        print(f"Bullish wick index found at {bullish_wick_index, bullish_ob, bullish_formation, symbol}")
                                        print(f"Bullish pivot index and pullback index found at {bullish_pivot_index, bullish_pullback_index}")
                                        print(f"Bullish break index found at {bullish_break}")
                                        print(f"Bullish impulse index found at {bullish_impulse_index}")
                                        print(f"Bullish lower boundary found at {lower_boundaries}")
                                        print("Bullish entry found and Order appended")
                                        print(f"Timestamp: {bullish_wick_datetime}")
                                        
            
            elif bearish_wick_index is not None:
                bearish_pivot_index, bearish_pullback_index = find_bearish_pullback(current_data, bearish_wick_index)
                if bearish_pivot_index is not None and bearish_pullback_index is not None:
                        bearish_break, final_bearish_pullback = validate_bearish_break(current_data, bearish_wick_index, bearish_pullback_index, bearish_pivot_index)
                        if bearish_break is not None:
                            bearish_impulse_index = find_bearish_impulse(current_data, bearish_pivot_index, final_bearish_pullback)
                            if bearish_impulse_index is not None:
                                upper_boundaries, lower_boundary = determine_bearish_range(current_data, bearish_impulse_index, bearish_break)
                                if upper_boundaries is not None:
                                    entry_signal, bearish_boundary = find_bearish_entry_candle(current_data, bearish_ob, bearish_formation, bearish_wick_index, upper_boundaries, symbol)
                                    if entry_signal is not None:
                                        entry_price = current_data['low'][entry_signal] - 1 * mt5.symbol_info(symbol).point
                                        stop_loss = current_data['high'][entry_signal] + 1 * mt5.symbol_info(symbol).point
                                        take_profit = current_data['low'][bearish_boundary]
                                        lot_size = calculate_lot_size_EU(entry_price, stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(entry_price, stop_loss)
                
                                        pending_orders.append({
                                            'type': 'sell_stop',
                                            'entry_time': current_data.index[-1],
                                            'entry_price': entry_price,
                                            'stop_loss': stop_loss,
                                            'take_profit': take_profit,
                                            'lot_size': lot_size,
                                            'time': current_candle.name
                                        })
                                        # Get the time associated with the bearish_wick_index
                                        bearish_wick_time = current_data.iloc[bearish_wick_index]['time']

                                        # Convert the time to a human-readable format
                                        bearish_wick_datetime = pd.to_datetime(bearish_wick_time, unit='s')

                                        print(f"bearish wick index found at {bearish_wick_index, bearish_ob, bearish_formation, symbol}")
                                        print(f"bearish pivot index and pullback index found at {bearish_pivot_index, bearish_pullback_index}")
                                        print(f"bearish break index found at {bearish_break}")
                                        print(f"bearish impulse index found at {bearish_impulse_index}")
                                        print(f"bearish lower boundary found at {upper_boundaries}")
                                        print("Bearish entry found and Order appended")
                                        print(f"Timestamp: {bearish_wick_datetime}")
    
            
            # Check for exit conditions and update trades
            # Manage pending orders
            for order in pending_orders[:]:
                if order['type'] == 'buy_stop':
                    if (current_candle['low'] <= order['stop_loss'] and current_candle['close'] > order['stop_loss'] and current_candle['high'] < order['entry_price']) or \
                       (current_candle['high'] < order['entry_price'] and current_candle['low'] > order['stop_loss'] and current_candle['low'] - order['stop_loss'] >= 2 * mt5.symbol_info(symbol).point):
                        new_entry_price = current_candle['high'] + 1 * mt5.symbol_info(symbol).point
                        new_stop_loss = current_candle['low'] - 1 * mt5.symbol_info(symbol).point if (current_candle['low'] <= order['stop_loss'] and current_candle['close'] > order['stop_loss'] and current_candle['high'] < order['entry_price']) else order['stop_loss']
                        new_lot_size = calculate_lot_size_EU(new_entry_price, new_stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(new_entry_price, new_stop_loss)                        
                        existing_order = next((o for o in pending_orders if o['entry_price'] == new_entry_price and o['stop_loss'] == new_stop_loss), None)
                        if existing_order:
                            # Delete the current order
                            pending_orders.remove(order)
                        else:
                            # Modify buy stop order
                            order.update({
                                'entry_price': new_entry_price,
                                'stop_loss': new_stop_loss,
                                'lot_size': new_lot_size
                            })
                    elif current_candle['close'] <= order['stop_loss']:
                        # Delete the order
                        pending_orders.remove(order)
                    elif current_candle['high'] >= order['entry_price']:
                     # Check if the current candle has triggered the stop loss
                        if current_candle['low'] <= order['stop_loss'] and current_candle['close'] > order['stop_loss']:
                            # Check if there's an order in pending_orders with the same new entry price and stop loss
                            new_entry_price = current_candle['high'] + 1 * mt5.symbol_info(symbol).point
                            new_stop_loss = current_candle['low'] - 1 * mt5.symbol_info(symbol).point
                            existing_order = next((o for o in pending_orders if o['entry_price'] == new_entry_price and o['stop_loss'] == new_stop_loss), None)
                            if existing_order:
                             # Delete the existing order
                                pending_orders.remove(existing_order)
    
                        # Activate the order
                        trades.append({
                            'type': 'buy',
                            'entry_time': current_candle.name,
                            'entry_price': order['entry_price'],
                            'stop_loss': order['stop_loss'],
                            'take_profit': order['take_profit'],
                            'lot_size': order['lot_size']
                        })
                        # Remove the current order from pending_orders
                        pending_orders.remove(order)

                elif order['type'] == 'sell_stop':
                    if (current_candle['high'] >= order['stop_loss'] and current_candle['close'] < order['stop_loss'] and current_candle['low'] > order['entry_price']) or \
                       (current_candle['low'] > order['entry_price'] and current_candle['high'] < order['stop_loss'] and order['stop_loss'] - current_candle['high'] >= 2 * mt5.symbol_info(symbol).point):
                        # Modify sell stop order
                        new_entry_price = current_candle['low'] - 1 * mt5.symbol_info(symbol).point
                        new_stop_loss = current_candle['high'] + 1 * mt5.symbol_info(symbol).point if (current_candle['high'] >= order['stop_loss'] and current_candle['close'] < order['stop_loss'] and current_candle['low'] > order['entry_price']) else order['stop_loss']
                        new_lot_size = calculate_lot_size_EU(new_entry_price, new_stop_loss) if symbol == "EURUSDz" else calculate_lot_size_GU(new_entry_price, new_stop_loss)
                        existing_order = next((o for o in pending_orders if o['entry_price'] == new_entry_price and o['stop_loss'] == new_stop_loss), None)
                        if existing_order:
                            # Delete the current order
                            pending_orders.remove(order)
                        else:
                            order.update({
                                'entry_price': new_entry_price,
                                'stop_loss': new_stop_loss,
                                'lot_size': new_lot_size
                            })
                    elif current_candle['close'] >= order['stop_loss']:
                        # Delete the order
                        pending_orders.remove(order)
                    elif current_candle['low'] <= order['entry_price']:
                     # Check if the current candle has triggered the stop loss
                        if current_candle['high'] >= order['stop_loss'] and current_candle['close'] < order['stop_loss']:
                            # Check if there's an order in pending_orders with the same new entry price and stop loss
                            new_entry_price = current_candle['low'] + 1 * mt5.symbol_info(symbol).point
                            new_stop_loss = current_candle['high'] - 1 * mt5.symbol_info(symbol).point
                            existing_order = next((o for o in pending_orders if o['entry_price'] == new_entry_price and o['stop_loss'] == new_stop_loss), None)
                            if existing_order:
                             # Delete the existing order
                                pending_orders.remove(existing_order)
    
                        # Activate the order
                        trades.append({
                            'type': 'sell',
                            'entry_time': current_candle.name,
                            'entry_price': order['entry_price'],
                            'stop_loss': order['stop_loss'],
                            'take_profit': order['take_profit'],
                            'lot_size': order['lot_size']
                        })
                        # Remove the current order from pending_orders
                        pending_orders.remove(order)
    
            # Manage active trades
            for trade in trades[:]:
                if trade['type'] == 'buy':
                    if current_candle['low'] <= trade['stop_loss'] or current_candle['high'] >= trade['take_profit']:
                        trade['exit_time'] = current_candle.name
                        trade['exit_price'] = trade['stop_loss'] if current_candle['low'] <= trade['stop_loss'] else trade['take_profit']
                        trade['profit'] = (trade['exit_price'] - trade['entry_price']) * trade['lot_size'] * 100000
                        trade['commission'] = trade['lot_size'] * 7
                        equity += trade['profit']
                        equity -= trade['commission']
                        commission += trade['commission']

                        if trade['profit'] > 0:
                            profits += 1
                            profit_amount += trade['profit']
                        else:
                            losses += 1
                            loss_amount += trade['profit']
                        trades.remove(trade)
                        total_trades_counter += 1
                          # Increment the counter
                elif trade['type'] == 'sell':
                    if current_candle['high'] >= trade['stop_loss'] or current_candle['low'] <= trade['take_profit']:
                        trade['exit_time'] = current_candle.name
                        trade['exit_price'] = trade['stop_loss'] if current_candle['high'] >= trade['stop_loss'] else trade['take_profit']
                        trade['profit'] = (trade['entry_price'] - trade['exit_price']) * trade['lot_size'] * 100000
                        trade['commission'] = trade['lot_size'] * 7
                        equity += trade['profit']
                        equity -= trade['commission']
                        commission += trade['commission']
                        if trade['profit'] > 0:
                            profits += 1
                            profit_amount += trade['profit']
                        else:
                            losses += 1
                            loss_amount += trade['profit']
                        trades.remove(trade)
                        total_trades_counter += 1
                      # Increment the counter


        # Calculate performance metrics
        total_trades = total_trades_counter
        total_profit = profits
        total_losses = losses
        total_loss_amount = loss_amount
        total_profit_amount = profit_amount
        win_rate = total_profit / total_trades if total_trades > 0 else 0
        
        print(f"Results for {symbol}:")
        print(f"Total trades: {total_trades}")
        print(f"Wins: {total_profit}")
        print(f"Losses: {total_losses}")
        print(f"Win rate: {win_rate:.2%}")
        print(f"Amount made: ${total_profit_amount:.2f}")
        print(f"Amount lost: ${total_loss_amount:.2f}")
        print(f"Total commission: ${commission:.2f}")
        print(f"Final equity: ${equity:.2f}")
        print("---")

    mt5.shutdown()

# Run the backtest
start_date = datetime(2024, 7, 1)
end_date = datetime(2024, 8, 10)
symbols_to_trade = ["EURUSDz"]
backtest(start_date, end_date, symbols_to_trade)