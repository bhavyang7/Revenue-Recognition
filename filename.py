import pandas as pd
import os

dataset_path = 'dataset'

# Load a sample from key tables
companies = pd.read_csv(os.path.join(dataset_path, 'companies.csv'))
sales_invoices = pd.read_csv(os.path.join(dataset_path, 'sales_invoices_sample.csv'))
bank_transactions = pd.read_csv(os.path.join(dataset_path, 'bank_transactions_sample.csv'))

print("=== Companies (sample) ===")
print(companies.head(5))
print(f"\nShape: {companies.shape} | Columns: {companies.columns.tolist()}\n")

print("=== Sales Invoices (sample) ===")
print(sales_invoices.head(5))
print(f"\nShape: {sales_invoices.shape} | Columns: {sales_invoices.columns.tolist()}\n")

print("=== Bank Transactions (sample) ===")
print(bank_transactions.head(5))
print(f"\nShape: {bank_transactions.shape} | Columns: {bank_transactions.columns.tolist()}\n")
