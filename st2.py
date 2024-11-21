import streamlit as st
import os, sys
from st_components.imports_and_utils import *
from core.config_utils import load_key
from io import StringIO
# SET PATH
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['PATH'] += os.pathsep + current_dir
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="VideoLingo", page_icon="docs/logo.svg")

def text_processing_asr_section():
    st.header("Convert audio to subtitles")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. WhisperX word-level transcription<br>
            2. Sentence segmentation using NLP and LLM<br>
        """, unsafe_allow_html=True)

        if not os.path.exists("output/trans_subs_for_audio.srt"):
            if st.button("Start ASR for Subtitles", key="text_processing_asr_button"):
                process_asr()
                st.rerun()
        else:
            st.success("Subtitle ASR is complete! It's recommended to download the srt file and double-check it by yourself.")
            # if load_key("resolution") != "0x0":
            #     st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text="Download Source Subtitles")
            
            if st.button("Archive to 'history'", key="cleanup_in_text_processing_asr"):
                cleanup()
                st.rerun()
            return True
        

def upload_srt(save_path="output/trans_subs_for_audio.srt"):
    uploaded_file = st.file_uploader("Choose a SRT file")
    if uploaded_file is not None:
        # write the uploaded file to overwrite "output/log/trans_subs_for_audio.srt"
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success("Upload successful! You can start translating the subtitles now.")
        return save_path
    else:
        st.error("No file uploaded. Please upload a file.")
        return None
    

def download_subtitle_zip_button_extend(text: str):
    zip_buffer = io.BytesIO()
    output_dir = "output"
    
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_name in os.listdir(output_dir):
            if file_name.endswith(".srt") and not file_name.endswith("trans_subs_for_audio.srt"):
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, "rb") as file:
                    zip_file.writestr(file_name, file.read())

        file_name = "translation_results.xlsx"
        file_path = f"{output_dir}/log/{file_name}"
        with open(file_path, "rb") as file:
            zip_file.writestr(file_name, file.read())
    
    zip_buffer.seek(0)
    
    st.download_button(
        label=text,
        data=zip_buffer,
        file_name="subtitles_bilingual.zip",
        mime="application/zip"
    )

def text_processing_translation_section():
    st.header("Translate and Generate Subtitles")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            3. Summarization and multi-step translation<br>
            4. Cutting and aligning long subtitles<br>
            5. Generating timeline and subtitles<br>
            6. Merging subtitles into the video
        """, unsafe_allow_html=True)


        upload_srt_path = upload_srt("output/trans_subs_for_audio.srt")        

        if not os.path.exists("output/log/translation_results.xlsx"):
            if st.button("Start Translating Subtitles", key="text_processing_translation_button"):
                process_translation(upload_srt_path)
                st.rerun()
        else:
            st.success("Subtitle translation is complete! It's recommended to download the srt file and process it yourself.")
            # if load_key("resolution") != "0x0":
            #     st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button_extend(text="Download All Subtitles")
            
            if st.button("Archive to 'history'", key="cleanup_in_text_processing_translation"):
                cleanup()
                st.rerun()
            return True
        

def process_asr():
    from core import step3_3_generate_src_subtitle
    with st.spinner("Using Whisper for transcription..."):
        step2_whisper.transcribe()
    with st.spinner("Using Whisper for transcription..."):
        step2_whisper.transcribe()
    with st.spinner("Splitting long sentences..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
        split_file = "output/log/sentence_splitbymeaning.txt"
        # later add punctuation split
        step3_3_generate_src_subtitle.gen_src_srt(split_sentence_path=split_file)
    st.success("Subtitle ASR processing complete! 🎉")
    st.balloons()

def process_translation(upload_srt_path:str=None):
    from core import step4_3_translate_all_from_srt
    with st.spinner("Summarizing and translating..."):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue...")

        if upload_srt_path is None:
            step4_2_translate_all.translate_all()
        else:            
            step4_3_translate_all_from_srt.translate_all(srt_path=upload_srt_path)
    with st.spinner("Processing and aligning subtitles..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    # with st.spinner("Merging subtitles to video..."):
    #     step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("Subtitle processing complete! 🎉")
    st.balloons()


def text_processing_section():
    st.header("Translate and Generate Subtitles")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. WhisperX word-level transcription<br>
            2. Sentence segmentation using NLP and LLM<br>
            3. Summarization and multi-step translation<br>
            4. Cutting and aligning long subtitles<br>
            5. Generating timeline and subtitles<br>
            6. Merging subtitles into the video
        """, unsafe_allow_html=True)

        if not os.path.exists("output/output_video_with_subs.mp4"):
            if st.button("Start Processing Subtitles", key="text_processing_button"):
                process_text()
                st.rerun()
        else:
            st.success("Subtitle translation is complete! It's recommended to download the srt file and process it yourself.")
            if load_key("resolution") != "0x0":
                st.video("output/output_video_with_subs.mp4")
            download_subtitle_zip_button(text="Download All Subtitles")
            
            if st.button("Archive to 'history'", key="cleanup_in_text_processing"):
                cleanup()
                st.rerun()
            return True
        
def process_text():
    with st.spinner("Using Whisper for transcription..."):
        step2_whisper.transcribe()
    with st.spinner("Splitting long sentences..."):  
        step3_1_spacy_split.split_by_spacy()
        step3_2_splitbymeaning.split_sentences_by_meaning()
    with st.spinner("Summarizing and translating..."):
        step4_1_summarize.get_summary()
        if load_key("pause_before_translate"):
            input("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue...")
        step4_2_translate_all.translate_all()
    with st.spinner("Processing and aligning subtitles..."): 
        step5_splitforsub.split_for_sub_main()
        step6_generate_final_timeline.align_timestamp_main()
    with st.spinner("Merging subtitles to video..."):
        step7_merge_sub_to_vid.merge_subtitles_to_video()
    
    st.success("Subtitle processing complete! 🎉")
    st.balloons()

def audio_processing_section():
    st.header("Dubbing (beta)")
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        This stage includes the following steps:
        <p style='font-size: 20px;'>
            1. Generate audio tasks<br>
            2. Generate audio<br>
            3. Merge audio into the video
        """, unsafe_allow_html=True)
        if not os.path.exists("output/output_video_with_audio.mp4"):
            if st.button("Start Audio Processing", key="audio_processing_button"):
                process_audio()
                st.rerun()
        else:
            st.success("Audio processing is complete! You can check the audio files in the `output` folder.")
            if load_key("resolution") != "0x0": 
                st.video("output/output_video_with_audio.mp4") 
            if st.button("Delete dubbing files", key="delete_dubbing_files"):
                delete_dubbing_files()
                st.rerun()
            if st.button("Archive to 'history'", key="cleanup_in_audio_processing"):
                cleanup()
                st.rerun()

def process_audio():
    with st.spinner("Generate audio tasks"): 
        step8_gen_audio_task.gen_audio_task_main()
    with st.spinner("Extract refer audio"):
        step9_extract_refer_audio.extract_refer_audio_main()
    with st.spinner("Generate audio"):
        step10_gen_audio.process_sovits_tasks()
    with st.spinner("Merge audio into the video"):
        step11_merge_audio_to_vid.merge_main()
    
    st.success("Audio processing complete! 🎇")
    st.balloons()

def main():
    logo_col, _ = st.columns([2,1])
    with logo_col:
        st.image("docs/logo.png", use_column_width=True)
    st.markdown(button_style, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 20px; color: #808080;'>Hello, welcome to VideoLingo. This project is currently under construction. If you encounter any issues, please feel free to ask questions on Github! You can also visit our website: <a href='https://videolingo.io' target='_blank'>videolingo.io</a></p>", unsafe_allow_html=True)
    # add settings
    with st.sidebar:
        page_setting()
        st.markdown(give_star_button, unsafe_allow_html=True)
    download_video_section()
    # text_processing_section()
    text_processing_asr_section()
    text_processing_translation_section()
    audio_processing_section()

if __name__ == "__main__":
    main()
