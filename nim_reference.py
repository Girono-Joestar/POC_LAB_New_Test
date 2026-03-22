from langchain_nvidia_ai_endpoints import ChatNVIDIA

client = ChatNVIDIA(
  model="moonshotai/kimi-k2.5",
  api_key="$NVIDIA_API_KEY",
  temperature=1,
  top_p=1,
  max_completion_tokens=16384,
)

for chunk in client.stream([{"role":"user","content":""}], chat_template_kwargs={"thinking":True}):
  
    if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
      print(chunk.additional_kwargs["reasoning_content"], end="")
  
    print(chunk.content, end="")

