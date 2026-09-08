import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
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
        area_ha = st.number_input("Área (Hectáreas)", value=None, step=0.5, placeholder="Ej. 9.0")
        fecha_siembra = st.date_input("Fecha de Siembra", value=None)
        pls_sembradas = st.number_input("Larvas/Juv Sembradas", value=None, step=10000, placeholder="Ej. 1350000")
    
    with col_conf2:
        st.write("**Precios de Alimento e Insumos (Lempiras)**")
        precio_08 = st.number_input("0.8 mm | 40% (Saco 55 lbs)", value=None, step=10.0, placeholder="Ej. 1300.0")
        precio_12 = st.number_input("1.2 mm | 35% (Saco 55 lbs)", value=None, step=10.0, placeholder="Ej. 1150.0")
        precio_18 = st.number_input("1.8 mm | 30% (Saco 100 lbs)", value=None, step=10.0, placeholder="Ej. 1000.0")
        st.divider()
        precio_bacillus = st.number_input("Bacillus (Costo por gramo)", value=None, step=0.1, placeholder="Ej. 1.5")
        precio_semolina = st.number_input("Semolina (Costo por lb)", value=None, step=1.0, placeholder="Ej. 10.0")
    
    if st.button("Guardar Configuración Inicial"):
        if None in [area_ha, pls_sembradas, precio_08, precio_12, precio_18, precio_bacillus, precio_semolina, fecha_siembra]:
            st.error("⚠️ Por favor, llena todos los campos numéricos y la fecha antes de guardar.")
        else:
            columnas_config = ["Laguna", "Area_ha", "Fecha_Siembra", "PLs_Sembradas", "Precio_08", "Precio_12", "Precio_18", "Precio_Bacillus", "Precio_Semolina"]
            nueva_config = pd.DataFrame([{
                "Laguna": nombre_laguna, "Area_ha": area_ha, "Fecha_Siembra": str(fecha_siembra),
                "PLs_Sembradas": pls_sembradas, "Precio_08": precio_08, 
                "Precio_12": precio_12, "Precio_18": precio_18,
                "Precio_Bacillus": precio_bacillus, "Precio_Semolina": precio_semolina
            }])[columnas_config]
            
            try:
                config_actual = conn.read(worksheet="Configuracion", ttl=0)
                config_actual.columns = config_actual.columns.str.strip()
                config_actual = config_actual[config_actual["Laguna"] != nombre_laguna]
                config_actualizada = pd.concat([config_actual, nueva_config], ignore_index=True)
            except:
                config_actualizada = nueva_config
            
            conn.update(worksheet="Configuracion", data=config_actualizada)
            st.success(f"Configuración guardada en la base de datos para {nombre_laguna}.")

# -----------------------------------------
# PESTAÑA 2: REGISTRO DIARIO Y MUESTREOS SEPARADOS
# -----------------------------------------
with tab_diario:
    st.subheader("📝 Ingreso de Datos en Isla")
    
    laguna_registro = st.selectbox("Laguna a Reportar", ["Laguna 03", "Laguna 06", "Laguna 08"])
    
    area_ha_db = 0.0
    pls_sembradas_db = 0
    p_08_db, p_12_db, p_18_db = 0.0, 0.0, 0.0
    p_bac_db, p_sem_db = 0.0, 0.0
    fecha_siembra_db = None
    
    try:
        df_conf = conn.read(worksheet="Configuracion", ttl=0)
        df_conf.columns = df_conf.columns.str.strip()
        df_conf_lag = df_conf[df_conf["Laguna"] == laguna_registro]
        if not df_conf_lag.empty:
            conf = df_conf_lag.iloc[-1]
            area_ha_db = float(conf["Area_ha"])
            pls_sembradas_db = float(conf["PLs_Sembradas"])
            p_08_db, p_12_db, p_18_db = float(conf["Precio_08"]), float(conf["Precio_12"]), float(conf["Precio_18"])
            p_bac_db, p_sem_db = float(conf["Precio_Bacillus"]), float(conf["Precio_Semolina"])
            if pd.notna(conf["Fecha_Siembra"]):
                fecha_siembra_db = datetime.datetime.strptime(str(conf["Fecha_Siembra"]), "%Y-%m-%d").date()
    except:
        pass

    if area_ha_db == 0.0:
        st.warning(f"⚠️ {laguna_registro} no tiene configuración guardada. Las estimaciones de biomasa serán cero. Ve a la pestaña Configuración.")

    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        fecha_registro = st.date_input("Fecha de Registro", datetime.date.today())
        tipo_alimento = st.selectbox("Dieta Utilizada", ["0.8 mm - 40% (55 lbs)", "1.2 mm - 35% (55 lbs)", "1.8 mm - 30% (100 lbs)"])
        
        st.write("**Calidad de Agua (Mañana y Tarde)**")
        do_am = st.number_input("OD AM (mg/L)", value=None, step=0.1, placeholder="Ej. 4.0")
        temp_am = st.number_input("Temp AM (°C)", value=None, step=0.1, placeholder="Ej. 28.5")
        do_pm = st.number_input("OD PM (mg/L)", value=None, step=0.1, placeholder="Ej. 6.5")
        temp_pm = st.number_input("Temp PM (°C)", value=None, step=0.1, placeholder="Ej. 31.0")
        secchi = st.number_input("Secchi (cm)", value=None, step=1, placeholder="Ej. 35")
        salinidad = st.number_input("Salinidad (ppt)", value=None, step=0.5, placeholder="Ej. 28.0")
        
    with col_in2:
        st.write("**1. Muestreo Poblacional (Atarraya)**")
        hizo_poblacional = st.checkbox("¿Se hizo conteo por atarraya hoy?", value=False)
        lances, camarones_red = None, None
        if hizo_poblacional:
            lances = st.number_input("Total Lances", value=None, step=1, placeholder="Ej. 27")
            camarones_red = st.number_input("Camarones Capturados (Total)", value=None, step=10, placeholder="Ej. 250")
        else:
            st.caption("ℹ️ Sin conteo hoy. Se usará la última densidad registrada.")

        st.write("**2. Muestreo de Peso (Biometría)**")
        hizo_peso = st.checkbox("¿Se midió peso promedio hoy?", value=True)
        peso_promedio = None
        if hizo_peso:
            peso_promedio = st.number_input("Peso Promedio Medido (g)", value=None, step=0.1, placeholder="Ej. 2.5")
        else:
            st.caption("ℹ️ Día sin biometría. Se proyectará el peso anterior.")
        
        doc_dias = 0
        if fecha_siembra_db is not None:
            doc_dias = (fecha_registro - fecha_siembra_db).days
            if doc_dias >= 0:
                st.success(f"**DOC Actual:** {doc_dias} días")
            else:
                st.warning("Faltan días para siembra")
            
    with col_in3:
        st.write("**Lectura de Charolas**")
        charolas_1 = st.number_input("Cant. en '1' (Todo)", value=None, step=1, placeholder="Ej. 0")
        charolas_2 = st.number_input("Cant. en '2' (Poco)", value=None, step=1, placeholder="Ej. 2")
        charolas_3 = st.number_input("Cant. en '3' (Nada)", value=None, step=1, placeholder="Ej. 10")
        
        st.write("**Movimientos Extraordinarios**")
        transferidos_hoy = st.number_input("Juveniles Transferidos / Raleo (Salida)", value=None, step=1000, placeholder="Ej. 0")
        
        st.write("**Insumos (Simbióticos)**")
        g_bacillus = st.number_input("Bacillus Aplicado (g)", value=None, step=10.0, placeholder="Ej. 0.0")
        lb_semolina = st.number_input("Semolina Aplicada (lb)", value=None, step=1.0, placeholder="Ej. 0.0")

    c_do = do_am if do_am is not None else 0.0
    c_temp = temp_am if temp_am is not None else 0.0
    c_do_pm = do_pm if do_pm is not None else 0.0
    c_temp_pm = temp_pm if temp_pm is not None else 0.0
    c_secchi = secchi if secchi is not None else 0
    c_sal = salinidad if salinidad is not None else 0.0
    c_lances = lances if lances is not None else 0
    c_cam_red = camarones_red if camarones_red is not None else 0
    c_peso_input = peso_promedio if peso_promedio is not None else 0.0
    c_transf = transferidos_hoy if transferidos_hoy is not None else 0
    c_char1 = charolas_1 if charolas_1 is not None else 0
    c_char2 = charolas_2 if charolas_2 is not None else 0
    c_char3 = charolas_3 if charolas_3 is not None else 0
    c_bac = g_bacillus if g_bacillus is not None else 0.0
    c_sem = lb_semolina if lb_semolina is not None else 0.0

    AREA_ATARRAYA_M2 = 7.07 
    area_total_m2 = area_ha_db * 10000
    
    densidad_real = 0.0
    ultima_densidad = 0.0
    ultimo_peso = 0.0

    try:
        df_hist = conn.read(worksheet="Operacion_Diaria", ttl=0)
        df_hist.columns = df_hist.columns.str.strip()
        df_lag = df_hist[df_hist["Laguna"] == laguna_registro]
        
        if not df_lag.empty:
            df_densidad_valida = df_lag[df_lag["Densidad"] > 0]
            if not df_densidad_valida.empty:
                ultima_densidad = float(df_densidad_valida.iloc[-1]["Densidad"])
            else:
                if area_total_m2 > 0:
                    ultima_densidad = pls_sembradas_db / area_total_m2
                    
            df_peso_valido = df_lag[df_lag["Peso_g"] > 0]
            if not df_peso_valido.empty:
                ultimo_peso = float(df_peso_valido.iloc[-1]["Peso_g"])
            else:
                ultimo_peso = 0.1
        else:
            if area_total_m2 > 0:
                ultima_densidad = pls_sembradas_db / area_total_m2
            ultimo_peso = 0.1
    except:
        if area_total_m2 > 0:
            ultima_densidad = pls_sembradas_db / area_total_m2
        ultimo_peso = 0.1

    if hizo_poblacional and c_lances > 0 and c_cam_red > 0:
        area_muestreada = c_lances * AREA_ATARRAYA_M2
        densidad_real = c_cam_red / area_muestreada
    else:
        densidad_real = ultima_densidad

    peso_final_calculado = c_peso_input if hizo_peso else ultimo_peso

    poblacion_estimada = (densidad_real * area_total_m2) - c_transf
    biomasa_lbs = (poblacion_estimada * peso_final_calculado) / 453.59
    tope_alimento_lbs = biomasa_lbs * 0.03 
    
    supervivencia_dinamica = (poblacion_estimada / pls_sembradas_db) * 100 if pls_sembradas_db > 0 else 0.0

    total_charolas = c_char1 + c_char2 + c_char3
    indice_apetito = 0.0
    ajuste = 1.0
    if total_charolas > 0:
        indice_apetito = ((c_char1 * 1) + (c_char2 * 2) + (c_char3 * 3)) / total_charolas
        if indice_apetito <= 1.4: ajuste = 1.05
        elif 1.4 < indice_apetito <= 2.2: ajuste = 0.90
        else: ajuste = 0.70
    else:
        ajuste = 1.0

    racion_final_lbs = tope_alimento_lbs * ajuste

    if "0.8 mm" in tipo_alimento:
        peso_saco_lbs, costo_saco_activo = 55, p_08_db
    elif "1.2 mm" in tipo_alimento:
        peso_saco_lbs, costo_saco_activo = 55, p_12_db
    else:
        peso_saco_lbs, costo_saco_activo = 100, p_18_db

    sacos_necesarios = racion_final_lbs / peso_saco_lbs if peso_saco_lbs > 0 else 0
    costo_alimento = sacos_necesarios * costo_saco_activo
    costo_insumos = (c_bac * p_bac_db) + (c_sem * p_sem_db)
    costo_diario_total = costo_alimento + costo_insumos

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
        columnas_operacion = [
            "Fecha", "DOC", "Laguna", "OD_AM", "Temp_C", "OD_PM", "Temp_PM", "Secchi_cm", "Salinidad_ppt", "Dieta", 
            "Densidad", "Peso_g", "Supervivencia_%", "Biomasa_lbs", "Indice_Apetito", 
            "Racion_lbs", "Sacos_Usados", "Gramos_Bacillus", "Libras_Semolina", "Costo_Lempiras"
        ]
        nuevo_dato = pd.DataFrame([{
            "Fecha": str(fecha_registro), "DOC": max(0, doc_dias), "Laguna": laguna_registro,
            "OD_AM": c_do, "Temp_C": c_temp, "OD_PM": c_do_pm, "Temp_PM": c_temp_pm, 
            "Secchi_cm": c_secchi, "Salinidad_ppt": c_sal, "Dieta": tipo_alimento,
            "Densidad": round(densidad_real, 4), "Peso_g": peso_final_calculado, "Supervivencia_%": round(supervivencia_dinamica, 1),
            "Biomasa_lbs": round(biomasa_lbs, 2), "Indice_Apetito": round(indice_apetito, 2),
            "Racion_lbs": round(racion_final_lbs, 2), "Sacos_Usados": round(sacos_necesarios, 2),
            "Gramos_Bacillus": c_bac, "Libras_Semolina": c_sem,
            "Costo_Lempiras": round(costo_diario_total, 2)
        }])[columnas_operacion]
        
        try:
            datos_actuales = conn.read(worksheet="Operacion_Diaria", ttl=0)
            datos_actuales.columns = datos_actuales.columns.str.strip()
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
        df_hist = conn.read(worksheet="Operacion_Diaria", ttl=0)
        df_hist.columns = df_hist.columns.str.strip()
        
        if not df_hist.empty and "Laguna" in df_hist.columns:
            laguna_dash = st.selectbox("Seleccionar Laguna para Análisis", df_hist["Laguna"].unique())
            df_filtro = df_hist[df_hist["Laguna"] == laguna_dash].sort_values(by="DOC")
            
            fig_crecimiento = px.line(df_filtro, x="DOC", y="Peso_g", markers=True, 
                                      title="Curva de Crecimiento (Pesos Registrados)")
            st.plotly_chart(fig_crecimiento, use_container_width=True)
            
            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                fig_agua = go.Figure()
                fig_agua.add_trace(go.Scatter(x=df_filtro["DOC"], y=df_filtro["OD_AM"], name="OD AM (mg/L)", mode="lines+markers"))
                fig_agua.add_trace(go.Scatter(x=df_filtro["DOC"], y=df_filtro["OD_PM"], name="OD PM (mg/L)", mode="lines+markers"))
                fig_agua.add_trace(go.Scatter(x=df_filtro["DOC"], y=df_filtro["Indice_Apetito"], name="Índice Apetito", mode="lines+markers", yaxis="y2"))
                
                fig_agua.update_layout(
                    title="Relación: Oxígeno (AM/PM) vs Índice de Apetito",
                    xaxis=dict(title="DOC"),
                    yaxis=dict(title="Oxígeno (mg/L)"),
                    yaxis2=dict(title="Índice de Apetito", overlaying="y", side="right", range=[0, 3.5]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
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