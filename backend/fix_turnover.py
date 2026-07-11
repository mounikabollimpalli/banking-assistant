with open("import_data.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'credit_score = row.get("Credit_Score")',
    'credit_score = row.get("Credit_Score")\n        annual_turnover = row.get("Annual_Turnover")'
)

content = content.replace(
    'credit_score=int(credit_score) if pd.notna(credit_score) else None,',
    'credit_score=int(credit_score) if pd.notna(credit_score) else None,\n            annual_turnover=float(annual_turnover) if pd.notna(annual_turnover) else None,'
)

with open("import_data.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")