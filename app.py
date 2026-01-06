import os
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request, redirect, abort, send_file

app = Flask(__name__)

# =========================
# Paths (robusto para Render)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.csv")
XLSX_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.xlsx")

# =========================
# Seguridad de descarga
# =========================
# En Render: Settings -> Environment -> agrega ADMIN_TOKEN
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hd_2026_iso_descarga_segura")

# =========================
# Campos esperados (de tu HTML)
# =========================
# Si algún campo no existe en el HTML, se guarda vacío sin romper el flujo.
CAMPOS = [
    "timestamp",
    "problema",
    "objetivo",
    "area",
    "urgencia",
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

# =========================
# Helpers
# =========================
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _check_admin_token():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(403)

def guardar_respuesta_desde_form(form):
    """
    Guarda en CSV y Excel. No falla si faltan campos.
    """
    ensure_data_dir()

    fila = {c: "" for c in CAMPOS}
    fila["timestamp"] = datetime.utcnow().isoformat(timespec="seconds")

    for c in CAMPOS:
        if c == "timestamp":
            continue
        fila[c] = (form.get(c) or "").strip()

    df_nuevo = pd.DataFrame([fila])

    # CSV append
    if os.path.exists(CSV_PATH):
        df_existente = pd.read_csv(CSV_PATH, dtype=str).fillna("")
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_csv(CSV_PATH, index=False, encoding="utf-8")
    df_final.to_excel(XLSX_PATH, index=False)

# =========================
# Rutas UI
# =========================
@app.route("/")
def home():
    return redirect("/diagnostico")

@app.route("/diagnostico", methods=["GET"])
def diagnostico():
    return render_template("diagnostico.html")

# ESTA ES LA CLAVE: tu HTML hace POST a /submit
@app.route("/submit", methods=["POST"])
def submit():
    guardar_respuesta_desde_form(request.form)
    return redirect("/gracias")

@app.route("/gracias", methods=["GET"])
def gracias():
    return render_template("gracias.html")

# =========================
# Descargas protegidas (URL)
# =========================
@app.route("/admin/download/csv", methods=["GET"])
def download_csv():
    _check_admin_token()
    if not os.path.exists(CSV_PATH):
        abort(404)
    return send_file(
        CSV_PATH,
        as_attachment=True,
        download_name="diagnostico_procesos.csv"
    )

@app.route("/admin/download/excel", methods=["GET"])
def download_excel():
    _check_admin_token()
    if not os.path.exists(XLSX_PATH):
        abort(404)
    return send_file(
        XLSX_PATH,
        as_attachment=True,
        download_name="diagnostico_procesos.xlsx"
    )

# =========================
# Run (Render / local)
# =========================
if __name__ == "__main__":
    ensure_data_dir()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
