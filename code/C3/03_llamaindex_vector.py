import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. 配置全局嵌入模型
Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-small-zh-v1.5")

# 2. 创建示例文档
texts = [
    "张三是法外狂徒",
    "LlamaIndex是一个用于构建和查询私有或领域特定数据的框架。",
    "它提供了数据连接、索引和查询接口等工具。"
]
docs = [Document(text=t) for t in texts]

# 3. 创建索引并持久化到本地
index = VectorStoreIndex.from_documents(docs)
persist_path = "./llamaindex_index_store"
index.storage_context.persist(persist_dir=persist_path)
print(f"LlamaIndex 索引已保存至: {persist_path}")

query = '张三是谁？'

# 4. 创建检索器并执行检索
retriever = index.as_retriever(similarity_top_k=2)  # 返回最相似的 2 个节点
nodes = retriever.retrieve(query)

# 5. 打印检索结果
print(f"\n查询: {query}")
print("-" * 40)
for i, node in enumerate(nodes):
    print(f"[结果 {i+1}] 相似度得分: {node.score:.4f}")
    print(f"  文本: {node.text}")
    print()
