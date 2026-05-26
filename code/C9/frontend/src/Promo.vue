<template>
  <main class="promo-page">
    <nav class="promo-nav glass-card">
      <a class="promo-brand" href="/">
        <span class="brand-glyph"><Network /></span>
        <span>Graph RAG Cooking</span>
      </a>
      <div class="nav-links">
        <a
          v-for="link in navLinks"
          :key="link.id"
          :href="`#${link.id}`"
          :class="{ active: activeSection === link.id }"
          @click="activeSection = link.id"
        >
          {{ link.label }}
        </a>
      </div>
      <a class="nav-action" href="/">打开控制台</a>
    </nav>

    <section class="hero">
      <div class="hero-copy">
        <h1>
          会推理的
          <span>菜谱知识图谱</span>
        </h1>
        <p class="hero-subtitle">
          从食材、步骤到搭配关系，让烹饪问答有迹可循。
        </p>
        <p class="hero-text">
          结合 Neo4j 图数据、Milvus 向量检索、BM25
          关键词召回和智能路由，让菜谱问答不止“搜到文本”，还能理解食材、步骤、替换与搭配关系。
        </p>
        <div class="hero-actions">
          <a class="primary-cta" href="/">进入 Web 控制台</a>
          <a class="secondary-cta" href="#workflow">查看工作流</a>
        </div>
      </div>

      <figure class="hero-visual glass-card">
        <div class="visual-frame">
          <img :src="graphImage" alt="Graph RAG 项目图谱示意图" />
        </div>
        <figcaption>
          <span>Hybrid Retrieval</span>
          <strong>Graph + Vector + BM25</strong>
        </figcaption>
      </figure>
    </section>

    <section id="features" class="feature-grid">
      <article
        v-for="feature in features"
        :key="feature.title"
        class="glass-card feature-card"
      >
        <span class="feature-icon"><component :is="feature.icon" /></span>
        <h2>{{ feature.title }}</h2>
        <p>{{ feature.text }}</p>
      </article>
    </section>

    <section id="workflow" class="split-section glass-card">
      <div>
        <p class="eyebrow">Workflow</p>
        <h2>从图数据到可解释回答</h2>
        <p>
          控制台把原本命令行中的初始化、构建知识库、智能问答和路由分析拆成清晰步骤，适合演示、调试和教学。
        </p>
      </div>
      <ol class="workflow-list">
        <li v-for="step in workflow" :key="step.title">
          <span>{{ step.no }}</span>
          <div>
            <strong>{{ step.title }}</strong>
            <p>{{ step.text }}</p>
          </div>
        </li>
      </ol>
    </section>

    <section id="architecture" class="architecture">
      <div class="section-heading">
        <p class="eyebrow">Architecture</p>
        <h2>
          为烹饪场景定制的
          <span>Graph RAG 架构</span>
        </h2>
      </div>
      <div class="architecture-grid">
        <article
          v-for="item in architecture"
          :key="item.name"
          class="glass-card arch-card"
        >
          <span>{{ item.tag }}</span>
          <h3>{{ item.name }}</h3>
          <p>{{ item.text }}</p>
        </article>
      </div>
    </section>

    <section class="final-cta glass-card">
      <div>
        <p class="eyebrow">Ready</p>
        <h2>启动服务，开始和你的菜谱知识库对话</h2>
      </div>
      <a class="primary-cta" href="/">打开控制台</a>
    </section>
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  Bot,
  Database,
  GitBranch,
  Network,
  Route,
  Sparkles,
} from "lucide-vue-next";
import graphImage from "./assets/main-ui.jpg";

const features = [
  {
    icon: Route,
    title: "智能路由",
    text: "根据问题复杂度与关系密度，自动选择传统混合检索、Graph RAG 或组合策略。",
  },
  {
    icon: GitBranch,
    title: "图结构推理",
    text: "利用菜谱、食材、步骤和关系路径，支持替换、搭配、步骤关联等推理型问题。",
  },
  {
    icon: Bot,
    title: "流式问答",
    text: "回答以 Markdown 形式实时输出，适合展示长步骤、菜谱列表和结构化建议。",
  },
  {
    icon: Database,
    title: "知识库可观测",
    text: "可视化查看菜谱、食材、文本块、检索路由和系统状态，调试更直观。",
  },
];

const navLinks = [
  { id: "features", label: "能力" },
  { id: "workflow", label: "流程" },
  { id: "architecture", label: "架构" },
];

const activeSection = ref("features");

function updateActiveSection() {
  const offset = 140;
  let current = navLinks[0].id;

  for (const link of navLinks) {
    const section = document.getElementById(link.id);
    if (section && section.getBoundingClientRect().top <= offset) {
      current = link.id;
    }
  }

  activeSection.value = current;
}

onMounted(() => {
  updateActiveSection();
  window.addEventListener("scroll", updateActiveSection, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", updateActiveSection);
});

const workflow = [
  {
    no: "01",
    title: "连接图数据库",
    text: "从 Neo4j 读取菜谱、食材和烹饪步骤节点。",
  },
  {
    no: "02",
    title: "构建多路索引",
    text: "生成文本分块、向量索引、BM25 索引和图键值索引。",
  },
  {
    no: "03",
    title: "分析用户问题",
    text: "判断问题复杂度、关系密度和推荐检索策略。",
  },
  {
    no: "04",
    title: "生成可读答案",
    text: "整合检索结果，输出 Markdown 格式的烹饪建议。",
  },
];

const architecture = [
  {
    tag: "Neo4j",
    name: "图谱知识层",
    text: "承载菜谱实体、食材依赖、步骤顺序和类别关系。",
  },
  {
    tag: "Milvus",
    name: "向量召回层",
    text: "为语义相似菜谱、模糊意图和自然语言提问提供召回能力。",
  },
  {
    tag: "BM25",
    name: "关键词召回层",
    text: "使用 jieba 分词与 BM25，弥补实体词、菜名和口语表达的精确匹配。",
  },
  {
    tag: "LLM",
    name: "生成整合层",
    text: "基于检索上下文生成结构化、可解释、实用的烹饪回答。",
  },
];
</script>
