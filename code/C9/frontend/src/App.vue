<template>
  <main :class="['shell', { 'sidebar-collapsed': sidebarCollapsed }]">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"><Network /></div>
        <div class="brand-copy">
          <h2>Graph RAG</h2>
        </div>
      </div>
      <button
        class="collapse-btn"
        :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        <PanelLeftClose v-if="!sidebarCollapsed" />
        <PanelLeftOpen v-else />
        <span>{{ sidebarCollapsed ? "展开侧栏" : "收起侧栏" }}</span>
      </button>

      <nav class="nav">
        <button
          v-for="item in navItems"
          :key="item.id"
          :class="{ active: activeView === item.id }"
          :title="item.label"
          @click="activeView = item.id"
        >
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <section class="status-block">
        <div class="status-row">
          <span :class="['pulse', status.ready ? 'ok' : 'warn']"></span>
          <strong>{{ status.ready ? "知识库就绪" : "等待启动" }}</strong>
        </div>
        <p>{{ operation.message || "服务状态未知" }}</p>
        <p v-if="operation.error" class="error-text">{{ operation.error }}</p>
      </section>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <h2>智能烹饪问答工作台</h2>
          <!-- <p class="eyebrow">{{ currentTitle }}</p> -->
        </div>
        <div class="actions">
          <button class="icon-btn" title="刷新状态" @click="loadEverything">
            <RefreshCw />
          </button>
          <button class="primary" :disabled="busy" @click="initializeSystem">
            <Power /> 初始化
          </button>
          <button
            class="primary muted"
            :disabled="busy"
            @click="buildKnowledge"
          >
            <Database /> 构建
          </button>
        </div>
      </header>

      <section v-if="activeView === 'chat'" class="chat-layout">
        <div class="chat-panel">
          <div class="messages" ref="messagesEl">
            <article
              v-for="message in messages"
              :key="message.id"
              :class="['message', message.role]"
            >
              <div class="avatar">
                <User v-if="message.role === 'user'" />
                <Sparkles v-else />
              </div>
              <div class="bubble">
                <p class="message-meta">
                  {{ message.role === "user" ? "你" : "RAG 助手" }}
                </p>
                <div
                  class="answer markdown-body"
                  v-html="renderMarkdown(message.content)"
                ></div>
                <div v-if="message.streaming" class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
                <div v-if="message.analysis" class="analysis-strip">
                  <span>{{
                    strategyLabel(message.analysis.recommended_strategy)
                  }}</span>
                  <span
                    >复杂度
                    {{ percent(message.analysis.query_complexity) }}</span
                  >
                  <span
                    >关系密度
                    {{ percent(message.analysis.relationship_intensity) }}</span
                  >
                  <span>置信度 {{ percent(message.analysis.confidence) }}</span>
                </div>
              </div>
            </article>
          </div>

          <form class="composer" @submit.prevent="askQuestion">
            <textarea
              v-model="question"
              placeholder="例如：家里有鸡胸肉和西兰花，推荐一道低脂晚餐，并说明为什么这样搭配。"
            />
            <div class="composer-actions">
              <label class="switch">
                <input type="checkbox" v-model="explainRouting" />
                <span></span>
                路由解释
              </label>
              <button
                type="submit"
                class="send"
                :disabled="busy || !question.trim()"
              >
                <Send /> 发送
              </button>
            </div>
          </form>
        </div>

        <aside class="inspector">
          <div class="compact-metrics">
            <MetricCard label="总查询" :value="routeStats.total_queries || 0" />
            <MetricCard
              label="传统检索"
              :value="routeStats.traditional_count || 0"
            />
            <MetricCard
              label="Graph RAG"
              :value="routeStats.graph_rag_count || 0"
            />
            <MetricCard
              label="组合策略"
              :value="routeStats.combined_count || 0"
            />
          </div>
          <div class="quick-card">
            <h3>快速试问</h3>
            <button
              v-for="sample in samples"
              :key="sample"
              @click="question = sample"
            >
              {{ sample }}
            </button>
          </div>
        </aside>
      </section>

      <section v-if="activeView === 'stats'" class="dashboard-grid">
        <MetricCard label="菜谱数量" :value="knowledge.total_recipes || 0" />
        <MetricCard
          label="食材数量"
          :value="knowledge.total_ingredients || 0"
        />
        <MetricCard
          label="烹饪步骤"
          :value="knowledge.total_cooking_steps || 0"
        />
        <MetricCard label="文本块" :value="knowledge.total_chunks || 0" />

        <div class="wide-panel">
          <h3>知识库分布</h3>
          <div class="bars">
            <DataBar
              v-for="item in categoryItems"
              :key="item.name"
              :label="item.name"
              :value="item.value"
              :max="categoryMax"
            />
          </div>
        </div>

        <div class="wide-panel">
          <h3>检索路由</h3>
          <div class="route-mix">
            <DataBar
              label="传统混合检索"
              :value="routeStats.traditional_count || 0"
              :max="routeMax"
            />
            <DataBar
              label="图结构检索"
              :value="routeStats.graph_rag_count || 0"
              :max="routeMax"
            />
            <DataBar
              label="组合策略"
              :value="routeStats.combined_count || 0"
              :max="routeMax"
            />
          </div>
        </div>
      </section>

      <section v-if="activeView === 'routing'" class="two-column">
        <div class="wide-panel">
          <h3>路由分析</h3>
          <textarea
            v-model="routingQuestion"
            class="analysis-input"
            placeholder="输入问题，查看系统会选择哪种检索策略。"
          />
          <button
            class="primary"
            :disabled="busy || !routingQuestion.trim()"
            @click="explainRoute"
          >
            <Route /> 分析问题
          </button>
        </div>
        <div class="wide-panel result-panel">
          <h3>分析结果</h3>
          <div v-if="routeAnalysis" class="analysis-card">
            <strong>{{
              strategyLabel(routeAnalysis.recommended_strategy)
            }}</strong>
            <p>{{ routeAnalysis.reasoning }}</p>
            <div class="ring-metrics">
              <RingMetric
                label="查询复杂度"
                :value="routeAnalysis.query_complexity * 100"
              />
              <RingMetric
                label="关系密度"
                :value="routeAnalysis.relationship_intensity * 100"
              />
              <RingMetric
                label="置信度"
                :value="routeAnalysis.confidence * 100"
              />
            </div>
          </div>
          <p v-else class="muted-text">等待分析结果。</p>
        </div>
      </section>

      <section v-if="activeView === 'config'" class="config-grid">
        <div class="wide-panel">
          <h3>运行配置</h3>
          <div class="form-grid">
            <label v-for="field in configFields" :key="field.key">
              <span>{{ field.label }}</span>
              <input
                v-model="configDraft[field.key]"
                :type="field.type || 'text'"
              />
            </label>
          </div>
          <div class="panel-actions">
            <button
              class="primary"
              :disabled="status.initialized"
              @click="saveConfig"
            >
              <SlidersHorizontal /> 保存配置
            </button>
            <span v-if="status.initialized" class="muted-text"
              >系统启动后配置会锁定。</span
            >
          </div>
        </div>

        <div class="danger-panel">
          <h3>知识库维护</h3>
          <p>
            重建会删除当前 Milvus 集合并重新加载 Neo4j 图数据、分块、建索引。
          </p>
          <button class="danger" :disabled="busy" @click="rebuildKnowledge">
            <Trash2 /> 重建知识库
          </button>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import {
  Database,
  LayoutDashboard,
  MessageSquareText,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  Power,
  RefreshCw,
  Route,
  Send,
  Settings,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  User,
} from "lucide-vue-next";
import MarkdownIt from "markdown-it";
import MetricCard from "./components/MetricCard.vue";
import DataBar from "./components/DataBar.vue";
import RingMetric from "./components/RingMetric.vue";

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const activeView = ref("chat");
const sidebarCollapsed = ref(false);
const status = ref({ ready: false, initialized: false, operation: {} });
const stats = ref({});
const configDraft = ref({});
const busy = ref(false);
const question = ref("");
const explainRouting = ref(true);
const routingQuestion = ref("");
const routeAnalysis = ref(null);
const messages = ref([
  {
    id: newId(),
    role: "assistant",
    content:
      "控制台已连接。先初始化系统并构建知识库，然后就可以开始询问菜谱、食材替换、步骤推理和搭配建议。",
  },
]);
const messagesEl = ref(null);

const navItems = [
  { id: "chat", label: "问答", icon: MessageSquareText },
  { id: "stats", label: "统计", icon: LayoutDashboard },
  { id: "routing", label: "路由", icon: Route },
  { id: "config", label: "配置", icon: Settings },
];

const samples = [
  "推荐几道适合减脂的鸡胸肉菜谱",
  "土豆和牛肉能做什么下饭菜？",
  "如果没有生抽，红烧类菜谱可以怎么替换？",
  "给我一道适合新手的快手晚餐，并说明步骤关系",
];

const configFields = [
  { key: "neo4j_uri", label: "Neo4j URI" },
  { key: "neo4j_user", label: "Neo4j 用户" },
  { key: "neo4j_password", label: "Neo4j 密码" },
  { key: "neo4j_database", label: "Neo4j 数据库" },
  { key: "milvus_host", label: "Milvus 主机" },
  { key: "milvus_port", label: "Milvus 端口", type: "number" },
  { key: "milvus_collection_name", label: "集合名" },
  { key: "embedding_model", label: "Embedding 模型" },
  { key: "llm_model", label: "LLM 模型" },
  { key: "top_k", label: "Top K", type: "number" },
  { key: "temperature", label: "Temperature", type: "number" },
  { key: "max_tokens", label: "Max Tokens", type: "number" },
  { key: "chunk_size", label: "Chunk Size", type: "number" },
  { key: "chunk_overlap", label: "Chunk Overlap", type: "number" },
  { key: "max_graph_depth", label: "图遍历深度", type: "number" },
];

const operation = computed(() => status.value.operation || {});
const knowledge = computed(() => stats.value.knowledge || {});
const routeStats = computed(() => stats.value.routes || {});
const currentTitle = computed(
  () => navItems.find((item) => item.id === activeView.value)?.label || "控制台"
);
const categoryItems = computed(() =>
  Object.entries(knowledge.value.categories || {})
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }))
);
const categoryMax = computed(() =>
  Math.max(1, ...categoryItems.value.map((item) => item.value))
);
const routeMax = computed(() =>
  Math.max(
    1,
    routeStats.value.traditional_count || 0,
    routeStats.value.graph_rag_count || 0,
    routeStats.value.combined_count || 0
  )
);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

async function loadEverything() {
  const [health, statsResponse, configResponse] = await Promise.all([
    api("/api/health"),
    api("/api/stats"),
    api("/api/config"),
  ]);
  status.value = health;
  stats.value = statsResponse.stats;
  configDraft.value = { ...configResponse.config };
}

async function runAction(fn) {
  busy.value = true;
  try {
    await fn();
    await loadEverything();
  } catch (error) {
    messages.value.push({
      id: newId(),
      role: "assistant",
      content: `操作失败：${error.message}`,
    });
  } finally {
    busy.value = false;
  }
}

function initializeSystem() {
  runAction(() => api("/api/system/initialize", { method: "POST" }));
}

function buildKnowledge() {
  runAction(() => api("/api/knowledge/build", { method: "POST" }));
}

function rebuildKnowledge() {
  if (!window.confirm("确认删除并重建 Milvus 知识库？")) return;
  runAction(() =>
    api("/api/knowledge/rebuild", {
      method: "POST",
      body: JSON.stringify({ confirm: "REBUILD" }),
    })
  );
}

function saveConfig() {
  runAction(() =>
    api("/api/config", {
      method: "PUT",
      body: JSON.stringify(configDraft.value),
    })
  );
}

async function askQuestion() {
  const text = question.value.trim();
  if (!text) return;
  messages.value.push({ id: newId(), role: "user", content: text });
  const assistantMessage = {
    id: newId(),
    role: "assistant",
    content: "",
    analysis: null,
    streaming: true,
  };
  messages.value.push(assistantMessage);
  const assistantIndex = messages.value.length - 1;
  question.value = "";
  busy.value = true;
  await scrollToBottom();
  try {
    await streamQuestion(text, assistantIndex);
  } catch (error) {
    updateAssistantMessage(assistantIndex, {
      content: `问答失败：${error.message}`,
    });
  } finally {
    updateAssistantMessage(assistantIndex, { streaming: false });
    busy.value = false;
    await loadEverything();
    await scrollToBottom();
  }
}

async function streamQuestion(text, assistantIndex) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: text,
      explain_routing: explainRouting.value,
    }),
  });

  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || "流式请求失败");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";

    for (const block of blocks) {
      await handleStreamEvent(block, assistantIndex);
    }
  }

  if (buffer.trim()) {
    await handleStreamEvent(buffer, assistantIndex);
  }
}

async function handleStreamEvent(block, assistantIndex) {
  const eventLine = block.split("\n").find((line) => line.startsWith("event:"));
  const dataLines = block
    .split("\n")
    .filter((line) => line.startsWith("data:"));
  const event = eventLine ? eventLine.slice(6).trim() : "message";
  const dataText = dataLines
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  if (!dataText) return;

  const data = JSON.parse(dataText);
  if (event === "meta") {
    updateAssistantMessage(assistantIndex, { analysis: data.analysis });
  } else if (event === "chunk") {
    appendAssistantContent(assistantIndex, data.text || "");
    await scrollToBottom();
  } else if (event === "done") {
    updateAssistantMessage(assistantIndex, {
      analysis: data.analysis || messages.value[assistantIndex]?.analysis,
      streaming: false,
    });
    if (data.stats) {
      stats.value = data.stats;
    }
  } else if (event === "error") {
    const currentContent = messages.value[assistantIndex]?.content || "";
    updateAssistantMessage(assistantIndex, {
      streaming: false,
      content: currentContent
        ? `${currentContent}\n\n${data.error}`
        : `问答失败：${data.error}`,
    });
  }
}

function updateAssistantMessage(index, patch) {
  if (!messages.value[index]) return;
  messages.value[index] = {
    ...messages.value[index],
    ...patch,
  };
}

function appendAssistantContent(index, text) {
  if (!messages.value[index] || !text) return;
  messages.value[index] = {
    ...messages.value[index],
    content: `${messages.value[index].content}${text}`,
  };
}

async function explainRoute() {
  busy.value = true;
  try {
    const response = await api("/api/routing/explain", {
      method: "POST",
      body: JSON.stringify({ question: routingQuestion.value }),
    });
    routeAnalysis.value = response.analysis;
  } catch (error) {
    routeAnalysis.value = {
      recommended_strategy: "error",
      reasoning: error.message,
      query_complexity: 0,
      relationship_intensity: 0,
      confidence: 0,
    };
  } finally {
    busy.value = false;
  }
}

async function scrollToBottom() {
  await nextTick();
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  }
}

function percent(value = 0) {
  return `${Math.round(value * 100)}%`;
}

function strategyLabel(strategy) {
  const labels = {
    hybrid_traditional: "传统混合检索",
    graph_rag: "Graph RAG",
    combined: "组合策略",
    error: "分析失败",
  };
  return labels[strategy] || strategy || "未知策略";
}

function renderMarkdown(text = "") {
  return markdown.render(text);
}

function newId() {
  const cryptoApi =
    typeof globalThis !== "undefined" ? globalThis.crypto : null;
  if (cryptoApi && typeof cryptoApi.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

onMounted(loadEverything);
</script>
