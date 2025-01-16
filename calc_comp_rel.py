#!/usr/bin/env python3

import argparse
import pandas as pd
import os

def calculate_reliability(
    df, 
    input_period, 
    period_lower_limit = 1, 
    period_upper_limit = 1,
    ls = None, 
    ls_lower_limit = 0.05, 
    ls_upper_limit = 0.05, 
    t = None, 
    t_lower_limit = 0.5, 
    t_upper_limit = 0.5,
    snr = None, 
    snr_lower_limit = 2.5, 
    snr_upper_limit = 2.5,
    mode='match'
):
    
    """
    Description
    -----------
    
    This function calculates the reliability of a given period measurement. As a reminder, reliability is defined
    as the number of stars that fall within a given period and parameter range that are a match or an alias
    of the true rotation period over the total number of stars within that period and parameter range. This function
    works be defining a box in period and parameter space around a given input period and parameter value and calculates
    reliability in that box. The measured Lomb-Scargle power, TESS magnitude, or signal-to-noise ratio MUST be given
    for this code to work.
    
    Inputs
    ------
    
    input_period, period_lower_limit, period_upper_limit: float, int, string. The measured rotation period of the star and              corresponding bin size. Defaults  to +/- 1 day. Period must be greater than 0.
                                                                              
    ls, ls_lower_limit, ls_upper_limit: float, int, string. The lomb-scargle power of the rotation measurement and corresponding        bin size. Defaults  to +/- 0.05. ls must be between 0 and 1.
                                                            
    t, t_lower_limit, t_upper_limit: float, int, string. The star's TESS magnitude and corresponding bin size. Defaults  to +/-          0.5 mag.
    
    snr, snr_lower_limit, snr_upper_limit: float, int, string. The SNR of the rotation measurement and corresponding bin size.
       Defaults to +/- 2.5. snr must be greater than 0.
    
    mode: string. One of 'match' (to measure match reliability), 'alias' (to measure alias reliability), 'recovery' (to measure         recovery reliability)

    df: Pandas dataframe. This is the input dataframe containing the true RH20 measurements and the corresponding rotation             periods as measured by TESS. This will almost always be from the csv that shipped with the code, however the user could           replace this dataframe with their own if they so choose.

    
    Outputs
    -------
    
    rel: float. The reliability of a given rotation period / parameter combination.
    
    Example
    -------
    
    >>> period = 9 # days
    >>> ls_power = 0.1 # lomb scargle power
    >>> rel = calculate_reliability(input_period = 9, ls = ls_power)
    >>> print(rel)
    >>> 0.708
    
    """

    input_period = float(input_period)
    period_lower_limit = float(period_lower_limit)
    period_upper_limit = float(period_upper_limit)
    
    assert 0.2 < input_period < 20, "The input rotation period must be between 0.2 and 20 days"
    assert any(value is not None for value in [ls, t, snr]), "Please specify a value for at least one of LS, T, SNR"
    assert mode in ['match', 'alias', 'recovery'], "Mode must be one of 'match', 'alias', or 'recovery'"
    
    # Filter by period
    param_df = df.loc[
        (df.prot_rh20 < input_period + period_upper_limit) & 
        (df.prot_rh20 > input_period - period_lower_limit)
    ]
        
    # Lomb-Scargle power
    if ls is not None:
        ls = float(ls)
        ls_lower_limit, ls_upper_limit = float(ls_lower_limit), float(ls_upper_limit)
        assert 0 < ls < 1, "Lomb-Scargle power must be between 0 and 1"
        param_df = param_df.loc[
            (param_df.power > ls - ls_lower_limit) & 
            (param_df.power < ls + ls_upper_limit)
        ]

    # TESS magnitude
    if t is not None:
        t = float(t)
        t_lower_limit, t_upper_limit = float(t_lower_limit), float(t_upper_limit)
        param_df = param_df.loc[
            (param_df.Tmag > t - t_lower_limit) & 
            (param_df.Tmag < t + t_upper_limit)
        ]

    # SNR
    if snr is not None:
        snr = float(snr)
        snr_lower_limit, snr_upper_limit = float(snr_lower_limit), float(snr_upper_limit)
        assert snr > 0, "SNR must be greater than 0"
        param_df = param_df.loc[
            (param_df.snr > snr - snr_lower_limit) & 
            (param_df.snr < snr + snr_upper_limit)
        ]

    if len(param_df) < 3:
        return None  # Avoid division by zero if no stars remain after filtering

    # Calculate reliability for the specified mode
    if mode == 'match':
        rel_df = param_df.loc[param_df.status == 'match']
    elif mode == 'alias':
        rel_df = param_df.loc[param_df.status == 'alias']
    else:  # mode == 'recovery'
        rel_df = param_df.loc[param_df.status != 'not_recovered']

    return len(rel_df) / len(param_df)


def calculate_completeness(
    df, 
    input_period, 
    mode='match', 
    period_lower_limit = 1, 
    period_upper_limit = 1,
    ls = None, 
    ls_lower_limit = 0.05, 
    ls_upper_limit = 0.05, 
    t = None, 
    t_lower_limit = 0.5, 
    t_upper_limit = 0.5,
    snr = None, 
    snr_lower_limit = 2.5, 
    snr_upper_limit = 2.5
):
    """
    See docstring for calculate_reliability. The arguments and output are the same, this function just calculates completeness instead of reliability.
    """
    
    input_period = float(input_period)
    period_lower_limit = float(period_lower_limit)
    period_upper_limit = float(period_upper_limit)
    
    assert 0.2 < input_period < 20, "The input rotation period must be between 0 and 20 days"
    assert any(value is not None for value in [ls, t, snr]), "Please specify a value for at least one of LS, T, SNR"
    assert mode in ['match', 'alias', 'recovery'], "Mode must be one of 'match', 'alias', or 'recovery'"
    
    # All stars within the period window
    all_df = df.loc[
        (df.prot_rh20 < input_period + period_upper_limit) & 
        (df.prot_rh20 > input_period - period_lower_limit)
    ]
    
    param_df = all_df

    # Lomb-Scargle
    if ls is not None:
        ls = float(ls)
        ls_lower_limit, ls_upper_limit = float(ls_lower_limit), float(ls_upper_limit)
        assert 0 < ls < 1, "Lomb-Scargle power must be between 0 and 1"
        param_df = param_df.loc[
            (param_df.power > ls - ls_lower_limit) & 
            (param_df.power < ls + ls_upper_limit)
        ]

    # TESS magnitude
    if t is not None:
        t = float(t)
        t_lower_limit, t_upper_limit = float(t_lower_limit), float(t_upper_limit)
        param_df = param_df.loc[
            (param_df.Tmag > t - t_lower_limit) & 
            (param_df.Tmag < t + t_upper_limit)
        ]

    # SNR
    if snr is not None:
        snr = float(snr)
        snr_lower_limit, snr_upper_limit = float(snr_lower_limit), float(snr_upper_limit)
        assert snr > 0, "SNR must be greater than 0"
        param_df = param_df.loc[
            (param_df.snr > snr - snr_lower_limit) & 
            (param_df.snr < snr + snr_upper_limit)
        ]

    if len(all_df) < 3:
        return None  # Avoid division by zero if no stars in all_df

    # Calculate completeness for the specified mode
    if mode == 'match':
        comp_df = param_df.loc[param_df.status == 'match']
    elif mode == 'alias':
        comp_df = param_df.loc[param_df.status == 'alias']
    else:  # mode == 'recovery'
        comp_df = param_df.loc[param_df.status != 'not_recovered']

    return len(comp_df) / len(all_df)


def _get_val_limits(row, columns, param_name):
    """
    Helper function to read a parameter value and (optionally) its two subsequent limit columns.
    
    If 'param_name' is in the DataFrame columns, we get its value from this row.
    Then we check the *next* two columns (i+1, i+2) but only use them if their column names
    contain 'lim' or 'limit'. If so, we treat them as the lower and upper limit, respectively.
    
    Returns (val, val_lower, val_upper).
     - If param_name doesn't exist in columns, returns (None, None, None).
     - If we can't find limit columns with 'lim'/'limit' in their names, returns (val, None, None).
     - If the user left them blank/NaN, we treat them as None.
    """
    if param_name not in columns:
        return None, None, None
    
    i = columns.get_loc(param_name)
    val = row[param_name]
    if pd.isna(val):
        val = None
    
    val_lower = None
    val_upper = None
    
    # Check the next two columns, but only if they have 'lim' or 'limit' in the name
    if i + 1 < len(columns):
        col1 = columns[i + 1]
        if "lim" in col1.lower() or "limit" in col1.lower():
            tmp = row[col1]
            if pd.notna(tmp):
                val_lower = tmp

    if i + 2 < len(columns):
        col2 = columns[i + 2]
        if "lim" in col2.lower() or "limit" in col2.lower():
            tmp = row[col2]
            if pd.notna(tmp):
                val_upper = tmp
    
    return val, val_lower, val_upper


def main():
    parser = argparse.ArgumentParser(
        description="Calculate reliability or completeness from a given dataset."
    )
    
    # Which function to run
    parser.add_argument(
        "function",
        type=str,
        choices=["reliability", "completeness"],
        help="Which calculation to perform."
    )
    
    # Single-star input parameters (only used if not in batch mode)
    parser.add_argument(
        "--input-period",
        type=float,
        default=None,
        help="Measured rotation period of the star (if doing a single calculation)."
    )
    parser.add_argument(
        "--ls",
        type=float,
        default=None,
        help="Lomb-Scargle power (must be between 0 and 1). (default: None)"
    )
    parser.add_argument(
        "--t",
        type=float,
        default=None,
        help="TESS magnitude. (default: None)"
    )
    parser.add_argument(
        "--snr",
        type=float,
        default=None,
        help="Signal-to-noise ratio. (default: None)"
    )
    
    # Limits
    parser.add_argument(
        "--period-lower-limit",
        type=float,
        default=1.0,
        help="Lower bound for the period window. (default: 1.0)"
    )
    parser.add_argument(
        "--period-upper-limit",
        type=float,
        default=1.0,
        help="Upper bound for the period window. (default: 1.0)"
    )
    parser.add_argument(
        "--ls-lower-limit",
        type=float,
        default=0.05,
        help="Lower bound for Lomb-Scargle power window. (default: 0.05)"
    )
    parser.add_argument(
        "--ls-upper-limit",
        type=float,
        default=0.05,
        help="Upper bound for Lomb-Scargle power window. (default: 0.05)"
    )
    parser.add_argument(
        "--t-lower-limit",
        type=float,
        default=0.5,
        help="Lower bound for TESS magnitude window. (default: 0.5)"
    )
    parser.add_argument(
        "--t-upper-limit",
        type=float,
        default=0.5,
        help="Upper bound for TESS magnitude window. (default: 0.5)"
    )
    parser.add_argument(
        "--snr-lower-limit",
        type=float,
        default=2.5,
        help="Lower bound for the SNR window. (default: 2.5)"
    )
    parser.add_argument(
        "--snr-upper-limit",
        type=float,
        default=2.5,
        help="Upper bound for the SNR window. (default: 2.5)"
    )
    
    # Mode (used only for single-star mode now)
    parser.add_argument(
        "--mode",
        type=str,
        default="match",
        choices=["match", "alias", "recovery"],
        help="Mode for single-star calculation. (default: match)"
    )
    
    # Batch file option
    parser.add_argument(
        "--batch-file",
        type=str,
        default=None,
        help=(
            "Optional CSV with multiple stars/rows. The FIRST column must be the star name. "
            "Each row must have at least 'input_period'. If you include 'ls', 't', 'snr', "
            "the next two columns (if their names contain 'lim'/'limit') will be interpreted "
            "as their lower & upper limits. If missing, the defaults are used."
        )
    )
    
    args = parser.parse_args()
    
    # Read in the main dataframe
    df = pd.read_csv('final_comp_rel_df.csv')
    
    # Decide whether to do single-star or batch processing
    if args.batch_file:
        # BATCH MODE: output file is derived from the batch file name
        batch_filename = os.path.basename(args.batch_file)  # e.g., "my_batch.csv"
        batch_stem, _ = os.path.splitext(batch_filename)    # e.g., "my_batch"
        output_file = f"{batch_stem}_output.csv"            # e.g., "my_batch_output.csv"
        
        # Read the batch CSV
        batch_df = pd.read_csv(args.batch_file)
        
        if batch_df.shape[1] < 2:
            raise ValueError(
                "The batch CSV must have at least 3 columns: "
                "1) star name, 2) input_period, and 3) at least one of 'ls', 't', 'snr'."
            )
        
        # Prepare output columns
        if args.function == "reliability":
            match_list = []
            alias_list = []
            recovery_list = []
        else:  # completeness
            match_list = []
            alias_list = []
            recovery_list = []
        
        star_name_col = batch_df.columns[0]
        
        for idx, row in batch_df.iterrows():
            star_name = str(row[star_name_col])
            
            try:
                input_period = row.get("input_period", None)
                if input_period is None:
                    raise ValueError("Missing 'input_period'.")
                
                # Attempt to get ls & its limits
                ls_val, ls_low, ls_up = _get_val_limits(row, batch_df.columns, "ls")
                # Fall back to command-line defaults if needed
                if ls_val is not None and (ls_low is None or ls_up is None):
                    ls_low = ls_low if ls_low is not None else args.ls_lower_limit
                    ls_up  = ls_up  if ls_up  is not None else args.ls_upper_limit
                
                # Attempt to get t & its limits
                t_val, t_low, t_up = _get_val_limits(row, batch_df.columns, "t")
                if t_val is not None and (t_low is None or t_up is None):
                    t_low = t_low if t_low is not None else args.t_lower_limit
                    t_up  = t_up  if t_up  is not None else args.t_upper_limit
                
                # Attempt to get snr & its limits
                snr_val, snr_low, snr_up = _get_val_limits(row, batch_df.columns, "snr")
                if snr_val is not None and (snr_low is None or snr_up is None):
                    snr_low = snr_low if snr_low is not None else args.snr_lower_limit
                    snr_up  = snr_up  if snr_up  is not None else args.snr_upper_limit
                
                # Now call the appropriate function for each mode
                if args.function == "reliability":
                    r_match = calculate_reliability(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='match'
                    )
                    r_alias = calculate_reliability(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='alias'
                    )
                    r_recovery = calculate_reliability(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='recovery'
                    )
                    match_list.append(r_match)
                    alias_list.append(r_alias)
                    recovery_list.append(r_recovery)
                
                else:  # completeness
                    c_match = calculate_completeness(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='match'
                    )
                    c_alias = calculate_completeness(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='alias'
                    )
                    c_recovery = calculate_completeness(
                        df=df,
                        input_period=input_period,
                        period_lower_limit=args.period_lower_limit,
                        period_upper_limit=args.period_upper_limit,
                        ls=ls_val, 
                        ls_lower_limit=ls_low if ls_low is not None else args.ls_lower_limit, 
                        ls_upper_limit=ls_up  if ls_up  is not None else args.ls_upper_limit,
                        t=t_val, 
                        t_lower_limit=t_low if t_low is not None else args.t_lower_limit, 
                        t_upper_limit=t_up  if t_up  is not None else args.t_upper_limit,
                        snr=snr_val, 
                        snr_lower_limit=snr_low if snr_low is not None else args.snr_lower_limit, 
                        snr_upper_limit=snr_up  if snr_up  is not None else args.snr_upper_limit,
                        mode='recovery'
                    )
                    match_list.append(c_match)
                    alias_list.append(c_alias)
                    recovery_list.append(c_recovery)

            except Exception as e:
                print(f"[Warning] Skipping row {idx} (star: {star_name}): {e}")
                match_list.append(None)
                alias_list.append(None)
                recovery_list.append(None)
        
        # Append new columns
        if args.function == "reliability":
            batch_df["reliability_match"] = match_list
            batch_df["reliability_alias"] = alias_list
            batch_df["reliability_recovery"] = recovery_list
            batch_df.to_csv(output_file, index=False)
            print(f"[Batch Mode] Wrote reliability results to {output_file}")
        else:
            batch_df["completeness_match"] = match_list
            batch_df["completeness_alias"] = alias_list
            batch_df["completeness_recovery"] = recovery_list
            batch_df.to_csv(output_file, index=False)
            print(f"[Batch Mode] Wrote completeness results to {output_file}")
    
    else:
        # SINGLE-STAR MODE
        if args.input_period is None:
            raise ValueError(
                "You must provide --input-period or use --batch-file. "
                "No batch file supplied, so single-star mode expects an input period."
            )
        
        if args.function == "reliability":
            result = calculate_reliability(
                df=df,
                input_period=args.input_period,
                period_lower_limit=args.period_lower_limit,
                period_upper_limit=args.period_upper_limit,
                ls=args.ls,
                ls_lower_limit=args.ls_lower_limit,
                ls_upper_limit=args.ls_upper_limit,
                t=args.t,
                t_lower_limit=args.t_lower_limit,
                t_upper_limit=args.t_upper_limit,
                snr=args.snr,
                snr_lower_limit=args.snr_lower_limit,
                snr_upper_limit=args.snr_upper_limit,
                mode=args.mode
            )
            print(f"Calculated reliability ({args.mode}): {result}")
        
        else:  # COMPLETENESS
            result = calculate_completeness(
                df=df,
                input_period=args.input_period,
                mode=args.mode,
                period_lower_limit=args.period_lower_limit,
                period_upper_limit=args.period_upper_limit,
                ls=args.ls,
                ls_lower_limit=args.ls_lower_limit,
                ls_upper_limit=args.ls_upper_limit,
                t=args.t,
                t_lower_limit=args.t_lower_limit,
                t_upper_limit=args.t_upper_limit,
                snr=args.snr,
                snr_lower_limit=args.snr_lower_limit,
                snr_upper_limit=args.snr_upper_limit
            )
            print(f"Calculated completeness ({args.mode}): {result}")


if __name__ == "__main__":
    main()
