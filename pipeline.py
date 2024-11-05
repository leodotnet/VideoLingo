import os
import string
from core.step1_ytdlp import download_video_ytdlp, find_video_files
from core.all_whisper_methods.whisperX import transcribe as ts
from rich import print as rprint
from st_components.imports_and_utils import step3_1_spacy_split, step5_splitforsub, step6_generate_final_timeline
import pandas as pd
from rich.console import Console
from core.step6_generate_final_timeline import align_timestamp
from core.step8_gen_audio_task import check_len_then_trim
from core.config_utils import load_key
from deepmultilingualpunctuation import PunctuationModel

console = Console()
punc_model = None

def download_video(url, resolution='1080'):
    resolution = int(resolution) if resolution.isdigit() else 1080
    download_video_ytdlp(url, save_path='output', resolution=resolution)
    print(f"🎥 Video has been downloaded to {find_video_files()}")


def convert2audio():
    video_file = find_video_files()
    rprint(f"[green]Found video file:[/green] {video_file}, [green]starting transcription...[/green]")
    ts(video_file)


def get_punc_model():
    global punc_model
    if punc_model is None:
        rprint("Loading punctuation model...")
        punc_model = PunctuationModel()
    return punc_model


def split_by_addpunc(split_sentence_path="output/log/sentence_splitbynlp.txt", long_sentence_threshold=30):

    punc_model = get_punc_model()


    def split_long_sentence_by_detect_punc(text):
        clean_text = text.split(' ')
        labled_words = punc_model.predict(clean_text)

        sub_sents = []
        start = 0
        for i, (word, label, prob) in enumerate(labled_words):
            if label in ['.', '?', '!', ',', ';']:
                sub_sent = ' '.join(clean_text[start:i+1])
                len_sub_sent = len(sub_sent.split(' '))

                last_sub_sent = sub_sents[-1] if sub_sents else ''
                len_last_sub_sent = len(last_sub_sent.split(' '))

                if sub_sents and len_last_sub_sent + len_sub_sent < long_sentence_threshold / 4:
                    sub_sents[-1] = last_sub_sent + label + ' ' + sub_sent
                else:
                    sub_sents.append(sub_sent)
                start = i+1

        if start < len(clean_text):
            sub_sents.append(' '.join(clean_text[start:]))
        
        return sub_sents


    with open(split_sentence_path, "r", encoding="utf-8") as file:
        sentences = file.read().strip().split('\n')

    all_split_sentences = []
    for sentence in sentences:
        doc = sentence.split(' ')
        if len(doc) > long_sentence_threshold:
            split_sentences = split_long_sentence_by_detect_punc(sentence)
            all_split_sentences.extend(split_sentences)
            print(f"[yellow]✂️  Splitting long sentences by detecting punctuation: {split_sentences}...[/yellow]")
        else:
            all_split_sentences.append(sentence.strip())

    punctuation = string.punctuation + "'" + '"'  # include all punctuation and apostrophe ' and "

    with open("output/log/sentence_splitbydetectpunc.txt", "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(all_split_sentences):
            stripped_sentence = sentence.strip()
            if not stripped_sentence or all(char in punctuation for char in stripped_sentence):
                print(f"[yellow]⚠️  Warning: Empty or punctuation-only line detected at index {i}[/yellow]")
                if i > 0:
                    all_split_sentences[i-1] += sentence
                continue
            output_file.write(sentence + "\n")

    # delete the original file
    # os.remove(split_sentence_path)

    print("[green]💾 Long sentences split by detect punctuation saved to →  `sentence_splitbydetectpunc.txt`[/green]")
        


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


def fake_translate(split_sentence_path="output/log/sentence_splitbydetectpunc.txt"):

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
    subtitle_output_configs = [('trans_subs_for_audio.srt', ['Translation'])]
    df_time = align_timestamp(df_text, df_translate, subtitle_output_configs, output_dir="output/log/", for_display=False)
    console.print(df_time)
    # apply check_len_then_trim to df_time['Translation'], only when duration > MIN_TRIM_DURATION.
    df_time['Translation'] = [""] * len(df_time) #df_time.apply(lambda x: check_len_then_trim(x['Translation'], x['duration']) if x['duration'] > min_trim_duration else x['Translation'], axis=1)
    console.print(df_time)
    
    df_time.to_excel("output/log/translation_results.xlsx", index=False)
    console.print("[bold green]✅ Translation completed and results saved.[/bold green]")


def process_text():
    rprint("Splitting long sentences...")
    step3_1_spacy_split.split_by_spacy()
    split_by_addpunc(split_sentence_path="output/log/sentence_splitbynlp.txt", long_sentence_threshold=30)
        # step3_2_splitbymeaning.split_sentences_by_meaning()
    # rprint("Summarizing and translating...")
    #     step4_1_summarize.get_summary()
    #     if load_key("pause_before_translate"):
    #         input("⚠️ PAUSE_BEFORE_TRANSLATE. Go to `output/log/terminology.json` to edit terminology. Then press ENTER to continue...")
    #     step4_2_translate_all.translate_all()
    
    rprint("Translating...")
    fake_translate(split_sentence_path="output/log/sentence_splitbydetectpunc.txt")

    rprint("Processing and aligning subtitles...")
    # step5_splitforsub.split_for_sub_main()
    # step6_generate_final_timeline.align_timestamp_main()
    # rprint("Merging subtitles to video...")
    #     step7_merge_sub_to_vid.merge_subtitles_to_video()



if __name__ == '__main__':
    # Example usage
    url = input('Please enter the URL of the video you want to download: ')
    resolution = input('Please enter the desired resolution (360/1080, default 1080): ')
    resolution = int(resolution) if resolution != "" and resolution.isdigit() else 1080
    if url != "":
        print(f"🎥 Download from URL {url} with resolution {resolution}")
        download_video_ytdlp(url, resolution=resolution)
        print(f"🎥 Video has been downloaded to {find_video_files()}")
    else:
        rprint("No URL provided, skipping download...")

    convert2audio()

    process_text()

    
