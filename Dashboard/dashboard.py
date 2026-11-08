import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import altair as alt
from pathlib import Path


# Konfigurasi dashboard

st.set_page_config(
    page_title="Dashboard Analisis Olist",
    page_icon="🛒",
    layout="wide"
)

sns.set_theme(style="whitegrid")

st.title("🛒 Dashboard Analisis E-Commerce Olist")
st.caption("Analisis Penjualan dan Perilaku Pelanggan di Brazil")


# Memuat data

DATA_PATH = Path(__file__).parent / "main_data.csv"


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    data["order_purchase_timestamp"] = pd.to_datetime(
        data["order_purchase_timestamp"],
        errors="coerce"
    )

    data["price"] = pd.to_numeric(
        data["price"],
        errors="coerce"
    )

    data = data.dropna(subset=[
        "order_id",
        "order_purchase_timestamp",
        "price",
        "customer_unique_id"
    ])

    return data


df = load_data()


# Filter periode

st.sidebar.header("Filter Dashboard")

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range

    filtered_df = df[
        (df["order_purchase_timestamp"].dt.date >= start_date) &
        (df["order_purchase_timestamp"].dt.date <= end_date)
    ].copy()
else:
    filtered_df = df.copy()


if filtered_df.empty:
    st.warning("Tidak terdapat data pada periode yang dipilih.")
    st.stop()


# Ringkasan penjualan

st.subheader("Ringkasan Penjualan")

total_orders = filtered_df["order_id"].nunique()
total_sales = filtered_df["price"].sum()
total_customers = filtered_df["customer_unique_id"].nunique()
average_order = total_sales / total_orders if total_orders else 0

col1, col2, col3, col4 = st.columns(
    [1, 1.5, 1, 1.5],
    gap="medium"
)

with col1:
    st.metric(
        "Total Pesanan",
        f"{total_orders:,}"
    )

with col2:
    st.metric(
        "Total Penjualan",
        f"BRL {total_sales:,.2f}"
    )

with col3:
    st.metric(
        "Total Pelanggan",
        f"{total_customers:,}"
    )

with col4:
    st.metric(
        "Rata-rata Pesanan",
        f"BRL {average_order:,.2f}"
    )

st.divider()


# Tren penjualan bulanan

st.subheader("Tren Penjualan Bulanan")

monthly_df = filtered_df.copy()

monthly_df["bulan"] = (
    monthly_df["order_purchase_timestamp"].dt.to_period("M")
)

monthly_orders_df = monthly_df.groupby("bulan").agg(
    order_count=("order_id", "nunique"),
    total_revenue=("price", "sum")
).reset_index()

monthly_orders_df["order_purchase_timestamp"] = (
    monthly_orders_df["bulan"].dt.to_timestamp()
)

monthly_orders_df["year_month"] = (
    monthly_orders_df["bulan"].astype(str)
)

monthly_orders_df = monthly_orders_df.sort_values(
    "order_purchase_timestamp"
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Tren Jumlah Pesanan Bulanan**")

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.plot(
        monthly_orders_df["year_month"],
        monthly_orders_df["order_count"],
        marker="o",
        linewidth=2,
        color="#7289DA"
    )

    ax.set_xlabel("Bulan-Tahun")
    ax.set_ylabel("Jumlah Pesanan")
    ax.yaxis.set_major_formatter(
        mtick.StrMethodFormatter("{x:,.0f}")
    )

    tick_positions = range(
        0,
        len(monthly_orders_df),
        2
    )

    ax.set_xticks(list(tick_positions))
    ax.set_xticklabels(
        monthly_orders_df["year_month"].iloc[
            list(tick_positions)
        ],
        rotation=45,
        ha="right"
    )

    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

with col2:
    st.markdown("**Tren Total Pendapatan Bulanan**")

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.plot(
        monthly_orders_df["year_month"],
        monthly_orders_df["total_revenue"],
        marker="o",
        linewidth=2,
        color="#5865F2"
    )

    ax.set_xlabel("Bulan-Tahun")
    ax.set_ylabel("Total Pendapatan (BRL)")

    ax.yaxis.set_major_formatter(
        mtick.StrMethodFormatter("BRL {x:,.0f}")
    )

    ax.set_xticks(list(tick_positions))
    ax.set_xticklabels(
        monthly_orders_df["year_month"].iloc[
            list(tick_positions)
        ],
        rotation=45,
        ha="right"
    )

    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

st.caption(
    "Pendapatan dihitung berdasarkan penjumlahan kolom price "
    "dan tidak termasuk biaya pengiriman."
)

st.divider()


# Analisis kategori produk

st.subheader("Performa Kategori Produk")


category_df = filtered_df.groupby(
    "product_category_name_english"
).agg(
    total_orders=("order_id", "nunique"),
    total_revenue=("price", "sum")
).reset_index()


category_df = category_df[
    category_df["product_category_name_english"] != "unknown"
].copy()


category_df = category_df.sort_values(
    "total_revenue",
    ascending=False
)


top_5_products = category_df.head(5).copy()


bottom_5_products = (
    category_df.sort_values(
        "total_revenue",
        ascending=True
    )
    .head(5)
    .copy()
)


# Mengubah nama kategori untuk tampilan

def format_category_name(name):
    category_names = {
        "health_beauty": "Health & Beauty",
        "watches_gifts": "Watches & Gifts",
        "bed_bath_table": "Bed, Bath & Table",
        "sports_leisure": "Sports & Leisure",
        "computers_accessories": "Computers & Accessories",
        "furniture_decor": "Furniture & Decor",
        "housewares": "Housewares",
        "auto": "Automotive",
        "toys": "Toys",
        "cool_stuff": "Cool Stuff",
        "garden_tools": "Garden Tools",
        "perfumery": "Perfumery",
        "telephony": "Telephony",
        "baby": "Baby",
        "electronics": "Electronics",
        "stationery": "Stationery",
        "pet_shop": "Pet Shop",
        "computers": "Computers",
        "small_appliances": "Small Appliances",
        "fashion_bags_accessories": "Fashion Bags & Accessories",
        "home_confort": "Home Comfort",
        "home_appliances": "Home Appliances",
        "fixed_telephony": "Fixed Telephony",
        "musical_instruments": "Musical Instruments",
        "construction_tools_construction": "Construction Tools",
        "food_drink": "Food & Drink",
        "agro_industry_and_commerce": "Agro Industry & Commerce",
        "drinks": "Drinks",
        "food": "Food",
        "market_place": "Market Place",
        "fashion_shoes": "Fashion Shoes",
        "fashion_male_clothing": "Fashion Male Clothing",
        "fashion_underwear_beach": "Fashion Underwear & Beach",
        "fashion_sport": "Fashion Sport",
        "fashion_childrens_clothes": "Fashion Children's Clothes",
        "office_furniture": "Office Furniture",
        "furniture_living_room": "Living Room Furniture",
        "furniture_bedroom": "Bedroom Furniture",
        "home_comfort_2": "Home Comfort 2",
        "home_appliances_2": "Home Appliances 2",
        "la_cuisine": "La Cuisine",
        "christmas_supplies": "Christmas Supplies",
        "party_supplies": "Party Supplies",
        "luggage_accessories": "Luggage & Accessories",
        "arts_and_craftmanship": "Arts & Craftsmanship",
        "cds_dvds_musicals": "CDs, DVDs & Musicals",
        "books_general_interest": "Books - General Interest",
        "books_technical": "Technical Books",
        "books_imported": "Imported Books",
        "cine_photo": "Cinema & Photography",
        "audio": "Audio",
        "signaling_and_security": "Signaling & Security",
        "security_and_services": "Security & Services",
        "construction_tools_lights": "Construction Tools & Lights",
        "construction_tools_safety": "Construction Tools & Safety",
        "construction_tools_garden": "Construction Tools & Garden",
        "construction_tools_screws": "Construction Tools & Screws",
        "construction_tools_drills": "Construction Tools & Drills",
        "small_appliances_home_oven_and_coffee": "Small Appliances - Oven & Coffee",
        "small_appliances_home_laundry": "Small Appliances - Laundry",
        "tablets_printing_image": "Tablets, Printing & Image",
        "fashion_female_clothing": "Fashion Female Clothing",
        "flowers": "Flowers",
        "diapers_and_hygiene": "Diapers & Hygiene",
        "home_comfort": "Home Comfort",
    }

    return category_names.get(
        name,
        name.replace("_", " ").title()
    )


def tampilkan_grafik_kategori(data, judul, key, ascending):
    st.markdown(f"**{judul}**")

    chart_data = data.copy()

    chart_data["category_display"] = (
        chart_data["product_category_name_english"]
        .apply(format_category_name)
    )

    pilihan = alt.selection_point(
        name=key,
        fields=["product_category_name_english"],
        on="click",
        clear="dblclick"
    )

    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X(
            "total_revenue:Q",
            title="Total Pendapatan (BRL)",
            axis=alt.Axis(format="~s")
        ),
        y=alt.Y(
            "category_display:N",
            sort=alt.SortField(
                field="total_revenue",
                order="ascending" if ascending else "descending"
            ),
            title="Kategori Produk",
            axis=alt.Axis(labelLimit=400)
        ),
        color=alt.condition(
            pilihan,
            alt.value("#5865F2"),
            alt.value("cornflowerblue")
        ),
        tooltip=[
            alt.Tooltip(
                "category_display:N",
                title="Kategori Produk"
            ),
            alt.Tooltip(
                "total_revenue:Q",
                title="Total Pendapatan",
                format=",.2f"
            ),
            alt.Tooltip(
                "total_orders:Q",
                title="Jumlah Pesanan",
                format=","
            )
        ]
    ).add_params(pilihan).properties(height=280)

    event = st.altair_chart(
        chart,
        use_container_width=True,
        on_select="rerun",
        key=f"chart_{key}"
    )

    selected = event.selection.get(key, [])

    if selected:
        nama = selected[0]["product_category_name_english"]

        detail = chart_data[
            chart_data["product_category_name_english"] == nama
        ].iloc[0]

        st.info(
            f"Kategori dipilih: {format_category_name(nama)}"
        )
        st.write(
            f"Total pendapatan: BRL {detail['total_revenue']:,.2f}"
        )
        st.write(
            f"Jumlah pesanan: {detail['total_orders']:,}"
        )
    else:
        st.caption("Klik batang grafik untuk melihat detail.")


col1, col2 = st.columns(2)

with col1:
    tampilkan_grafik_kategori(
        top_5_products,
        "5 Kategori Produk dengan Pendapatan Tertinggi",
        "pilihan_top",
        False
    )

with col2:
    tampilkan_grafik_kategori(
        bottom_5_products,
        "5 Kategori Produk dengan Pendapatan Terendah",
        "pilihan_bottom",
        True
    )

st.divider()


# Analisis RFM

st.subheader("Analisis Karakteristik dan Segmentasi Pelanggan (RFM)")


recent_date = (
    filtered_df["order_purchase_timestamp"].max()
    + pd.Timedelta(days=1)
)


rfm_df = filtered_df.groupby("customer_unique_id").agg(
    recency=(
        "order_purchase_timestamp",
        lambda x: (recent_date - x.max()).days
    ),
    frequency=("order_id", "nunique"),
    monetary=("price", "sum")
).reset_index()


rfm_df["r_score"] = pd.qcut(
    rfm_df["recency"].rank(method="first"),
    5,
    labels=[5, 4, 3, 2, 1]
).astype(int)


rfm_df["f_score"] = pd.cut(
    rfm_df["frequency"],
    bins=[0, 1, 2, 3, 4, float("inf")],
    labels=[1, 2, 3, 4, 5]
).astype(int)


rfm_df["m_score"] = pd.qcut(
    rfm_df["monetary"].rank(method="first"),
    5,
    labels=[1, 2, 3, 4, 5]
).astype(int)


rfm_df["rfm_score"] = (
    rfm_df["r_score"]
    + rfm_df["f_score"]
    + rfm_df["m_score"]
)


def segment_customer(score):
    if score >= 13:
        return "Champions"
    elif score >= 10:
        return "Loyal Customers"
    elif score >= 7:
        return "Potential Customers"
    else:
        return "Need Attention"


rfm_df["customer_segment"] = rfm_df[
    "rfm_score"
].apply(segment_customer)


# Menyiapkan warna segmen

segment_colors = {
    "Champions": "#7289DA",
    "Loyal Customers": "#A5B4FC",
    "Potential Customers": "#C7D2FE",
    "Need Attention": "#D3D3D3"
}


segment_order = [
    "Champions",
    "Loyal Customers",
    "Potential Customers",
    "Need Attention"
]


# Visualisasi indikator RFM

st.markdown("### Indikator RFM")

col1, col2, col3 = st.columns(3)


# Rata-rata recency berdasarkan segmen

with col1:
    st.markdown("**Average Recency by Customer Segment**")

    recency_segment_df = (
        rfm_df.groupby("customer_segment")["recency"]
        .mean()
        .reset_index()
        .sort_values("recency", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(6, 4))

    sns.barplot(
        data=recency_segment_df,
        x="recency",
        y="customer_segment",
        hue="customer_segment",
        palette=segment_colors,
        legend=False,
        ax=ax
    )

    ax.set_xlabel("Average Recency (Days)")
    ax.set_ylabel("Customer Segment")
    ax.xaxis.set_major_formatter(
        mtick.StrMethodFormatter("{x:,.0f}")
    )
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# Distribusi frequency pelanggan

with col2:
    st.markdown("**Customer Distribution by Frequency**")

    frequency_group = pd.cut(
        rfm_df["frequency"],
        bins=[0, 1, 2, 3, 4, float("inf")],
        labels=["1", "2", "3", "4", "5+"]
    )

    frequency_distribution = (
        frequency_group.value_counts(sort=False)
    )

    fig, ax = plt.subplots(figsize=(6, 4))

    bars = ax.bar(
        frequency_distribution.index.astype(str),
        frequency_distribution.values,
        color="#7289DA"
    )

    ax.set_xlabel("Frequency (Orders)")
    ax.set_ylabel("Number of Customers")
    ax.yaxis.set_major_formatter(
        mtick.StrMethodFormatter("{x:,.0f}")
    )

    ax.bar_label(
        bars,
        labels=[
            f"{int(value):,}"
            for value in frequency_distribution.values
        ],
        padding=3,
        fontsize=8
    )

    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# Top 5 pelanggan berdasarkan monetary

with col3:
    st.markdown("**Top 5 Customers by Monetary**")

    rfm_df_short = rfm_df.copy()

    rfm_df_short["short_id"] = (
        rfm_df_short["customer_unique_id"].str[:8] + "..."
    )

    top_monetary = (
        rfm_df_short
        .sort_values("monetary", ascending=False)
        .head(5)
        .sort_values("monetary", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(6, 4))

    ax.barh(
        top_monetary["short_id"],
        top_monetary["monetary"],
        color="#7289DA"
    )

    ax.invert_yaxis()
    ax.set_xlabel("Monetary (BRL)")
    ax.set_ylabel("Customer ID")

    ax.xaxis.set_major_formatter(
        mtick.FuncFormatter(
            lambda x, pos: f"R$ {x / 1000:.0f}K"
        )
    )

    ax.xaxis.set_major_locator(
        mtick.MaxNLocator(nbins=4)
    )

    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# Donut chart segmentasi pelanggan

st.markdown("### Proporsi Segmen Pelanggan")

segment_counts = (
    rfm_df["customer_segment"]
    .value_counts()
    .reindex(segment_order, fill_value=0)
)

fig, ax = plt.subplots(figsize=(9, 5))

colors_pie = [
    segment_colors[segment]
    for segment in segment_counts.index
]

wedges, texts, autotexts = ax.pie(
    segment_counts,
    labels=segment_counts.index,
    autopct="%1.1f%%",
    startangle=140,
    colors=colors_pie,
    textprops={
        "color": "black",
        "fontsize": 11
    },
    pctdistance=0.75
)

centre_circle = plt.Circle(
    (0, 0),
    0.50,
    fc="white"
)

ax.add_artist(centre_circle)

ax.text(
    0,
    0,
    f"{segment_counts.sum():,}\nCustomers",
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold"
)

ax.set_title(
    "Proporsi Segmen Pelanggan Berdasarkan Analisis RFM",
    fontsize=14,
    pad=15
)

ax.set_aspect("equal")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# Ringkasan segmentasi pelanggan

st.markdown("### Ringkasan Segmentasi Pelanggan")

segment_summary = (
    rfm_df["customer_segment"]
    .value_counts()
    .reindex(segment_order, fill_value=0)
    .reset_index()
)

segment_summary.columns = [
    "customer_segment",
    "total_customers"
]

segment_summary["percentage"] = (
    segment_summary["total_customers"]
    / len(rfm_df) * 100
)

segment_summary = segment_summary.rename(columns={
    "customer_segment": "Customer Segment",
    "total_customers": "Total Customers",
    "percentage": "Percentage"
})

st.dataframe(
    segment_summary.style.format({
        "Total Customers": "{:,.0f}",
        "Percentage": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Segmentasi pelanggan dihitung berdasarkan penjumlahan skor "
    "Recency, Frequency, dan Monetary."
)

st.divider()


# Detail data pelanggan berdasarkan segmen

st.subheader("Detail Data Pelanggan")

selected_segment = st.selectbox(
    "Pilih Segmen Pelanggan",
    ["Semua Segmen"] + segment_order
)

if selected_segment == "Semua Segmen":
    customer_detail = rfm_df.copy()
else:
    customer_detail = rfm_df[
        rfm_df["customer_segment"] == selected_segment
    ].copy()

st.metric(
    "Jumlah Pelanggan",
    f"{len(customer_detail):,}"
)

customer_detail = customer_detail.sort_values(
    "monetary",
    ascending=False
)

customer_detail = customer_detail.rename(columns={
    "customer_unique_id": "Customer ID",
    "recency": "Recency (Days)",
    "frequency": "Frequency",
    "monetary": "Monetary (BRL)",
    "r_score": "R Score",
    "f_score": "F Score",
    "m_score": "M Score",
    "rfm_score": "RFM Score",
    "customer_segment": "Customer Segment"
})

st.dataframe(
    customer_detail[
        [
            "Customer ID",
            "Recency (Days)",
            "Frequency",
            "Monetary (BRL)",
            "R Score",
            "F Score",
            "M Score",
            "RFM Score",
            "Customer Segment"
        ]
    ],
    use_container_width=True,
    height=450,
    hide_index=True
)


# Sumber data

st.divider()

st.caption(
    "Source: Brazilian E-Commerce Public Dataset by Olist."
)

st.caption(
    "Note: Monetary dan total pendapatan dihitung dari kolom price "
    "tanpa memasukkan biaya pengiriman (freight_value)."
)
