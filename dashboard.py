"""
Revenue Recognition Dashboard — Streamlit
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from revenue_recognition import (
    load_data,
    detect_contract_modifications,
    build_recognition_schedule,
    build_deferred_rollforward,
    build_ar_aging,
    build_journal_reconciliation,
)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title='Revenue Recognition',
    page_icon='📊',
    layout='wide',
)

st.title('📊 Revenue Recognition Tool')
st.caption('Outback Outdoor Supplies Pty Ltd — IFRS 15 / ASC 606')

# ─────────────────────────────────────────────────────────────
# LOAD & COMPUTE
# ─────────────────────────────────────────────────────────────

@st.cache_data
def get_all_data():
    invoices, orders, lines, customers, products, coa, je, jel = load_data()
    mods     = detect_contract_modifications(invoices, orders, lines)
    schedule = build_recognition_schedule(invoices, orders, lines, products, mods)
    rollfw   = build_deferred_rollforward(schedule)
    ar, _    = build_ar_aging(invoices, customers)
    recon    = build_journal_reconciliation(schedule, je, jel, coa)
    return invoices, orders, lines, customers, products, coa, je, jel, mods, schedule, rollfw, ar, recon

invoices, orders, lines, customers, products, coa, je, jel, \
    mods, schedule, rollfw, ar, recon = get_all_data()

# ─────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header('Filters')

    periods = sorted(schedule['period'].dropna().astype(str).unique())
    selected_periods = st.multiselect('Period(s)', periods, default=periods)

    categories = sorted(schedule['category'].dropna().unique())
    selected_cats = st.multiselect('Product Category', categories, default=categories)

    statuses = sorted(schedule['invoice_status'].dropna().unique())
    selected_status = st.multiselect('Invoice Status', statuses, default=statuses)

    st.divider()
    st.caption('IFRS 15 / ASC 606 — 5-step model')
    st.caption('Point-in-time recognition (goods delivered)')

# Apply filters
filtered = schedule[
    schedule['period'].astype(str).isin(selected_periods) &
    schedule['category'].isin(selected_cats) &
    schedule['invoice_status'].isin(selected_status)
]

# ─────────────────────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────────────────────

tabs = st.tabs([
    '📈 Overview',
    '📅 Monthly Schedule',
    '⏳ Deferred Roll-Forward',
    '🏷️ By Category & Product',
    '👥 By Customer',
    '🔔 AR Aging',
    '⚠️ Contract Modifications',
    '🔍 Journal Reconciliation',
    '📋 Raw Schedule',
])

# ─────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────

with tabs[0]:
    total_invoiced   = invoices['subtotal'].sum()
    total_recognised = filtered['recognised_revenue'].sum()
    total_deferred   = filtered['deferred_revenue'].sum()
    total_ar         = invoices['amount_due'].sum()
    recog_rate       = total_recognised / filtered['allocated_revenue'].sum() * 100 if filtered['allocated_revenue'].sum() > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Total Invoiced (ex-GST)', f'${total_invoiced:,.0f}')
    c2.metric('Recognised Revenue',      f'${total_recognised:,.0f}')
    c3.metric('Deferred Revenue',        f'${total_deferred:,.0f}')
    c4.metric('AR Outstanding',          f'${total_ar:,.0f}')
    c5.metric('Recognition Rate',        f'{recog_rate:.1f}%')

    st.divider()

    col_left, col_right = st.columns(2)

    # Revenue recognised vs deferred by month
    monthly = (
        filtered.groupby(filtered['period'].astype(str))
        .agg(recognised=('recognised_revenue','sum'), deferred=('deferred_revenue','sum'))
        .reset_index().rename(columns={'period':'Period'})
    )
    fig_monthly = go.Figure()
    fig_monthly.add_bar(x=monthly['Period'], y=monthly['recognised'], name='Recognised', marker_color='#2ecc71')
    fig_monthly.add_bar(x=monthly['Period'], y=monthly['deferred'],   name='Deferred',   marker_color='#e67e22')
    fig_monthly.update_layout(barmode='stack', title='Revenue by Month', xaxis_title='Period',
                               yaxis_title='AUD', height=350)
    col_left.plotly_chart(fig_monthly, use_container_width=True)

    # Category donut
    cat_data = (
        filtered.groupby('category')['recognised_revenue'].sum()
        .reset_index().sort_values('recognised_revenue', ascending=False)
    )
    fig_cat = px.pie(cat_data, values='recognised_revenue', names='category',
                     title='Recognised Revenue by Category', hole=0.45, height=350)
    fig_cat.update_traces(textposition='inside', textinfo='percent+label')
    col_right.plotly_chart(fig_cat, use_container_width=True)

    # Recognition status breakdown
    status_counts = filtered['recognition_status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Lines']
    col_left2, col_right2 = st.columns(2)
    fig_status = px.bar(status_counts, x='Status', y='Lines',
                        color='Status', title='Lines by Recognition Status',
                        color_discrete_map={
                            'recognised':'#2ecc71',
                            'partially_recognised':'#e67e22',
                            'unrecognised':'#e74c3c'
                        }, height=300)
    col_left2.plotly_chart(fig_status, use_container_width=True)

    # Top 5 customers
    top_cust = (
        filtered.groupby('customer_id')['recognised_revenue'].sum()
        .reset_index()
        .merge(customers[['id','name']].rename(columns={'id':'customer_id'}), on='customer_id', how='left')
        .sort_values('recognised_revenue', ascending=False).head(5)
    )
    fig_cust = px.bar(top_cust, x='recognised_revenue', y='name', orientation='h',
                      title='Top 5 Customers', labels={'recognised_revenue':'Recognised','name':''},
                      color='recognised_revenue', color_continuous_scale='Teal', height=300)
    fig_cust.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
    col_right2.plotly_chart(fig_cust, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 2 — MONTHLY SCHEDULE
# ─────────────────────────────────────────────────────────────

with tabs[1]:
    st.subheader('Monthly Revenue Recognition Schedule')
    monthly_full = (
        filtered.groupby(filtered['period'].astype(str))
        .agg(
            invoices       = ('invoice_id','nunique'),
            gross_revenue  = ('allocated_revenue','sum'),
            recognised     = ('recognised_revenue','sum'),
            deferred       = ('deferred_revenue','sum'),
        )
        .reset_index().rename(columns={'period':'Period'})
    )
    monthly_full['Recog %'] = (monthly_full['recognised'] / monthly_full['gross_revenue'] * 100).round(1)

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_bar(x=monthly_full['Period'], y=monthly_full['gross_revenue'],  name='Gross Invoiced', marker_color='#95a5a6')
    fig.add_bar(x=monthly_full['Period'], y=monthly_full['recognised'],     name='Recognised',     marker_color='#2ecc71')
    fig.add_bar(x=monthly_full['Period'], y=monthly_full['deferred'],       name='Deferred',       marker_color='#e67e22')
    fig.add_scatter(x=monthly_full['Period'], y=monthly_full['Recog %'],    name='Recog %',
                    mode='lines+markers', line=dict(color='#8e44ad', width=2), secondary_y=True)
    fig.update_layout(barmode='group', height=420, title='Monthly Revenue Breakdown')
    fig.update_yaxes(title_text='AUD', secondary_y=False)
    fig.update_yaxes(title_text='Recognition %', secondary_y=True, range=[0,110])
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        monthly_full.style.format({
            'gross_revenue': '${:,.2f}', 'recognised': '${:,.2f}',
            'deferred': '${:,.2f}', 'Recog %': '{:.1f}%'
        }),
        use_container_width=True, hide_index=True
    )


# ─────────────────────────────────────────────────────────────
# TAB 3 — DEFERRED ROLL-FORWARD
# ─────────────────────────────────────────────────────────────

with tabs[2]:
    st.subheader('Deferred Revenue Roll-Forward')
    st.caption('Tracks how deferred revenue moves between periods as partial payments resolve.')

    fig_rf = go.Figure()
    fig_rf.add_bar(x=rollfw['period'], y=rollfw['newly_deferred'],      name='Newly Deferred',      marker_color='#e67e22')
    fig_rf.add_bar(x=rollfw['period'], y=rollfw['released_to_revenue'], name='Released to Revenue',  marker_color='#2ecc71')
    fig_rf.add_scatter(x=rollfw['period'], y=rollfw['closing_deferred'],
                       name='Closing Balance', mode='lines+markers',
                       line=dict(color='#8e44ad', width=2, dash='dash'))
    fig_rf.update_layout(barmode='group', height=380,
                         title='Deferred Revenue Movement', yaxis_title='AUD')
    st.plotly_chart(fig_rf, use_container_width=True)

    st.dataframe(
        rollfw.style.format({c: '${:,.2f}' for c in rollfw.columns if c != 'period'}),
        use_container_width=True, hide_index=True
    )

    with st.expander('Accounting Policy Note'):
        st.markdown("""
**Deferred Revenue Recognition Policy (IFRS 15.56)**

Revenue is constrained when there is uncertainty about whether payment will be received.
For partially-paid invoices, only the collected portion of the transaction price is recognised.
The remaining amount is held as deferred (constrained) revenue until:
- Payment is received, or
- The constraint is lifted (e.g. enforceable right to payment established)

**Roll-forward mechanics:**
- *Newly Deferred* = deferred revenue created from partially-paid invoices issued this period
- *Released to Revenue* = prior-period deferred amounts now recognised (constraint lifted)
- *Closing Balance* = cumulative deferred revenue remaining at period end
""")


# ─────────────────────────────────────────────────────────────
# TAB 4 — BY CATEGORY & PRODUCT
# ─────────────────────────────────────────────────────────────

with tabs[3]:
    st.subheader('Revenue by Category & Product')

    cat_detail = (
        filtered.groupby(['category','product_name'])
        .agg(qty=('quantity','sum'), gross=('allocated_revenue','sum'),
             recognised=('recognised_revenue','sum'), deferred=('deferred_revenue','sum'))
        .reset_index()
    )
    cat_detail['margin_proxy'] = (
        (cat_detail['recognised'] -
         cat_detail['qty'] * filtered.merge(
             products[['id','cost_price']].rename(columns={'id':'product_id'}),
             on='product_id', how='left'
         ).groupby('product_name')['cost_price'].first().reindex(cat_detail['product_name']).values
         * cat_detail['qty']) / cat_detail['recognised'].replace(0, float('nan')) * 100
    ).round(1)

    col1, col2 = st.columns(2)

    fig_treemap = px.treemap(
        cat_detail, path=['category','product_name'],
        values='recognised', color='recognised',
        color_continuous_scale='Teal',
        title='Revenue Treemap — Category → Product'
    )
    fig_treemap.update_layout(height=450)
    col1.plotly_chart(fig_treemap, use_container_width=True)

    cat_sum = (
        filtered.groupby('category')
        .agg(recognised=('recognised_revenue','sum'), deferred=('deferred_revenue','sum'))
        .sort_values('recognised').reset_index()
    )
    fig_hbar = px.bar(cat_sum, x='recognised', y='category', orientation='h',
                      color='recognised', color_continuous_scale='Teal',
                      title='Recognised Revenue by Category', height=400)
    fig_hbar.update_layout(coloraxis_showscale=False, yaxis_title='')
    col2.plotly_chart(fig_hbar, use_container_width=True)

    st.subheader('Product Detail')
    st.dataframe(
        cat_detail.sort_values('recognised', ascending=False)
        .style.format({'qty': '{:,.0f}', 'gross': '${:,.2f}',
                       'recognised': '${:,.2f}', 'deferred': '${:,.2f}'}),
        use_container_width=True, hide_index=True
    )


# ─────────────────────────────────────────────────────────────
# TAB 5 — BY CUSTOMER
# ─────────────────────────────────────────────────────────────

with tabs[4]:
    st.subheader('Revenue by Customer')

    cust_rev = (
        filtered.groupby('customer_id')
        .agg(invoices=('invoice_id','nunique'), recognised=('recognised_revenue','sum'),
             deferred=('deferred_revenue','sum'), gross=('allocated_revenue','sum'))
        .reset_index()
        .merge(customers[['id','name','customer_type','payment_terms_days','reliability']]
               .rename(columns={'id':'customer_id'}), on='customer_id', how='left')
        .sort_values('recognised', ascending=False)
    )
    cust_rev['recog_rate'] = (cust_rev['recognised'] / cust_rev['gross'] * 100).round(1)

    top_n = st.slider('Show top N customers', 5, len(cust_rev), 15)
    top = cust_rev.head(top_n)

    col1, col2 = st.columns(2)

    fig_cust = px.bar(top.sort_values('recognised'), x='recognised', y='name',
                      orientation='h', color='customer_type',
                      title=f'Top {top_n} Customers by Recognised Revenue',
                      labels={'recognised':'Recognised Revenue','name':''},
                      color_discrete_map={'business':'#2980b9','individual':'#27ae60'},
                      height=max(350, top_n * 28))
    fig_cust.update_layout(yaxis={'categoryorder':'total ascending'})
    col1.plotly_chart(fig_cust, use_container_width=True)

    fig_scatter = px.scatter(
        cust_rev, x='reliability', y='recognised',
        color='customer_type', size='invoices', hover_name='name',
        title='Customer Reliability vs Recognised Revenue',
        labels={'reliability':'Reliability Score','recognised':'Recognised Revenue'},
        color_discrete_map={'business':'#2980b9','individual':'#27ae60'},
        height=420
    )
    col2.plotly_chart(fig_scatter, use_container_width=True)

    st.dataframe(
        top[['name','customer_type','payment_terms_days','invoices',
             'recognised','deferred','recog_rate','reliability']]
        .style.format({'recognised':'${:,.2f}','deferred':'${:,.2f}',
                       'recog_rate':'{:.1f}%','reliability':'{:.2f}'}),
        use_container_width=True, hide_index=True
    )


# ─────────────────────────────────────────────────────────────
# TAB 6 — AR AGING
# ─────────────────────────────────────────────────────────────

with tabs[5]:
    st.subheader('Accounts Receivable Aging')

    bucket_order = ['Current','1–30 days','31–60 days','61–90 days','90+ days']
    aging_summary = (
        ar.groupby('aging_bucket')
        .agg(invoices=('id','count'), amount=('amount_due','sum'))
        .reindex(bucket_order).fillna(0).reset_index()
    )
    aging_summary.columns = ['Bucket','Invoices','Amount Due']

    col1, col2 = st.columns(2)

    color_map = {
        'Current':    '#2ecc71',
        '1–30 days':  '#f1c40f',
        '31–60 days': '#e67e22',
        '61–90 days': '#e74c3c',
        '90+ days':   '#8e44ad',
    }
    fig_aging = px.bar(aging_summary, x='Bucket', y='Amount Due',
                       color='Bucket', color_discrete_map=color_map,
                       title='AR by Aging Bucket', text_auto='.2s', height=350)
    fig_aging.update_layout(showlegend=False)
    col1.plotly_chart(fig_aging, use_container_width=True)

    fig_pie = px.pie(aging_summary[aging_summary['Amount Due'] > 0],
                     values='Amount Due', names='Bucket',
                     color='Bucket', color_discrete_map=color_map,
                     hole=0.45, title='AR Distribution', height=350)
    col2.plotly_chart(fig_pie, use_container_width=True)

    col1.metric('Total AR Outstanding', f'${ar["amount_due"].sum():,.2f}')
    col2.metric('Overdue (>0 days)', f'${ar[ar["days_overdue"]>0]["amount_due"].sum():,.2f}')

    st.subheader('Overdue Invoice Detail')
    overdue = ar[ar['days_overdue'] > 0].sort_values('days_overdue', ascending=False)
    st.dataframe(
        overdue[['invoice_number','customer_name','customer_type','due_date',
                 'amount_due','days_overdue','aging_bucket','reliability']]
        .style.format({'amount_due':'${:,.2f}','reliability':'{:.2f}'})
        .background_gradient(subset=['days_overdue'], cmap='Reds'),
        use_container_width=True, hide_index=True
    )


# ─────────────────────────────────────────────────────────────
# TAB 7 — CONTRACT MODIFICATIONS
# ─────────────────────────────────────────────────────────────

with tabs[6]:
    st.subheader('Contract Modifications (IFRS 15.18–21)')

    if mods.empty:
        st.success('No contract modifications detected.')
    else:
        type_counts = mods['modification_type'].value_counts().reset_index()
        type_counts.columns = ['Type','Count']

        col1, col2, col3 = st.columns(3)
        col1.metric('Total Modifications', len(mods))
        col2.metric('Total Revenue Impact', f'${mods["amount_impact"].sum():,.2f}')
        col3.metric('Affected Invoices', mods['invoice_number'].nunique())

        fig_mods = px.bar(type_counts, x='Type', y='Count', color='Type',
                          title='Modifications by Type', height=300)
        fig_mods.update_layout(showlegend=False, xaxis_tickangle=-20)
        st.plotly_chart(fig_mods, use_container_width=True)

        st.subheader('Modification Detail')
        for mod_type in mods['modification_type'].unique():
            subset = mods[mods['modification_type'] == mod_type]
            with st.expander(f'{mod_type}  ({len(subset)} instances)', expanded=True):
                for _, row in subset.iterrows():
                    st.markdown(f"""
**{row["invoice_number"]}**
- Detail: {row["detail"]}
- Revenue impact: `${row["amount_impact"]:,.2f}`
- Treatment: _{row["treatment"]}_
---""")

        with st.expander('IFRS 15 Treatment Guide'):
            st.markdown("""
| Type | Scenario | Treatment |
|------|----------|-----------|
| A — Price Reduction | Discount agreed after original order | Cumulative catch-up in current period |
| B — Partial Scope | Fewer goods delivered than contracted | Treat as separate contract; recognise delivered obligations only |
| C — Partial Payment | Customer paying in instalments / dispute | Constrain variable consideration; recognise only collected amount |
""")


# ─────────────────────────────────────────────────────────────
# TAB 8 — JOURNAL RECONCILIATION
# ─────────────────────────────────────────────────────────────

with tabs[7]:
    st.subheader('Journal Entry Reconciliation')

    col1, col2, col3 = st.columns(3)
    col1.metric('Posted Revenue (GL)',       f'${recon["posted_revenue"]:,.2f}')
    col2.metric('Recognition Schedule',     f'${recon["schedule_revenue"]:,.2f}')
    delta_color = 'normal' if recon['reconciled'] else 'inverse'
    col3.metric('Variance', f'${recon["variance"]:,.2f}',
                delta=f'{"✓ Reconciled" if recon["reconciled"] else "⚠ Investigate"}',
                delta_color=delta_color)

    if not recon['reconciled']:
        st.warning(recon['note'])

    st.subheader('Revenue Account Journal Lines')
    rev_detail = recon['revenue_account_detail']
    if not rev_detail.empty:
        cols_show = [c for c in ['entry_date','description','source_module','code','name','debit','credit'] if c in rev_detail.columns]
        st.dataframe(
            rev_detail[cols_show]
            .sort_values('entry_date') if 'entry_date' in rev_detail.columns
            else rev_detail[cols_show],
            use_container_width=True, hide_index=True
        )

        by_account = rev_detail.groupby('name')[['debit','credit']].sum().reset_index()
        by_account['net_credit'] = by_account['credit'] - by_account['debit']
        fig_recon = px.bar(by_account, x='name', y='net_credit',
                           title='Net Revenue Posted by Account',
                           labels={'name':'Account','net_credit':'Net Credit (AUD)'},
                           color='net_credit', color_continuous_scale='Teal', height=350)
        fig_recon.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_recon, use_container_width=True)

    with st.expander('Reconciliation Notes'):
        st.markdown("""
**Why is there a variance?**

Both `journal_entries_sample.csv` and `sales_order_lines_sample.csv` are *sample* extracts
covering a subset of invoices. A full GL load would bring the two figures into agreement.

**Steps to fully reconcile:**
1. Load complete journal entry lines for all posted revenue-account entries
2. Match each journal entry `source_id` to its invoice
3. Compare net credit per invoice to `recognised_revenue` in the schedule
4. Investigate any remaining differences as potential timing or classification issues
""")


# ─────────────────────────────────────────────────────────────
# TAB 9 — RAW SCHEDULE
# ─────────────────────────────────────────────────────────────

with tabs[8]:
    st.subheader('Line-Level Recognition Schedule')

    search = st.text_input('Search invoice / product / category', '')
    disp = filtered.copy()
    if search:
        mask = (
            disp['invoice_number'].str.contains(search, case=False, na=False) |
            disp['product_name'].str.contains(search, case=False, na=False) |
            disp['category'].str.contains(search, case=False, na=False)
        )
        disp = disp[mask]

    st.caption(f'{len(disp):,} lines shown')
    cols = ['period','invoice_date','invoice_number','invoice_status','product_name',
            'category','quantity','unit_price','discount_percent','line_total',
            'allocated_revenue','recognised_revenue','deferred_revenue','recognition_status']
    st.dataframe(
        disp[cols].sort_values(['invoice_date','invoice_number'])
        .style.format({
            'unit_price':'${:,.2f}','line_total':'${:,.2f}',
            'allocated_revenue':'${:,.2f}','recognised_revenue':'${:,.2f}',
            'deferred_revenue':'${:,.2f}','discount_percent':'{:.1f}%',
        })
        .applymap(lambda v: 'background-color:#d5f5e3' if v == 'recognised'
                  else ('background-color:#fdebd0' if v == 'partially_recognised'
                        else ''), subset=['recognition_status']),
        use_container_width=True, hide_index=True, height=500
    )

    st.download_button(
        '⬇ Download Schedule CSV',
        data=disp[cols].to_csv(index=False).encode(),
        file_name='revenue_recognition_schedule.csv',
        mime='text/csv',
    )
