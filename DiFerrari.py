# ==========================================
# DIFERRARI PRO MAX - SISTEMA COMPLETO
# ==========================================

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from pymongo import MongoClient
import qrcode
import io
import pandas as pd

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="DiFerrari PRO MAX", layout="wide")

MONGO_URI = "mongodb+srv://lsouzamalheiros_db_user:Malheiros76@cluster0.rch6yzm.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["diferrari"]
colecao = db["etiquetas"]

# ==========================================
# SABORES FIXOS
# ==========================================
SABORES = [
    "Brigadeiro",
    "Beijinho",
    "Ninho",
    "Maracujá",
    "Prestígio",
    "Limão",
    "Morango",
    "Trufa"
]

# ==========================================
# ETIQUETA
# ==========================================
def criar_etiqueta(sabor, fab_str, val_str, lote):

    largura, altura = 384, 384
    img = Image.new("L", (largura, altura), 255)
    draw = ImageDraw.Draw(img)

    cor = 0

    draw.ellipse((10, 10, largura-10, altura-10), outline=cor, width=6)
    draw.line((30, 150, largura-30, 150), fill=cor, width=4)

    try:
        titulo = ImageFont.truetype("arial.ttf", 42)
        texto = ImageFont.truetype("arial.ttf", 22)
    except:
        titulo = ImageFont.load_default()
        texto = ImageFont.load_default()

    draw.text((60, 80), "DiFerrari", font=titulo, fill=cor)
    draw.text((60, 170), f"fab: {fab_str}", font=texto, fill=cor)
    draw.text((60, 200), f"val: {val_str}", font=texto, fill=cor)
    draw.text((60, 230), sabor, font=texto, fill=cor)

    qr = qrcode.make(lote).resize((80, 80))
    img.paste(qr, (280, 280))

    return img.convert("1")

# ==========================================
# LOTE
# ==========================================
def gerar_lote(sabor, quantidade):

    fab = datetime.now()
    val = fab + timedelta(days=7)

    fab_str = fab.strftime("%d/%m/%Y")
    val_str = val.strftime("%d/%m/%Y")

    lote = f"{sabor}-{fab.strftime('%Y%m%d%H%M%S')}"

    largura = 384
    altura_total = 384 * quantidade

    img_final = Image.new("L", (largura, altura_total), 255)

    y = 0
    for _ in range(quantidade):
        etiqueta = criar_etiqueta(sabor, fab_str, val_str, lote)
        img_final.paste(etiqueta, (0, y))
        y += 384

    img_final = img_final.convert("1")

    colecao.insert_one({
        "sabor": sabor,
        "quantidade": quantidade,
        "fabricacao": fab_str,
        "validade": val_str,
        "lote": lote,
        "criado_em": datetime.now()
    })

    buffer = io.BytesIO()
    img_final.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer, lote

# ==========================================
# INTERFACE
# ==========================================
st.title("🍫 DiFerrari PRO MAX")

menu = st.sidebar.selectbox("Menu", ["Produção", "Histórico", "Dashboard"])

# ==========================================
# PRODUÇÃO
# ==========================================
if menu == "Produção":

    st.subheader("Produção Rápida")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Sabores rápidos")
        sabor = None
        for s in SABORES:
            if st.button(s):
                sabor = s

    with col2:
        sabor_manual = st.text_input("Ou digite outro sabor")
        quantidade = st.number_input("Quantidade", 1, 200, 20)

    if sabor_manual:
        sabor = sabor_manual

    if st.button("🚀 GERAR ETIQUETAS"):

        if not sabor:
            st.warning("Escolha ou digite um sabor")
        else:
            imagem, lote = gerar_lote(sabor, quantidade)

            st.success(f"Lote: {lote}")

            st.image(imagem)

            st.download_button(
                "📥 Baixar para impressão",
                data=imagem,
                file_name="etiquetas.png",
                mime="image/png"
            )

            st.info("Abra no RawBT e imprima")

# ==========================================
# HISTÓRICO
# ==========================================
elif menu == "Histórico":

    st.subheader("Histórico")

    dados = list(colecao.find().sort("criado_em", -1).limit(50))

    for d in dados:
        st.write(
            f"{d.get('sabor')} | Qtd: {d.get('quantidade',1)} | "
            f"Fab: {d.get('fabricacao')} | Lote: {d.get('lote')}"
        )

# ==========================================
# DASHBOARD
# ==========================================
elif menu == "Dashboard":

    st.subheader("Produção diária")

    dados = list(colecao.find())

    if dados:

        df = pd.DataFrame(dados)
        df['data'] = pd.to_datetime(df['criado_em']).dt.date

        resumo = df.groupby('data')['quantidade'].sum()

        st.line_chart(resumo)

        st.metric("Produção hoje", int(resumo.iloc[-1]))
    else:
        st.info("Sem dados ainda")
