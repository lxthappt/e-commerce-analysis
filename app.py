import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# ===== 页面配置 =====
st.set_page_config(
    page_title="Olist 电商数据分析 Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Olist 巴西电商数据分析平台")
st.markdown(
    "数据范围：2016.09 - 2018.10 | "
    "数据来源：[Kaggle Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)"
)

# ===== 加载数据（缓存 — 避免每次交互都重新跑） =====
@st.cache_data
def load_data():
    """加载 9 张表 → JOIN → 清洗 → 返回分析用宽表"""
    # 读取所有表
    orders = pd.read_csv('data/olist_orders_dataset.csv')
    customers = pd.read_csv('data/olist_customers_dataset.csv')
    order_items = pd.read_csv('data/olist_order_items_dataset.csv')
    order_payments = pd.read_csv('data/olist_order_payments_dataset.csv')
    order_reviews = pd.read_csv('data/olist_order_reviews_dataset.csv')
    products = pd.read_csv('data/olist_products_dataset.csv')
    sellers = pd.read_csv('data/olist_sellers_dataset.csv')
    category_translation = pd.read_csv('data/product_category_name_translation.csv')

    # 日期转换
    date_cols = ['order_purchase_timestamp', 'order_approved_at',
                 'order_delivered_carrier_date', 'order_delivered_customer_date',
                 'order_estimated_delivery_date']
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col])

    # 只保留 delivered
    orders = orders[orders['order_status'] == 'delivered'].copy()

    # payments 聚合
    payments_agg = order_payments.groupby('order_id').agg({
        'payment_value': 'sum',
        'payment_type': lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0],
        'payment_installments': 'max'
    }).reset_index()
    payments_agg.columns = ['order_id', 'total_payment', 'payment_type', 'max_installments']

    # reviews 聚合
    reviews_agg = order_reviews.groupby('order_id').agg({
        'review_score': 'min',
        'review_comment_message': 'first'
    }).reset_index()

    # JOIN
    df = order_items.merge(orders, on='order_id', how='left')
    df = df.merge(products[['product_id', 'product_category_name']], on='product_id', how='left')
    df = df.merge(category_translation, on='product_category_name', how='left')
    df = df.merge(customers[['customer_id', 'customer_unique_id', 'customer_state']],
                  on='customer_id', how='left')
    df = df.merge(payments_agg, on='order_id', how='left')
    df = df.merge(reviews_agg, on='order_id', how='left')
    df = df.merge(sellers[['seller_id', 'seller_state']], on='seller_id', how='left')

    # 计算列
    df['delivery_days'] = (df['order_delivered_customer_date'] -
                            df['order_purchase_timestamp']).dt.days
    df['item_total'] = df['price'] + df['freight_value']
    df['purchase_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)

    # 清洗
    df['product_category_name_english'] = df['product_category_name_english'].fillna('unknown')
    df = df[df['price'] > 0]
    df = df[df['delivery_days'] >= 0]

    return df

df = load_data()

# ===== 侧边栏筛选器 =====
st.sidebar.header("🔍 筛选条件")

# 时间筛选
date_min = df['order_purchase_timestamp'].min().date()
date_max = df['order_purchase_timestamp'].max().date()
date_range = st.sidebar.date_input(
    "订单日期范围",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

# 州筛选
all_states = sorted(df['customer_state'].dropna().unique())
selected_states = st.sidebar.multiselect("选择州（留空=全选）", options=all_states, default=[])

# 品类筛选
all_cats = sorted(df['product_category_name_english'].dropna().unique())
selected_cats = st.sidebar.multiselect("选择品类（留空=全选）", options=all_cats, default=[])

# 应用筛选
filtered = df.copy()
if len(date_range) == 2:
    filtered = filtered[
        (filtered['order_purchase_timestamp'].dt.date >= date_range[0]) &
        (filtered['order_purchase_timestamp'].dt.date <= date_range[1])
    ]
if selected_states:
    filtered = filtered[filtered['customer_state'].isin(selected_states)]
if selected_cats:
    filtered = filtered[filtered['product_category_name_english'].isin(selected_cats)]

# ===== KPI 指标卡片 =====
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 总订单数", f"{filtered['order_id'].nunique():,}")
with col2:
    st.metric("💰 总 GMV", f"R$ {filtered['item_total'].sum():,.0f}")
with col3:
    st.metric("👥 总客户数", f"{filtered['customer_unique_id'].nunique():,}")
with col4:
    avg_score = filtered['review_score'].dropna().mean()
    st.metric("⭐ 平均评分", f"{avg_score:.2f}")
with col5:
    avg_delivery = filtered['delivery_days'].mean()
    st.metric("🚚 平均配送", f"{avg_delivery:.1f} 天")
st.markdown("---")

# ===== Tab 页签 =====
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 时间趋势", "🌍 地理分布", "👥 客户分析", "📦 产品 & 支付"
])

# ----- Tab 1：时间趋势 -----
with tab1:
    st.subheader("月度 GMV 与订单量趋势")

    monthly = filtered.groupby('purchase_month').agg({
        'order_id': 'nunique',
        'item_total': 'sum'
    }).reset_index()
    monthly.columns = ['Month', 'Orders', 'GMV']

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly['Month'], y=monthly['GMV'],
        mode='lines+markers', name='GMV (R$)',
        line=dict(color='#6b5500', width=3),
        fill='tozeroy', fillcolor='rgba(107,85,0,0.15)'
    ))
    fig.add_trace(go.Scatter(
        x=monthly['Month'], y=monthly['Orders'],
        mode='lines+markers', name='Orders',
        line=dict(color='#c4b05a', width=2, dash='dot'),
        yaxis='y2'
    ))
    fig.update_layout(
        xaxis=dict(title='Month'),
        yaxis=dict(title=dict(text='GMV (R$)', font=dict(color='#6b5500'))),
        yaxis2=dict(title=dict(text='Orders', font=dict(color='#c4b05a')),
                    overlaying='y', side='right'),
        hovermode='x unified', height=450,
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 星期分布
    st.subheader("星期 × 时段下单分布")
    filtered['day_of_week'] = filtered['order_purchase_timestamp'].dt.day_name()
    filtered['hour'] = filtered['order_purchase_timestamp'].dt.hour

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_hour = filtered.groupby(['day_of_week', 'hour'])['order_id'].nunique().unstack()
    dow_hour = dow_hour.reindex(day_order)

    fig2 = px.imshow(
        dow_hour, aspect='auto', color_continuous_scale='YlOrBr',
        labels=dict(x='Hour of Day', y='Day of Week', color='Orders')
    )
    fig2.update_layout(height=350)
    st.plotly_chart(fig2, use_container_width=True)

# ----- Tab 2：地理分布 -----
with tab2:
    st.subheader("各州销售分布")

    state_sales = filtered.groupby('customer_state').agg({
        'item_total': 'sum',
        'order_id': 'nunique',
        'customer_unique_id': 'nunique',
        'review_score': 'mean',
        'delivery_days': 'mean'
    }).reset_index()
    state_sales.columns = ['State', 'GMV', 'Orders', 'Customers', 'AvgScore', 'AvgDelivery']
    state_sales = state_sales.sort_values('GMV', ascending=False)

    col_a, col_b = st.columns(2)
    with col_a:
        fig3 = px.bar(
            state_sales.head(10).iloc[::-1],
            x='GMV', y='State', orientation='h',
            color='GMV', color_continuous_scale='YlOrBr',
            title='Top 10 States by GMV'
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig4 = px.scatter(
            state_sales[state_sales['Orders'] >= 30],
            x='AvgDelivery', y='AvgScore',
            size='Customers', color='GMV',
            hover_name='State', color_continuous_scale='YlOrBr',
            title='State Performance: Delivery vs Rating\n(Bubble=Customers, Color=GMV)'
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

# ----- Tab 3：客户分析（RFM） -----
with tab3:
    st.subheader("RFM 客户价值分层")

    # RFM 计算（基于筛选后的数据）
    analysis_date = filtered['order_purchase_timestamp'].max() + timedelta(days=1)
    rfm = filtered.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (analysis_date - x.max()).days,
        'order_id': 'nunique',
        'item_total': 'sum'
    }).reset_index()
    rfm.columns = ['customer_unique_id', 'Recency', 'Frequency', 'Monetary']
    rfm = rfm[rfm['Monetary'] > 0]

    # qcut 打分（labels=False → 0 基索引，避免 duplicates='drop' 时标签数量不匹配）
    try:
        r_idx = pd.qcut(rfm['Recency'], q=5, labels=False, duplicates='drop')
        f_idx = pd.qcut(rfm['Frequency'], q=5, labels=False, duplicates='drop')
        m_idx = pd.qcut(rfm['Monetary'], q=5, labels=False, duplicates='drop')

        # Recency：越小越好 → 反转（bin 0 = 最近 = 最高分）
        rfm['R_Score'] = r_idx.max() - r_idx + 1
        # Frequency / Monetary：越大越好 → 直接映射
        rfm['F_Score'] = f_idx + 1
        rfm['M_Score'] = m_idx + 1
    except ValueError:
        st.warning("当前筛选条件下数据不足以做 RFM 分档，请放宽筛选条件")
        st.stop()

    # 分段
    def segment(r):
        s = f"{r['R_Score']}{r['F_Score']}{r['M_Score']}"
        if s in ['555','554','544','545','454','455','445']: return 'Champions'
        elif s in ['543','444','435','355','354','345','344','335']: return 'Loyal'
        elif r['R_Score'] >= 4 and r['F_Score'] <= 2: return 'New'
        elif r['R_Score'] <= 2 and (r['F_Score'] >= 3 or r['M_Score'] >= 3): return 'At Risk'
        elif r['R_Score'] <= 2 and r['F_Score'] <= 2 and r['M_Score'] <= 2: return 'Hibernating'
        elif r['R_Score'] >= 3 and r['F_Score'] <= 2 and r['M_Score'] <= 2: return 'About to Sleep'
        else: return 'Others'

    rfm['Segment'] = rfm.apply(segment, axis=1)

    col_c, col_d, col_e = st.columns(3)

    with col_c:
        seg_counts = rfm['Segment'].value_counts()
        fig5 = px.pie(
            names=seg_counts.index, values=seg_counts.values,
            title='Customer Segment Distribution',
            color_discrete_sequence=px.colors.sequential.YlOrBr
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_d:
        seg_revenue = rfm.groupby('Segment')['Monetary'].sum()
        fig6 = px.pie(
            names=seg_revenue.index, values=seg_revenue.values,
            title='Revenue by Segment',
            color_discrete_sequence=px.colors.sequential.YlOrBr_r
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col_e:
        seg_avg = rfm.groupby('Segment').agg(
            Avg_Recency=('Recency', 'mean'),
            Avg_Monetary=('Monetary', 'mean'),
            Count=('customer_unique_id', 'count')
        ).reset_index()
        fig7 = px.scatter(
            seg_avg, x='Avg_Recency', y='Avg_Monetary',
            size='Count', color='Segment', hover_name='Segment',
            title='Recency vs Monetary by Segment'
        )
        fig7.update_layout(height=400)
        st.plotly_chart(fig7, use_container_width=True)

# ----- Tab 4：产品 & 支付 -----
with tab4:
    st.subheader("品类分析")

    cat_analysis = filtered.groupby('product_category_name_english').agg({
        'item_total': 'sum',
        'order_id': 'nunique',
        'review_score': 'mean',
        'delivery_days': 'mean'
    }).reset_index()
    cat_analysis.columns = ['Category', 'GMV', 'Orders', 'AvgScore', 'AvgDelivery']
    cat_analysis = cat_analysis[cat_analysis['Orders'] >= 10].sort_values('GMV', ascending=False)

    col_f, col_g = st.columns(2)
    with col_f:
        fig8 = px.bar(
            cat_analysis.head(15).iloc[::-1],
            x='GMV', y='Category', orientation='h',
            color='AvgScore', color_continuous_scale='YlOrBr',
            title='Top 15 Categories (Color = Avg Rating)'
        )
        fig8.update_layout(height=450)
        st.plotly_chart(fig8, use_container_width=True)

    with col_g:
        fig9 = px.scatter(
            cat_analysis.head(30),
            x='AvgDelivery', y='AvgScore',
            size='GMV', color='Orders',
            hover_name='Category', color_continuous_scale='YlOrBr',
            title='Category: Delivery vs Rating'
        )
        fig9.update_layout(height=450)
        st.plotly_chart(fig9, use_container_width=True)

    # 支付行为
    st.subheader("支付行为分析")
    col_h, col_i = st.columns(2)

    with col_h:
        payment_dist = filtered['payment_type'].value_counts().reset_index()
        payment_dist.columns = ['Payment Type', 'Count']
        fig10 = px.pie(
            payment_dist, names='Payment Type', values='Count',
            title='Payment Method Distribution',
            color_discrete_sequence=px.colors.sequential.YlOrBr
        )
        st.plotly_chart(fig10, use_container_width=True)

    with col_i:
        installment_dist = filtered['max_installments'].value_counts().sort_index()
        installment_dist = installment_dist[installment_dist.index <= 20]
        fig11 = px.bar(
            x=installment_dist.index, y=installment_dist.values,
            labels={'x': 'Number of Installments', 'y': 'Orders'},
            title='Installments Distribution'
        )
        fig11.update_traces(marker_color='#6b5500')
        fig11.update_layout(height=350)
        st.plotly_chart(fig11, use_container_width=True)

# ===== 底部 =====
st.markdown("---")
st.caption(
    "📊 Olist E-Commerce Analytics Dashboard | "
    "Built with Streamlit + Plotly | "
    "Data: Kaggle Olist Brazilian E-Commerce Dataset"
)