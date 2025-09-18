"""
Tokenizer for all Indian languages in SSF format (fixed for Assamese apostrophes).

"""

import re
import argparse
import os
from string import punctuation

# ---------------- Regular Expressions ---------------- #
token_specification = [
    ('datemonth',
     r'^(0?[1-9]|1[012])[-\/\.](0?[1-9]|[12][0-9]|3[01])[-\/\.](1|2)\d\d\d$'),
    ('monthdate',
     r'^(0?[1-9]|[12][0-9]|3[01])[-\/\.](0?[1-9]|1[012])[-\/\.](1|2)\d\d\d$'),
    ('yearmonth',
     r'^((1|2)\d\d\d)[-\/\.](0?[1-9]|1[012])[-\/\.](0?[1-9]|[12][0-9]|3[01])'),
    ('EMAIL1', r'([\w\.])+@(\w)+\.(com|org|co\.in)$'),
    ('url', r'(https?\:\/\/www\.|https?\:\\\\www\.)(?:[-a-z0-9]+\.)*([-a-z0-9]+.*)'),
    ('url1', r'(www\.)([-a-z0-9]+\.)*([-a-z0-9]+.*)(\/[-a-z0-9]+)*'),
    ('BRACKET', r'[\(\)\[\]\{\}]'),
    ('urdu_year', r'^(ء)(\d{4,4})'),
    ('bullets', r'(\d+\.)$'),
    ('NUMBER', r'^(\d+)([,\.٫٬]\d+)*(\w)*'),
    ('ASSIGN', r'[~:]'),
    ('END', r'[;!_]'),
    ('EQUAL', r'='),
    ('OP', r'[+*\/\-]'),
    ('Fullstop', r'(\.+)$'),
    ('ellips', r'\.(\.)+'),
    ('HYPHEN', r'[-+\|+]'),
    ('Slashes', r'[\\\/]'),
    ('COMMA12', r'[,%]'),
    ('hin_stop', r'।'),
    ('urdu_stop', r'۔'),
    ('urdu_comma', r'،'),
    ('urdu_semicolon', r'؛'),
    ('urdu_question_mark', r'؟'),
    ('urdu_percent', r'٪'),
    ('quotes_question', r'[”\?]'),
    ('hashtag', r'#'),
    ('join', r'–')
]
tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
get_token = re.compile(tok_regex, re.U)
punctuations = punctuation + '\"\'‘’“”'

# ---------------- Tokenizer ---------------- #
def tokenize(list_s):
    """Tokenize a list of tokens, keeping Assamese/Bengali words with internal apostrophes intact."""
    tkns = []
    bengali_range = r'\u0980-\u09FF'
    apos_variants = r"'\u2019\u02BC\u02BB"   # straight ', curly ’, modifier ʻ, etc.

    token_re = re.compile(
        rf"[{bengali_range}]+(?:[{apos_variants}][{bengali_range}]+)*"  # Assamese/Bengali words with apostrophes
        r"|[A-Za-z]+(?:'[A-Za-z]+)*"                                   # Latin words with apostrophes
        r"|\d+(?:[.,]\d+)*"                                            # Numbers
        r"|[।۔،؛؟]|[^\s]", re.UNICODE)                                # Punctuations & misc

    for wrds in list_s:
        matches = token_re.findall(wrds)
        if matches:
            tkns.extend(matches)
        else:
            tkns.append(wrds)
    return tkns

# ---------------- Helpers ---------------- #
def read_lines_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file_read:
        return [line.strip() for line in file_read.readlines() if line.strip()]

def read_file_and_tokenize(input_file, lang_type=0, sentence_tokenize=True):
    lines = read_lines_from_file(input_file)
    text = '\n'.join(lines)

    if lang_type == 0:
        sentences = re.findall('.*?।|.*?\n', text + '\n', re.UNICODE)
        end_markers = ['?', '।', '!', '|']
    elif lang_type == 1:
        sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
        end_markers = ['؟', '!', '|', '۔']
    else:
        sentences = re.findall('.*?\n', text + '\n', re.UNICODE)
        end_markers = ['?', '.', '!', '|']

    if not sentence_tokenize:
        sentences = lines

    proper_sentences = []
    for index, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if sentence != '':
            list_tokens = tokenize(sentence.split())
            end_sentence_markers = [index + 1 for index, token in enumerate(list_tokens) if token in end_markers]
            if len(end_sentence_markers) > 0:
                if end_sentence_markers[-1] != len(list_tokens):
                    end_sentence_markers += [len(list_tokens)]
                end_sentence_markers_with_sentence_end_positions = [0] + end_sentence_markers
                sentence_boundaries = list(zip(end_sentence_markers_with_sentence_end_positions, end_sentence_markers_with_sentence_end_positions[1:]))
                for start, end in sentence_boundaries:
                    individual_sentence = list_tokens[start: end]
                    proper_sentences.append(' '.join(individual_sentence))
            else:
                proper_sentences.append(' '.join(list_tokens))

            if index < len(sentences) - 1:
                next_sentence = sentences[index + 1]
                next_tokens = tokenize(next_sentence.split())
                punct_flag = True
                for token in next_tokens:
                    punct_flag &= token in punctuations
                if punct_flag:
                    if proper_sentences:
                        proper_sentences[-1] += ' ' + ' '.join(next_tokens)
                        sentences[index + 1] = ''
    return proper_sentences

def convert_raw_sentences_into_ssf_format(raw_sentences):
    ssf_sentences = []
    for index, raw_sentence in enumerate(raw_sentences):
        sentence_header = f"<Sentence id='{index+1}'>"
        tokens = raw_sentence.split()
        mapped_tokens = [f"{i+1}\t{tok.strip()}\tunk" for i, tok in enumerate(tokens)]
        sentence_footer = "</Sentence>"
        ssf_sentence = sentence_header + '\n' + '\n'.join(mapped_tokens) + '\n' + sentence_footer + '\n'
        ssf_sentences.append(ssf_sentence)
    return ssf_sentences

def write_list_to_file(output_file, data_list):
    with open(output_file, 'w', encoding='utf-8') as file_write:
        file_write.write('\n'.join(data_list) + '\n')

# ---------------- Main ---------------- #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='inp', help="enter the input file path")
    parser.add_argument('--output', dest='out', help="enter the output file path")
    parser.add_argument('--lang', dest='lang', help="enter the language code, 2 lettered ISO 639-1 language codes", default='hi')
    args = parser.parse_args()

    if os.path.isdir(args.inp) and not os.path.isdir(args.out):
        os.mkdir(args.out)

    lang_code = args.lang
    if not os.path.isdir(args.inp):
        if lang_code in ['hi', 'or', 'mn', 'as', 'bn', 'pa']:
            lang = 0
        elif lang_code in ['ur', 'ks']:
            lang = 1
        elif lang_code in ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta']:
            lang = 2
        sentences = read_file_and_tokenize(args.inp, lang)
        ssf_sentences = convert_raw_sentences_into_ssf_format(sentences)
        write_list_to_file(args.out, ssf_sentences)
    else:
        for root, dirs, files in os.walk(args.inp):
            for fl in files:
                input_file_path = os.path.join(root, fl)
                if lang_code in ['hi', 'or', 'mn', 'as', 'bn', 'pa']:
                    lang = 0
                elif lang_code in ['ur', 'ks']:
                    lang = 1
                elif lang_code in ['en', 'gu', 'mr', 'ml', 'kn', 'te', 'ta']:
                    lang = 2
                sentences = read_file_and_tokenize(input_file_path, lang)
                ssf_sentences = convert_raw_sentences_into_ssf_format(sentences)
                output_file_path = os.path.join(args.out, fl)
                write_list_to_file(output_file_path, ssf_sentences)

if __name__ == '__main__':
    main()
