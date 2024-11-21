import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import string

from core.step1_ytdlp import download_video_ytdlp, find_video_files
from core.all_whisper_methods.whisperX import transcribe as ts
from rich import print as rprint
from core import step3_1_spacy_split
import pandas as pd
from rich.console import Console
from core.step6_generate_final_timeline import align_timestamp
from core.config_utils import load_key

console = Console()

def split_chunks_by_chars(split_sentence_path="output/log/sentence_splitbymeaning.txt",chunk_size=600, max_i=12): 
    """Split text into chunks based on character count, return a list of multi-line text chunks"""
    with open(split_sentence_path, "r", encoding="utf-8") as file:
        sentences = file.read().strip().split('\n')

    chunks = []
    chunk = ''
    sentence_count = 0
    for sentence in sentences:
        if len(chunk) + len(sentence + '\n') > chunk_size or sentence_count == max_i:
            chunks.append(chunk.strip())
            chunk = sentence + '\n'
            sentence_count = 1
        else:
            chunk += sentence + '\n'
            sentence_count += 1
    chunks.append(chunk.strip())
    return chunks

def gen_src_srt(split_sentence_path="output/log/sentence_splitbydetectpunc.txt"):

    min_trim_duration = load_key("min_trim_duration")
    rprint(f"min_trim_duration: {min_trim_duration}")

    chunks = split_chunks_by_chars(split_sentence_path=split_sentence_path)

    translations = chunks.copy()
  
    src_text, trans_text = [], []
    for chunk, translation in zip(chunks, translations):
        src_text.extend(chunk.split('\n'))
        trans_text.extend(translation.split('\n'))
    
    # Trim long translation text
    df_text = pd.read_excel('output/log/cleaned_chunks.xlsx')
    df_text['text'] = df_text['text'].str.strip('"').str.strip()
    df_translate = pd.DataFrame({'Source': src_text, 'Translation': trans_text})
    subtitle_output_configs = [('../trans_subs_for_audio.srt', ['Translation'])]
    df_time = align_timestamp(df_text, df_translate, subtitle_output_configs, output_dir="output/log/", for_display=False)
    console.print(df_time)
    # apply check_len_then_trim to df_time['Translation'], only when duration > MIN_TRIM_DURATION.
    #df_time['Translation'] = [""] * len(df_time) #df_time.apply(lambda x: check_len_then_trim(x['Translation'], x['duration']) if x['duration'] > min_trim_duration else x['Translation'], axis=1)    
    
    #df_time.to_excel("output/log/translation_results.xlsx", index=False)
    console.print("[bold green]✅ Translation completed and results saved.[/bold green]")