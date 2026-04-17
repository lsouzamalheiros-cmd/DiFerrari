# ==========================================
# SISTEMA DIFERRARI - ETIQUETAS COMPLETO
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
st.set_page_config(page_title="DiFerrari Etiquetas", layout="centered")

MONGO_URI = "mongodb+srv://lsouzamalheiros_db_user:Malheiros76@cluster0.rch6yzm.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["diferrari"]
colecao = db["etiquetas"]

# ==========================================
# GERAR ETIQUETA
# ==========================================
def gerar_etiqueta(sabor):

    largura, altura = 384, 384

    img = Image.new("L", (largura, altura), 255)
    draw = ImageDraw.Draw(img)

    cor = 0

    # círculo
    draw.ellipse((10, 10, largura-10, altura-10), outline=cor, width=6)

    # linha
    draw.line((30, 150, largura-30, 150), fill=cor, width=4)

    # fontes
    try:
        titulo = ImageFont.truetype("arial.ttf", 42)
        texto = ImageFont.truetype("arial.ttf", 22)
    except:
        titulo = ImageFont.load_default()
        texto = ImageFont.load_default()

    # título (marca)
    draw.text((60, 80), "DiFerrari", font=titulo, fill=cor)

    # datas
    fab = datetime.now()
    val = fab + timedelta(days=7)

    fab_str = fab.strftime("%d/%m/%Y")
    val_str = val.strftime("%d/%m/%Y")

    # textos
    draw.text((60, 170), f"fab: {fab_str}", font=texto, fill=cor)
    draw.text((60, 200), f"val: {val_str}", font=texto, fill=cor)
    draw.text((60, 230), sabor, font=texto, fill=cor)

    # QR CODE (lote)
    lote = f"{sabor}-{fab.strftime('%Y%m%d%H%M%S')}"
    qr = qrcode.make(lote)
    qr = qr.resize((80, 80))
    img.paste(qr, (280, 280))

    img = img.convert("1")

    # salvar em memória
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    # salvar no banco
    colecao.insert_one({
        "sabor": sabor,
        "fabricacao": fab_str,
        "validade": val_str,
        "lote": lote,
        "criado_em": datetime.now()
    })

    return buffer.getvalue()

# ==========================================
# INTERFACE
# ==========================================
st.title("🍫 Sistema DiFerrari")

menu = st.sidebar.selectbox("Menu", ["Gerar Etiqueta", "Histórico"])

# ==========================================
# GERAR
# ==========================================
if menu == "Gerar Etiqueta":

    st.subheader("Nova Etiqueta")

    sabor = st.text_input("Sabor do bombom")

    if st.button("🖨️ Gerar Etiqueta"):

        if sabor.strip() == "":
            st.warning("Digite o sabor")
        else:
            imagem = gerar_etiqueta(sabor)

            st.success("Etiqueta gerada!")

            st.image(imagem, caption="Pré-visualização")

            st.download_button(
                label="📥 Baixar etiqueta",
                data=imagem,
                file_name="etiqueta.png",
                mime="image/png"
            )

            st.info("Abra o arquivo no app RawBT para imprimir via Bluetooth")

# ==========================================
# HISTÓRICO
# ==========================================
elif menu == "Histórico":

    st.subheader("Últimas etiquetas")

    dados = list(colecao.find().sort("criado_em", -1).limit(20))

    for d in dados:
        st.write(f"🍫 {d['sabor']} | Fab: {d['fabricacao']} | Val: {d['validade']}")
