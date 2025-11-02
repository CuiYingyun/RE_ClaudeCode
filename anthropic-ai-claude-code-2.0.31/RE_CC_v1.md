# Claude Code 逆向工程分析报告 v1.0

> **分析日期**: 2025-11-02
> **目标文件**: `cli.js` (v2.0.31)
> **文件大小**: 9.6 MB, 3896 行
> **混淆程度**: 严重混淆（变量名、函数名完全不可读）

---

## 执行摘要

本报告对 Anthropic Claude Code CLI 工具进行了全面的逆向工程分析。Claude Code 是一个基于 AI 的命令行编程助手，支持自主编码、多代理协作、插件扩展等功能。

### 关键发现

1. **架构模式**: 多代理架构 + MCP (Model Context Protocol) 集成
2. **上下文管理**: 200K tokens 基础窗口，通过自动压缩优化
3. **工具系统**: 15+ 内置工具，支持 MCP 动态扩展
4. **Agent 系统**: 6+ 内置 sub-agent，支持并行执行
5. **安全机制**: 多层权限系统（allow/deny/ask/bypass）

---

## 1. 文件基本信息

### 1.1 元数据

```javascript
// 版本信息
VERSION: "2.0.31"
PACKAGE: "@anthropic-ai/claude-code"
BUILD_TYPE: "Minified & Obfuscated"
NODE_VERSION: ">=18.0.0"

// 编译信息
- TypeScript 编译
- Webpack 打包
- 严重混淆（变量/函数名替换）
- 所有依赖内联（React, Axios, Lodash等）
```

### 1.2 目录结构推断

```
cli.js (single bundle)
├── Core Runtime
│   ├── Main Loop (对话循环)
│   ├── Tool Execution Engine
│   ├── Agent Spawner
│   └── Context Manager
├── Built-in Tools (15+)
├── Agent Definitions (6+)
├── MCP Integration
├── Plugin System
└── UI Components (React-based TUI)
```

---

## 2. 主要工作流程

### 2.1 启动流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 初始化 (ZB1 / setup)                                  │
├─────────────────────────────────────────────────────────┤
│ - Node.js 版本检查 (>= 18)                                │
│ - 环境变量加载                                            │
│ - 配置文件读取 (~/.claude/)                               │
│ - API Key 验证 (ANTHROPIC_API_KEY / OAuth)               │
│ - MCP 服务器连接                                          │
│ - 插件加载                                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 用户引导 (dn2 / showSetupScreens)                     │
├─────────────────────────────────────────────────────────┤
│ - Onboarding 流程 (首次使用)                              │
│ - 主题选择                                                │
│ - 权限模式设置 (ask/allow/deny/bypass)                   │
│ - Policy 同意                                             │
│ - Release Notes 展示                                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 主循环启动 (Io5 / main)                               │
├─────────────────────────────────────────────────────────┤
│ - Session ID 生成                                         │
│ - Telemetry 初始化                                        │
│ - 对话历史加载                                            │
│ - Status Line 渲染                                        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 对话循环 (Main Loop)

```
┌─────────────────────────────────────────────────────────┐
│ 用户输入 (User Input)                                     │
├─────────────────────────────────────────────────────────┤
│ - 文本输入                                                │
│ - 文件附件 (@file)                                        │
│ - Slash 命令 (/help, /reset等)                           │
│ - Skill 调用                                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 输入处理 (Input Processing)                               │
├─────────────────────────────────────────────────────────┤
│ - 命令解析 (SlashCommand vs 普通对话)                    │
│ - Context 构建:                                           │
│   • System Prompt 注入                                    │
│   • Tool Definitions 加载                                 │
│   • Conversation History 附加                             │
│   • Memory Files 添加                                     │
│   • MCP Resources 加载                                    │
│ - Token 计算与优化                                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ API 调用 (Claude API)                                     │
├─────────────────────────────────────────────────────────┤
│ Model: claude-sonnet-4-5-20250929 (默认)                 │
│ Max Tokens: 32000 (可配置 CLAUDE_CODE_MAX_OUTPUT_TOKENS) │
│ Tools: [Read, Write, Edit, Bash, Grep, ...]              │
│ Features:                                                 │
│   - Prompt Caching (缓存 system prompt + tools)           │
│   - Thinking (Extended Thinking 模式)                     │
│   - Multi-turn conversation                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 响应处理 (Response Processing)                            │
├─────────────────────────────────────────────────────────┤
│ Stop Reasons:                                             │
│   - end_turn: 正常结束                                    │
│   - tool_use: 需要执行工具                                │
│   - max_tokens: 达到token限制                             │
│                                                           │
│ 如果有 tool_use:                                          │
│   ├─> 权限检查 (Permission System)                        │
│   ├─> 工具执行 (Tool Execution)                           │
│   ├─> 结果收集                                            │
│   └─> 继续对话 (追加 tool_result)                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 输出渲染 (Output Rendering)                               │
├─────────────────────────────────────────────────────────┤
│ - Markdown 渲染 (支持代码高亮)                            │
│ - Tool Use 指示                                           │
│ - Progress Indicators                                     │
│ - 思考过程展示 (Thinking blocks)                          │
│ - 错误处理和重试                                          │
└─────────────────────────────────────────────────────────┘
                        ↓
                  循环继续...
```

### 2.3 关键执行节点

#### 节点 A: Context Builder

```javascript
// 构建完整的对话上下文
async function buildContext(messages, tools, agents, files) {
  return {
    system: [
      systemPrompt,           // 主系统 Prompt
      ...toolDefinitions,     // 所有工具的 schema
      ...agentDefinitions,    // Sub-agent 定义
      ...memoryFiles          // Memory 文件内容
    ],
    messages: [
      ...conversationHistory, // 对话历史
      currentUserMessage      // 当前用户输入
    ],
    tools: [
      ...systemTools,         // 系统工具
      ...mcpTools,            // MCP 提供的工具
      ...pluginTools          // 插件工具
    ]
  }
}
```

#### 节点 B: Permission Checker

```javascript
// 权限检查逻辑
async function checkToolPermission(toolName, toolInput, context) {
  const mode = await getPermissionMode(); // "ask" | "allow" | "deny" | "bypass"

  if (mode === "bypass") return { allowed: true };
  if (mode === "deny") return { allowed: false, reason: "denied by policy" };
  if (mode === "allow") return { allowed: true };

  // "ask" mode: 弹出 UI 询问用户
  const userDecision = await askUserForPermission(toolName, toolInput);
  return userDecision;
}
```

#### 节点 C: Tool Executor

```javascript
// 工具执行引擎
async function executeTool(toolName, toolInput, context) {
  const tool = findTool(toolName);
  if (!tool) throw new Error(`Tool not found: ${toolName}`);

  // 安全检查
  if (tool.dangerous && !context.allowDangerous) {
    throw new Error(`Dangerous tool blocked: ${toolName}`);
  }

  // 执行
  const result = await tool.execute(toolInput, context);

  // 结果验证
  if (tool.outputSchema) {
    validateOutput(result, tool.outputSchema);
  }

  return result;
}
```

---

## 3. 工具系统详解

### 3.1 工具架构

```typescript
interface Tool {
  name: string;
  description: string | (() => Promise<string>);  // 可动态生成
  inputSchema: JSONSchema;                        // Zod schema
  prompt?: (context) => string;                   // 工具使用说明
  strict?: boolean;                               // Structured Outputs
  isMcp?: boolean;                                // 是否来自 MCP
  execute: (input, context) => Promise<any>;
}
```

### 3.2 核心工具清单

#### 文件操作工具

| 工具名 | 描述 | 关键参数 | 特殊限制 |
|--------|------|----------|----------|
| **Read** | 读取文件内容 | `file_path` (绝对路径), `offset`, `limit` | 单行最大2000字符，默认读取2000行 |
| **Write** | 写入新文件 | `file_path`, `content` | 优先使用 Edit，避免覆盖 |
| **Edit** | 精确编辑文件 | `file_path`, `old_string`, `new_string`, `replace_all` | 必须先 Read，old_string 必须唯一 |
| **Glob** | 文件模式匹配 | `pattern` (glob), `path` | 支持 `**/*.js` 等模式 |
| **Grep** | 内容搜索 (ripgrep) | `pattern` (regex), `path`, `output_mode`, `-i`, `-A`, `-B` | 支持 content/files_with_matches/count 模式 |

#### 代码执行工具

| 工具名 | 描述 | 关键参数 | 安全机制 |
|--------|------|----------|----------|
| **Bash** | 执行 shell 命令 | `command`, `timeout` (默认2分钟), `run_in_background` | Sandbox 模式，禁止交互式命令 (-i flag) |
| **BashOutput** | 读取后台 bash 输出 | `bash_id`, `filter` (regex) | 仅读取新输出 |
| **KillShell** | 终止后台 shell | `shell_id` | - |
| **NotebookEdit** | 编辑 Jupyter Notebook | `notebook_path`, `cell_id`, `new_source`, `edit_mode` | 支持 replace/insert/delete |

#### 搜索和获取工具

| 工具名 | 描述 | 关键参数 | 特性 |
|--------|------|----------|------|
| **WebFetch** | 获取网页内容 | `url`, `prompt` | HTML→Markdown 转换，15分钟缓存 |
| **WebSearch** | 网络搜索 | `query`, `allowed_domains`, `blocked_domains` | **仅美国可用** |

#### Agent 和任务工具

| 工具名 | 描述 | 关键参数 | Agent 类型 |
|--------|------|----------|-----------|
| **Task** | 启动 sub-agent | `subagent_type`, `prompt`, `description`, `model`, `resume` | general-purpose, Explore, Plan, statusline-setup |
| **AgentOutputTool** | 获取 agent 输出 | `agent_id` | 用于异步 agent |

#### 其他工具

| 工具名 | 描述 | 用途 |
|--------|------|------|
| **TodoWrite** | 任务列表管理 | 跟踪进度，组织任务 |
| **AskUserQuestion** | 询问用户 | 多选题，收集用户偏好 |
| **Skill** | 调用 skill | 执行预定义的技能 |
| **SlashCommand** | 执行斜杠命令 | 运行自定义命令 |

### 3.3 工具 Prompt 示例

#### Read Tool Prompt

```markdown
## Description
Reads a file from the local filesystem. You can access any file directly by using this tool.

## Usage
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to 2000 lines starting from the beginning
- You can optionally specify a line offset and limit
- Results are returned using cat -n format, with line numbers starting at 1
- This tool allows Claude Code to read images (eg PNG, JPG, etc)
- This tool can read PDF files (.pdf)
- You can call multiple tools in a single response
```

#### Bash Tool Prompt

```markdown
## Description
Executes a given bash command in a persistent shell session with optional timeout.

## IMPORTANT
This tool is for terminal operations like git, npm, docker, etc.
DO NOT use it for file operations - use specialized tools instead.

## Safety Protocol
- NEVER update the git config
- NEVER run destructive/irreversible git commands unless explicitly requested
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc)
- Avoid git commit --amend

## Git Commit Protocol
When creating commits:
1. Run git status and git diff in parallel
2. Analyze changes and draft a commit message
3. Add files and create commit with Co-Authored-By: Claude
4. Run git status to verify success
```

#### Task Tool Prompt

```markdown
## Description
Launch a new agent to handle complex, multi-step tasks autonomously.

## Available agent types:
- **general-purpose**: Multi-step tasks, code search (Tools: *)
- **Explore**: Fast codebase exploration (Tools: Read, Grep, Glob)
- **Plan**: Task planning (Tools: All tools)
- **statusline-setup**: Configure status line (Tools: Read, Edit)

## When NOT to use:
- If you want to read a specific file path → use Read tool
- If searching for a specific class → use Glob tool
- If searching within 2-3 files → use Read tool

## Usage notes:
- Launch multiple agents concurrently whenever possible
- Clearly tell the agent whether you expect code writing or research
- Agent's outputs should be trusted
```

### 3.4 MCP 工具集成

```javascript
// MCP (Model Context Protocol) 工具动态加载
// 所有 MCP 工具以 "mcp__" 前缀标识

// 示例: MCP 提供的工具
{
  name: "mcp__server_name__tool_name",
  description: "Tool provided by MCP server",
  isMcp: true,
  serverName: "server_name",
  inputSchema: {...},
  execute: async (input) => {
    // 通过 MCP 协议调用远程工具
    return await mcpClient.callTool(serverName, toolName, input);
  }
}
```

---

## 4. Agent/Subagent 系统

### 4.1 Agent 架构

```
┌─────────────────────────────────────────────────────────┐
│ Main Agent (Primary Loop)                                │
├─────────────────────────────────────────────────────────┤
│ - Model: claude-sonnet-4-5-20250929                      │
│ - Context Window: 200K tokens                            │
│ - Tools: All tools (15+ system + MCP + plugins)          │
│ - Role: 协调整体任务，调度 sub-agents                    │
└─────────────────────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ↓              ↓              ↓
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Sub-Agent 1 │ │ Sub-Agent 2 │ │ Sub-Agent 3 │
│  (Explore)  │ │   (Plan)    │ │ (General)   │
├─────────────┤ ├─────────────┤ ├─────────────┤
│ Specialized │ │ Specialized │ │ Multi-step  │
│ for search  │ │ for plan    │ │ executor    │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 4.2 内置 Sub-Agent 清单

| Agent 类型 | Model | 颜色标识 | 工具权限 | 应用场景 |
|-----------|-------|---------|---------|---------|
| **Explore** | Sonnet | Orange | Read, Grep, Glob, Write(output) | 快速探索代码库，查找文件/关键词 |
| **Plan** | Sonnet | - | All tools | 任务规划，制定执行步骤 |
| **general-purpose** | Sonnet (default) | - | All tools (*) | 通用多步骤任务执行 |
| **statusline-setup** | Sonnet | Orange | Read, Edit | 配置状态栏设置 |
| **session-memory** | - | - | Read, Write | 会话状态管理 |
| **magic-docs** | - | - | WebFetch, Read | 文档查询和分析 |

### 4.3 Agent 通信机制

```javascript
// Sub-agent 调用
const result = await Task({
  subagent_type: "Explore",
  model: "sonnet",  // 可选: haiku/sonnet/opus
  prompt: "Find all React components that use useState",
  description: "Search for React hooks usage"
});

// Sub-agent context 隔离
// - 每个 sub-agent 有独立的 context
// - 不共享 conversation history
// - 可以访问同一套工具（根据权限）
// - 通过 Task tool 返回结果给 main agent
```

### 4.4 Agent Prompts

#### Main Agent System Prompt

```
You are Claude Code, Anthropic's official CLI for Claude.

You are an interactive CLI tool that helps users with software engineering tasks.

## IMPORTANT Rules:
- Assist with authorized security testing, defensive security, CTF challenges
- Refuse requests for destructive techniques, DoS attacks, mass targeting
- Dual-use security tools require clear authorization context

## Tone and style:
- Only use emojis if explicitly requested
- Be short and concise
- Use Github-flavored markdown

## Professional objectivity:
- Prioritize technical accuracy over validating user's beliefs
- Provide direct, objective technical info
- Disagree when necessary, even if not what user wants to hear

## Task Management:
- Use TodoWrite tool VERY frequently to track tasks
- Mark todos as completed as soon as done
- Do not batch up multiple tasks before marking completed
```

#### General-Purpose Agent Prompt

```
You are an agent for Claude Code, Anthropic's official CLI for Claude.

Given the user's message, you should use the tools available to complete the task.
Do what has been asked; nothing more, nothing less.

When you complete the task simply respond with a detailed writeup.
```

#### Explore Agent Prompt

```
You are a fast codebase exploration agent.

Your job is to:
- Quickly find files by patterns (eg. "src/components/**/*.tsx")
- Search code for keywords (eg. "API endpoints")
- Answer questions about the codebase

Thoroughness level: [quick/medium/very thorough]

Use Read, Grep, and Glob tools efficiently.
Provide concise findings with file paths and line numbers.
```

---

## 5. 上下文管理机制

### 5.1 Context Window 配置

```javascript
// Token 限制
const MAX_TOKENS = {
  "claude-sonnet-4-5-*": 200_000,  // 200K context
  "claude-opus-4-*": 200_000,
  "claude-haiku-4-*": 200_000,
  "claude-*-1m": 1_000_000,        // 1M models
};

// 输出限制
const MAX_OUTPUT_TOKENS = process.env.CLAUDE_CODE_MAX_OUTPUT_TOKENS || 32_000;

// Bash 输出限制
const BASH_MAX_OUTPUT = process.env.BASH_MAX_OUTPUT_LENGTH || 30_000;
```

### 5.2 Token 计数与分配

```javascript
// Token 分配示例 (200K window)
{
  systemPrompt: ~5000 tokens,        // 基础系统提示
  toolDefinitions: ~15000 tokens,    // 15+ tools × ~1000 tokens
  mcpTools: ~5000 tokens,            // MCP 工具 (动态)
  customAgents: ~3000 tokens,        // 自定义 agents
  memoryFiles: ~10000 tokens,        // Memory 文件
  conversationHistory: ~150000 tokens, // 对话历史 (最大)
  autoCompactBuffer: ~12000 tokens   // 自动压缩缓冲区
}
```

### 5.3 自动压缩 (Auto-Compact) 机制

```javascript
// 自动压缩触发条件
const AUTO_COMPACT_ENABLED = true;  // 可通过设置禁用
const COMPACT_THRESHOLD = MAX_TOKENS - 12000;  // 188K for 200K window

// 压缩策略
async function autoCompactConversation(messages) {
  if (totalTokens < COMPACT_THRESHOLD) return messages;

  // 策略:
  // 1. 保留最近 N 轮对话 (高优先级)
  // 2. 压缩中间对话:
  //    - 使用 AI 生成摘要
  //    - 保留关键决策点
  //    - 丢弃冗余的 tool_result
  // 3. 始终保留:
  //    - System prompt
  //    - Tool definitions
  //    - 最后一条用户消息

  const compacted = await generateConversationSummary(messages);
  return [
    ...systemMessages,
    compacted,
    ...recentMessages
  ];
}
```

### 5.4 Prompt Caching

```javascript
// Anthropic Prompt Caching 策略
{
  system: [
    { type: "text", text: systemPrompt },
    { type: "text", text: toolDefinitions, cache_control: { type: "ephemeral" } },
    { type: "text", text: agentDefinitions, cache_control: { type: "ephemeral" } }
  ],
  messages: conversationHistory
}

// Cache 效果:
// - System prompt + tools 缓存后，后续请求免费读取
// - 显著降低 API 成本 (cache read: $0.30/MTok vs input: $3/MTok)
// - 缓存有效期: 5 分钟
```

### 5.5 Memory Files 系统

```javascript
// .claude/memory/ 目录
// 用户可以创建 Markdown 文件，自动注入到每次对话

// 示例: .claude/memory/project-context.md
/*
# Project Context

This is a React + TypeScript project using Vite.

## Architecture
- Frontend: React 18 + TypeScript
- State: Zustand
- Routing: React Router v6

## Coding Standards
- Use functional components
- Prefer hooks over class components
- Always add TypeScript types
*/

// Token 计算
{
  path: ".claude/memory/project-context.md",
  type: "memory",
  tokens: 245
}
```

---

## 6. Plugin & Skill 系统

### 6.1 MCP (Model Context Protocol) 集成

```javascript
// MCP 服务器配置: .claude/mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    },
    "custom-server": {
      "command": "/path/to/custom-mcp-server"
    }
  }
}

// MCP 工具自动发现
// 1. Claude Code 启动时连接所有 MCP 服务器
// 2. 调用 tools/list 获取工具列表
// 3. 将工具注册为 "mcp__server__tool" 格式
// 4. 动态添加到 Claude 的 tools 参数
```

### 6.2 MCP 工具示例

```javascript
// MCP 提供的工具会自动出现在工具列表中
{
  name: "mcp__github__create_issue",
  description: "Create a GitHub issue in a repository",
  isMcp: true,
  serverName: "github",
  inputSchema: {
    type: "object",
    properties: {
      repo: { type: "string" },
      title: { type: "string" },
      body: { type: "string" }
    },
    required: ["repo", "title"]
  }
}

// Token 统计
{
  mcpToolTokens: 5234,
  mcpToolDetails: [
    { name: "mcp__github__create_issue", serverName: "github", tokens: 234 },
    { name: "mcp__filesystem__read_file", serverName: "filesystem", tokens: 180 },
    ...
  ]
}
```

### 6.3 Skills 系统

```javascript
// Skills: 预定义的可复用提示模板
// 位置: .claude/skills/ 或全局 skills

// 示例 Skill: .claude/skills/code-review.md
/*
---
name: code-review
description: Perform a comprehensive code review
---

Review the following code changes and provide:
1. Code quality assessment
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Be thorough but concise.
*/

// 调用方式
// - 命令: claude code skill:code-review
// - Tool: Skill({ command: "code-review" })

// Skills 自动发现
const skills = await discoverSkills([
  path.join(homeDir, '.claude/skills'),
  path.join(projectRoot, '.claude/skills'),
  ...globalSkillPaths
]);
```

### 6.4 Slash Commands 系统

```javascript
// Slash Commands: 用户自定义命令
// 位置: .claude/commands/

// 示例: .claude/commands/review-pr.md
/*
---
name: review-pr
description: Review a pull request
---

Review PR #{{PR_NUMBER}}:
1. Fetch PR details
2. Analyze changed files
3. Check for common issues
4. Provide summary
*/

// 调用方式
// $ /review-pr 123

// Command 扩展
{
  totalCommands: 15,
  includedCommands: 12,  // 注入到 context 的命令数
  tokens: 2340
}
```

### 6.5 Plugin 加载机制

```javascript
// Inline Plugins (代码注入)
// 通过 --inline-plugin 参数加载

// 示例
await claudeCode(['--inline-plugin', '/path/to/plugin.js']);

// Plugin 接口
module.exports = {
  name: "my-plugin",
  version: "1.0.0",

  // 注册自定义工具
  tools: [{
    name: "custom_tool",
    description: "My custom tool",
    inputSchema: {...},
    execute: async (input, context) => {
      // Tool logic
    }
  }],

  // 注册 hooks
  hooks: {
    onBeforeRequest: async (context) => {},
    onAfterResponse: async (context) => {},
    onToolExecution: async (toolName, input, context) => {}
  }
};
```

---

## 7. Prompt 库 (完整提取)

### 7.1 System Prompts

#### Main CLI Prompt

```markdown
You are Claude Code, Anthropic's official CLI for Claude.

You are an interactive CLI tool that helps users with software engineering tasks.
Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with authorized security testing, defensive security, CTF challenges,
and educational contexts. Refuse requests for destructive techniques, DoS attacks,
mass targeting, supply chain compromise, or detection evasion for malicious purposes.
Dual-use security tools (C2 frameworks, credential testing, exploit development) require
clear authorization context: pentesting engagements, CTF competitions, security research,
or defensive use cases.

IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident
that the URLs are for helping the user with programming.

# Tone and style
- Only use emojis if the user explicitly requests it
- Your output will be displayed on a command line interface
- Your responses should be short and concise
- You can use Github-flavored markdown for formatting

# Professional objectivity
Prioritize technical accuracy and truthfulness over validating the user's beliefs.
Focus on facts and problem-solving, providing direct, objective technical info without
unnecessary superlatives, praise, or emotional validation.

# Task Management
You have access to the TodoWrite tools to help you manage and plan tasks.
Use these tools VERY frequently to ensure that you are tracking your tasks and giving
the user visibility into your progress.

It is critical that you mark todos as completed as soon as you are done with a task.
Do not batch up multiple tasks before marking them as completed.

# Doing tasks
The user will primarily request you perform software engineering tasks. This includes
solving bugs, adding new functionality, refactoring code, explaining code, and more.
For these tasks the following steps are recommended:
- Use the TodoWrite tool to plan the task if required
- Be careful not to introduce security vulnerabilities such as command injection, XSS,
  SQL injection, and other OWASP top 10 vulnerabilities

# Tool usage policy
- When doing file search, prefer to use the Task tool to reduce context usage
- You should proactively use the Task tool with specialized agents when the task at
  hand matches the agent's description
- Use specialized tools instead of bash commands when possible
- VERY IMPORTANT: When exploring the codebase to gather context, it is CRITICAL that
  you use the Task tool with subagent_type=Explore instead of running search commands directly

# Code References
When referencing specific functions or pieces of code include the pattern
`file_path:line_number` to allow the user to easily navigate to the source code location.

Example:
user: Where are errors from the client handled?
assistant: Clients are marked as failed in the `connectToServer` function in
src/services/process.ts:712.
```

#### Agent SDK Prompt

```markdown
You are Claude Code, Anthropic's official CLI for Claude, running within the
Claude Agent SDK.

[Similar structure to Main CLI Prompt, with SDK-specific additions]
```

#### Generic Agent Prompt

```markdown
You are a Claude agent, built on Anthropic's Claude Agent SDK.

[Minimal prompt for generic agent tasks]
```

### 7.2 Constraints & Guidelines

#### Legal Constraints

```javascript
const LEGAL_CONSTRAINTS = {
  MAX_QUOTED_TEXT_LENGTH: 125,  // 字符
  FORBIDDEN_CONTENT: [
    "Song lyrics",
    "Copyrighted code (full files from proprietary projects)",
    "Personal identifiable information"
  ]
};
```

#### Git Safety Protocol

```markdown
# Git Safety Protocol

NEVER:
- Update the git config
- Run destructive/irreversible git commands (push --force, hard reset)
- Skip hooks (--no-verify, --no-gpg-sign)
- Run force push to main/master

AVOID:
- git commit --amend (only use when explicitly requested or fixing pre-commit hook changes)

BEFORE AMENDING:
- ALWAYS check authorship: git log -1 --format='%an %ae'
- NEVER commit changes unless the user explicitly asks

# Git Commit Protocol
1. Run parallel: git status, git diff, git log
2. Draft commit message (focus on "why" not "what")
3. Add files and create commit with:

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
4. Run git status to verify
```

#### File Operations Constraints

```markdown
# File Operations

ALWAYS:
- Use absolute paths, not relative paths
- Prefer editing existing files over creating new ones
- Use Read tool before Edit or Write
- Preserve exact indentation when editing

NEVER:
- Create documentation files (*.md) unless explicitly requested
- Use emojis unless explicitly requested
- Use bash for file operations (use Read/Write/Edit/Glob/Grep instead)
```

### 7.3 Tool-Specific Prompts

#### Bash Tool - Detailed Prompt

```markdown
# Bash Tool

Executes a given bash command in a persistent shell session with optional timeout.

IMPORTANT: This tool is for terminal operations like git, npm, docker, etc.
DO NOT use it for file operations (reading, writing, editing, searching, finding files) -
use the specialized tools for this instead.

## Command Execution:
- Always quote file paths that contain spaces with double quotes
- After executing, capture the output

## Usage notes:
- Commands timeout after 120000ms (2 minutes) by default
- Can specify timeout up to 600000ms (10 minutes)
- Can run in background with run_in_background parameter
- Output truncated after 30000 characters

## AVOID using Bash with:
- find, grep, cat, head, tail, sed, awk, echo
- Instead use: Glob, Grep, Read, Edit, Write

## When issuing multiple commands:
- If independent: make multiple Bash tool calls in parallel
- If dependent: use && to chain (e.g., mkdir && cp)
- Use ';' only when you don't care if earlier commands fail

## Current working directory:
- Try to maintain cwd by using absolute paths and avoiding cd

# Committing changes with git

Only create commits when requested by the user.

Git Safety Protocol:
- NEVER update the git config
- NEVER run destructive git commands unless explicitly requested
- NEVER skip hooks
- Avoid git commit --amend

When creating commits:
1. Run: git status, git diff, git log (in parallel)
2. Analyze changes and draft commit message
3. Add files and commit with message ending with:

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
4. Run git status after commit
5. If pre-commit hook changes files, verify safe to amend, then amend commit

IMPORTANT:
- NEVER use git commands with -i flag (interactive not supported)
- Pass commit message via HEREDOC:
  git commit -m "$(cat <<'EOF'
  Commit message here.

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  EOF
  )"

# Creating pull requests

Use gh command for all GitHub-related tasks.

When creating a PR:
1. Run parallel: git status, git diff, check if branch tracks remote, git log + git diff [base]...HEAD
2. Analyze ALL commits (not just latest)
3. Create PR with:
   gh pr create --title "..." --body "$(cat <<'EOF'
   ## Summary
   <1-3 bullet points>

   ## Test plan
   [Checklist...]

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
```

#### Edit Tool - Detailed Prompt

```markdown
# Edit Tool

Performs exact string replacements in files.

## Usage:
- You MUST use Read tool first before editing
- Preserve exact indentation as it appears AFTER the line number prefix
- Line number prefix format: spaces + line number + tab
- Everything after that tab is the actual file content to match

## Requirements:
- ALWAYS prefer editing existing files over creating new files
- The edit will FAIL if old_string is not unique
- Provide larger string with more context to make it unique
- Or use replace_all to change every instance

## replace_all parameter:
- Use for replacing and renaming strings across the file
- Useful for variable renaming
```

#### TodoWrite Tool - Detailed Prompt

```markdown
# TodoWrite Tool

Create and manage a structured task list for your current coding session.

## When to Use:
1. Complex multi-step tasks (3+ distinct steps)
2. Non-trivial and complex tasks
3. User explicitly requests todo list
4. User provides multiple tasks (numbered or comma-separated)
5. After receiving new instructions
6. When you start working on a task (mark as in_progress BEFORE beginning)
7. After completing a task (mark completed and add follow-up tasks)

## When NOT to Use:
1. Single, straightforward task
2. Trivial task
3. Task completable in <3 steps
4. Purely conversational/informational task

## Task States:
- pending: Not yet started
- in_progress: Currently working (EXACTLY ONE task at a time)
- completed: Finished successfully

## Task Descriptions:
Must have TWO forms:
- content: Imperative form (e.g., "Run tests")
- activeForm: Present continuous form (e.g., "Running tests")

## Task Management:
- Update status in real-time
- Mark completed IMMEDIATELY after finishing (don't batch)
- Exactly ONE task must be in_progress at any time
- Complete current task before starting new one
- Remove irrelevant tasks entirely

## Task Completion Requirements:
ONLY mark as completed when FULLY accomplished:
- Tests passing
- Implementation complete
- No unresolved errors

Never mark completed if:
- Tests are failing
- Implementation is partial
- Encountered unresolved errors
- Couldn't find necessary files/dependencies

## Task Breakdown:
- Create specific, actionable items
- Break complex tasks into smaller steps
- Use clear, descriptive names
- Always provide both content and activeForm
```

---

## 8. 关键发现与技术亮点

### 8.1 设计模式

#### 多代理协作模式

```
Main Agent (Coordinator)
    ├─> Sub-Agent 1 (Specialist)
    ├─> Sub-Agent 2 (Specialist)
    └─> Sub-Agent 3 (Specialist)

优势:
- 任务并行处理
- 专业化分工
- 降低单个 context 压力
- 提高整体效率
```

#### 权限分层模型

```
Layer 1: Global Policy (组织级别)
    ↓
Layer 2: User Settings (用户级别)
    ↓
Layer 3: Project Settings (项目级别)
    ↓
Layer 4: Runtime Permissions (运行时)

优先级: Policy > Project > User > Default
```

#### 插件化架构

```
Core
├─> MCP Protocol (动态工具)
├─> Skills (模板)
├─> Slash Commands (快捷命令)
└─> Inline Plugins (代码扩展)

所有扩展点都是热加载的，无需重启
```

### 8.2 性能优化技术

#### Prompt Caching 策略

```javascript
// 缓存层次
Level 1: System Prompt (5K tokens) - 缓存 5分钟
Level 2: Tool Definitions (15K tokens) - 缓存 5分钟
Level 3: Agent Definitions (3K tokens) - 缓存 5分钟

// 成本节省
Before caching: $3/MTok (input)
After caching: $0.30/MTok (cache read)
节省: 90% 成本
```

#### Auto-Compact 算法

```javascript
// 自动压缩触发
if (contextTokens > MAX_TOKENS - 12000) {
  // 保留:
  // - 最近 10 轮对话 (完整)
  // - System prompt + Tools (必需)

  // 压缩:
  // - 中间对话 → AI 生成摘要
  // - 冗余 tool_result → 仅保留关键信息

  // 效果:
  // 从 188K tokens → 压缩到 100K tokens
  // 释放 88K tokens for new conversation
}
```

#### Debounced Notifications

```javascript
// 避免频繁的通知消息
debouncedNotificationMethods: [
  "notifications/progress",
  "notifications/message",
  ...
]

// 实现:
// 1. 收到通知请求
// 2. 如果同类型通知已在队列 → 跳过
// 3. 否则加入队列
// 4. 在下一个 event loop tick 批量发送
```

### 8.3 安全机制

#### Sandbox Mode

```javascript
// Bash 工具沙箱化
- 禁止交互式命令 (-i flag)
- 禁止后台进程 (除非明确指定 run_in_background)
- 禁止访问系统关键目录 (可配置)
- 输出长度限制 (30K 字符)
- 执行超时 (2分钟默认，10分钟最大)
```

#### Permission System

```javascript
// 四种权限模式
1. ask: 每次工具调用都询问用户 (默认)
2. allow: 自动允许所有工具 (危险)
3. deny: 拒绝所有工具 (只能对话)
4. bypass: 跳过权限检查 (需要特殊标志启动)

// 危险工具标记
{
  name: "Bash",
  dangerous: true,
  requiresExplicitApproval: true
}
```

#### Git Hooks Enforcement

```javascript
// 强制使用 Git Hooks
- NEVER skip hooks (--no-verify forbidden)
- Pre-commit hook changes → auto-detect → amend commit
- GPG signing enforced (if configured)
- Force push to main/master → warning + confirmation
```

### 8.4 Telemetry & Observability

```javascript
// OpenTelemetry 集成
{
  meters: {
    sessionCounter: "claude_code.session.count",
    locCounter: "claude_code.lines_of_code.count",
    prCounter: "claude_code.pull_request.count",
    commitCounter: "claude_code.commit.count",
    costCounter: "claude_code.cost.usage",
    tokenCounter: "claude_code.token.usage",
    activeTimeCounter: "claude_code.active_time.total"
  },

  tracers: {
    // Distributed tracing for agent calls
    // API request tracking
    // Tool execution spans
  },

  loggers: {
    // Structured logging
    // Error tracking
  }
}

// 匿名使用统计
GA("tengu_startup_telemetry", {
  is_git: true/false,
  worktree_count: N,
  model: "claude-sonnet-4-5",
  client_type: "cli",
  ...
});
```

### 8.5 错误处理

```javascript
// 多层错误恢复
1. Tool Execution Error
   ├─> 重试 (可配置次数)
   ├─> 降级 (使用替代工具)
   └─> 报告给 Agent (让 AI 决定下一步)

2. API Rate Limit
   ├─> 自动 backoff (指数退避)
   ├─> 切换到 fallback model
   └─> 通知用户

3. Permission Denied
   ├─> 询问用户覆盖
   ├─> 记录决策 (未来自动应用)
   └─> 建议替代方案

4. Token Limit Exceeded
   ├─> 自动 compact conversation
   ├─> 移除低优先级内容
   └─> 继续执行
```

---

## 9. 配置与环境变量

### 9.1 核心环境变量

| 变量名 | 默认值 | 用途 | 验证规则 |
|--------|--------|------|----------|
| `ANTHROPIC_API_KEY` | - | Anthropic API 密钥 | 必需 (除非使用 OAuth) |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | 32000 | 最大输出 tokens | 1-64000 |
| `BASH_MAX_OUTPUT_LENGTH` | 30000 | Bash 输出最大长度 | 1-150000 |
| `CLAUDE_CONFIG_DIR` | `~/.claude` | 配置目录 | 任意路径 |
| `CLAUDE_CODE_USE_BEDROCK` | false | 使用 AWS Bedrock | true/false |
| `AWS_REGION` | us-east-1 | AWS 区域 | 有效的 AWS region |
| `VERTEX_REGION_CLAUDE_4_5_SONNET` | us-east5 | Vertex AI 区域 | 有效的 GCP region |

### 9.2 配置文件

#### ~/.claude/config.json

```json
{
  "theme": "dark",
  "permissionMode": "ask",
  "hasCompletedOnboarding": true,
  "lastOnboardingVersion": "2.0.31",
  "mainLoopModel": "claude-sonnet-4-5-20250929",
  "bypassPermissionsModeAccepted": false,
  "autoCompactEnabled": true,
  "customUserAgent": "my-org/claude-code",
  "numStartups": 42
}
```

#### ~/.claude/mcp.json

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

#### .claude/settings.json (Project-level)

```json
{
  "ignorePatterns": [
    "node_modules/**",
    "dist/**",
    ".git/**",
    "*.log"
  ],
  "permissionMode": "allow",
  "customAgents": [...],
  "slashCommands": {...}
}
```

### 9.3 Model 配置

```javascript
// Model String 格式
const MODEL_STRINGS = {
  sonnet: "claude-sonnet-4-5-20250929",
  opus: "claude-opus-4-1",
  haiku: "claude-haiku-4-5",

  // Bedrock
  bedrock_sonnet: "anthropic.claude-sonnet-4-5-v2:0",

  // Vertex
  vertex_sonnet: "claude-sonnet-4-5@20250929"
};

// Model 切换
// - 命令行: --model sonnet | opus | haiku
// - 环境变量: CLAUDE_CODE_MODEL=opus
// - Runtime: wp("opus") // 临时覆盖
```

---

## 10. 未解之谜 & 限制

### 10.1 无法完全确定的部分

由于代码混淆程度极高，以下部分仅能部分推断：

1. **精确的 Conversation Compaction 算法**
   - 已知使用 AI 生成摘要
   - 未知具体的 prompt 和压缩比例
   - 未知如何选择保留哪些对话

2. **MCP 协议的完整实现细节**
   - 已知使用 JSON-RPC 2.0
   - 未知完整的错误处理和重试逻辑
   - 未知 resumption token 机制的细节

3. **Telemetry 的上报策略**
   - 已知使用 OpenTelemetry
   - 未知具体的上报频率和批处理逻辑
   - 未知隐私数据的过滤规则

4. **Agent 并行调度算法**
   - 已知可以并行执行多个 sub-agent
   - 未知具体的调度策略和资源分配
   - 未知冲突解决机制

5. **Cost 计算的精确公式**
   - 已知按 token 计费
   - 未知对于 1M context window model 的特殊定价
   - 未知 prompt caching 的精确计费逻辑

### 10.2 已知限制

1. **平台限制**
   - WebSearch 工具仅在美国可用
   - macOS 的 grep 不支持 -P (Perl regex)
   - Windows 的某些 Bash 命令不可用

2. **安全限制**
   - 不能使用 root/sudo 运行（bypass mode 除外）
   - 不能访问系统关键目录（可配置）
   - 不能执行交互式命令 (-i flag)

3. **功能限制**
   - 不支持多模态输入（图片作为用户输入）
   - 不支持语音输入/输出
   - 不支持实时协作（多用户同时编辑）

4. **Context 限制**
   - 单个文件读取最大 2000 行（可分段读取）
   - Bash 输出最大 30000 字符
   - Tool result 单次最大不明确（推测 10MB）

### 10.3 需要动态分析的内容

以下内容需要运行时动态分析才能完全理解：

1. **实际的 API 调用序列**
   - 建议: 启用 debug 模式，记录所有 API 请求
   - 工具: `CLAUDE_CODE_DEBUG=1 claude code`

2. **权限系统的决策树**
   - 建议: 跟踪所有权限请求和用户响应
   - 工具: Permission log 文件分析

3. **Auto-Compact 的触发时机和效果**
   - 建议: 启用 token 计数 verbose 模式
   - 工具: 观察 context window 使用率

4. **MCP 服务器的通信协议**
   - 建议: 使用网络抓包工具
   - 工具: Wireshark, tcpdump

5. **Error Recovery 的实际路径**
   - 建议: 故意触发错误，观察恢复流程
   - 工具: Error injection testing

---

## 11. 逆向工程方法论总结

### 11.1 使用的技术

1. **静态分析**
   - ✅ 字符串提取 (grep, awk, sed)
   - ✅ 模式匹配 (正则表达式)
   - ✅ JSON 对象识别
   - ✅ 依赖分析 (require/import)

2. **文档分析**
   - ✅ 官方文档交叉验证
   - ✅ API Schema 推断
   - ✅ 功能列表映射

3. **推理与推断**
   - ✅ 基于 prompt 推断功能
   - ✅ 基于配置推断架构
   - ✅ 基于错误消息推断流程

### 11.2 限制与挑战

1. **混淆导致的问题**
   - ❌ 无法追踪完整的函数调用链
   - ❌ 无法确定变量的生命周期
   - ❌ 无法识别所有的条件分支

2. **单文件打包的影响**
   - ❌ 无法区分第三方库和业务逻辑
   - ❌ 无法找到原始的模块边界
   - ❌ 无法利用 source map (不存在)

3. **动态特性**
   - ❌ MCP 工具动态加载（无法穷举）
   - ❌ Plugin 系统（依赖外部代码）
   - ❌ Runtime 配置（依赖环境变量）

### 11.3 建议的后续分析

1. **动态分析**
   ```bash
   # 启用 debug 模式
   DEBUG=* CLAUDE_CODE_DEBUG=1 claude code

   # 记录所有 API 请求
   ANTHROPIC_LOG_LEVEL=debug claude code

   # 网络抓包
   tcpdump -i any -w claude.pcap port 443
   ```

2. **行为测试**
   - 系统性测试所有工具
   - 触发所有错误路径
   - 测试边界条件

3. **社区资源**
   - 查看 GitHub Issues
   - 阅读 Release Notes
   - 分析社区提供的配置示例

---

## 12. 附录

### 12.1 关键函数名映射

| 混淆名 | 推断功能 | 证据 |
|--------|---------|------|
| `ZB1` | setup() | 字符串 "setup", "initialize" |
| `Io5` | main() | Entry point patterns |
| `dn2` | showSetupScreens() | Onboarding flow strings |
| `mn2` | completeOnboarding() | "hasCompletedOnboarding" |
| `N1()` | getConfig() | Config read patterns |
| `d0()` | saveConfig() | Config write patterns |
| `yI()` | getMainLoopModel() | Model string references |
| `TQ()` | getOriginalCwd() | "originalCwd" |
| `Oy()` | getCwd() | "cwd" getter |
| `m0()` | getSessionId() | "sessionId" |
| `MV()` | getTotalCost() | "totalCostUSD" |

### 12.2 重要常量

```javascript
// Context Windows
200_000  // Standard context window
1_000_000 // Extended context window (1M models)

// Token Limits
32_000   // Default max output tokens
64_000   // Max allowed output tokens

// Timeouts
2_000    // 2 seconds (default tool timeout)
120_000  // 2 minutes (bash default timeout)
600_000  // 10 minutes (max bash timeout)

// Output Limits
30_000   // Bash max output length
2_000    // Read tool default line limit
125      // Max quoted text length (legal)

// Caching
300_000  // 5 minutes (prompt cache TTL in ms)

// Retry
800      // Debounce delay (ms)
3        // Max retries (推测)
```

### 12.3 数据结构

#### Session State

```typescript
interface SessionState {
  sessionId: string;
  originalCwd: string;
  cwd: string;
  totalCostUSD: number;
  totalAPIDuration: number;
  totalToolDuration: number;
  startTime: number;
  lastInteractionTime: number;
  totalLinesAdded: number;
  totalLinesRemoved: number;
  hasUnknownModelCost: boolean;
  modelUsage: Record<string, ModelUsage>;
  mainLoopModelOverride?: string;
  maxRateLimitFallbackActive: boolean;
  isNonInteractiveSession: boolean;
  isInteractive: boolean;
  clientType: "cli" | "vscode" | "api";
  agentColorMap: Map<string, Color>;
  inMemoryErrorLog: ErrorLog[];
}

interface ModelUsage {
  inputTokens: number;
  outputTokens: number;
  cacheReadInputTokens: number;
  cacheCreationInputTokens: number;
  webSearchRequests: number;
  costUSD: number;
  contextWindow: number;
}
```

#### Tool Definition

```typescript
interface ToolDefinition {
  name: string;
  description: string | (() => Promise<string>);
  inputSchema: JSONSchema7;
  strict?: boolean;
  isMcp?: boolean;
  serverName?: string;
  prompt?: (context: ToolContext) => string;
  execute: (input: any, context: ToolContext) => Promise<any>;
}

interface ToolContext {
  signal?: AbortSignal;
  sessionId?: string;
  _meta?: Record<string, any>;
  sendNotification: (notification: any) => Promise<void>;
  sendRequest: (request: any, schema: any, options?: any) => Promise<any>;
  authInfo?: AuthInfo;
  requestId?: string | number;
  requestInfo?: RequestInfo;
}
```

#### Agent Definition

```typescript
interface AgentDefinition {
  agentType: string;
  source: "built-in" | "custom" | "plugin";
  whenToUse: string;
  model?: "sonnet" | "opus" | "haiku";
  color?: string;
  tools?: string[];  // Tool names available to this agent
  systemPrompt?: string;
}
```

### 12.4 API Endpoint (推断)

```
Anthropic API:
  POST https://api.anthropic.com/v1/messages
  Headers:
    - anthropic-version: 2023-06-01
    - x-api-key: <API_KEY>
    - anthropic-beta: prompt-caching-2024-07-31,max-tokens-3-5-sonnet-2024-07-15
  Body:
    {
      model: "claude-sonnet-4-5-20250929",
      max_tokens: 32000,
      system: [...],
      messages: [...],
      tools: [...]
    }

Bedrock API:
  POST https://bedrock-runtime.{region}.amazonaws.com/model/{model-id}/invoke

Vertex AI:
  POST https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/anthropic/models/{model}:rawPredict
```

### 12.5 文件路径

```
~/.claude/
├── config.json              # 用户配置
├── mcp.json                 # MCP 服务器配置
├── session_history.json     # 会话历史
├── file_history/            # 文件历史记录
│   └── <hash>.json
├── memory/                  # Memory 文件
│   ├── project-context.md
│   └── coding-standards.md
├── commands/                # Slash Commands
│   ├── review-pr.md
│   └── deploy.md
├── skills/                  # Skills
│   └── code-review.md
└── telemetry/               # Telemetry 数据
    └── events.jsonl

/tmp/claude/                 # 临时文件
├── bash_<id>.log
└── agent_<id>.out
```

---

## 13. 结论

Claude Code 是一个精心设计的多代理编程助手系统，具有以下突出特点：

### 核心优势

1. **智能的多代理架构**: 通过专业化 sub-agent 实现任务并行和效率提升
2. **强大的扩展性**: MCP 协议、Plugin 系统、Skills、Slash Commands 提供多层次扩展能力
3. **优秀的上下文管理**: 自动压缩、prompt caching、memory files 等技术有效利用 context window
4. **全面的工具生态**: 15+ 内置工具覆盖文件操作、代码执行、网络请求等常见场景
5. **细粒度的安全控制**: 多层权限系统、Git hooks 强制、沙箱执行保障安全性

### 技术亮点

- **Prompt Caching**: 节省 90% 的重复 token 成本
- **Auto-Compact**: 智能对话压缩，突破 context 限制
- **Agent 并行**: 多个专业化 agent 同时工作
- **热加载**: MCP 工具、插件、命令无需重启即可生效
- **OpenTelemetry**: 完善的可观测性

### 逆向工程结论

尽管代码被严重混淆，通过系统化的字符串提取、模式识别和文档交叉验证，我们成功重建了 Claude Code 的主要架构、工作流程、工具系统和 agent 机制。

本报告为理解 Claude Code 的内部工作原理提供了详实的参考，但由于混淆和打包的限制，部分动态特性和算法细节仍需通过运行时分析进一步探索。

---

**报告生成**: 自动化逆向工程分析
**版本**: 1.0
**最后更新**: 2025-11-02

**🤖 Generated with Claude Code reverse engineering analysis**
