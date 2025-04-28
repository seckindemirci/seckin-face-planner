import streamlit as st
import cv2
import numpy as np
import openai
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import base64
from PIL import Image

# OpenAI API Anahtarını girin
openai.api_key = st.secrets["OPENAI_API_KEY"]

# PDF için Türkçe karakter uyumlu fontu yükle
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

# Fonksiyon: OpenAI Vision ile landmark analizi
def detect_landmarks_with_openai(image):
    _, img_encoded = cv2.imencode('.jpg', image)
    img_bytes = img_encoded.tobytes()

    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "Bu yüz fotoğrafında göz iç köşeleri, zigoma, gonion ve çene ucunun koordinatlarını JSON formatında ver."},
                {"type": "image", "image": img_bytes}
            ]}
        ],
        max_tokens=1000
    )
    landmarks = response['choices'][0]['message']['content']
    return landmarks

# Fonksiyon: İki nokta arası mesafe
def measure_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

# Fonksiyon: Açı ölçümü
def measure_angle(p1, p2, p3):
    a = np.array(p1) - np.array(p2)
    b = np.array(p3) - np.array(p2)
    cosine_angle = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

# Fonksiyon: PDF oluşturma
def create_pdf(patient_name, suggestions, measurements, doctor_notes, session_plan, logo_path, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    if logo_path:
        c.drawImage(logo_path, width/2 - 100, height - 150, width=200, preserveAspectRatio=True, mask='auto')

    c.setFont("DejaVuSans", 14)
    c.drawString(50, height-170, f"Hasta Adı: {patient_name}")
    c.drawString(50, height-190, f"Tarih: {datetime.now().strftime('%d/%m/%Y')}")

    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(50, height-220, "Ölçümler:")
    c.setFont("DejaVuSans", 12)
    y = height-240
    for key, value in measurements.items():
        c.drawString(70, y, f"{key}: {value}")
        y -= 20

    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(50, y-20, "Öneriler:")
    y -= 40
    c.setFont("DejaVuSans", 12)
    for suggestion in suggestions:
        c.drawString(70, y, f"- {suggestion}")
        y -= 20

    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(50, y-20, "Doktor Notları:")
    y -= 40
    c.setFont("DejaVuSans", 12)
    for line in doctor_notes.splitlines():
        c.drawString(70, y, f"{line}")
        y -= 20

    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(50, y-20, "Planlanan Seanslar:")
    y -= 40
    c.setFont("DejaVuSans", 12)
    for line in session_plan.splitlines():
        c.drawString(70, y, f"{line}")
        y -= 20

    c.save()

# Streamlit arayüzü
st.title("Seçkin Face Planner - Yüz Estetik Analiz")

uploaded_file = st.file_uploader("Fotoğraf yükleyin (jpg/png)", type=["jpg", "jpeg", "png"])
patient_name = st.text_input("Hasta Adı")
suggestions_input = st.text_area("Öneriler (virgül ile ayırınız)")
doctor_notes = st.text_area("Doktor Notları")
session_plan = st.text_area("Planlanan Seanslar")

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    st.image(image, channels="BGR")

    if st.button("Analiz Yap ve PDF Üret"):
        with st.spinner('Yüz landmarkları analiz ediliyor...'):
            try:
                landmarks_json = detect_landmarks_with_openai(image)
                landmarks = eval(landmarks_json)

                intercanthal_distance = measure_distance(landmarks['left_eye_inner'], landmarks['right_eye_inner'])
                bizygomatic_distance = measure_distance(landmarks['left_zygoma'], landmarks['right_zygoma'])
                gonial_angle = measure_angle(landmarks['left_gonion'], landmarks['chin'], landmarks['right_gonion'])

                measurements = {
                    "İnterkantal Mesafe": f"{intercanthal_distance:.2f} px",
                    "Bizigomatik Mesafe": f"{bizygomatic_distance:.2f} px",
                    "Gonial Açı": f"{gonial_angle:.2f} derece"
                }

                suggestions = [s.strip() for s in suggestions_input.split(",") if s.strip()]

                tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                create_pdf(patient_name, suggestions, measurements, doctor_notes, session_plan, "logo.png", tmp_pdf.name)

                with open(tmp_pdf.name, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="rapor.pdf">PDF çıktısını indir</a>'
                st.markdown(href, unsafe_allow_html=True)

                st.success("PDF başarıyla oluşturuldu!")

            except Exception as e:
                st.error(f"Hata oluştu: {e}")
