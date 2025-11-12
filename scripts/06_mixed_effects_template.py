# Mixed-effects template (statsmodels)
# After pilot, set CORPUS to "masac" or "seame" and use a real feature name.
import pandas as pd
import statsmodels.formula.api as smf

CORPUS = "masac"  # or "seame"
FEAT = f"features/{CORPUS}_disvoice_utt.csv"
df = pd.read_csv(FEAT)

feature = "F0_mean"  # EDIT to a real column

# Example: df = df.merge(prof_df, on="speaker")  # add proficiency later

# Random intercept per speaker; add conversation if available
model = smf.mixedlm(f"{feature} ~ C(condition)", df, groups=df["speaker"])
res = model.fit(method="lbfgs")
print(res.summary())
