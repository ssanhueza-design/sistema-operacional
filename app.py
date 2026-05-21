import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle

# ==================================================
# CONFIGURACIÓN
# ==================================================

st.set_page_config(
    page_title="Sistema Operacional Industrial",
    layout="wide"
)

# ==================================================
# ESTILO
# ==================================================

st.markdown("""
<style>

.main {
    background-color: #f4f6f9;
}

h1 {
    color: #0f172a;
}

div[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #dbe2ea;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 1px 4px rgba(0,0,0,0.1);
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# TÍTULO
# ==================================================

st.title("Sistema de Reporte Operacional")
st.subheader("Dashboard Industrial de Producción")

st.divider()

# ==================================================
# INFORMACIÓN GENERAL
# ==================================================

st.header("Información del Turno")

col1, col2, col3 = st.columns(3)

with col1:
    fecha = st.date_input("Fecha")

with col2:
    turno = st.selectbox("Turno", ["A", "B", "C", "D"])

with col3:
    supervisor = st.text_input("Supervisor")

st.divider()

# ==================================================
# PRODUCCIÓN TOTAL
# ==================================================

st.header("Producción Total")

col1, col2 = st.columns(2)

with col1:
    toneladas = float(st.number_input("Toneladas Totales", min_value=0.0))

with col2:
    meta = float(st.number_input("Meta Producción", min_value=1.0, value=100.0))

eficiencia = (toneladas / meta * 100) if meta > 0 else 0

st.metric("Eficiencia Producción", f"{eficiencia:.2f}%")

st.divider()

# ==================================================
# PRODUCCIÓN POR LÍNEA (refactorizado con loop)
# ==================================================

st.header("Producción por Línea")

LINEAS = ["2C", "3", "4", "5", "6", "7"]

col1, col2, col3 = st.columns(3)
columnas = [col1, col1, col2, col2, col3, col3]

prod_lineas = {}

for i, linea in enumerate(LINEAS):
    with columnas[i]:
        prod_lineas[linea] = float(
            st.number_input(
                f"Línea {linea} (Ton)",
                min_value=0.0,
                key=f"prod_{linea}"
            )
        )

# ==================================================
# VALIDACIÓN: suma de líneas vs total
# ==================================================

suma_lineas = sum(prod_lineas.values())

if toneladas > 0 and abs(suma_lineas - toneladas) > 0.1:
    st.warning(
        f"⚠️ La suma de líneas ({suma_lineas:.2f} ton) "
        f"difiere del total ingresado ({toneladas:.2f} ton). "
        f"Revisa los valores."
    )

st.divider()

# ==================================================
# RECICLADO POR LÍNEA (refactorizado con loop)
# ==================================================

st.header("Reciclado por Línea")

reciclados = {}

for linea in LINEAS:
    st.subheader(f"Línea {linea}")
    c1, c2 = st.columns(2)

    with c1:
        reciclados[f"seco_{linea}"] = float(
            st.number_input(
                f"Reciclado Seco {linea} (kg)",
                min_value=0.0,
                key=f"seco_{linea}"
            )
        )

    with c2:
        reciclados[f"aceitado_{linea}"] = float(
            st.number_input(
                f"Reciclado Aceitado {linea} (kg)",
                min_value=0.0,
                key=f"aceitado_{linea}"
            )
        )

st.divider()

# ==================================================
# EQUIPOS
# ==================================================

st.header("Equipos")

col1, col2 = st.columns(2)

with col1:
    gruas = int(st.number_input("Grúas Operativas", min_value=0))

with col2:
    equipos_fuera = int(st.number_input("Equipos Fuera Servicio", min_value=0))

st.divider()

# ==================================================
# PERSONAL
# ==================================================

st.header("Personal")

col1, col2, col3 = st.columns(3)

with col1:
    asistencia = int(st.number_input("Asistencia", min_value=0))

with col2:
    ausencias = int(st.number_input("Ausencias", min_value=0))

with col3:
    accidentes = int(st.number_input("Accidentes", min_value=0))

st.divider()

# ==================================================
# OBSERVACIONES
# ==================================================

st.header("Observaciones")

observaciones = st.text_area("Observaciones Generales")

st.divider()

# ==================================================
# HELPER: exportar figura Plotly a BytesIO (sin disco)
# ==================================================

def fig_to_image(fig, width, height):
    """Convierte un figura Plotly a un objeto BytesIO."""
    buf = BytesIO()
    fig.write_image(buf, format="png", width=width, height=height, scale=2)
    buf.seek(0)
    return buf

# ==================================================
# BOTÓN PDF
# ==================================================

if st.button("Generar Informe PDF"):

    # ==================================================
    # DATAFRAMES
    # ==================================================

    produccion_df = pd.DataFrame({
        "Línea": LINEAS,
        "Toneladas": [prod_lineas[l] for l in LINEAS]
    })

    reciclado_seco_df = pd.DataFrame({
        "Línea": LINEAS,
        "Kg": [reciclados[f"seco_{l}"] for l in LINEAS]
    })

    reciclado_aceitado_df = pd.DataFrame({
        "Línea": LINEAS,
        "Kg": [reciclados[f"aceitado_{l}"] for l in LINEAS]
    })

    # ==================================================
    # COLORES POR LÍNEA
    # ==================================================

    colores_lineas = {
        "2C": "#DC2626",
        "3":  "#16A34A",
        "4":  "#2563EB",
        "5":  "#EAB308",
        "6":  "#9333EA",
        "7":  "#EA580C"
    }

    # ==================================================
    # GRÁFICO PRODUCCIÓN
    # ==================================================

    fig_prod = px.bar(
        produccion_df,
        x="Línea",
        y="Toneladas",
        title="Producción por Línea",
        text_auto=True,
        color="Línea",
        color_discrete_map=colores_lineas,
        template="plotly_white"
    )

    fig_prod.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="black",
        title_font_size=20
    )

    # ==================================================
    # GRÁFICO RECICLADO SECO
    # ==================================================

    fig_seco = px.pie(
        reciclado_seco_df,
        names="Línea",
        values="Kg",
        title="Reciclado Seco por Línea (%)",
        hole=0.4,
        color="Línea",
        color_discrete_map=colores_lineas,
        template="plotly_white"
    )

    fig_seco.update_layout(
        paper_bgcolor="white",
        font_color="black",
        title_font_size=20
    )

    # ==================================================
    # GRÁFICO RECICLADO ACEITADO
    # ==================================================

    fig_aceitado = px.pie(
        reciclado_aceitado_df,
        names="Línea",
        values="Kg",
        title="Reciclado Aceitado por Línea (%)",
        hole=0.4,
        color="Línea",
        color_discrete_map=colores_lineas,
        template="plotly_white"
    )

    fig_aceitado.update_layout(
        paper_bgcolor="white",
        font_color="black",
        title_font_size=20
    )

    # ==================================================
    # EXPORTAR IMÁGENES EN MEMORIA (sin archivos en disco)
    # ==================================================

    try:
        img_prod     = fig_to_image(fig_prod,     width=1200, height=700)
        img_seco     = fig_to_image(fig_seco,     width=1000, height=700)
        img_aceitado = fig_to_image(fig_aceitado, width=1000, height=700)
    except Exception as e:
        st.error(
            f"❌ Error al generar los gráficos: {e}\n\n"
            "Asegúrate de tener instalado `kaleido` (`pip install kaleido`)."
        )
        st.stop()

    # ==================================================
    # CONSTRUIR PDF
    # ==================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=20
    )

    elementos = []
    styles    = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "titulo",
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=25
    )

    subtitulo_style = ParagraphStyle(
        "subtitulo",
        parent=styles['Heading2'],
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=12
    )

    # ---------- Título ----------
    elementos.append(Paragraph("INFORME OPERACIONAL INDUSTRIAL", titulo_style))

    elementos.append(Paragraph(
        f"<b>Fecha:</b> {fecha.strftime('%d-%m-%Y')}<br/>"
        f"<b>Turno:</b> {turno}<br/>"
        f"<b>Supervisor:</b> {supervisor}",
        styles["BodyText"]
    ))

    elementos.append(Spacer(1, 25))

    # ---------- Resumen ejecutivo ----------
    elementos.append(Paragraph("Resumen Ejecutivo", subtitulo_style))

    kpi_table = Table([
        ["Producción", "Eficiencia", "Rec. Seco", "Rec. Aceitado"],
        [
            f"{toneladas:.2f} ton",
            f"{eficiencia:.2f}%",
            f"{reciclado_seco_df['Kg'].sum():.0f} kg",
            f"{reciclado_aceitado_df['Kg'].sum():.0f} kg"
        ]
    ], colWidths=[120, 120, 120, 120])

    kpi_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('BACKGROUND',    (0, 1), (-1, 1), colors.HexColor("#E2E8F0")),
        ('GRID',          (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elementos.append(kpi_table)
    elementos.append(Spacer(1, 25))

    # ---------- Gráficos ----------
    elementos.append(Paragraph("Producción por Línea", subtitulo_style))
    elementos.append(RLImage(img_prod, width=500, height=280))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Distribución Reciclado Seco", subtitulo_style))
    elementos.append(RLImage(img_seco, width=420, height=280))
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("Distribución Reciclado Aceitado", subtitulo_style))
    elementos.append(RLImage(img_aceitado, width=420, height=280))
    elementos.append(Spacer(1, 25))

    # ---------- Tabla resumen operacional ----------
    elementos.append(Paragraph("Resumen Operacional", subtitulo_style))

    tabla_data = [
        ["Indicador",             "Valor"],
        ["Producción Total",      f"{toneladas:.2f} ton"],
        ["Meta",                  f"{meta:.2f} ton"],
        ["Eficiencia",            f"{eficiencia:.2f}%"],
        ["Suma Líneas",           f"{suma_lineas:.2f} ton"],
        ["Grúas Operativas",      str(gruas)],
        ["Equipos Fuera Servicio",str(equipos_fuera)],
        ["Asistencia",            str(asistencia)],
        ["Ausencias",             str(ausencias)],
        ["Accidentes",            str(accidentes)],
    ]

    tabla = Table(tabla_data, colWidths=[250, 220])

    tabla.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND',    (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 25))

    # ---------- Observaciones ----------
    elementos.append(Paragraph("Observaciones Generales", subtitulo_style))
    elementos.append(Paragraph(
        observaciones if observaciones else "Sin observaciones.",
        styles["BodyText"]
    ))

    # ---------- Build ----------
    doc.build(elementos)

    pdf = buffer.getvalue()
    buffer.close()

    st.success("✅ Informe generado correctamente.")

    st.download_button(
        label="📥 Descargar Informe PDF",
        data=pdf,
        file_name=f"Informe_Operacional_{fecha.strftime('%d-%m-%Y')}_Turno{turno}.pdf",
        mime="application/pdf"
    )