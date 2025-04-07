import pandas as pd
def save_df(papers):
    df = pd.DataFrame(columns=papers[0].keys())
    