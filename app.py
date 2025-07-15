import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy.stats import percentileofscore

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="업박스 고객사 에코(ESG) 리포트",
    page_icon="🌿",
    layout="wide"
)

# --- Helper: 안내 문구 및 함수 ---
KG_NOTICE = "> *음식물류는 1L=1kg으로 환산되었으며, 그 외 모든 폐기물은 kg 단위입니다.*"


def get_sigma_message(z_score):
    """Z-score를 기반으로 완곡한 표현의 메시지를 반환합니다."""
    if abs(z_score) <= 1:
        return "동종업계의 **평균적인 수준**으로 배출하고 있습니다."
    elif 1 < z_score <= 2:
        return "평균적인 범주 안에 있지만, **평균보다 약간 많은 양**을 배출하고 있습니다."
    elif 2 < z_score <= 3:
        return "**상당히 많은 양**을 배출하는 편입니다."
    elif z_score > 3:
        return "**매우 많은 양**을 배출하고 있어, 특별 관리가 필요해 보입니다."
    elif -2 <= z_score < -1:
        return "평균적인 범주 안에 있지만, **평균보다 약간 적은 양**을 배출하며 우위를 점하고 있습니다."
    else:  # z_score < -2
        return "**매우 효율적으로 관리**하며 배출량이 현저히 적은 수준입니다."


# --- 2. 데이터 로딩 및 전처리 ---
@st.cache_data
def load_data(monthly_path, industry_path):
    df_monthly = pd.read_csv(monthly_path)
    df_monthly['base_date'] = pd.to_datetime(df_monthly['base_date'])
    df_monthly['month'] = df_monthly['base_date'].dt.strftime('%Y-%m')
    df_monthly['mnthly_amount'] = df_monthly['mnthly_amount'].fillna(0)
    df_monthly['ly_mnthly_amount'] = df_monthly['ly_mnthly_amount'].fillna(0)

    df_industry = pd.read_csv(industry_path)
    df_industry['avg_mnthly_amount'] = df_industry['avg_mnthly_amount'].fillna(0)

    df_binggrae = df_industry[df_industry['tgt_customer_flag'] == 1].copy()
    df_competitor = df_industry[df_industry['tgt_customer_flag'] == 0].copy()

    return df_monthly, df_binggrae, df_competitor


df_monthly, df_binggrae, df_competitor = load_data('binggrae_mnthly_amount.csv', 'binggrae_industry_avg_amount.csv')

# --- 3. 사이드바 및 필터 설정 ---
latest_available_month = df_monthly['base_date'].max()
report_date = latest_available_month.replace(day=1) - pd.DateOffset(months=1)
report_month_str = report_date.strftime('%Y년 %m월')

try:
    st.sidebar.image("upbox_icon.png", width=150)
except FileNotFoundError:
    st.sidebar.warning("로고 파일(upbox_icon.png)을 찾을 수 없습니다.")
st.sidebar.title("Upbox Eco Report")
st.sidebar.markdown("---")

waste_groups_options = sorted(df_monthly['waste_item_group'].unique())
selected_waste_groups = st.sidebar.multiselect(
    "폐기물 종류 필터",
    options=waste_groups_options,
    default=waste_groups_options
)

df_monthly_filtered = df_monthly[
    (df_monthly['waste_item_group'].isin(selected_waste_groups)) &
    (df_monthly['base_date'] <= report_date)
    ]
df_report_month_filtered = df_monthly_filtered[df_monthly_filtered['base_date'] == report_date].copy()

# --- 4. 메인 대시보드 구성 ---
st.title("업박스 고객사 에코(ESG) 리포트")
st.subheader(f"B사 | {report_month_str} 기준")
st.markdown("---")

# --- 4.1. 환경 임팩트 성과 (KPI) ---
st.header("📈 24년 누적 환경 임팩트")
kpi_cols = st.columns(3)
with kpi_cols[0]: st.metric(label="이산화탄소 감축량 💨", value="1,134.7 MtCO2eq.")
with kpi_cols[1]: st.metric(label="물 절약량 💧", value="3,058.58 m³H₂Oeq")
with kpi_cols[2]: st.metric(label="에너지 회수량 🔥", value="758,923 MWh")
effect_cols = st.columns(2)
with effect_cols[0]: st.markdown(
    f"""<div style="background-color: #F0F2F6; padding: 20px; border-radius: 10px; text-align: center;"><p style="font-size: 1.2em; font-weight: bold; margin: 0;">🌲 녹화 효과</p><p style="font-size: 2.5em; font-weight: bold; color: #2E8B57; margin: 0;">소나무 112,501그루</p></div>""",
    unsafe_allow_html=True)
with effect_cols[1]: st.markdown(
    f"""<div style="background-color: #F0F2F6; padding: 20px; border-radius: 10px; text-align: center;"><p style="font-size: 1.2em; font-weight: bold; margin: 0;">🚗 승용차 감축 효과</p><p style="font-size: 2.5em; font-weight: bold; color: #4682B4; margin: 0;">승용차 873대</p></div>""",
    unsafe_allow_html=True)
with st.container():
    st.markdown("---")
    st.subheader("💡 임팩트 산정 기준")
    st.markdown(
        """- **이산화탄소 감축량**: 음식물류 폐기물의 비소각 처리 및 폐플라스틱 자원화를 통해 감축된 CO₂ 환산량입니다.\n- **물 절약량**: 폐기물의 소각 및 매립 공정 대신 자원순환 처리 시 절약되는 물의 양입니다.\n- **녹화/승용차 효과**: 감축된 이산화탄소 양을 소나무 연간 흡수량 및 승용차 연간 배출량 기준으로 환산한 값입니다.""")
st.markdown("---")

# --- 4.2. 수거량 현황 ---
st.header(f"📊 {report_month_str} 폐기물 수거 현황")
st.markdown(KG_NOTICE)
chart_cols = st.columns([0.45, 0.55])
with chart_cols[0]:
    st.subheader("폐기물 구성 비율")
    if not df_report_month_filtered.empty:
        sunburst_data = df_report_month_filtered.groupby(['waste_item_group', 'waste_item'])[
            'mnthly_amount'].sum().reset_index()
        sunburst_data = sunburst_data[sunburst_data['mnthly_amount'] > 0]
        fig_sunburst = px.sunburst(sunburst_data, path=['waste_item_group', 'waste_item'], values='mnthly_amount',
                                   color='waste_item_group', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_sunburst.update_traces(textinfo='percent entry+label', insidetextorientation='horizontal',
                                   hovertemplate='<b>%{label}</b><br>수거량: %{value:,.0f} kg<br>비중: %{percentEntry:.0%}')
        fig_sunburst.update_layout(margin=dict(t=20, l=0, r=0, b=0))
        st.plotly_chart(fig_sunburst, use_container_width=True)
    else:
        st.warning("선택된 필터에 해당하는 데이터가 없습니다.")

with chart_cols[1]:
    st.subheader("월별 폐기물 배출량 추이")


    def create_stacked_bar_with_line(df, group_by_col):
        fig = go.Figure()
        df_totals = df.groupby('base_date')['mnthly_amount'].sum().reset_index()
        for item in df[group_by_col].unique():
            item_df = df[df[group_by_col] == item]
            fig.add_trace(go.Bar(x=item_df['base_date'], y=item_df['mnthly_amount'], name=item))
        fig.add_trace(go.Scatter(x=df_totals['base_date'], y=df_totals['mnthly_amount'], mode='lines+text',
                                 line=dict(color='black', width=2, dash='solid'), name='총합',
                                 text=df_totals['mnthly_amount'].apply(lambda x: f'{x:,.0f}'),
                                 textposition="top center"))
        fig.update_layout(barmode='stack', height=300, margin=dict(t=10, l=10, r=10, b=20),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), showlegend=True)
        return fig


    st.markdown("##### 대분류별 추이")
    if not df_monthly_filtered.empty:
        fig_major = create_stacked_bar_with_line(df_monthly_filtered, 'waste_item_group')
        st.plotly_chart(fig_major, use_container_width=True)
    else:
        st.warning("표시할 데이터가 없습니다.")
    st.markdown("##### 중분류별 추이")
    if not df_monthly_filtered.empty:
        fig_medium = create_stacked_bar_with_line(df_monthly_filtered, 'waste_item')
        st.plotly_chart(fig_medium, use_container_width=True)
    else:
        st.warning("표시할 데이터가 없습니다.")

with st.expander("상세 데이터 보기 (월별 Pivot 테이블)"):
    st.subheader("폐기물 품목별 월별 수거량 변화")
    if not df_monthly_filtered.empty:
        pivot_table = df_monthly_filtered.pivot_table(index=['waste_item_group', 'waste_item'], columns='month',
                                                      values='mnthly_amount', aggfunc='sum').fillna(0)
        st.dataframe(pivot_table.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("표시할 데이터가 없습니다.")
st.markdown("---")

# --- 4.3. 전년 동월 대비 증감 분석 ---
st.header(f"🆚 {report_month_str} 전년 동월 대비 증감 분석 (YoY)")
st.markdown(KG_NOTICE)
yoy_data = df_report_month_filtered[df_report_month_filtered['ly_mnthly_amount'] > 0].copy()
yoy_data['delta'] = yoy_data['mnthly_amount'] - yoy_data['ly_mnthly_amount']

if not yoy_data.empty:
    yoy_data_sorted = yoy_data.sort_values('yoy_growth', ascending=True)
    total_ly = yoy_data_sorted['ly_mnthly_amount'].sum()
    total_ty = yoy_data_sorted['mnthly_amount'].sum()
    total_delta = total_ty - total_ly
    total_yoy_growth = total_delta / total_ly if total_ly != 0 else 0
    yoy_kpi_cols = st.columns(2)
    yoy_kpi_cols[0].metric(label=f"{report_month_str} 총 배출량", value=f"{total_ty:,.0f} kg",
                           delta=f"{total_delta:,.0f} kg (YoY)", delta_color="inverse")
    yoy_kpi_cols[1].metric(label="전년 동월 대비 증감률", value=f"{total_yoy_growth:.1%}")
    st.markdown("---")
else:
    yoy_data_sorted = pd.DataFrame()

yoy_cols = st.columns(2)
with yoy_cols[0]:
    st.subheader("폐기물 품목별 수거량 증감량")
    if not yoy_data_sorted.empty:
        fig_waterfall = go.Figure(go.Waterfall(name="증감분석", orientation="v",
                                               measure=["absolute"] + ["relative"] * len(yoy_data_sorted) + ["total"],
                                               x=["전년 동월 총량"] + yoy_data_sorted['waste_item'].tolist() + ["금년 동월 총량"],
                                               textposition="outside",
                                               text=[f"{total_ly:,.0f}"] + [f"{val:,.0f}" for val in
                                                                            yoy_data_sorted['delta']] + [
                                                        f"{total_ty:,.0f}"],
                                               y=[total_ly] + yoy_data_sorted['delta'].tolist() + [total_ty],
                                               connector={"visible": False},
                                               increasing={"marker": {"color": "#FF4136"}},
                                               decreasing={"marker": {"color": "#3D9970"}},
                                               totals={"marker": {"color": "#0074D9"}}))
        d = abs(total_ly - total_ty)
        y_max = max(total_ly, total_ty) + d
        y_min = min(total_ly, total_ty) - d
        fig_waterfall.update_yaxes(range=[y_min, y_max])
        fig_waterfall.update_layout(title_text="전년 동월 대비 품목별 수거량 변화", showlegend=False, height=500)
        st.plotly_chart(fig_waterfall, use_container_width=True)
    else:
        st.warning("비교할 전년 데이터가 없습니다.")

with yoy_cols[1]:
    st.subheader("폐기물 품목별 수거량 증감률(YoY)")
    if not yoy_data_sorted.empty:
        yoy_data_sorted['color'] = yoy_data_sorted['yoy_growth'].apply(lambda x: '증가' if x > 0 else '감소')
        yoy_order = yoy_data_sorted['waste_item'].tolist()
        fig_yoy_bar = px.bar(yoy_data_sorted, y='yoy_growth', x='waste_item', color='color',
                             color_discrete_map={'증가': '#FF4136', '감소': '#3D9970'},
                             labels={'yoy_growth': '증감률 (%)', 'waste_item': ''}, text='yoy_growth',
                             category_orders={'waste_item': yoy_order})
        fig_yoy_bar.update_traces(texttemplate='%{text:.1%}', textposition='outside')
        fig_yoy_bar.add_hline(y=0, line_width=1, line_dash="dash", line_color="black")
        # ✅ 요구사항 반영: x축 제목 제거
        fig_yoy_bar.update_layout(title_text="전년 동월 대비 품목별 수거량 증감률", yaxis_tickformat='.0%', showlegend=False,
                                  height=500, xaxis_title_text="")
        st.plotly_chart(fig_yoy_bar, use_container_width=True)
    else:
        st.warning("비교할 전년 데이터가 없습니다.")

with st.expander("상세 데이터 보기"):
    st.subheader(f"{report_month_str} 전년 동월 대비 수거량 상세")
    if not yoy_data_sorted.empty:
        yoy_table_data = yoy_data_sorted[
            ['waste_item_group', 'waste_item', 'ly_mnthly_amount', 'mnthly_amount', 'delta', 'yoy_growth']].rename(
            columns={'waste_item_group': '대분류', 'waste_item': '중분류', 'ly_mnthly_amount': '전년 동월 수거량 (kg)',
                     'mnthly_amount': '금년 동월 수거량 (kg)', 'delta': '증감량 (kg)', 'yoy_growth': '증감률 (%)'}).set_index(
            ['대분류', '중분류'])
        st.dataframe(yoy_table_data, use_container_width=True,
                     column_config={
                         "대분류": st.column_config.TextColumn(width="medium"),
                         "중분류": st.column_config.TextColumn(width="medium"),
                         "전년 동월 수거량 (kg)": st.column_config.NumberColumn(format="%.0f", width="small"),
                         "금년 동월 수거량 (kg)": st.column_config.NumberColumn(format="%.0f", width="small"),
                         "증감량 (kg)": st.column_config.NumberColumn(format="%.0f", width="small"),
                         "증감률 (%)": st.column_config.NumberColumn(format="%.4%", width="small"),  # ✅ 요구사항 반영: 포맷 수정
                     })
    else:
        st.warning("표시할 YoY 데이터가 없습니다.")
st.markdown("---")

# # --- 4.4. 동종 업계 비교 분석 (✅ 전체 재구성) ---
# st.header("🏢 동종 업계(식품 공장) 배출량 비교")

# # --- 인사이트 1: 배출 품목 다양성 분석 ---
# st.subheader("1. 배출 품목 다양성 분석")
# binggrae_total_item_count = df_binggrae['waste_item'].nunique()
# industry_item_counts = df_competitor.groupby('customer_company_name')['waste_item'].nunique()
# avg_industry_item_count = industry_item_counts.mean()
# st.markdown(
#     f"동종 업계(식품공장)는 평균 **{avg_industry_item_count:.0f}개**의 폐기물 품목을 배출하는데, B사는 **{binggrae_total_item_count}개**의 폐기물을 배출하고 있어, 보다 다양한 품목을 관리하고 있습니다.")

# # 밀도 함수 시각화
# fig_dist_items = ff.create_distplot([industry_item_counts.tolist()], ['동종업계'], show_hist=False, show_rug=False,
#                                     colors=['gray'])
# fig_dist_items.add_vline(x=binggrae_total_item_count, line_width=2, line_dash="dash", line_color="orange",
#                          annotation_text=f"B사: {binggrae_total_item_count}개", annotation_position="top right")
# # ✅ 요구사항 반영: 차트 제목 수정
# fig_dist_items.update_layout(title="동종 업계(식품공장) 배출 품목 수 분포", xaxis_title="배출 품목 수 (개)", yaxis_title="밀도",
#                              showlegend=False)
# st.plotly_chart(fig_dist_items, use_container_width=True)

# # --- 인사이트 2: 주요 품목 상세 분석 ---
# st.subheader("2. 주요 품목 상세 분석")
# # 이 계산은 필터와 무관하게 전체 데이터로 수행
# binggrae_top_volume_item = df_binggrae.sort_values('avg_mnthly_amount', ascending=False).iloc[0]['waste_item']
# # 가장 흔한 품목 계산 (내러티브에서만 사용)
# most_common_item = df_competitor['waste_item'].value_counts().idxmax()
# percentile_by_item = {}
# for item in df_binggrae['waste_item'].unique():
#     b_val = df_binggrae[df_binggrae['waste_item'] == item]['avg_mnthly_amount'].iloc[0]
#     c_vals = df_competitor[df_competitor['waste_item'] == item]['avg_mnthly_amount']
#     if len(c_vals) > 1:
#         percentile_by_item[item] = percentileofscore(c_vals, b_val, kind='rank')

# # 가장 흔한 품목에 대한 분석 내러티브
# c_vals_common = df_competitor[df_competitor['waste_item'] == most_common_item]['avg_mnthly_amount']
# if not c_vals_common.empty:
#     b_val_common = df_binggrae[df_binggrae['waste_item'] == most_common_item]['avg_mnthly_amount'].iloc[0]
#     z_score_common = (b_val_common - c_vals_common.mean()) / c_vals_common.std() if c_vals_common.std() > 0 else 0
#     sigma_message = get_sigma_message(z_score_common)
#     st.markdown(f"동종 업계에서 가장 흔하게 배출되는 품목은 `{most_common_item}`이며, 이 품목에 대해 B사는 {sigma_message}")

# # 상대적 최다 배출 품목 분석 내러티브
# if percentile_by_item:
#     relative_worst_item = max(percentile_by_item, key=percentile_by_item.get)
#     worst_percentile = percentile_by_item[relative_worst_item]
#     st.markdown(
#         f"한편, B사의 배출량을 단순 규모로 보면 `{binggrae_top_volume_item}`이 가장 큰 비중을 차지하지만, 동종 업계와 비교 시 상대적으로 가장 많이 배출하는 품목은 `{relative_worst_item}`으로, 업계 `상위 {100 - worst_percentile:.1f}%`에 해당됩니다.")

# # 품목별 밀도 분포 그리드
# st.markdown("##### 품목별 배출량 분포 상세")
# cols = st.columns(2)
# col_idx = 0
# if percentile_by_item:
#     for item, percentile in sorted(percentile_by_item.items(), key=lambda x: x[1], reverse=True):
#         with cols[col_idx % 2]:
#             b_val = df_binggrae[df_binggrae['waste_item'] == item]['avg_mnthly_amount'].iloc[0]
#             c_vals = df_competitor[df_competitor['waste_item'] == item]['avg_mnthly_amount']

#             if c_vals.empty:
#                 st.markdown(f"**{item}**")
#                 st.warning("동종업계 비교 데이터가 부족합니다.")
#                 col_idx += 1
#                 continue

#             mean_val = c_vals.mean()

#             fig_dist = ff.create_distplot([c_vals.tolist()], [item], show_hist=False, show_rug=False, colors=['gray'])
#             fig_dist.add_vline(x=b_val, line_width=2, line_dash="dash", line_color="orange")
#             fig_dist.add_vline(x=mean_val, line_width=2, line_dash="dot", line_color="blue")

#             fig_dist.update_layout(
#                 title=f"'{item}' 배출량 분포 (상위 {100 - percentile:.1f}%)",
#                 xaxis_title="월평균 배출량 (kg)", yaxis_title="밀도", showlegend=False, height=300,
#                 annotations=[
#                     dict(x=b_val, y=0.05, xref="x", yref="paper", showarrow=False, text="B사", bgcolor="orange",
#                          font=dict(color="white")),
#                     dict(x=mean_val, y=0.05, xref="x", yref="paper", showarrow=False, text="평균", bgcolor="blue",
#                          font=dict(color="white"))
#                 ]
#             )
#             st.plotly_chart(fig_dist, use_container_width=True)
#             col_idx += 1
# else:
#     st.warning("상세 비교를 위한 데이터가 부족합니다.")

# --- 5. 푸터 (저작권) ---
st.markdown("---")
st.markdown("""
<p style='text-align: center; color: grey; font-size: 0.9em;'>
    Copyright © 2025 Reco. All Rights Reserved.<br>
    본 리포트는 B사가 업박스(Upbox) 서비스를 통해 기록한 배출량 정보를 근거로 작성되었으며, Reco의 동의 없이 무단 복제 및 배포를 금합니다.
</p>
""", unsafe_allow_html=True)
