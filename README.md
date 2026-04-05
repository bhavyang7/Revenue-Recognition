# Revenue Recognition Tool

A revenue recognition engine and interactive dashboard built on the Australian SME Business Dataset (Outback Outdoor Supplies Pty Ltd).

Implements the **IFRS 15 / ASC 606 five-step model**:
1. Identify contracts with customers
2. Identify performance obligations
3. Determine transaction price
4. Allocate transaction price to performance obligations
5. Recognise revenue when/as obligations are satisfied

---

## Features

- **Recognition Engine** — line-level schedule with allocated, recognised, and deferred revenue per invoice
- **Contract Modification Detection** — automatically flags three IFRS 15 modification types:
  - Type A: Price reductions post-order
  - Type B: Partial scope delivery
  - Type C: Partial payment arrangements (constrained variable consideration)
- **Deferred Revenue Roll-Forward** — period-by-period waterfall of opening balance, newly deferred, released, and closing balance
- **AR Aging** — buckets outstanding receivables into Current, 1–30, 31–60, 61–90, and 90+ days
- **Journal Reconciliation** — compares recognised revenue against posted GL entries
- **Streamlit Dashboard** — 9-tab interactive UI with charts, filters, and CSV export

---

## Project Structure

```
Project1/
├── dashboard.py                      # Streamlit dashboard (9 tabs)
├── revenue_recognition.py            # Core engine + CLI reports
├── dataset/                          # Source CSV files
│   ├── sales_invoices_sample.csv
│   ├── sales_orders_sample.csv
│   ├── sales_order_lines_sample.csv
│   ├── journal_entries_sample.csv
│   ├── journal_entry_lines_sample.csv
│   ├── customers.csv
│   ├── products.csv
│   ├── companies.csv
│   └── ...
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install pandas streamlit plotly matplotlib
```

### 2. Run the dashboard

```bash
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

### 3. Run CLI reports only

```bash
python3 revenue_recognition.py
```

Outputs a summary report to the terminal and exports:
- `revenue_recognition_schedule.csv`
- `contract_modifications.csv`

---

## Dataset

[Australian SME Business Dataset](https://www.kaggle.com/datasets/mindweavetech/australian-sme-business-dataset) — a synthetic dataset representing a small Australian outdoor equipment retailer with tables covering sales, purchasing, payroll, inventory, fixed assets, and accounting.
