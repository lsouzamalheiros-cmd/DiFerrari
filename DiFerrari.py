# ==========================================
# DIFERRARI - IMPRESSÃO AUTOMÁTICA EM LOTE
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
st.set_page_config(page_title="DiFerrari PRO", layout="centered")

MONGO_URI = "mongodb+srv://lsouzamalheiros_db_user:Malheiros76@cluster0.rch6yzm.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["diferrari"]
colecao = db["etiquetas"]

# ==========================================
# GERAR ETIQUETA ÚNICA
# ==========================================
def criar_etiqueta_unitaria(sabor, fab_str, val_str, lote):

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

    # marca
    draw.text((60, 80), "DiFerrari", font=titulo, fill=cor)

    # textos
    draw.text((60, 170), f"fab: {fab_str}", font=texto, fill=cor)
    draw.text((60, 200), f"val: {val_str}", font=texto, fill=cor)
    draw.text((60, 230), sabor, font=texto, fill=cor)

    # QR
    qr = qrcode.make(lote)
    qr = qr.resize((80, 80))
    img.paste(qr, (280, 280))

    return img.convert("1")

# ==========================================
# GERAR LOTE EM UMA IMAGEM
# ==========================================
def gerar_lote(sabor, quantidade):

    fab = datetime.now()
    val = fab + timedelta(days=7)

    fab_str = fab.strftime("%d/%m/%Y")
    val_str = val.strftime("%d/%m/%Y")

    lote = f"{sabor}-{fab.strftime('%Y%m%d%H%M%S')}"

    largura = 384
    altura_unit = 384

    altura_total = altura_unit * quantidade

    img_final = Image.new("L", (largura, altura_total), 255)

    y_offset = 0

    for i in range(quantidade):
        etiqueta = criar_etiqueta_unitaria(sabor, fab_str, val_str, lote)
        img_final.paste(etiqueta, (0, y_offset))
        y_offset += altura_unit

    img_final = img_final.convert("1")

    # salvar no banco
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

    return buffer

# ==========================================
# INTERFACE
# ==========================================
st.title("🍫 DiFerrari PRO - Impressão Rápida")

sabor = st.text_input("Sabor")
quantidade = st.number_input("Quantidade", 1, 200, 20)

if st.button("🚀 GERAR E IMPRIMIR"):

    if sabor.strip() == "":
        st.warning("Digite o sabor")
    else:
        imagem = gerar_lote(sabor, quantidade)

        st.success("Imagem pronta!")

        st.image(imagem, caption="Visualização")

        st.download_button(
            label="📥 BAIXAR PARA IMPRIMIR",
            data=imagem,
            file_name="lote_etiquetas.png",
            mime="image/png"
        )

        st.info("Abra no RawBT e clique em imprimir — sairá tudo em sequência!")

# ==========================================
# HISTÓRICO
# ==========================================
st.subheader("Histórico")

dados = list(colecao.find().sort("criado_em", -1).limit(10))

for d in dados:
    st.write(f"🍫 {d['sabor']} | Qtd: {d['quantidade']} | Fab: {d['fabricacao']}")
