# 📊 Finance Invoice Coding Tool

This Streamlit app helps finance teams efficiently **code invoices** using a **Chart of Accounts (CoA)** that maps to both **Shipsure** and **HFM** accounts.

---

## 🚀 Features

- Upload invoices in `.xlsx`, `.csv`, or `.pdf`
- Chart of Accounts is preloaded (no upload needed)
- Auto-suggested account mappings via fuzzy matching
- Manual override and selection
- Download final coded invoices in `.csv`

---

## 📁 Input Expectations

### ✅ Chart of Accounts

Stored in the repo: `coa_data/chart_of_accounts.csv`

Example format:

```csv
Shipsure Account Number,Shipsure Account Description,Account Type,HFM Account Number,HFM Account Description
1001,Crew Costs,Income Statement,70001,Crew Expense
2001,Port Charges,Income Statement,70002,Port Costs
