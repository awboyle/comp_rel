# comp_rel
The completeness and reliability of TESS rotation

# Reliability and Completeness of TESS Rotation Period Measurements

This repository provides Python code to measure the reliability and completeness of TESS rotation periods.

* **Reliability**: Essentially, “If TESS detects a rotation period for a star, how likely is it to be the true period (or an alias, or a recovered period) given certain parameter constraints?”
* **Completeness**: “Below which parameters (e.g., SNR, Lomb-Scargle power) are we unable to detect a TESS rotation period?”

Example:

Let's say you know the true rotation period for 10 stars, but when you measure their rotation periods, you find that you only recover the true rotation period for 8 of them. In this case, your completeness is 80%. Now, let's say that for the two stars for which you did not recover the true rotation period, you didn't expect to be able to recover the true rotation periods (maybe because the star is faint or has too low of a lomb-scargle power). In this case the reliability is 100% --- you recovered the rotation period for every start for which you expected to be able to recover the rotation period.

The code includes two main functions:

1. `calculate_reliability(...)`
2. `calculate_completeness(...)`

Both functions expect:

* A **master `DataFrame (df)`** containing:
  * The true rotation period of each star (`Prot`). This is provided to the user as the output from Boyle et al. 2025
  * The TESS-measured rotation period and its associated parameters (e.g., `power`, `Tmag`, `snr`, `status`, etc.)
* User-specified input period and parameter constraints (e.g., `Lomb-Scargle power`, `TESS magnitude`, `SNR`) to define which portion of the parameter space is being measured.

The repository also includes a command-line tool (e.g., `calc_comp_rel.py`) that allows users to do:

* **Single-star mode**: Calculate reliability or completeness for a single star using command-line arguments.
* **Batch mode**: Read in a CSV of multiple stars, each with input_period, plus optional parameters (`ls`, `t`, `snr`), along with lower/upper limit columns. The code will:
  1. Calculate either reliability or completeness for each star in all three “modes” (match, alias, recovery)
  2. Append new columns (e.g., `reliability_match`, `reliability_alias`, `reliability_recovery`) to the output CSV
  3. Skip rows that cause errors, insert None for them, and keep processing the rest.
 
## Table of Contents

1. [Installation](#installation)  
2. [Usage](#usage)  
   1. [Single-Star Mode](#single-star-mode)  
   2. [Batch Mode](#batch-mode)  
3. [Command-Line Arguments](#command-line-arguments)  
4. [Description of Output](#description-of-output)  
5. [Example Data Format](#example-data-format)  
6. [Important Notes](#important-notes)  

---

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/awboyle/comp_rel.git
   cd comp_rel
2. **Install dependencies**:
   * Python 3.7+ is recommended.
   * You will also need pandas (and optionally numpy, argparse, etc., if not already installed).

---

## Usage

The main script is `calc_comp_rel.py`, which can be run directly from the command line. Below we show two modes: single-star and batch.

### Single-Star Mode

In single-star mode, you provide arguments like:

* `--input-period`: The measured rotation period you want to evaluate.
* `--mode`: The single mode you want (one of match, alias, recovery).
* Optionally, `--ls`, `--t`, `--snr` and their lower/upper limits, etc.

Example:
```
 python calc_comp_rel.py reliability \
  --input-period 10.0 \
  --ls 0.3 \
  --ls-lower-limit 0.05 \
  --ls-upper-limit 0.05 \
  --mode match
```
This will print a single reliability value to the console, e.g.:
```
Calculated reliability (match): 0.84
```
(Meaning 84% of stars in that parameter/period window match their true rotation period.)

### Batch Mode

In batch mode, you supply a `--batch-file` to process **multiple stars** at once. The code will:

1. Read each row of your batch CSV (which must have a first column of star names, one column called `input_period`, and at least one column title ls, t, snr, with corresponding value in it.
2. Look for the next two columns if their column names contain “lim” or “limit” (e.g. `ls_lower_limit`, `ls_upper_lim`) and use them as the parameter’s lower/upper limit if present. Otherwise, use defaults.
3. Calculate all three modes (match, alias, recovery) for each star.
4. Skip any row that raises an error (e.g., missing input_period), inserting None for that row’s results.
5. Output a new CSV with _output.csv appended to the original batch filename. For reliability, columns will be `reliability_match`, `reliability_alias`, `reliability_recovery`; for completeness, `completeness_match`, `completeness_alias`, `completeness_recovery`.

Example:
```
python calc_comp_rel.py completeness \
  --batch-file my_stars.csv
```
If `my_stars.csv` is:
```
star_name, input_period, ls, ls_lower_limit, ls_upper_limit, snr
StarA, 9.0, 0.25, 0.05, 0.05, 5
StarB, 14.2, , , , 8
StarC, 25.0,0.31 ,0.1 ,0.1 ,
```
The script will produce my_stars_output.csv with added columns: `completeness_match`, `completeness_alias`, `completeness_recovery`.

---

## Command-Line Arguments

* Positional
  * function: `reliability` or `completeness`
* Optional:
  * `--batch-file`: CSV with multiple rows (stars). If specified, calculates all three modes for each row.
  * `--input-period`: (Single-star) The measured rotation period you want to evaluate.
  * `--mode`: (Single-star) One of match, alias, or recovery.
  * `--ls`, `--t`, `--snr`: Parameter values for Lomb-Scargle power, TESS magnitude, and SNR (single-star).
  * `--ls-lower-limit`, `--ls-upper-limit`, etc.: Defaults for lower/upper limits if not found in CSV or not provided in single-star mode.
 * `--period-lower-limit`, `--period-upper-limit`: Bounds on the period window (defaults: 1.0 and 1.0).

Run:
```
python calc_comp_rel.py --help
```
for more details.

---

## Description of Output

### Reliability

* `reliability_match`: Fraction of stars within the specified parameter/period window whose TESS-measured period is exactly “match” (status == 'match').
* `reliability_alias`: Fraction that’s labeled “alias” (status == 'alias').
* `reliability_recovery`: Fraction that’s not labeled “not_recovered” (i.e., either match or alias).

### Completeness

* `completeness_match`: Among all the stars in that true-period window, how many were measured to be “match”?
* `completeness_alias`: Among all the stars in that window, how many were measured as “alias”?
* `completeness_recovery`: Among all the stars in that window, how many were measured as either “match” or “alias” (i.e., not “not_recovered”).

(Strictly speaking, you can interpret completeness as “the fraction of stars in a given parameter space for which TESS returns a valid period [match or alias].”)

## Example Data Format

Your batch CSV (`my_stars.csv`) might look like:
```
star_name,input_period,ls,ls_lower_limit,ls_upper_limit,snr, snr_lower_limit, snr_upper_limit
StarA,9.0,0.25,0.05,0.05,5,2.0,3.0
StarB,14.2,,,,8,,
StarC,25.0,0.31,0.1,0.1,,
```
* The script will parse `ls` and pick up `ls_lower_limit` and `ls_upper_limit` if their column names contain “_limit” or “_lim”.
* If a parameter column is present but the limit columns are missing or empty, the code uses default limits.
* If `snr_lower_limit` and `snr_upper_limit` are missing or empty, it again reverts to default values from the command-line arguments.

---

## Important Notes

1. **Assertion Checks**: The functions `calculate_reliability` and `calculate_completeness` enforce certain assertions (e.g., `ls` must be between 0 and 1, `snr` > 0, `input_period` > 0). Rows in your batch file that fail these checks will be skipped, and None is inserted for those rows.
2. **Skipping Errors**: In batch mode, any row that raises an error does not stop the entire script. It logs a warning to the console and moves on to the next row.
3. **Customization**: You can customize the code to point to your own DataFrame columns (e.g. renaming `power` to `lombscargle_power`) and adjust the logic for reliability/completeness as needed.




