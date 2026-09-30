"""python ui.py ile yalnız bu bilgisayarda açılan belge asistanı."""
import json
from pathlib import Path
import streamlit as st
from ragapp.ui_service import LocalService
from ragapp.ui_theme import CSS

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Notlarım · Yerel Asistan", page_icon="💬", layout="wide")

st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def get_service():
    return LocalService(ROOT)


def show_result(result):
    with st.chat_message("user"):
        st.text(result["question"])
    with st.chat_message("assistant", avatar="assistant"):
        if result["status"] == "answered":
            st.text(result["answer"])
        elif result["status"] in {"no_context", "model_abstained"}:
            st.info(result["answer"])
        else:
            st.warning(result["answer"])
        if result.get("cache_hit"):
            st.caption("Önbellekten getirildi")
        if result["retrieved"]:
            cited = {f"S{n}" for n in result["citations"]}
            with st.expander(f"Kaynaklar · {len(result['citations'])} kullanıldı"):
                st.caption(f"{result['total_seconds']:.2f} saniye · Ayrıntıları kaynak metninden kontrol edebilirsin.")
                for hit in result["retrieved"]:
                    chunk = hit["chunk"]
                    used = "Cevapta kullanıldı" if hit["id"] in cited else "Ek bağlam"
                    st.text(f"[{hit['id']}] {chunk['source']} · Sayfa {chunk['page']}")
                    st.caption(used)
                    st.text(chunk["content"])
                    st.divider()


def new_chat():
    st.session_state.history = []
    st.session_state.page = "Sohbet"


def open_documents():
    st.session_state.page = "Belgeler"


service = get_service()
st.session_state.setdefault("history", [])
with st.sidebar:
    st.markdown('<div class="sidebar-brand">Notlarım</div>', unsafe_allow_html=True)
    st.button("＋ Yeni sohbet", use_container_width=True, on_click=new_chat)
    page = st.radio("Çalışma alanı", ["Sohbet", "Belgeler"], key="page", label_visibility="collapsed")
    with st.expander("Ayarlar"):
        style = st.selectbox("Cevap biçimi", ["Kaynak cümleleri", "Model açıklaması"])
        st.caption("Kaynak cümleleri aynen aktarılır; model açıklaması yeniden yazılır.")
        st.caption("Her soru bağımsız yanıtlanır. Sohbet yalnız bu oturumda tutulur. İlk cevap daha uzun sürebilir.")
        st.caption("Qwen 2.5 · 7B / Yerel katalog")
    mode = "extractive" if style == "Kaynak cümleleri" else "generative"
    if st.session_state.history:
        st.download_button("Sohbeti indir", json.dumps(st.session_state.history, ensure_ascii=False, indent=2),
                           file_name="notlarim-sohbet.json", mime="application/json", use_container_width=True)

try:
    inventory = service.inventory()
except Exception as exc:
    st.error("Belge listesi okunamadı: " + str(exc))
    st.stop()

if page == "Belgeler":
    st.title("Bilgi kaynağın")
    st.write("Ders notlarını ekle; asistan cevaplarında bu belgeleri kullansın.")
    st.caption(f"{len(inventory)} belge · {sum(row['Parça'] for row in inventory)} metin parçası")
    if not inventory:
        st.info("Henüz belge yok. İlk notunu aşağıdan ekleyebilirsin.")
    if inventory:
        st.dataframe(inventory, hide_index=True, use_container_width=True)
    with st.form("upload_documents", clear_on_submit=True):
        st.subheader("Yeni bir kaynak ekle")
        uploaded = st.file_uploader("Yeni belge ekle", type=["txt", "md", "pdf"],
                                    accept_multiple_files=True, max_upload_size=20)
        st.caption("TXT, Markdown veya metin içeren PDF · En fazla 20 MB / dosya. Taranmış PDF için OCR desteği yok.")
        add = st.form_submit_button("Belgeleri ekle", type="primary")
    if add:
        if not uploaded:
            st.warning("Önce bir belge seç.")
        else:
            try:
                with st.spinner("Belgeler okunuyor ve aramaya hazırlanıyor…"):
                    summary = service.ingest([(f.name, f.getvalue()) for f in uploaded])
                st.session_state["ingest_notice"] = f"{summary['updated_documents']} belge işlendi."
                st.rerun()
            except Exception as exc:
                st.error("Belge eklenemedi: " + str(exc))
    if "ingest_notice" in st.session_state:
        st.success(st.session_state.pop("ingest_notice"))
    if st.button("Klasördeki belgeleri yeniden tara"):
        try:
            with st.spinner("Yeni ve değişmiş belgeler işleniyor…"):
                summary = service.ingest()
            st.session_state["ingest_notice"] = (
                f"{summary['updated_documents']} güncellendi, {summary['unchanged_documents']} aynı kaldı.")
            st.rerun()
        except Exception as exc:
            st.error("İndeks güncellenemedi: " + str(exc))
    st.caption("Aynı adlı yüklemeler mevcut dosyaları değiştirmez. Klasörden silinen belgeler otomatik olarak indeksten silinmez.")
else:
    if not st.session_state.history:
        st.markdown('<div class="empty-chat"><h1>Bugün ne öğrenmek istersin?</h1></div>', unsafe_allow_html=True)
        if not inventory:
            st.info("Başlamak için bir belge ekle.")
            st.button("Belgelerini ekle →", on_click=open_documents)
    for result in st.session_state.history:
        show_result(result)
    if st.session_state.history:
        question = st.chat_input("Notlarına sor…", max_chars=2000, disabled=not inventory, key="question")
    else:
        with st.container():
            question = st.chat_input("Notlarına sor…", max_chars=2000, disabled=not inventory, key="question")
    if question and question.strip():
        with st.chat_message("user"):
            st.text(question.strip())
        try:
            with st.chat_message("assistant", avatar="assistant"):
                with st.spinner("Yanıt hazırlanıyor…"):
                    result = service.ask(question.strip(), mode)
            st.session_state.history.append(result)
            st.rerun()
        except Exception as exc:
            st.error("Cevap oluşturulamadı: " + str(exc))
            st.caption("Yerel katalog veya model hazırlığı eksikse kurulum rehberini kontrol et.")
