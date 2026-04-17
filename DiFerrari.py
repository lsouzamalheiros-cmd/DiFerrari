# ==========================================
# DIFERRARI FINAL - ESTÁVEL E PROFISSIONAL
# ==========================================

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from pymongo import MongoClient
import qrcode
import io

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="DiFerrari", layout="centered")

MONGO_URI = "mongodb+srv://lsouzamalheiros_db_user:Malheiros76@cluster0.rch6yzm.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["diferrari"]
colecao = db["etiquetas"]

# ==========================================
# SABORES
# ==========================================
SABORES = ["Brigadeiro", "Beijinho", "Ninho", "Morango", "Maracujá"]

# ==========================================
# ETIQUETA 50x30 (FONTE GRANDE)
# ==========================================
def criar_etiqueta(sabor, fab_str, val_str, lote):

    largura, altura = 400, 240

    img = Image.new("L", (largura, altura), 255)
    draw = ImageDraw.Draw(img)

    cor = 0

    # borda
    draw.rounded_rectangle((5, 5, largura-5, altura-5), outline=cor, width=3, radius=20)

    # linha
    draw.line((10, 100, largura-10, 100), fill=cor, width=3)

    try:
        titulo = ImageFont.truetype("arial.ttf", 40)
        texto = ImageFont.truetype("arial.ttf", 24)
    except:
        titulo = ImageFont.load_default()
        texto = ImageFont.load_default()

    # título
    draw.text((10, 20), "DiFerrari", font=titulo, fill=cor)

    # dados
    draw.text((10, 115), f"Fab: {fab_str}", font=texto, fill=cor)
    draw.text((10, 145), f"Val: {val_str}", font=texto, fill=cor)
    draw.text((10, 175), sabor[:20], font=texto, fill=cor)

    # QR pequeno
    qr = qrcode.make(lote).resize((70, 70))
    img.paste(qr, (320, 130))

    return img.convert("1")

# ==========================================
# LOTE SEGURO (ANTI TRAVAMENTO)
# ==========================================
def gerar_lote_seguro(sabor, quantidade):

    MAX = 10  # máximo por imagem
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

    # salva no banco
    colecao.insert_one({
        "sabor": sabor,
        "quantidade": quantidade,
        "fabricacao": fab_str,
        "validade": val_str,
        "lote": lote,
        "criado_em": datetime.now()
    })

    return imagens

# ==========================================
# INTERFACE
# ==========================================
st.title("🍫 DiFerrari Etiquetas")

menu = st.sidebar.selectbox("Menu", ["Produção", "Histórico"])

# ==========================================
# PRODUÇÃO
# ==========================================
if menu == "Produção":

    st.subheader("Gerar Etiquetas")

    col1, col2 = st.columns(2)

    sabor = None

    with col1:
        st.write("Sabores rápidos")
        for s in SABORES:
            if st.button(s):
                sabor = s

    with col2:
        sabor_manual = st.text_input("Outro sabor")
        quantidade = st.number_input("Quantidade", 1, 100, 20)

    if sabor_manual:
        sabor = sabor_manual

    if st.button("🚀 GERAR ETIQUETAS"):

        if not sabor:
            st.warning("Escolha um sabor")
        else:
            imagens = gerar_lote_seguro(sabor, quantidade)

            st.success("Etiquetas prontas!")

            for i, img in enumerate(imagens):
                st.image(img, caption=f"Parte {i+1}")

                st.download_button(
                    f"📥 Baixar parte {i+1}",
                    data=img,
                    file_name=f"etiquetas_{i+1}.png",
                    mime="image/png"
                )

            st.info("Abra cada imagem no RawBT e imprima")

# ==========================================
# HISTÓRICO
# ==========================================
elif menu == "Histórico":

    st.subheader("Histórico")

    dados = list(colecao.find().sort("criado_em", -1).limit(20))

    for d in dados:
        st.write(
            f"{d.get('sabor','-')} | "
            f"Qtd: {d.get('quantidade',1)} | "
            f"Fab: {d.get('fabricacao','-')} | "
            f"Val: {d.get('validade','-')}"
        )
