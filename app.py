import os
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request, redirect, abort, send_file

app = Flask(__name__)

# =========================
# Config
# =========================
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.csv")
XLSX_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.xlsx")

# Token de descarga (NO lo hardcodees en producción si puedes evitarlo)
# En Render: Settings/Environment -> agrega ADMIN_TOKEN
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hd_2026_iso_descarga_segura")

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
# Rutas UI
# =========================
@app.route("/")
def home():
    return redirect("/diagnostico")

@app.route("/diagnostico", methods=["GET", "POST"])
def diagnostico():
    if request.method == "GET":
        return render_template("diagnostico.html")

    # POST: guardar respuesta
    os.makedirs(DATA_DIR, exist_ok=True)

    fila = {c: "" for c in CAMPOS}
    fila["timestamp"] = datetime.utcnow().isoformat(timespec="seconds")

    # Tomar del form (si un campo no existe en el HTML, queda vacío)
    for c in CAMPOS:
        if c == "timestamp":
            continue
        fila[c] = (request.form.get(c) or "").strip()

    df_nuevo = pd.DataFrame([fila])

    # Guardar/append CSV
    if os.path.exists(CSV_PATH):
        df_existente = pd.read_csv(CSV_PATH, dtype=str).fillna("")
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_csv(CSV_PATH, index=False, encoding="utf-8")
    df_final.to_excel(XLSX_PATH, index=False)

    return redirect("/gracias")

@app.route("/gracias")
def gracias():
    return render_template("gracias.html")


# =========================
# Descargas protegidas
# =========================
def _check_admin_token():
    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        abort(403)

@app.route("/admin/download/csv")
def download_csv():
    _check_admin_token()
    if not os.path.exists(CSV_PATH):
        abort(404)
    return send_file(CSV_PATH, as_attachment=True, download_name="diagnostico_procesos.csv")

@app.route("/admin/download/excel")
def download_excel():
    _check_admin_token()
    if not os.path.exists(XLSX_PATH):
        abort(404)
    return send_file(XLSX_PATH, as_attachment=True, download_name="diagnostico_procesos.xlsx")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True)
