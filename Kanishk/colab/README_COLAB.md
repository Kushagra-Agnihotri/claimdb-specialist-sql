# Colab runs (setup C)

Files: sqljudge_colab_bundle.zip (code + the 59 Qwen3-14B claims already done on the PC), sqljudge_colab.ipynb.

1. Google Drive: create MyDrive/sqljudge_colab and upload sqljudge_colab_bundle.zip into it (same Google account as Colab Pro).
2. Colab: File > Upload notebook > sqljudge_colab.ipynb.
3. Runtime > Change runtime type: Python 3, L4 GPU, High-RAM on. Save.
4. Runtime > Run all. Approve the Google Drive popup. Leave the last cell (monitor) running.
5. Keep the laptop on, plugged in, sleep off, the Colab tab open and online.

Job order: qwen3:14b + Arctic (finishes Section 1), then Section 3 cells:
qwen3:4b + OmniSQL-7B, llama3.1:8b + OmniSQL-7B, qwen3:4b + Qwen2.5-Coder-7B, qwen3:4b + SLM-SQL-1.5B, llama3.1:8b + SLM-SQL-1.5B.

Results: MyDrive/sqljudge_colab/results/*.jsonl (saved after every claim). Log: MyDrive/sqljudge_colab/queue_log.txt.
After a disconnect: open the notebook and Run all again; finished jobs are skipped, the running one resumes.
