
import numpy as np, pandas as pd
def fixed_window(df, start='10:00', end='11:00', time_col='timestamp'):
    mask = (df[time_col].dt.strftime('%H:%M') >= start) & (df[time_col].dt.strftime('%H:%M') <= end)
    return df.loc[mask].copy()
def nirs_feature_frame(df, side_col='side', value_cols=('hbo','hbt','pump_rpm','flow_l_min')):
    non_cann = df.loc[df[side_col]=='non_cannulated'].copy() if side_col in df else df.copy()
    out = {}
    for c in value_cols:
        if c in non_cann:
            s = non_cann[c].astype(float)
            out[f'{c}_mean'] = s.mean(); out[f'{c}_std'] = s.std()
            out[f'{c}_slope'] = (s.iloc[-1]-s.iloc[0]) / max(len(s)-1,1)
    return pd.DataFrame([out])
