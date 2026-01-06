import os
import csv
from datetime import datetime

import pandas as pd
from flask import Flask, request, render_template, redirect, abort, send_file

app = Flask(__name__)

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.csv")
XLSX_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.xlsx")

# =========================
# Seguridad para descargas
# (en Render: Settings -> Environment -> ADMIN_TOKEN)
# =========================
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hd_2026_iso_descarga_segura")

def _check_admin_token():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(403)

# =========================
# Columnas "oficiales" (según tu HTML)
# =========================
CAMPOS = [
    "fecha_envio",
    "ambito",
    "descripcion_problema",
    "impactos",
    "antiguedad_problema",
    "horizonte",
    "rol_contacto",
    "numero_participantes",
    "desea_recomendacion",
    "nombre",
    "correo",
    "empresa",
    "cargo",
    "datos_adicionales",
    "pais",
    "idioma",
]

def _load_existing_df():
    """
    Carga lo existente (prioriza XLSX), y normaliza columnas:
    - si hay columnas extra antiguas, se conservan
    - si faltan columnas de CAMPOS, se crean vacías
    """
    if os.path.exists(XLSX_PATH):
        df = pd.read_excel(XLSX_PATH, dtype=str).fillna("")
    elif os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    else:
        df = pd.DataFrame(columns=CAMPOS)

    # Asegurar que existan todas las columnas "oficiales"
    for c in CAMPOS:
        if c not in df.columns:
            df[c] = ""

    # Orden: primero CAMPOS, luego cualquier extra antigua al final
    ordered_cols = [c for c in CAMPOS] + [c for c in df.columns if c not in CAMPOS]
    df = df[ordered_cols]
    return df

def _write_outputs(df):
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
    df.to_excel(XLSX_PATH, index=False)

# =========================
# Rutas UI
# =========================
@app.route("/")
def home():
    return redirect("/diagnostico")

@app.route("/diagnostico", methods=["GET"])
def diagnostico():
    return render_template("diagnostico.html")

@app.route("/submit", methods=["GET", "POST"])
def submit():
    # Si alguien entra a /submit desde el navegador (GET), no debe romperse
    if request.method == "GET":
        return redirect("/diagnostico")

    os.makedirs(DATA_DIR, exist_ok=True)

    data = request.form

    # Construir fila nueva con los nombres EXACTOS del HTML
    fila = {
        "fecha_envio": datetime.now().isoformat(),
        "ambito": (data.get("ambito") or "").strip(),
        "descripcion_problema": (data.get("descripcion") or "").strip(),
        "impactos": ", ".join([x.strip() for x in data.getlist("impactos") if x and x.strip()]),
        "antiguedad_problema": (data.get("antiguedad") or "").strip(),
        "horizonte": (data.get("horizonte") or "").strip(),
        "rol_contacto": (data.get("rol") or "").strip(),
        "numero_participantes": (data.get("participantes") or "").strip(),
        "desea_recomendacion": (data.get("recomendacion") or "").strip(),
        "nombre": (data.get("nombre") or "").strip(),
        "correo": (data.get("correo") or "").strip(),
        "empresa": (data.get("empresa") or "").strip(),
        "cargo": (data.get("cargo") or "").strip(),
        "datos_adicionales": (data.get("extra") or "").strip(),
        "pais": (data.get("pais") or "").strip(),
        "idioma": (data.get("idioma") or "").strip(),
    }

    # Cargar existente y anexar sin romper columnas
    df = _load_existing_df()

    # Crear una fila con TODAS las columnas del df (incluye extras antiguas)
    nueva = {c: "" for c in df.columns}
    for k, v in fila.items():
        if k in nueva:
            nueva[k] = v

    df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)

    _write_outputs(df)

    return redirect("/gracias")

@app.route("/gracias", methods=["GET"])
def gracias():
    return render_template("gracias.html")

# =========================
# Descargas protegidas (sin Shell)
# =========================
@app.route("/admin/download/csv", methods=["GET"])
def download_csv():
    _check_admin_token()
    if not os.path.exists(CSV_PATH):
        abort(404)
    return send_file(CSV_PATH, as_attachment=True, download_name="diagnostico_procesos.csv")

@app.route("/admin/download/excel", methods=["GET"])
def download_excel():
    _check_admin_token()
    if not os.path.exists(XLSX_PATH):
        abort(404)
    return send_file(XLSX_PATH, as_attachment=True, download_name="diagnostico_procesos.xlsx")

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
