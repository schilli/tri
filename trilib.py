import fitparse
import numpy as np
import pandas as pd
import datetime

def fit2df(filename):

    fitfile = fitparse.FitFile(filename)

    df = []
    units = {}
    for record in fitfile.get_messages("record"):
        row = {}
        for data in record:
            row[data.name]   = data.value
            try:
                units[data.name].append(data.units)
            except KeyError:
                units[data.name] = [data.units]
        df.append(row)
        
    df = pd.DataFrame(df)
    
    for name in units:
        units[name] = set(units[name])
    
    return df, units


def make_timedelta(s, decimal_sep=','):
    t = s.split(decimal_sep)
    if len(t) == 1:
        t, tenth = t[0], 0
    else:
        t, tenth =  t
        
    t = [n.zfill(2) for n in t.split(':')]
    if len(t) == 2:
        t = ['00'] + t
    t = pd.Timedelta(':'.join(t))
    t += pd.Timedelta(seconds=0.1*int(tenth))
    return t


def read_rounds(filename, starttime=None):
    if starttime is None:
        starttime = datetime.datetime.today()
    
    rounds = pd.read_csv(filename)

    rounds.Zeit = rounds.Zeit.apply(lambda t: make_timedelta(t))
    rounds.Gesamtzeit = rounds.Gesamtzeit.apply(lambda t: make_timedelta(t))

    rounds['start'] = starttime + (rounds.Gesamtzeit - rounds.Zeit)
    rounds['end']   = starttime + rounds.Gesamtzeit
    
    return rounds


def best_one_minute_power(df, power_col='power'):
    """Compute the best one minute power."""
    dt = (df.timestamp.values[1:] - df.timestamp.values[:-1]).mean()
    rows_per_minute = round(np.timedelta64(60, 's') / dt)
    best_1m_power = df[[power_col]].rolling(rows_per_minute).mean().max().iloc[0]
    return best_1m_power


def ftp_ramp_test(df):
    """Compute the FTP from a ramp test as 75 % of the best one minute power.
    https://support.trainerroad.com/hc/en-us/articles/360006903031-Ramp-Test-FAQs"""
    return round(0.75*best_one_minute_power(df))