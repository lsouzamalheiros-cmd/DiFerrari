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

    largura, altura = 400, 240  # 50mm x 30mm

    img = Image.new("L", (largura, altura), 255)
    draw = ImageDraw.Draw(img)

    cor = 0

    # borda
    draw.rounded_rectangle((5, 5, largura-5, altura-5), outline=cor, width=3, radius=20)

    # linha
    draw.line((10, 100, largura-10, 100), fill=cor, width=3)

    # fontes GRANDES
    try:
        titulo = ImageFont.truetype("arial.ttf", 42)   # antes ~28
        texto = ImageFont.truetype("arial.ttf", 26)    # antes ~18
    except:
        titulo = ImageFont.load_default()
        texto = ImageFont.load_default()

    # título
    draw.text((10, 20), "DiFerrari", font=titulo, fill=cor)

    # datas (mais espaçadas)
    draw.text((10, 115), f"Fab: {fab_str}", font=texto, fill=cor)
    draw.text((10, 145), f"Val: {val_str}", font=texto, fill=cor)

    # sabor (limitado pra não estourar)
    draw.text((10, 175), sabor[:20], font=texto, fill=cor)

    # QR menor pra caber
    qr = qrcode.make(lote)
    qr = qr.resize((70, 70))
    img.paste(qr, (320, 130))

    return img.convert("1")
    
# ==========================================
# LOTE
# ==========================================
def gerar_lote_seguro(sabor, quantidade):

    MAX = 10  # limite por imagem
    imagens = []

    fab = datetime.now()
    val = fab + timedelta(days=7)

    fab_str = fab.strftime("%d/%m/%Y")
    val_str = val.strftime("%d/%m/%Y")

    lote = f"{sabor}-{fab.strftime('%Y%m%d%H%M%S')}"

    while quantidade > 0:

        qtd_atual = min(MAX, quantidade)

        largura = 400
        altura_unit = 240
        altura_total = altura_unit * qtd_atual

        img_final = Image.new("L", (largura, altura_total), 255)

        y = 0
        for _ in range(qtd_atual):
            etiqueta = criar_etiqueta(sabor, fab_str, val_str, lote)
            img_final.paste(etiqueta, (0, y))
            y += altura_unit

        buffer = io.BytesIO()
        img_final.save(buffer, format="PNG")
        buffer.seek(0)

        imagens.append(buffer.getvalue())

        quantidade -= qtd_atual

    return imagens
    
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
