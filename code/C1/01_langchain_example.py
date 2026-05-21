import os
# hugging face镜像设置，如果国内环境无法使用启用该设置
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

load_dotenv()

markdown_path = "../../data/C1/markdown/easy-rl-chapter1.md"

# 加载本地markdown文件
loader = UnstructuredMarkdownLoader(markdown_path)
docs = loader.load()

# 文本分块
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20,
    length_function=len,)
chunks = text_splitter.split_documents(docs)

# 文本嵌入模型
embeddings = OpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    # With the `text-embedding-3` class
    # of models, you can specify the size
    # of the embeddings you want returned.
    # dimensions=1024
)
  
# 构建向量存储
vectorstore = InMemoryVectorStore(embeddings)
vectorstore.add_documents(chunks)

# 提示词模板
prompt = ChatPromptTemplate.from_template("""请根据下面提供的上下文信息来回答问题。
请确保你的回答完全基于这些上下文。
如果上下文中没有足够的信息来回答问题，请直接告知：“抱歉，我无法根据提供的上下文找到相关信息来回答此问题。”

上下文:
{context}

问题: {question}

回答:"""
                                          )

# 配置大语言模型

# 使用 AIHubmix
llm = ChatOpenAI(
    model=os.getenv("LLM"),
    temperature=float(os.getenv("TEMPERATURE")),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# llm = ChatOpenAI(
#     model="deepseek-chat",
#     temperature=0.7,
#     max_tokens=4096,
#     api_key=os.getenv("DEEPSEEK_API_KEY"),
#     base_url="https://api.deepseek.com"
# )

# 用户查询
question = "文中举了哪些例子？"

# 在向量存储中查询相关文档
retrieved_docs = vectorstore.similarity_search(question, k=3)
docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

answer = llm.invoke(prompt.format(question=question, context=docs_content))
print(answer)


"""
(all-in-rag) PS D:\project\LearnAgent\all-in-rag\code\C1> python.exe .\01_langchain_example.py
content='文中举了以下例子：\n\n- **监督学习对比例子**：图片分类（如区分汽车、飞机、椅子等）。\n- **强化学习游戏例子**：雅达利游戏 Breakout（打砖块）、雅达利游戏 Pong。\n- **现实生活中的强化学习例子**：自然界中的羚羊通过试错学会站立和奔跑、股票交 易、玩雅达利或其他电脑游戏。\n- **超人类表现的例子**：DeepMind 的 AlphaGo 打败人类顶尖棋手。\n- **Gym 实验环境例子**：\n  - Taxi-v3（用于展示代码框架）\n  - 经典控制问题：Acrobot（双连杆机器人）、CartPole（小车倒立摆）、MountainCar（小车上山）\n  - 详细交互示例：MountainCar-v0、CartPole-v0\n- **单步强化学习任务例子**：K-臂赌博机（多臂赌博机）。' additional_kwargs={'refusal': None} response_metadata={'token_usage': {'completion_tokens': 800, 'prompt_tokens': 5429, 'total_tokens': 6229, 'completion_tokens_details': {'accepted_prediction_tokens': None, 'audio_tokens': None, 'reasoning_tokens': 600, 'rejected_prediction_tokens': None}, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'model_name': 'deepseek-v4-pro', 'system_fingerprint': None, 'id': 'chatcmpl-d887b613-a5ee-9ec7-8436-ea475e5c8679', 'service_tier': None, 'finish_reason': 'stop', 'logprobs': None} id='run--85323489-af09-4321-b9a3-7d8f694f6361-0' usage_metadata={'input_tokens': 5429, 'output_tokens': 800, 'total_tokens': 6229, 'input_token_details': {'cache_read': 0}, 'output_token_details': {'reasoning': 600}}
"""
