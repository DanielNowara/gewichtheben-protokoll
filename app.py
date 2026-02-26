import streamlit as st
import pandas as pd

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Gewichtheben Protokoll", layout="wide")
st.title("🏋️‍♂️ Gewichtheben Wettkampf-Protokoll")

# --- DATEN LADEN ---
@st.cache_data
def load_relativ_tables():
pfad_m = "tabelle_m.csv"
pfad_w = "tabelle_w.csv"
    
    try:
        # skiprows=2 überspringt die ersten beiden Zeilen (die Überschriften wie ",männlich" und "KG,")
        df_m = pd.read_csv(pfad_m, names=["KG", "Abzug"], skiprows=2)
        df_w = pd.read_csv(pfad_w, names=["KG", "Abzug"], skiprows=2)
        
        # Formatierung reparieren: Kommas zu Punkten machen und als Zahl speichern
        for df in [df_m, df_w]:
            df['KG'] = df['KG'].astype(str).str.replace(',', '.').astype(float)
            df['Abzug'] = df['Abzug'].astype(str).str.replace(',', '.').astype(float)
            # Zur Sicherheit nach Gewicht aufsteigend sortieren
            df.sort_values('KG', inplace=True)
            
        return df_m, df_w
    except FileNotFoundError:
        st.error("Fehler: Die Relativtabellen konnten unter den angegebenen Pfaden nicht gefunden werden!")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Fehler beim Verarbeiten der Tabellen: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_m, df_w = load_relativ_tables()

def get_relativ_abzug(geschlecht, gewicht):
    if df_m.empty or df_w.empty: return 0.0
    
    df = df_m if geschlecht == 'm' else df_w
    gewicht_float = float(gewicht)
    
    # Finde alle Gewichte in der Tabelle, die kleiner oder gleich dem Körpergewicht des Athleten sind
    valid_weights = df[df['KG'] <= gewicht_float]
    
    if not valid_weights.empty:
        # Nimm den Abzug vom schwersten passenden Gewicht (also den letzten Wert in der Liste)
        return valid_weights.iloc[-1]['Abzug']
    
    return 0.0

# --- SESSION STATE FÜR DIE ATHLETEN ---
if 'athleten' not in st.session_state:
    st.session_state.athleten = []

# --- EINGABEBEREICH ---
st.header("Neuen Athleten hinzufügen")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    name = st.text_input("Name")
    verein = st.text_input("Verein")
with col2:
    jg = st.text_input("Jahrgang")
    geschlecht = st.selectbox("Geschlecht", ["m", "w"])
with col3:
    gewicht = st.number_input("Körpergewicht (kg)", min_value=30.0, max_value=200.0, step=0.1, value=80.0)
with col4:
    st.markdown("**Reißen (kg)**")
    r1 = st.number_input("1. Versuch R", step=1.0)
    r2 = st.number_input("2. Versuch R", step=1.0)
    r3 = st.number_input("3. Versuch R", step=1.0)
with col5:
    st.markdown("**Stoßen (kg)**")
    s1 = st.number_input("1. Versuch S", step=1.0)
    s2 = st.number_input("2. Versuch S", step=1.0)
    s3 = st.number_input("3. Versuch S", step=1.0)

if st.button("Athlet hinzufügen / Berechnen", type="primary"):
    # Beste gültige Versuche ermitteln (> 0)
    best_r = max([x for x in [r1, r2, r3] if x > 0], default=0)
    best_s = max([x for x in [s1, s2, s3] if x > 0], default=0)
    zweikampf = best_r + best_s
    
    abzug = get_relativ_abzug(geschlecht, gewicht)
    
    # Relativpunkte berechnen (Punkte können nicht negativ werden)
    rel_r = max(0, best_r - abzug) if best_r > 0 else 0
    rel_s = max(0, best_s - abzug) if best_s > 0 else 0
    
    # Zweikampf-Relativpunkte
    rel_zk = rel_r + rel_s

    st.session_state.athleten.append({
        "Name": name,
        "Verein": verein,
        "m/w": geschlecht,
        "KG": gewicht,
        "Abzug": abzug,
        "Reißen Bester": best_r,
        "Relativ Reißen": rel_r,
        "Stoßen Bester": best_s,
        "Relativ Stoßen": rel_s,
        "Zweikampf": zweikampf,
        "Relativ Gesamt": rel_zk
    })
    st.success(f"{name} wurde erfolgreich hinzugefügt! (Abzug: {abzug} Punkte)")

# --- ERGEBNISTABELLE ---
st.header("Aktuelles Wettkampf-Protokoll")
if len(st.session_state.athleten) > 0:
    df_results = pd.DataFrame(st.session_state.athleten)
    
    # Sortieren nach Relativpunkten Gesamt (absteigend)
    df_results = df_results.sort_values(by="Relativ Gesamt", ascending=False).reset_index(drop=True)
    
    # Tabelle anzeigen
    st.dataframe(df_results, use_container_width=True)
    
    # Mannschaftssumme
    st.subheader(f"Gesamt-Relativpunkte: {df_results['Relativ Gesamt'].sum():.2f}")
    
    # Option zum Exportieren als neue CSV
    csv = df_results.to_csv(index=False, sep=";").encode('utf-8')
    st.download_button(
        label="Protokoll als CSV herunterladen",
        data=csv,
        file_name='wettkampf_ergebnis.csv',
        mime='text/csv',
    )
else:
    st.info("Noch keine Athleten eingetragen.")