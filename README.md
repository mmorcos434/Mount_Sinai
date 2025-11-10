1. Initialize faiss indexing
    - curl -X POST http://127.0.0.1:8000/init_index

2. Example of a file upload curl command: Be sure to replace with your file path after file=@
   - curl -X POST \                                                                                                                                           ─╯
  --form 'file=@"/Users/kristasingh/Desktop/Mount Sinai/MSCGemini/MAIN CAMPUS  MRI ROOM ASSIGNMENTS UPDATED 5.22.pdf";type=application/pdf' \
  http://127.0.0.1:8000/upload

3. Example of a question to run
   - curl -X POST -F 'query=Which Gastrointestinal clips  are listed as MR Unsafe in our documents?' http://127.0.0.1:8000/chat 
