# PyInstaller hook for faster-whisper
# Ensures ctranslate2 native DLLs and tokenizer data are included.

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("faster_whisper")
datas += collect_data_files("ctranslate2")
datas += collect_data_files("tokenizers")
binaries = collect_dynamic_libs("ctranslate2")
