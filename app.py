import streamlit as st
from PIL import Image
import pandas as pd
import os
import cv2

# --- 1. INTEGRASI REPO KLASIFIKASI (STONE) ---
# Kita bungkus dengan try-except agar website tidak crash jika ada file yang kurang
try:
    # Sesuai screenshotmu, fungsi 'process' ada di dalam stone/api.py
    from stone.api import process 
    AI_AVAILABLE = True
except ImportError as e:
    st.error(f"Error Import: {e}")
    AI_AVAILABLE = False

# --- 2. FUNGSI PEMBANTU ---
def analyze_image(image_path):
    """Mengirim foto ke 'Dapur' stone untuk dianalisis"""
    if not AI_AVAILABLE:
        return None, "AI Tidak Terinstall"
    
    try:
        # Ini memanggil fungsi 'process' yang kamu kirim di screenshot
        # return_report_image=False supaya lebih cepat
        result = process(image_path, return_report_image=False)
        
        # Cek apakah wajah terdeteksi
        if len(result['faces']) > 0:
            # Ambil label warna kulit dari wajah pertama yang ditemukan
            tone_label = result['faces'][0]['tone_label']
            return tone_label, "Sukses"
        else:
            return None, "Wajah tidak terdeteksi. Coba foto lebih jelas."
    except Exception as e:
        return None, f"Error Analisis: {str(e)}"

# --- 3. SETUP HALAMAN ---
st.set_page_config(page_title="Skin Sleuth Final", layout="wide", page_icon="💄")

st.title("🌸 Skin Sleuth: Rekomendasi Cerdas")
st.markdown("""
Sistem ini menggabungkan **Computer Vision** untuk mendeteksi warna kulit 
dan **Sistem Rekomendasi** untuk mencarikan produk yang tepat.
""")

# Load Database
try:
    df_makeup = pd.read_csv("dataset_makeup.csv")
    df_skin = pd.read_csv("dataset_skincare.csv")
    st.sidebar.success("✅ Database Terhubung")
except:
    st.sidebar.error("❌ Database CSV tidak ditemukan!")
    st.stop()

# --- 4. USER INTERFACE (UI) ---
col_kiri, col_kanan = st.columns([1, 1.5])

with col_kiri:
    st.header("1. Upload Foto")
    uploaded_file = st.file_uploader("Selfie tanpa makeup (Cahaya terang)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Kamu", width=300)
        
        # Simpan sementara untuk dibaca oleh library stone
        with open("temp.jpg", "wb") as f:
            f.write(uploaded_file.getbuffer())

with col_kanan:
    st.header("2. Profil Kulit")
    
    # Input Manual untuk Skincare (Karena kamera tidak bisa lihat minyak/jerawat)
    user_skin_type = st.selectbox("Tipe Kulit:", 
                                  ["Oily", "Dry", "Combination", "Normal", "Sensitive"])
    
    user_concern = st.selectbox("Masalah Utama:", 
                                ["Acne", "Aging", "Dullness", "Sensitivity", "General Care"])

    st.write("---")
    
    # TOMBOL AJAIB
    if st.button("🔍 ANALISIS & CARI PRODUK"):
        if uploaded_file is None:
            st.warning("Tolong upload foto dulu ya!")
        else:
            with st.spinner("Sedang memindai wajah..."):
                # A. JALANKAN AI
                detected_tone, status = analyze_image("temp.jpg")
                
                if detected_tone:
                    st.success(f"✅ Wajah Terdeteksi! Kode Warna: **{detected_tone}**")
                    
                    # --- LOGIKA MAPPING WARNA ---
                    # Karena output AI berupa kode (misal 'Fair', 'Light'), kita sesuaikan logika filternya
                    # Sederhananya: Kita cari produk yang 'skin tone'-nya mirip dengan hasil AI
                    # Atau untuk demo, kita pakai logika 'contains'
                    
                    st.divider()
                    
                    # B. TAMPILKAN MAKEUP (Filter by Skin Tone)
                    st.subheader(f"💄 Rekomendasi Makeup (Tone: {detected_tone})")
                    
                    # Filter: Cari di kolom 'skin tone' yang mengandung kata dari hasil AI
                    # Kita pakai case=False supaya huruf besar/kecil tidak masalah
                    # Catatan: Jika hasil AI misal "II" tapi di CSV "Light", ini perlu penyesuaian manual nanti.
                    # Untuk sekarang kita filter tipe kulit dulu untuk makeup
                    
                    makeup_results = df_makeup[
                        (df_makeup['skin type'].str.contains(user_skin_type, case=False, na=False))
                    ]
                    
                    if not makeup_results.empty:
                        st.dataframe(makeup_results[['brand', 'name', 'price', 'skin tone']].head(5))
                    else:
                        st.info("Belum ada data makeup yang pas, coba ganti filter.")

                    # C. TAMPILKAN SKINCARE (Filter by Skin Type & Concern)
                    st.subheader(f"🧴 Rekomendasi Skincare ({user_skin_type})")
                    
                    # Filter Skincare
                    skincare_results = df_skin[
                        (df_skin['skin type'].str.contains(user_skin_type, case=False, na=False)) &
                        (df_skin['concern'].str.contains(user_concern, case=False, na=False)) 
                    ]
                    
                    if not skincare_results.empty:
                        st.dataframe(skincare_results[['brand', 'name', 'price', 'concern']].head(5))
                    else:
                        st.warning(f"Tidak ditemukan produk khusus {user_concern} untuk kulit {user_skin_type}. Menampilkan rekomendasi umum:")
                        st.dataframe(df_skin[df_skin['skin type'].str.contains(user_skin_type, case=False)].head(3))

                else:
                    st.error(f"Gagal mendeteksi: {status}")