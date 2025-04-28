import streamlit as st import openai import tempfile import base64 from PIL import Image import fitz import io

Streamlit uygulaması

st.set_page_config(page_title="Seçkin Face Planner", page_icon=":guardsman:", layout="centered")

st.image("logo.png", use_column_width=True) st.title("Seçkin Face Planner") st.write("Fotoğraf üzerinden yüz analizi yapın ve PDF raporu oluşturun.")

uploaded_file = st.file_uploader("Bir yüz fotoğrafı yükleyin", type=["jpg", "jpeg", "png"]) patient_name = st.text_input("Hasta Adı ve Soyadı")

if uploaded_file and patient_name: if st.button("Analiz Yap ve PDF Üret"): with st.spinner("Analiz yapılıyor..."): try: # Görüntüyü yükle image = Image.open(uploaded_file) buf = io.BytesIO() image.save(buf, format="JPEG") byte_im = buf.getvalue()

# Örnek yüz ölçümleri
            measurements = {
                "İnterkantal Mesafe": "32mm",
                "Bizigomatik Mesafe": "128mm",
                "Gonial Açı": "120°"
            }

            # OpenAI API'yi kullanarak estetik önerileri al
            openai.api_key = st.secrets["OPENAI_API_KEY"]

            messages = [
                {"role": "system", "content": "Sen bir medikal estetik uzmanısın. Hastanın yüz ölçümlerine ve analizine göre dolgu ve botoks önerileri yap."},
                {"role": "user", "content": f"Hasta adı: {patient_name}\nÖlçümler: {measurements}\nBu hastaya dolgu ve botoks planı öner."}
            ]

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            suggestions = response.choices[0].message.content.strip()

            # PDF oluştur
            tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf_doc = fitz.open()
            page = pdf_doc.new_page()

            rect = fitz.Rect(50, 50, 300, 300)
            page.insert_image(rect, stream=byte_im)

            text = f"Hasta Adı: {patient_name}\n\n\n\n"
            for key, value in measurements.items():
                text += f"{key}: {value}\n"
            text += "\n\nEstetik Öneriler:\n" + suggestions

            page.insert_text((50, 350), text, fontsize=11, fontname="DejaVuSans")

            pdf_doc.save(tmp_pdf.name)

            with open(tmp_pdf.name, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')

            href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="{patient_name}_analiz.pdf">PDF Dosyasını İndir</a>'
            st.markdown(href, unsafe_allow_html=True)

            st.success("PDF başarıyla oluşturuldu!")

        except Exception as e:
            st.error(f"Hata oluştu: {e}")

else: st.info("Lütfen bir fotoğraf yükleyin ve hasta adını girin.")

