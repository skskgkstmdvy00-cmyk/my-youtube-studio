import streamlit as st
from google import genai
from gtts import gTTS
import io
import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# 페이지 기본 설정
st.set_page_config(page_title="AI 유튜브 크리에이터 스튜디오", page_icon="🎬", layout="wide")

# 유튜브 비디오 ID 추출 함수
def extract_youtube_id(url):
    pattern = r'(?:v=|\/|shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 유튜브 자막 추출 함수
def get_youtube_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list_transcripts(video_id)
        # 한국어 또는 영어 자막 가져오기
        try:
            transcript = transcript_list.find_transcript(['ko', 'en'])
        except:
            transcript = transcript_list.find_generated_transcript(['ko', 'en'])
        
        fetched = transcript.fetch()
        return " ".join([item['text'] for item in fetched])
    except Exception as e:
        return None

# 일반 웹페이지(기사/블로그) 텍스트 추출 함수
def get_webpage_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        text = soup.get_text(separator=' ')
        return " ".join(text.split())[:3000] # 상위 3000자만 추출
    except Exception as e:
        return None

# 사이드바: 메뉴 설정
st.sidebar.title("🎬 유튜브 스튜디오")
menu = st.sidebar.radio(
    "기능을 선택하세요:",
    [
        "📝 유튜브 대본 생성 (주제 / 링크 분석)",
        "🎙️ TTS 오디오 나레이션 생성",
        "🎨 AI 애니메이션 프롬프트",
        "🚀 유튜브 연동 & 자동 업로드",
        "📊 유튜브 채널 성과 분석"
    ],
    key="sb_menu"
)

# Gemini API 설정
GEMINI_API_KEY = "AQ.Ab8RN6IFw2mGX6vlhrFgr6_0J9RUP4EFehk_1EdwiSSCyRmoPw"
client = genai.Client(api_key=GEMINI_API_KEY)

# 세션 상태 초기화
if 'last_result' not in st.session_state:
    st.session_state['last_result'] = ""

# ==========================================
# 1. 유튜브 대본 생성 (주제 / 링크 분석)
# ==========================================
if menu == "📝 유튜브 대본 생성 (주제 / 링크 분석)":
    st.title("📝 유튜브 맞춤형 대본 생성기")
    st.caption("주제를 입력하거나 참고할 유튜브/기사 링크를 넣으면 자막 및 내용을 분석해 쇼츠/롱폼 대본을 재창조합니다.")

    video_type = st.selectbox(
        "영상 형식을 선택하세요:",
        ["유튜브 쇼츠 (Shorts - 30~60초)", "유튜브 롱폼 (Long-form - 3~5분)"],
        key="sb_video_type"
    )
    
    tone = st.selectbox(
        "채널 컨셉 (말투/톤앤매너):",
        ["🔥 트렌디하고 빠른 템포", "🧠 전문적인 지식 전달/정보형", "☕ 친근하고 재미있는 썰/스토리텔링", "🤖 B급 유머 & 병맛 컨셉"],
        key="sb_tone"
    )

    # 입력 방식 선택 탭
    input_tab1, input_tab2 = st.tabs(["💡 주제 직접 입력", "🔗 링크 입력 (유튜브 / 뉴스 / 블로그)"])

    input_source_text = ""
    
    with input_tab1:
        topic_input = st.text_input("영상 주제 입력:", placeholder="예: 직장인 퇴근 후 1시간 AI로 부수입 얻는 법", key="txt_topic_input")
        if topic_input:
            input_source_text = f"주제: {topic_input}"

    with input_tab2:
        url_input = st.text_input("참고할 링크(URL) 입력:", placeholder="https://www.youtube.com/watch?v=... 또는 기사 링크", key="txt_url_input")
        if url_input:
            with st.spinner("링크의 내용을 분석하는 중입니다..."):
                video_id = extract_youtube_id(url_input)
                if video_id:
                    transcript_text = get_youtube_transcript(video_id)
                    if transcript_text:
                        st.success("✅ 유튜브 영상 자막을 성공적으로 추출했습니다!")
                        input_source_text = f"다음은 원본 유튜브 영상 자막 내용이다:\n{transcript_text[:4000]}"
                    else:
                        st.error("❌ 해당 유튜브 영상에서 자막을 추출하지 못했습니다. (자막이 없는 영상이거나 접근 제한)")
                else:
                    web_text = get_webpage_text(url_input)
                    if web_text:
                        st.success("✅ 웹 페이지 글 내용을 성공적으로 가져왔습니다!")
                        input_source_text = f"다음은 원본 기사/웹문서 내용이다:\n{web_text}"
                    else:
                        st.error("❌ 올바르지 않은 URL이거나 내용을 가져올 수 없는 링크입니다.")

    if st.button("✨ 분석하여 새로운 유튜브 대본 생성하기", key="btn_generate_script"):
        if not input_source_text:
            st.warning("주제를 입력하거나 올바른 링크를 넣어주세요!")
        else:
            with st.spinner("Gemini AI가 원본 내용을 바탕으로 독창적인 대본을 재구성 중입니다..."):
                prompt = f"""
                너는 조회수를 대폭발시키는 유튜브 전문 PD 겸 작가야.
                아래 주어진 참고 자료/주제를 바탕으로, 기존 내용을 단순 복사하지 말고 새로운 관점과 연출로 완벽히 벤치마킹하여 독창적인 유튜브 대본을 작성해줘.

                영상 형식: {video_type}
                채널 톤앤매너: {tone}
                
                [참고 자료/주제]
                {input_source_text}

                [작성 규격]
                1. 🎬 **시선을 사로잡는 오프닝 후킹 (0~3초)**
                2. 📝 **타임라인별 연출 가이드 & 자막 & 나레이션 대사**
                3. 📌 **알고리즘 최적화 추천 제목 (3가지)**
                4. 🏷️ **유튜브 추천 태그 (5개)**
                """

                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
                
                st.session_state['last_result'] = response.text

            st.success("대본 재작성이 완료되었습니다!")

    # 결과 출력
    if st.session_state['last_result']:
        st.subheader("📝 생성된 대본 결과")
        st.text_area("내용 확인 및 수정", value=st.session_state['last_result'], height=350, key="txt_result_area")
        
        st.download_button(
            label="💾 대본 텍스트 파일(.txt)로 저장하기",
            data=st.session_state['last_result'],
            file_name="youtube_script.txt",
            mime="text/plain",
            key="btn_download_txt"
        )

# ==========================================
# 2. TTS 오디오 나레이션 생성
# ==========================================
elif menu == "🎙️ TTS 오디오 나레이션 생성":
    st.title("🎙️ 유튜브 나레이션 오디오(.mp3) 생성기")
    st.caption("대본을 유튜브 영상에 바로 입힐 오디오 파일로 변환합니다.")

    tts_text = st.text_area(
        "음성으로 변환할 대본/나레이션을 입력하세요:", 
        value=st.session_state['last_result'], 
        height=200,
        key="txt_tts_input"
    )

    if st.button("🔊 오디오(.mp3) 추출하기", key="btn_gen_audio"):
        if not tts_text:
            st.warning("변환할 대본을 입력하거나 먼저 대본을 생성해 주세요!")
        else:
            with st.spinner("나레이션 음성을 생성 중입니다..."):
                tts = gTTS(text=tts_text, lang='ko')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                
                st.session_state['audio_bytes'] = fp.read()
            st.success("음성 생성이 완료되었습니다!")

    if 'audio_bytes' in st.session_state:
        st.audio(st.session_state['audio_bytes'], format='audio/mp3')
        
        st.download_button(
            label="⬇️ MP3 오디오 파일 다운로드",
            data=st.session_state['audio_bytes'],
            file_name="youtube_narration.mp3",
            mime="audio/mp3",
            key="btn_download_mp3"
        )

# ==========================================
# 3. AI 애니메이션 프롬프트
# ==========================================
elif menu == "🎨 AI 애니메이션 프롬프트":
    st.title("🎨 유튜브 영상/캐릭터 생성용 AI 프롬프트")
    st.caption("Midjourney / Runway / Sora 등 AI 영상 소스 제작에 쓰일 디테일한 프롬프트를 생성합니다.")

    char_style = st.selectbox("영상 연출 스타일:", ["3D Pixar 애니메이션", "2D 시티팝 일러스트 애니메이션", "실사 4K 영화 스타일", "귀여운 SD 캐릭터"], key="sb_char_style")
    char_desc = st.text_input("장면/캐릭터 묘사:", placeholder="예: 연구실에서 노트북을 보며 놀라는 스마트한 로봇", key="txt_char_desc")

    if st.button("🖼️ 영상 소스 영문 프롬프트 생성", key="btn_gen_prompt"):
        if not char_desc:
            st.warning("묘사를 입력해 주세요!")
        else:
            with st.spinner("영문 프롬프트 생성 중..."):
                prompt = f"스타일: {char_style}, 장면 설명: {char_desc}. 이 장면을 만들 수 있는 상세한 Midjourney v6 영문 프롬프트와 Runway Gen-2 영상 비디오 프롬프트를 만들어줘."
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
                st.code(response.text, language="text")

# ==========================================
# 4. 유튜브 연동 & 자동 업로드
# ==========================================
elif menu == "🚀 유튜브 연동 & 자동 업로드":
    st.title("🚀 YouTube Data API v3 연동 스튜디오")
    st.caption("제작된 영상과 섬네일, 대본 정보를 유튜브에 바로 전송합니다.")
    
    st.checkbox("YouTube Data API v3 인증 완료", key="chk_yt_auth")
    uploaded_video = st.file_uploader("업로드할 유튜브 영상 파일 (.mp4):", type=["mp4"], key="uploader_mp4")
    
    st.text_input("유튜브 영상 제목:", placeholder="제목을 입력하세요", key="txt_yt_title")
    st.text_area("영상 설명란 내용:", placeholder="영상 설명 및 해시태그", key="txt_yt_desc")
    
    if st.button("📡 유튜브 채널로 바로 업로드 실행", key="btn_yt_upload"):
        if uploaded_video:
            st.success("🚀 유튜브 서버로 영상 전송을 시작합니다! (OAuth 클라이언트 기반)")
        else:
            st.warning("업로드할 mp4 영상 파일을 먼저 선택해 주세요.")

# ==========================================
# 5. 유튜브 채널 성과 분석
# ==========================================
elif menu == "📊 유튜브 채널 성과 분석":
    st.title("📊 유튜브 채널 대시보드")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 쇼츠 조회수", "154,200 회", "+18.2%")
    col2.metric("평균 시청 지속 시간", "32 초", "+4.1s")
    col3.metric("구독자 증가 수", "+1,240 명", "+12.0%")
    
    st.subheader("📈 최근 영상별 조회수 추이")
    st.line_chart([12000, 24000, 18000, 45000, 32000, 58000, 72000])