import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control Operativo - Golfo de Fonseca", layout="wide")
st.title("Panel de Control Acuícola y Financiero")

conn = st.connection("gsheets", type=GSheetsConnection)

tab_config, tab_diario, tab_dash = st.tabs(["⚙️ Configuración", "📝 Registro Diario", "📊 Dashboard Analítico"])

# -----------------------------------------
# PESTAÑA 1: CONFIGURACIÓN MAESTRA
# -----------------------------------------
with tab_config:
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        nombre_laguna = st.selectbox("Laguna a Configurar", ["Laguna 03", "Laguna 06", "Laguna 08"])
        area_ha = st.number_input("Área (Hectáreas)", value=9.0, step=0.5)
        fecha_siembra = st.date_input("Fecha de Siembra", value=None)
        pls_sembradas = st.number_input("Larvas/Juv Sembradas", value=1350000, step=10000)
    
    with col_conf2:
        st.write("**Precios de Alimento e Insumos (Lempiras)**")
        precio_08 = st.number_input("0.8 mm | 40% (Saco 55 lbs)", value=1300.0, step=10.0)
        precio_12 = st.number_input("1.2 mm | 35% (Saco 55 lbs)", value=1150.0, step=10.0)
        precio_18 = st.number_input("1.8 mm | 30% (Saco 100 lbs)", value=1000.0, step=10.0)
        st.divider()
        precio_bacillus = st.number_input("Bacillus (Costo por gramo)", value=1.5, step=0.1)
        precio_semolina = st.number_input("Semolina (Costo por lb)", value=10.0, step=1.0)
    
    if st.button("Guardar Configuración Inicial"):
        if fecha_siembra is None:
            st.error("⚠️ Selecciona la fecha de siembra.")
        else:
            nueva_config = pd.DataFrame([{
                "Laguna": nombre_laguna, "Area_ha": area_ha, "Fecha_Siembra": str(fecha_siembra),
                "PLs_Sembradas": pls_sembradas, "Precio_08": precio_08, 
                "Precio_12": precio_12, "Precio_18": precio_18,
                "Precio_Bacillus": precio_bacillus, "Precio_Semolina": precio_semolina
            }])
            try:
                config_actual = conn.read(worksheet="Configuracion")
                config_actual = config_actual[config_actual["Laguna"] != nombre_laguna]
                config_actualizada = pd.concat([config_actual, nueva_config], ignore_index=True)
            except:
                config_actualizada = nueva_config
            conn.update(worksheet="Configuracion", data=config_actualizada)
            st.success(f"Configuración guardada para {nombre_laguna}.")

# -----------------------------------------
# PESTAÑA 2: REGISTRO DIARIO Y MUESTREOS SEPARADOS
# -----------------------------------------
with tab_diario:
    st.subheader("📝 Ingreso de Datos en Isla")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        laguna_registro = st.selectbox("Laguna a Reportar", ["Laguna 03", "Laguna 06", "Laguna 08"])
        fecha_registro = st.date_input("Fecha de Registro", datetime.date.today())
        tipo_alimento = st.selectbox("Dieta Utilizada", ["0.8 mm - 40% (55 lbs)", "1.2 mm - 35% (55 lbs)", "1.8 mm - 30% (100 lbs)"])
        
        st.write("**Calidad de Agua**")
        do_am = st.number_input("OD AM (mg/L)", value=4.0, step=0.1)
        temp_am = st.number_input("Temp AM (°C)", value=28.5, step=0.1)
        secchi = st.number_input("Secchi (cm)", value=35, step=1)
        
    with col_in2:
        st.write("**1. Muestreo Poblacional (Atarraya)**")
        hizo_poblacional = st.checkbox("¿Se hizo conteo por atarraya hoy?", value=False)
        lances = 0
        camarones_red = 0
        if hizo_poblacional:
            lances = st.number_input("Total Lances", value=27, step=1)
            camarones_red = st.number_input("Camarones Capturados (Total)", value=0, step=10)
        else:
            st.caption("ℹ️ Sin conteo hoy. Se usará la última densidad registrada.")

        st.write("**2. Muestreo de Peso (Biometría)**")
        hizo_peso = st.checkbox("¿Se midió peso promedio hoy?", value=True)
        peso_promedio = st.number_input("Peso Promedio Medido (g)", value=2.5, step=0.1)
        
        doc_dias = 0
        if fecha_siembra is not None:
            doc_dias = (fecha_registro - fecha_siembra).days
            st.success(f"**DOC Actual:** {doc_dias} días") if doc_dias >= 0 else st.warning("Faltan días para siembra")
            
    with col_in3:
        st.write("**Lectura de Charolas**")
        charolas_1 = st.number_input("Cant. en '1' (Todo)", value=0, step=1)
        charolas_2 = st.number_input("Cant. en '2' (Poco)", value=0, step=1)
        charolas_3 = st.number_input("Cant. en '3' (Nada)", value=0, step=1)
        
        st.write("**Movimientos Extraordinarios**")
        transferidos_hoy = st.number_input("Juveniles Transferidos / Raleo (Salida)", value=0, step=1000)
        
        st.write("**Insumos (Simbióticos)**")
        g_bacillus = st.number_input("Bacillus Aplicado (g)", value=0.0, step=10.0)
        lb_semolina = st.number_input("Semolina Aplicada (lb)", value=0.0, step=1.0)

    # ------------------------------------------------    
    # MOTOR INTELIGENTE: MEMORIA Y CÁLCULOS
    # ------------------------------------------------    
    AREA_ATARRAYA_M2 = 7.07 
    area_total_m2 = area_ha * 10000
    
    densidad_real = 0.0

    try:
        df_hist = conn.read(worksheet="Operacion_Diaria")
        df_lag = df_hist[df_hist["Laguna"] == laguna_registro]
        
        if not df_lag.empty:
            df_densidad_valida = df_lag[df_lag["Densidad"] > 0]
            ultima_densidad = df_densidad_valida.iloc[-1]["Densidad"] if not df_densidad_valida.empty else 15.0
            ultimo_peso = df_lag.iloc[-1]["Peso_g"] if not df_lag.empty else 2.5
        else:
            ultima_densidad = 15.0
            ultimo_peso = 2.5
    except:
        ultima_densidad = 15.0
        ultimo_peso = 2.5

    # Lógica de Densidad independiente
    if hizo_poblacional and lances > 0 and camarones_red > 0:
        area_muestreada = lances * AREA_ATARRAYA_M2
        densidad_real = camarones_red / area_muestreada
    else:
        densidad_real = ultima_densidad

    # Lógica de Peso independiente (si no marcó peso hoy, arrastra el último registrado)
    peso_final_calculado = peso_promedio if hizo_peso else ultimo_peso

    # Población y Biomasa
    poblacion_estimada = (densidad_real * area_total_m2) - transferidos_hoy
    biomasa_lbs = (poblacion_estimada * peso_final_calculado) / 453.59
    tope_alimento_lbs = biomasa_lbs * 0.03 
    
    supervivencia_dinamica = (poblacion_estimada / pls_sembradas) * 100 if pls_sembradas > 0 else 0

    # Freno de Charolas
    total_charolas = charolas_1 + charolas_2 + charolas_3
    indice_apetito = 0.0
    ajuste = 1.0
    if total_charolas > 0:
        indice_apetito = ((charolas_1 * 1) + (charolas_2 * 2) + (charolas_3 * 3)) / total_charolas
        if indice_apetito <= 1.4: ajuste = 1.05
        elif 1.4 < indice_apetito <= 2.2: ajuste = 0.90
        else: ajuste = 0.70

    racion_final_lbs = tope_alimento_lbs * ajuste

    # Costos (Alimento + Insumos)
    if "0.8 mm" in tipo_alimento:
        peso_saco_lbs, costo_saco_activo = 55, precio_08
    elif "1.2 mm" in tipo_alimento:
        peso_saco_lbs, costo_saco_activo = 55, precio_12
    else:
        peso_saco_lbs, costo_saco_activo = 100, precio_18

    sacos_necesarios = racion_final_lbs / peso_saco_lbs if peso_saco_lbs > 0 else 0
    costo_alimento = sacos_necesarios * costo_saco_activo
    costo_insumos = (g_bacillus * precio_bacillus) + (lb_semolina * precio_semolina)
    costo_diario_total = costo_alimento + costo_insumos

    # KPIs Históricos
    fca_actual = 0.0
    crecimiento_sem = 0.0
    try:
        if not df_lag.empty:
            alimento_acumulado = df_lag["Racion_lbs"].sum() + racion_final_lbs
            fca_actual = alimento_acumulado / biomasa_lbs if biomasa_lbs > 0 else 0.0
            
            df_semana = df_lag[df_lag["DOC"] <= doc_dias - 7]
            if not df_semana.empty:
                peso_anterior = df_semana.iloc[-1]["Peso_g"]
                crecimiento_sem = peso_final_calculado - peso_anterior
    except:
        pass

    st.divider()
    st.subheader("🎯 Resultados y Autorización")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Biomasa Estimada", f"{biomasa_lbs:,.0f} lbs", f"Supervivencia: {supervivencia_dinamica:.1f}%")
    col_r2.metric("Factor de Conversión (FCA)", f"{fca_actual:.2f}")
    col_r3.metric("Ración Autorizada", f"{racion_final_lbs:,.1f} lbs", f"Crecimiento 7d: +{crecimiento_sem:.2f}g")
    col_r4.metric("Costo Total Diario", f"L {costo_diario_total:,.2f}", f"Alimento: L {costo_alimento:,.0f} | Insumos: L {costo_insumos:,.0f}")

    if st.button("Guardar Reporte Diario", use_container_width=True):
        nuevo_dato = pd.DataFrame([{
            "Fecha": str(fecha_registro), "DOC": max(0, doc_dias), "Laguna": laguna_registro,
            "OD_AM": do_am, "Temp_C": temp_am, "Secchi_cm": secchi, "Dieta": tipo_alimento,
            "Densidad": round(densidad_real, 2), "Peso_g": peso_final_calculado, "Supervivencia_%": round(supervivencia_dinamica, 1),
            "Biomasa_lbs": round(biomasa_lbs, 2), "Indice_Apetito": round(indice_apetito, 2),
            "Racion_lbs": round(racion_final_lbs, 2), "Sacos_Usados": round(sacos_necesarios, 2),
            "Gramos_Bacillus": g_bacillus, "Libras_Semolina": lb_semolina,
            "Costo_Lempiras": round(costo_diario_total, 2)
        }])
        try:
            datos_actuales = conn.read(worksheet="Operacion_Diaria")
            datos_actualizados = pd.concat([datos_actuales, nuevo_dato], ignore_index=True)
        except:
            datos_actualizados = nuevo_dato
        conn.update(worksheet="Operacion_Diaria", data=datos_actualizados)
        st.success(f"Reporte de {laguna_registro} guardado exitosamente.")

# -----------------------------------------
# PESTAÑA 3: DASHBOARD ANALÍTICO
# -----------------------------------------
with tab_dash:
    st.subheader("Análisis de Tendencias")
    
    try:
        df_hist = conn.read(worksheet="Operacion_Diaria")
        
        if not df_hist.empty:
            laguna_dash = st.selectbox("Seleccionar Laguna para Análisis", df_hist["Laguna"].unique())
            df_filtro = df_hist[df_hist["Laguna"] == laguna_dash].sort_values(by="DOC")
            
            fig_crecimiento = px.line(df_filtro, x="DOC", y="Peso_g", markers=True, 
                                      title="Curva de Crecimiento (Pesos Registrados)")
            st.plotly_chart(fig_crecimiento, use_container_width=True)
            
            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                fig_agua = px.line(df_filtro, x="DOC", y=["OD_AM", "Indice_Apetito"], markers=True,
                                   title="Relación: Oxígeno Matutino vs Apetito (1=Bueno, 3=Malo)")
                st.plotly_chart(fig_agua, use_container_width=True)
                
            with col_graf2:
                fig_costo = px.bar(df_filtro, x="DOC", y="Costo_Lempiras", 
                                   title="Gasto Diario Total (Alimento + Insumos en Lempiras)", color="Dieta")
                st.plotly_chart(fig_costo, use_container_width=True)
            
            csv = df_filtro.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Historial a Excel/CSV",
                data=csv,
                file_name=f'Historial_{laguna_dash}.csv',
                mime='text/csv',
            )
        else:
            st.info("No hay datos históricos suficientes para generar las gráficas.")
    except:
        st.warning("Guarda al menos un reporte para visualizar el Dashboard.")