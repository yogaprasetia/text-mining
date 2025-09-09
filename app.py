import streamlit as st
import pymupdf as fitz
import pandas as pd
import re

# --- KAMUS KATA KUNCI UNTUK ANALISIS ---
POJK51_KEYWORDS = {
    "Aspek Ekonomi": ["kinerja keuangan", "pertumbuhan ekonomi", "dampak ekonomi", "kontribusi pada negara"],
    "Aspek Sosial": ["tenaga kerja", "hak asasi manusia", "keselamatan dan kesehatan kerja", "pengembangan masyarakat"],
    "Aspek Lingkungan": ["emisi gas rumah kaca", "pengelolaan limbah", "penggunaan energi", "penggunaan air", "konservasi keanekaragaman hayati"],
}

GRI_KEYWORDS = {
    "Economic": ["economic performance", "market presence", "indirect economic impacts", "procurement practices"],
    "Environmental": ["materials", "energy", "water", "biodiversity", "emissions", "effluents and waste", "environmental compliance"],
    "Social": ["employment", "labor/management relations", "occupational health and safety", "training and education", "diversity and equal opportunity", "non-discrimination", "human rights assessment"],
}

SASB_KEYWORDS = {
    "Environment": ["greenhouse gas emissions", "air quality", "water & wastewater management", "waste & hazardous materials management"],
    "Social Capital": ["customer welfare", "data security", "access & affordability", "product safety"],
    "Human Capital": ["labor practices", "employee health and safety", "employee engagement, diversity & inclusion"],
    "Business Model & Innovation": ["supply chain management", "business ethics", "product design & lifecycle management"],
    "Leadership & Governance": ["risk management", "corporate governance", "management of the legal & regulatory environment"],
}

# --- FUNGSI BANTU ---
def get_year_from_filename(filename):
    """Mendeteksi 4 digit tahun dari nama file menggunakan regex."""
    match = re.search(r'\b(20\d{2})\b', filename)
    if match:
        return int(match.group(1))
    return None

def ekstrak_teks_dari_pdf(file_bytes):
    """Fungsi untuk membuka file PDF dari byte-stream dan mengekstrak teksnya."""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as dokumen:
            return "\n".join([halaman.get_text("text") for halaman in dokumen])
    except Exception as e:
        st.error(f"Gagal memproses salah satu PDF: {e}")
        return ""

# --- TAMPILAN APLIKASI WEB STREAMLIT ---

st.title("📊 Dashboard Analisis Laporan Keberlanjutan")

# --- LANGKAH 1: UPLOAD & ANALISIS ---
st.header("Langkah 1: Unggah & Analisis Laporan")

st.write("Unggah satu atau beberapa laporan (PDF) dari tahun yang berbeda. Pastikan nama file mengandung tahun (contoh: 'Laporan 2023.pdf').")
uploaded_files = st.file_uploader("Pilih file PDF...", type="pdf", accept_multiple_files=True)

if uploaded_files:
    standar_analisis = st.selectbox(
        "Pilih Standar untuk Analisis:",
        ("POJK 51", "GRI", "SASB")
    )

    if st.button("🚀 Proses & Analisis Laporan"):
        yearly_results = []
        all_text = ""
        keywords_map = {"POJK 51": POJK51_KEYWORDS, "GRI": GRI_KEYWORDS, "SASB": SASB_KEYWORDS}
        keywords = keywords_map[standar_analisis]

        with st.spinner('Mengekstrak teks dan menganalisis laporan per tahun...'):
            for file in uploaded_files:
                year = get_year_from_filename(file.name)
                if not year:
                    st.warning(f"Tidak dapat menemukan tahun pada nama file: '{file.name}'. File ini dilewati.")
                    continue

                teks_laporan = ekstrak_teks_dari_pdf(file.getvalue())
                if not teks_laporan:
                    continue
                
                all_text += f"--- START OF {file.name} ---"
                all_text += teks_laporan
                all_text += f"\n--- END OF {file.name} ---"

                total_score = 0
                max_score = 0
                for category, kws in keywords.items():
                    for kw in kws:
                        max_score += 2
                        if kw.lower() in teks_laporan.lower():
                            total_score += 2
                
                disclosure_index = (total_score / max_score) * 100 if max_score > 0 else 0
                yearly_results.append({
                    "Tahun": year,
                    "Nama File": file.name,
                    "Indeks Disclosure (%)": disclosure_index,
                    "Total Skor": total_score,
                    "Skor Maksimum": max_score
                })

        if yearly_results:
            st.success("✅ Analisis Selesai!")
            st.session_state['yearly_results'] = yearly_results
            st.session_state['teks_lengkap'] = all_text
        else:
            st.error("Tidak ada laporan yang berhasil dianalisis. Pastikan nama file mengandung tahun.")

# --- LANGKAH 2: DASHBOARD INTERAKTIF ---
if 'yearly_results' in st.session_state:
    st.header("Langkah 2: Dashboard Hasil Analisis")
    results = st.session_state['yearly_results']
    
    df = pd.DataFrame(results).sort_values(by="Tahun").set_index("Tahun")

    st.subheader("Tren Indeks Disclosure dari Tahun ke Tahun")
    st.line_chart(df[["Indeks Disclosure (%)"]])

    st.subheader("Detail Hasil Analisis")
    st.dataframe(df)

# --- Tampilkan Hasil Ekstraksi Teks ---
if 'teks_lengkap' in st.session_state:
    with st.expander("Tampilkan Hasil Ekstraksi Teks Lengkap"):
        st.subheader("Teks Lengkap dari Semua Laporan")
        st.text_area("Teks", st.session_state['teks_lengkap'], height=400)
