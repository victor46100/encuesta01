from flask import Flask, request, render_template, redirect
from datetime import datetime
import csv
import pandas as pd
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.csv")
XLSX_PATH = os.path.join(DATA_DIR, "diagnostico_procesos.xlsx")

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
    "idioma"
]

# ✅ NUEVO: ruta raíz para que Render y el navegador no vean 404
@app.route("/")
def home():
    return redirect("/diagnostico")

@app.route("/diagnostico")
def diagnostico():
    return render_template("diagnostico.html")

@app.route("/submit", methods=["POST"])
def submit():
    os.makedirs(DATA_DIR, exist_ok=True)

    data = request.form

    fila = [
        datetime.now().isoformat(),
        data.get("ambito"),
        data.get("descripcion"),
        ", ".join(data.getlist("impactos")),
        data.get("antiguedad"),
        data.get("horizonte"),
        data.get("rol"),
        data.get("participantes"),
        data.get("recomendacion"),
        data.get("nombre"),
        data.get("correo"),
        data.get("empresa"),
        data.get("cargo"),
        data.get("extra"),
        data.get("pais"),
        data.get("idioma")
    ]

    # === CSV ===
    existe_csv = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe_csv:
            writer.writerow(CAMPOS)
        writer.writerow(fila)

    # === EXCEL ===
    df_nuevo = pd.DataFrame([fila], columns=CAMPOS)
    if os.path.exists(XLSX_PATH):
        df_existente = pd.read_excel(XLSX_PATH)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_excel(XLSX_PATH, index=False)

    return redirect("/gracias")

@app.route("/gracias")
def gracias():
    return render_template("gracias.html")

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    # ✅ recomendado (local / Render): host 0.0.0.0 y PORT si existe
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
