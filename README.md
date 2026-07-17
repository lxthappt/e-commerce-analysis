# 巴西电商用户行为分析 — Olist E-Commerce Analytics

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📊 项目概述

对巴西最大电商平台 Olist **2016.09-2018.08**（约 23 个月）的 9.6 万订单数据进行深度分析。
整合 9 张数据表（订单、客户、产品、卖家、支付、评分、地理信息），通过 pandas merge 构建 110,189 行分析宽表，
完成从多表整合到业务洞察的完整分析链路，并部署可交互的 Streamlit 数据看板。

**🔗 在线体验：** [Streamlit Dashboard]https://e-commerce-analysis-ffmmwxyumt2rtwakrj45ta.streamlit.app

## 🎯 分析维度

| 模块 | 方法 | 核心发现 |
|------|------|---------|
| 数据整合 | 9表 JOIN，pandas merge | 整合为 110,189 行 × 35 列宽表，行数一致性验证通过 |
| KPI 概览 | pandas 聚合 | 总GMV R$ 15.42M，总订单 96,470，客户 93,350，卖家 2,970 |
| 时间趋势 | 月度聚合 + 折线图 | 月均 GMV R$ 687K，月均订单 4,291，2017-11 达峰值 |
| 地理分布 | 按州聚合 + 柱状图 | SP（圣保罗）占 37.4% GMV，Top 3 州占 62.5% |
| 产品品类 | groupby 品类多维度 | 72 品类，Top 3（健康美容/手表礼品/床浴桌品）占 25.3% GMV |
| RFM 客户分层 | qcut 打分 6 级分类 | 40.1% 客户仅购买一次，Loyal + Champions（8.5%）为高价值客户 |
| Cohort 留存 | pivot + heatmap | 月度复购率约 0.5%，巴西电商以低频单次消费为主 |
| 物流时效 | datetime 差值统计 | 平均配送 12 天（中位 10 天），超时率 7.9% |
| 评分分析 | 评分与物流/品类交叉 | 平均评分 4.08/5.0，超时订单评分低 1.66 分 |
| 支付行为 | 支付类型/分期统计 | 信用卡占 76.4%，boleto（巴西票据支付）占 20.3% |

## 🛠 技术栈

- **数据整合：** Pandas（多表 JOIN、merge、groupby、pivot_table）
- **可视化：** Matplotlib, Seaborn, Plotly
- **Dashboard：** Streamlit
- **部署：** Streamlit Cloud

## 📁 项目结构

```
e-commerce-analysis/
├── olist_analysis.ipynb      # 完整分析 Notebook（从数据整合到业务结论）
├── app.py                     # Streamlit 交互式 Dashboard
├── data/
│   └── .gitkeep               # 数据文件请从 Kaggle 下载
├── images/
│   ├── dashboard_overview.png # Dashboard 截图
│   └── rfm_segments.png       # RFM 分析截图
├── requirements.txt           # Python 依赖
└── README.md
```

## 🚀 如何运行

### 1. 克隆仓库

```bash
git clone git@github.com:lxthappt/e-commerce-analysis.git
cd e-commerce-analysis
```

### 2. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 下载数据

从 [Kaggle Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下载所有 CSV 文件，
放入 `data/` 目录。

### 4. 运行 Notebook

```bash
jupyter notebook olist_analysis.ipynb
```

### 5. 启动 Dashboard

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`。

## 📈 关键业务发现

1. **市场集中度高**：圣保罗州（SP）占 37.4% GMV，Top 3 州（SP + RJ + MG）合计占 62.5%
2. **客户结构分化**：RFM 模型识别 40.1% 客户为一次性购买（At Risk），Loyal Customers + Champions（8.5%）为高价值群体
3. **留存率低**：月度复购率约 0.5%，符合巴西电商低频消费特征
4. **物流影响评分**：配送超时率 7.9%，超时订单评分平均低 1.66 分
5. **支付偏好**：信用卡占 76.4%，boleto（巴西特有票据支付）占 20.3%

## 📝 License

MIT
