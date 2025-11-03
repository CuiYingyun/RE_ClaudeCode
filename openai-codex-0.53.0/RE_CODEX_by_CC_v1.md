# OpenAI Codex CLI 逆向工程分析报告

**分析日期:** 2025-11-03
**二进制文件:** vendor/aarch64-apple-darwin/codex/codex
**架构:** Mach-O 64-bit executable arm64
**大小:** 34MB
**编程语言:** Rust
**分析者:** Claude Code

---

## 执行摘要

OpenAI Codex CLI 是一个用 Rust 构建的自主编码助手工具，能够根据用户描述自动生成和修改代码。该二进制实现了一个复杂的代理系统，包含虚拟工具、沙箱安全机制、上下文管理和基于 JSONRPC 的通信协议。

**核心发现:**
- **工具是虚拟的**: 所有工具（apply_patch、read_file 等）都是内部 Rust 处理器，而非外部系统命令
- **模型:** 声称基于 "GPT-5"（可能是营销名称，实际为高级 GPT-4 或 o1 模型）
- **架构:** 客户端-服务器模式，本地 CLI + 远程 OpenAI API
- **安全:** 多层沙箱（macOS 使用 Seatbelt，Linux 使用 Landlock）
- **协议:** 通过 HTTP/SSE 的 JSONRPC 双向通信

---

## 目录

1. [架构概览](#1-架构概览)
2. [工具系统详解](#2-工具系统详解)
3. [完整的系统提示词](#3-完整的系统提示词)
4. [主要工作流程](#4-主要工作流程)
5. [上下文管理](#5-上下文管理)
6. [安全与沙箱系统](#6-安全与沙箱系统)
7. [JSONRPC 协议](#7-jsonrpc-协议)
8. [配置参考](#8-配置参考)

---

## 1. 架构概览

### 1.1 整体架构图

```
┌────────────────────────────────────────────────────────────┐
│                    用户界面层                               │
│         (TUI - 终端界面 / Exec 模式 - 无头执行)             │
├────────────────────────────────────────────────────────────┤
│                   JSONRPC 客户端/服务器                     │
│          (与 OpenAI 后端的双向通信)                         │
├────────────────────────────────────────────────────────────┤
│                   消息处理器                                │
│          (事件处理、状态管理)                               │
├────────────────────────────────────────────────────────────┤
│              会话与上下文管理器                             │
│   (rollout.jsonl, history.jsonl, 会话管理)                 │
├────────────────────────────────────────────────────────────┤
│                    工具执行层                               │
│  ┌──────────────┬──────────────┬──────────────────────┐   │
│  │   内置工具   │  MCP 工具    │   Shell 执行         │   │
│  │   处理器     │  (外部)      │   (unified_exec)     │   │
│  └──────────────┴──────────────┴──────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│              审批与沙箱安全层                               │
│      (风险评估、权限控制、沙箱隔离)                         │
├────────────────────────────────────────────────────────────┤
│                 认证层                                      │
│      (ChatGPT OAuth、API Key、钥匙串存储)                   │
├────────────────────────────────────────────────────────────┤
│              OpenAI API / 后端服务                          │
│   https://chatgpt.com/backend-api/codex                   │
│   https://api.openai.com/v1/responses/chat/completions    │
└────────────────────────────────────────────────────────────┘
```

### 1.2 二进制结构

**段信息:**
- `__TEXT` (33.8MB): 代码、常量、字符串、异常表
  - `__text`: 23.4MB 可执行代码
  - `__const`: 6.7MB 常量数据
  - `__cstring`: 127KB C 字符串
- `__DATA_CONST` (966KB): 加载后只读数据
- `__DATA` (49KB): 可写数据
- `__LINKEDIT` (392KB): 链接编辑信息

**动态库依赖:**
- AppKit, Foundation, CoreGraphics (macOS UI)
- Security.framework (钥匙串访问)
- SystemConfiguration.framework (网络检测)
- SSL/TLS 库 (安全通信)

---

## 2. 工具系统详解

### 2.1 关键发现：工具执行模型

**重大发现:** 所有 Codex "工具" 都是 **虚拟工具** - 它们是内部 Rust 函数，作为 LLM 和系统操作之间的接口层，而不是外部操作系统命令。

### 2.2 工具源码位置

从二进制中提取的文件路径表明，所有工具都在以下目录实现：

```
core/src/tools/
├── handlers/                    # 工具处理器实现
│   ├── apply_patch.rs          # 补丁应用工具
│   ├── shell.rs                # Shell 执行工具
│   ├── read_file.rs            # 文件读取工具
│   ├── list_dir.rs             # 目录列表工具
│   ├── grep_files.rs           # 文件搜索工具
│   ├── mcp.rs                  # MCP 工具集成
│   ├── mcp_resource.rs         # MCP 资源工具
│   ├── plan.rs                 # 计划更新工具
│   ├── unified_exec.rs         # 统一执行工具
│   ├── view_image.rs           # 图像查看工具
│   └── test_sync.rs            # 测试同步工具
├── runtimes/                    # 工具运行时
│   ├── apply_patch.rs          # 补丁运行时
│   ├── shell.rs                # Shell 运行时
│   └── unified_exec.rs         # 统一执行运行时
├── registry.rs                  # 工具注册表
├── spec.rs                      # 工具规格定义
├── router.rs                    # 工具路由器
├── orchestrator.rs              # 工具编排器
├── parallel.rs                  # 并行工具执行
├── sandboxing.rs                # 工具沙箱化
├── events.rs                    # 工具事件
└── mod.rs                       # 模块定义
```

**证据:**
```
core/src/tools/handlers/apply_patch.rs:142
core/src/tools/handlers/shell.rs:198
core/src/tools/registry.rs:185
core/src/tools/spec.rs:994
```

### 2.3 完整工具目录

#### 2.3.1 文件系统工具（内置虚拟工具）

##### **read_file**
**用途:** 读取文件内容，支持切片和偏移

**参数结构:**
```rust
struct ReadFileArgs {
    file_path: String,      // 文件绝对路径（必需）
    offset: Option<u64>,    // 起始行号（1 索引）
    limit: Option<u64>,     // 读取行数
    mode: Option<String>,   // "slice" 或缩进模式
    anchor_line: Option<u64>, // 基于缩进的读取
}
```

**执行方式:**
- **虚拟**: `core/src/tools/handlers/read_file.rs` 中的内部 Rust 函数
- 使用 Rust 的 `std::fs` 打开文件
- 应用偏移/限制逻辑
- 以字符串形式返回文件内容
- 处理 UTF-8 验证

**参数验证:**
- `file_path` 必须是绝对路径
- `offset` 必须 >= 1
- `anchor_line` 不能超过文件长度

**错误处理:**
- "file_path must be an absolute path"（file_path 必须是绝对路径）
- "offset must be a 1-indexed line number"（offset 必须是 1 索引的行号）
- "failed to read file"（读取文件失败）

---

##### **list_dir**
**用途:** 列出目录内容，支持深度控制

**参数结构:**
```rust
struct ListDirArgs {
    dir_path: String,       // 目录绝对路径
    offset: Option<u64>,    // 条目起始编号（1 索引）
    limit: Option<u64>,     // 返回的最大条目数
    depth: Option<u64>,     // 遍历深度（默认: 1）
}
```

**执行方式:**
- **虚拟**: 内部目录遍历
- 使用 Rust 的文件系统 API
- 遵守 .codexignore 模式
- 可通过 `depth` 参数递归遍历

**参数验证:**
- `dir_path` 必须是绝对路径
- `offset` 必须 >= 1
- `depth` 必须 > 0

---

##### **grep_files**
**用途:** 在文件中搜索模式（类似 ripgrep）

**参数结构:**
```rust
struct GrepFilesArgs {
    pattern: String,        // 正则表达式模式
    path: Option<String>,   // 搜索目录（默认: cwd）
    glob: Option<String>,   // 文件模式过滤器（如 "*.rs"）
    limit: Option<u64>,     // 返回的最大匹配数
}
```

**执行方式:**
- **虚拟但调用外部**: 作为子进程调用 `rg`（ripgrep）
- 如果 `rg` 不可用，回退到 `grep`
- 解析输出并结构化
- 30 秒后超时

**参数验证:**
- `pattern` 不能为空
- `limit` 必须 > 0

**错误处理:**
- "pattern must not be empty"（模式不能为空）
- "rg failed"（rg 失败）
- "rg timed out after 30 seconds"（rg 在 30 秒后超时）
- "failed to launch rg: . Ensure ripgrep is installed and on PATH"（启动 rg 失败：确保已安装 ripgrep 并在 PATH 中）

**特殊行为:**
- 优先使用 `rg` 以提高速度（来自系统提示词）
- 系统提示词指示："在搜索文本或文件时，优先使用 `rg`"

---

##### **apply_patch**
**用途:** 应用统一 diff 补丁来修改文件

**参数结构:**
```rust
struct ApplyPatchToolArgs {
    patch: String,          // 统一 diff 格式的补丁
}
```

**补丁格式:**
```
*** Begin Patch
*** Add File: path/to/new_file.py
+def hello():
+    print("Hello")
*** Update File: path/to/existing.py
@@ def example():
- pass
+ return 123
*** Delete File: path/to/old.py
*** End Patch
```

**执行方式:**
- **虚拟**: `core/src/tools/handlers/apply_patch.rs` 中的自定义补丁解析器
- 解析自定义补丁格式（非标准统一 diff）
- 支持三种操作:
  - Add File（添加文件 - 创建新文件）
  - Update File（更新文件 - 使用统一 diff 块修改现有文件）
  - Delete File（删除文件 - 删除文件）
- 验证每个 hunk
- 可请求 `escalated` 权限以在工作区外写入
- 跟踪 `preexisting_untracked_files` 以支持撤销

**参数验证:**
- 行必须以 '+'、'-' 或 ' '（上下文）开头
- 头部必须指定操作（Add/Delete/Update）
- Hunk 必须能够干净应用

**错误处理:**
- "Invalid patch: invalid hunk at line X"（无效补丁：第 X 行的 hunk 无效）
- "Unexpected line found in update hunk"（在更新 hunk 中发现意外行）
- "apply_patch handler received invalid patch input"（apply_patch 处理器收到无效补丁输入）
- 在某些模式下内部调用 `git apply` 进行验证

**特殊功能:**
- **审批请求**: 可请求 `grant_root` 获取额外写权限
- **预检模式**: 可在不应用的情况下验证补丁
- **自由格式模式**: `experimental_use_freeform_apply_patch` 允许不太结构化的补丁

---

#### 2.3.2 Shell 执行工具（混合：虚拟包装器 → 外部进程）

##### **exec_command** (统一执行)
**用途:** 执行带超时和工作目录的 shell 命令

**参数结构:**
```rust
struct ExecCommandArgs {
    command: Vec<String>,        // 命令和参数（如 ["bash", "-lc", "ls"]）
    working_directory: Option<String>, // 命令的 CWD
    timeout_ms: Option<u64>,     // 超时（毫秒）
    with_escalated_permissions: Option<bool>, // 请求提升访问权限
    justification: Option<String>, // 提升原因
}
```

**执行方式:**
- **混合**: 生成外部进程的虚拟工具
- 使用 Rust 的 `std::process::Command` 创建子进程
- 将 STDOUT/STDERR 重定向到管道
- 实现超时机制
- 根据策略在沙箱中执行
- 跟踪执行时间和退出代码

**沙箱集成:**
在 macOS 上:
```rust
// 根据 sandbox_policy 配置应用 Seatbelt 配置文件
sandbox::apply_profile(policy, writable_roots, network_access);
execvp(command);
```

**参数验证:**
- `command` 参数不能为空
- 工作目录必须存在

**错误处理:**
- "command args are empty"（命令参数为空）
- "command failed inside sandbox with exit code X"（命令在沙箱中失败，退出代码 X）
- "command timed out after X ms"（命令在 X 毫秒后超时）
- "exec error: operation not permitted"（执行错误：操作不被允许）
- "read-only file system"（只读文件系统）

**特殊功能:**
- **风险评估**: `experimental_sandbox_command_assessment` 分析命令的风险
- **提升权限**: 命令可请求 `with_escalated_permissions`
- **流式输出**: 执行期间发送 `exec_command_output_delta` 事件

---

##### **write_stdin**
**用途:** 向正在运行的 unified_exec 会话的 stdin 写入数据

**参数结构:**
```rust
struct WriteStdinArgs {
    session_id: String,     // 执行会话的 ID
    data: String,           // 要写入 stdin 的数据
    close_stdin: Option<bool>, // 写入后关闭 stdin
}
```

**执行方式:**
- **虚拟**: 管理后台进程的 stdin 管道
- 通过 ID 查找现有执行会话
- 将字节写入 stdin 管道
- 可选择关闭 stdin

---

#### 2.3.3 MCP（模型上下文协议）工具（外部）

##### **list_mcp_resources**
**用途:** 列出 MCP 服务器的可用资源

**参数结构:**
```rust
struct ListResourcesArgs {
    server: Option<String>, // 特定 MCP 服务器名称
    cursor: Option<String>, // 分页游标
}
```

**执行方式:**
- **外部**: 通过 stdio 或 HTTP 调用 MCP 服务器
- MCP 服务器是配置中定义的独立进程
- 向服务器发送 JSONRPC "resources/list"
- 解析结构化响应

---

##### **read_mcp_resource**
**用途:** 从 MCP 资源读取内容

**参数结构:**
```rust
struct ReadResourceArgs {
    uri: String,            // 资源 URI（如 "file:///path"）
    server: Option<String>, // 要查询的 MCP 服务器
}
```

**执行方式:**
- **外部**: 向 MCP 服务器发出 JSONRPC 调用
- 发送 "resources/read" 请求
- 返回资源内容

---

#### 2.3.4 元数据/规划工具（虚拟）

##### **update_plan**
**用途:** 更新任务计划/待办事项列表

**参数结构:**
```rust
struct UpdatePlanArgs {
    items: Vec<PlanItem>,   // 计划项目列表
    explanation: Option<String>, // 计划变更原因
}

struct PlanItem {
    content: String,        // 步骤描述
    status: String,         // "pending" | "in_progress" | "completed"
}
```

**执行方式:**
- **虚拟**: 更新内部状态
- 向 UI 发出 `plan_update` 事件
- 用于向用户显示进度

---

##### **view_image**
**用途:** 将图像附加到会话中用于多模态输入

**参数结构:**
```rust
struct ViewImageArgs {
    file_path: String,      // 图像文件路径
}
```

**执行方式:**
- **虚拟**: 读取图像文件并编码供 API 使用
- 将图像转换为 base64
- 作为 `InputImage` 内容项附加到会话中
- 发送到 OpenAI API 进行视觉处理

---

### 2.4 工具执行汇总表

| 工具名称 | 类型 | 调用外部进程 | 处理器位置 |
|---------|------|------------|----------|
| `read_file` | 虚拟 | 否 | `core/src/tools/handlers/read_file.rs` |
| `list_dir` | 虚拟 | 否 | `core/src/tools/handlers/list_dir.rs` |
| `grep_files` | 混合 | 是（`rg`/`grep`）| `core/src/tools/handlers/grep_files.rs` |
| `apply_patch` | 虚拟 | 部分（git apply 用于验证）| `core/src/tools/handlers/apply_patch.rs` |
| `exec_command` | 混合 | 是（生成 shell/命令）| `core/src/tools/handlers/shell.rs` |
| `write_stdin` | 虚拟 | 否（管理管道）| `core/src/tools/handlers/shell.rs` |
| `list_mcp_resources` | 外部 | 是（MCP 服务器）| `core/src/tools/handlers/mcp_resource.rs` |
| `read_mcp_resource` | 外部 | 是（MCP 服务器）| `core/src/tools/handlers/mcp_resource.rs` |
| `list_mcp_resource_templates` | 外部 | 是（MCP 服务器）| `core/src/tools/handlers/mcp_resource.rs` |
| `update_plan` | 虚拟 | 否 | `core/src/tools/handlers/plan.rs` |
| `view_image` | 虚拟 | 否 | `core/src/tools/handlers/view_image.rs` |
| `barrier` | 虚拟 | 否（测试用）| `core/src/tools/handlers/test_sync.rs` |
| `test_sync_tool` | 虚拟 | 否（测试用）| `core/src/tools/handlers/test_sync.rs` |

**关键区分:**
- **虚拟工具**: 直接操作状态或执行操作的内部 Rust 函数
- **混合工具**: 生成和管理外部进程的虚拟包装器
- **外部工具**: 到独立 MCP 服务器进程的代理

---

## 3. 完整的系统提示词

### 3.1 主系统提示词

```
You are Codex, based on GPT-5. You are running as a coding agent in the Codex CLI on a user's computer.
（你是 Codex，基于 GPT-5。你作为编码代理在用户计算机上的 Codex CLI 中运行。）
```

### 3.2 核心任务指示

```
You are a coding agent. Please keep going until the query is completely resolved,
before ending your turn and yielding back to the user. Only terminate your turn
when you are sure that the problem is solved. Autonomously resolve the query to
the best of your ability, using the tools available to you, before coming back
to the user. Do NOT guess or make up an answer.

（你是一个编码代理。在结束回合并交还给用户之前，请继续直到查询完全解决。
只有在确定问题已解决时才终止回合。在返回用户之前，使用可用的工具自主解决查询。
不要猜测或编造答案。）
```

### 3.3 人格与风格

```
## Personality
Your default personality and tone is concise, direct, and friendly. You communicate
efficiently, always keeping the user clearly informed about ongoing actions without
unnecessary detail. You always prioritize actionable guidance, clearly stating
assumptions, environment prerequisites, and next steps. Unless explicitly asked,
you avoid excessively verbose explanations about your work.

（## 人格
你的默认人格和语气是简洁、直接和友好的。你高效地沟通，始终让用户清楚地了解正在进行的操作，
而不提供不必要的细节。你始终优先提供可操作的指导，明确说明假设、环境先决条件和后续步骤。
除非明确要求，否则避免对你的工作进行过于冗长的解释。）
```

### 3.4 工具使用指南

#### apply_patch 工具

```
## `apply_patch`
Use the `apply_patch` shell command to edit files.

Your patch language is a stripped-down, file-oriented diff format designed to be
easy to parse and safe to apply. You can think of it as a high-level envelope:

*** Begin Patch
[ one or more file sections ]
*** End Patch

Within that envelope, you get a sequence of file operations.
You MUST include a header to specify the action you are taking.

Each operation starts with one of three headers:
*** Add File: <path> - create a new file. Every following line is a + line (the initial contents).
*** Delete File: <path> - remove an existing file. Nothing follows.
*** Update File: <path> - patch an existing file in place (optionally with a rename).
May be immediately followed by *** Move to: <new path> if you want to rename the file.
Then one or more hunks, each introduced by @@ (optionally followed by a hunk header).

Within a hunk each line starts with:
- ' ' (space) for context lines
- '+' for added lines
- '-' for removed lines

For instructions on [context_before] and [context_after]:
- By default, show 3 lines of code immediately above and 3 lines immediately below each change.
- If 3 lines of context is insufficient to uniquely identify the snippet of code within
  the file, use the @@ operator to indicate the class or function to which the snippet belongs.

（## `apply_patch`
使用 `apply_patch` shell 命令编辑文件。

你的补丁语言是一种精简的、面向文件的 diff 格式，设计为易于解析且安全应用。
你可以将其视为一个高层封套：

*** Begin Patch
[ 一个或多个文件部分 ]
*** End Patch

在该封套内，你可以获得一系列文件操作。
你必须包含一个头部来指定你正在执行的操作。

每个操作以三个头部之一开始：
*** Add File: <path> - 创建新文件。每一行都是 + 行（初始内容）。
*** Delete File: <path> - 删除现有文件。后面没有内容。
*** Update File: <path> - 就地修补现有文件（可选择重命名）。
如果要重命名文件，可以紧接着 *** Move to: <new path>。
然后是一个或多个 hunk，每个都由 @@ 引入（可选地后跟 hunk 头部）。

在 hunk 内，每行以以下内容开头：
- ' '（空格）用于上下文行
- '+' 用于添加的行
- '-' 用于删除的行

关于 [context_before] 和 [context_after] 的说明：
- 默认情况下，在每个更改的正上方和正下方显示 3 行代码。
- 如果 3 行上下文不足以唯一标识文件中的代码片段，使用 @@ 操作符指示片段所属的类或函数。）
```

#### Shell 命令指南

```
## Shell commands
- The arguments to `shell` will be passed to execvp(). Most terminal commands should
  be prefixed with ["bash", "-lc"].
- Always set the `workdir` param when using the shell function. Do not use `cd`
  unless absolutely necessary.
- When searching for text or files, prefer using `rg` or `rg --files` respectively
  because `rg` is much faster than alternatives like `grep`. (If the `rg` command
  is not found, then use alternatives.)

（## Shell 命令
- `shell` 的参数将传递给 execvp()。大多数终端命令应以 ["bash", "-lc"] 为前缀。
- 使用 shell 函数时始终设置 `workdir` 参数。除非绝对必要，否则不要使用 `cd`。
- 在搜索文本或文件时，优先使用 `rg` 或 `rg --files`，因为 `rg` 比 `grep` 等替代品快得多。
  （如果找不到 `rg` 命令，则使用替代品。））
```

#### 编码准则

```
If completing the user's task requires writing or modifying files, your code and
final answer should follow these coding guidelines, though user instructions (i.e.
AGENTS.md) may override these guidelines:

- Fix the problem at the root cause rather than applying surface-level patches, when possible.
- Avoid unneeded complexity in your solution.
- Do not attempt to fix unrelated bugs or broken tests. It is not your responsibility
  to fix them. (You may mention them to the user in your final message though.)
- Update documentation as necessary.
- Keep changes consistent with the style of the existing codebase. Changes should be
  minimal and focused on the task.
- Use `git log` and `git blame` to search the history of the codebase if additional
  context is required.
- NEVER add copyright or license headers unless specifically requested.
- Do not waste tokens by re-reading files after calling `apply_patch` on them.
  The tool call will fail if it didn't work. The same goes for making folders,
  deleting folders, etc.
- Do not `git commit` your changes or create new git branches unless explicitly requested.
- Do not add inline comments within code unless explicitly requested.
- Do not use one-letter variable names unless explicitly requested.

（如果完成用户的任务需要编写或修改文件，你的代码和最终答案应遵循以下编码准则，
但用户指示（即 AGENTS.md）可能会覆盖这些准则：

- 在可能的情况下，从根本原因修复问题，而不是应用表面修补。
- 避免解决方案中不必要的复杂性。
- 不要试图修复无关的错误或损坏的测试。这不是你的责任。
  （不过，你可以在最终消息中向用户提及它们。）
- 必要时更新文档。
- 保持更改与现有代码库的风格一致。更改应该是最小的且专注于任务。
- 如果需要额外的上下文，使用 `git log` 和 `git blame` 搜索代码库的历史。
- 除非特别要求，否则绝不添加版权或许可证头部。
- 调用 `apply_patch` 后不要通过重新读取文件来浪费 token。
  如果不起作用，工具调用将失败。创建文件夹、删除文件夹等也是如此。
- 除非明确要求，否则不要 `git commit` 你的更改或创建新的 git 分支。
- 除非明确要求，否则不要在代码中添加内联注释。
- 除非明确要求，否则不要使用单字母变量名。）
```

### 3.5 沙箱与审批

```
## Sandbox and approvals
The Codex CLI harness supports several different sandboxing, and approval configurations
that the user can choose from.

Filesystem sandboxing prevents you from editing files without user approval. The options are:
- **read-only**: You can only read files.
- **workspace-write**: You can read files. You can write to files in your workspace
  folder, but not outside it.
- **danger-full-access**: No filesystem sandboxing.

Network sandboxing prevents you from accessing network without approval. Options are:
- **restricted**
- **enabled**

Approvals are your mechanism to get user consent to perform more privileged actions.
Although they introduce friction to the user because your work is paused until the
user responds, you should leverage them to accomplish your important work. Do not
let these settings or the sandbox deter you from attempting to accomplish the user's task.

Approval options are:
- **untrusted**: The harness will escalate most commands for user approval, apart
  from a limited allowlist of safe "read" commands.
- **on-failure**: The harness will allow all commands to run in the sandbox (if enabled),
  and failures will be escalated to the user for approval to run again without the sandbox.
- **on-request**: Commands will be run in the sandbox by default, and you can specify
  in your tool call if you want to escalate a command to run without sandboxing.
- **never**: This is a non-interactive mode where you may NEVER ask the user for
  approval to run commands. Instead, you must always persist and work around constraints
  to solve the task for the user.

（## 沙箱与审批
Codex CLI 支持多种沙箱和审批配置，用户可以从中选择。

文件系统沙箱阻止你在未经用户批准的情况下编辑文件。选项包括：
- **read-only**（只读）：你只能读取文件。
- **workspace-write**（工作区写入）：你可以读取文件。你可以写入工作区文件夹中的文件，
  但不能写入其外部。
- **danger-full-access**（危险完全访问）：无文件系统沙箱。

网络沙箱阻止你在未经批准的情况下访问网络。选项包括：
- **restricted**（受限）
- **enabled**（启用）

审批是你获得用户同意以执行更多特权操作的机制。尽管它们会给用户带来摩擦，因为你的工作会暂停，
直到用户响应，但你应该利用它们来完成重要工作。不要让这些设置或沙箱阻止你尝试完成用户的任务。

审批选项包括：
- **untrusted**（不受信任）：除了有限的安全"读取"命令白名单外，工具将大多数命令升级为用户审批。
- **on-failure**（失败时）：工具将允许所有命令在沙箱中运行（如果启用），失败将升级为用户审批，
  以便在没有沙箱的情况下再次运行。
- **on-request**（请求时）：默认情况下命令将在沙箱中运行，你可以在工具调用中指定是否要升级命令以在没有沙箱的情况下运行。
- **never**（从不）：这是一种非交互模式，你绝不可以要求用户批准运行命令。相反，你必须始终坚持并解决约束以解决用户的任务。）
```

### 3.6 AGENTS.md 规范

```
# AGENTS.md spec
- Repos often contain AGENTS.md files. These files can appear anywhere within the repository.
- These files are a way for humans to give you (the agent) instructions or tips for
  working within the container.
- Some examples might be: coding conventions, info about how code is organized, or
  instructions for how to run or test code.
- Instructions in AGENTS.md files:
    - The scope of an AGENTS.md file is the entire directory tree rooted at the folder
      that contains it.
    - For every file you touch in the final patch, you must obey instructions in any
      AGENTS.md file whose scope includes that file.
    - Instructions about code style, structure, naming, etc. apply only to code within
      the AGENTS.md file's scope, unless the file states otherwise.
    - More-deeply-nested AGENTS.md files take precedence in the case of conflicting instructions.
    - Direct system/developer/user instructions (as part of a prompt) take precedence
      over AGENTS.md instructions.
- The contents of the AGENTS.md file at the root of the repo and any directories from
  the CWD up to the root are included with the developer message and don't need to be
  re-read. When working in a subdirectory of CWD, or a directory outside the CWD, check
  for any AGENTS.md files that may be applicable.

（# AGENTS.md 规范
- 仓库通常包含 AGENTS.md 文件。这些文件可以出现在仓库中的任何位置。
- 这些文件是人类向你（代理）提供在容器中工作的指示或提示的一种方式。
- 一些示例可能是：编码约定、代码组织方式信息或如何运行或测试代码的指示。
- AGENTS.md 文件中的指示：
    - AGENTS.md 文件的范围是包含它的文件夹根目录下的整个目录树。
    - 对于你在最终补丁中接触的每个文件，你必须遵守其范围包括该文件的任何 AGENTS.md 文件中的指示。
    - 关于代码风格、结构、命名等的指示仅适用于 AGENTS.md 文件范围内的代码，除非文件另有说明。
    - 在指示冲突的情况下，更深嵌套的 AGENTS.md 文件优先。
    - 直接系统/开发人员/用户指示（作为提示的一部分）优先于 AGENTS.md 指示。
- 仓库根目录的 AGENTS.md 文件内容以及从 CWD 到根目录的任何目录都包含在开发人员消息中，
  不需要重新读取。在 CWD 的子目录或 CWD 外部的目录中工作时，检查可能适用的任何 AGENTS.md 文件。）
```

### 3.7 输出格式指南

```
## Presenting your work and final message
You are producing plain text that will later be styled by the CLI. Follow these rules
exactly. Formatting should make results easy to scan, but not feel mechanical. Use
judgment to decide how much structure adds value.

- Don't dump large files you've written; reference paths only.
- The user does not command execution outputs. When asked to show the output of a
  command (e.g. `git show`), relay the important details in your answer or summarize
  the key lines so the user understands the result.
- Don'ts: no nested bullets/hierarchies; no ANSI codes; don't cram unrelated keywords;
  keep keyword lists short

（## 展示你的工作和最终消息
你正在生成将由 CLI 稍后设置样式的纯文本。严格遵循这些规则。格式应使结果易于扫描，
但不要感觉机械化。使用判断来决定多少结构增加价值。

- 不要转储你编写的大文件；仅引用路径。
- 用户不命令执行输出。当被要求显示命令的输出时（例如 `git show`），在你的答案中传达重要细节，
  或总结关键行，以便用户理解结果。
- 不要：无嵌套项目符号/层次结构；无 ANSI 代码；不要塞进不相关的关键字；保持关键字列表简短）
```

### 3.8 计划工具使用

```
## Plan tool
When using the planning tool:
- Skip using the planning tool for straightforward tasks (roughly the easiest 25%).
- Do not make single-step plans.
- When you made a plan, update it after having performed one of the sub-tasks that
  you shared on the plan.

The plan format should be a list of sentence steps (no more than 5-7 words each)
with a `status` for each step (`pending`, `in_progress`, or `completed`).

When steps have been completed, use `update_plan` to mark each finished step as
`completed` and the next step you are working on as `in_progress`. There should
always be exactly one `in_progress` step until everything is done. You can mark
multiple items as complete in a single `update_plan` call.

If all steps are complete, ensure you call `update_plan` to mark all steps as `completed`.

（## 计划工具
使用规划工具时：
- 对于简单的任务（大约最简单的 25%），跳过使用规划工具。
- 不要制定单步计划。
- 当你制定了计划后，在执行了你在计划中分享的子任务之一后更新它。

计划格式应该是一个句子步骤列表（每个不超过 5-7 个单词），每个步骤都有一个 `status`
（`pending`、`in_progress` 或 `completed`）。

当步骤完成后，使用 `update_plan` 将每个完成的步骤标记为 `completed`，
将你正在处理的下一步标记为 `in_progress`。在所有事情完成之前，应该始终只有一个 `in_progress` 步骤。
你可以在单个 `update_plan` 调用中将多个项目标记为完成。

如果所有步骤都完成了，确保调用 `update_plan` 将所有步骤标记为 `completed`。）
```

### 3.9 环境上下文注入

每个回合都包含环境上下文：

```xml
<environment_context>
  <cwd>/path/to/project</cwd>
  <approval_policy>on-failure</approval_policy>
  <sandbox_mode>workspace-write</sandbox_mode>
  <network_access>false</network_access>
  <writable_roots>
    <root>/path/to/project</root>
  </writable_roots>
  <shell>/bin/zsh</shell>
</environment_context>
```

此上下文被注入到每个回合中，以告知模型：
- 当前工作目录
- 权限边界
- 安全约束

---

## 4. 主要工作流程

### 4.1 初始化序列

```
1. 二进制启动
   ├─> 解析 CLI 参数（codex / codex exec / codex resume）
   ├─> 从 ~/.codex/config.toml 加载配置
   ├─> 检查托管首选项
   ├─> 验证工作区限制（如果已配置）
   └─> 初始化日志记录/遥测

2. 认证检查
   ├─> 检查 API 密钥（OPENAI_API_KEY / CODEX_API_KEY 环境变量）
   ├─> 或从钥匙串加载 ChatGPT 凭据
   ├─> 如果已配置，强制执行 forced_login_method
   └─> 如果需要，显示登录提示

3. 项目分析
   ├─> 检测目录是否为 Git 仓库
   ├─> 检查项目是否"受信任"（存储在配置中）
   ├─> 如果不受信任，提示审批策略
   └─> 加载 .codexignore / .gitignore 模式

4. 会话初始化
   ├─> 恢复现有会话（如果 --resume）
   │   ├─> 加载 rollout.jsonl
   │   ├─> 加载 history.jsonl
   │   └─> 恢复会话状态
   ├─> 或创建新会话
   │   ├─> 为会话生成 UUID
   │   ├─> 创建会话元数据文件
   │   └─> 初始化空 rollout
   └─> 向后端发送 JSONRPC "initialize" 请求

5. 配置注入
   ├─> 收集环境上下文：
   │   ├─> 当前工作目录
   │   ├─> Shell 类型（$SHELL）
   │   ├─> 审批策略（untrusted/on-failure/on-request/never）
   │   ├─> 沙箱模式（read-only/workspace-write/danger-full-access）
   │   ├─> 网络访问权限
   │   └─> 可写根目录
   ├─> 加载 developer_instructions（自定义系统提示）
   ├─> 加载 compact_prompt（用于上下文压缩）
   └─> 向 UI 发送 "SessionConfigured" 事件

6. 进入主事件循环
```

### 4.2 主事件循环

Codex 的核心是事件驱动架构：

```rust
loop {
    event = receive_event();  // 来自 JSONRPC 或用户输入

    match event {
        UserInput => {
            // 向后端发送用户消息
            send_jsonrpc_request("sendUserTurn", user_message);
        }

        AgentMessage => {
            // 在 UI 中显示代理响应
            render_message(message);
        }

        FunctionCall => {
            // 代理想要使用工具
            tool_name = extract_tool_name(function_call);

            // 检查是否需要审批
            if requires_approval(tool_name, approval_policy) {
                approval = prompt_user_for_approval();
                if !approval { continue; }
            }

            // 执行工具
            result = execute_tool(tool_name, args);

            // 将结果发送回模型
            send_tool_result(result);
        }

        SessionEnd => break,
    }
}
```

**关键事件类型:**
- `task_started` - 新用户回合开始
- `agent_message` - 模型的文本响应
- `agent_reasoning` - 模型的思考过程（o1 模型）
- `exec_command_begin` - Shell 命令开始
- `exec_command_end` - Shell 命令完成
- `mcp_tool_call_begin/end` - MCP 工具调用
- `patch_apply_begin/end` - 文件修改事件
- `exec_approval_request` - 需要用户审批
- `session_configured` - 会话准备就绪

### 4.3 工具执行流程

```
┌─────────────────────────────────────────────┐
│   模型生成函数调用                           │
│   { "name": "read_file",                    │
│     "arguments": "{\"file_path\": \"/..\"}" }│
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   解析函数调用                               │
│   - 提取工具名称                             │
│   - 解析 JSON 参数                           │
│   - 验证参数类型                             │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   检查审批策略                               │
│   ┌──────────────────────────────────────┐  │
│   │ untrusted: 总是询问                 │  │
│   │ on-failure: 沙箱失败时询问          │  │
│   │ on-request: 模型请求时询问          │  │
│   │ never: 自主执行                     │  │
│   └──────────────────────────────────────┘  │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   路由到工具处理器                           │
│   ┌──────────────────────────────────────┐  │
│   │ 内置: apply_patch, read_file,       │  │
│   │       list_dir, grep_files          │  │
│   │ Shell: exec_command, write_stdin    │  │
│   │ MCP: list_mcp_resources, read_mcp_  │  │
│   │ 元数据: update_plan, barrier        │  │
│   └──────────────────────────────────────┘  │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   使用沙箱执行（如果适用）                   │
│   - macOS: Seatbelt 沙箱配置文件             │
│   - Linux: Landlock + seccomp               │
│   - Windows: 受限令牌                        │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   捕获输出和错误                             │
│   - shell 命令的 STDOUT/STDERR              │
│   - 内置工具的结构化响应                     │
│   - 执行时间、退出代码等                     │
└────────────────┬────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────┐
│   将结果返回给模型                           │
│   - 格式化为 FunctionCallOutput            │
│   - 包含在会话历史中                         │
│   - 模型处理并继续                           │
└─────────────────────────────────────────────┘
```

---

## 5. 上下文管理

### 5.1 存储格式

Codex 使用多个文件进行上下文存储：

```
~/.codex/
├── config.toml                 # 用户配置
├── auth.json                   # 认证凭据
├── sessions/
│   ├── {session-uuid}/
│   │   ├── rollout.jsonl       # 完整会话日志
│   │   ├── history.jsonl       # 消息历史（紧凑）
│   │   ├── session_metadata    # 会话信息（模型、时间戳）
│   │   └── ghost_commits/      # 撤销快照（git 提交）
│   └── archived_sessions/      # 旧会话
└── mcp_oauth_tokens/           # MCP 服务器 OAuth 令牌
```

### 5.2 Rollout 格式（rollout.jsonl）

每行都是一个表示回合项的 JSON 对象：

```jsonl
{"UserMessage": {"items": [{"Text": "Write a hello world program"}]}}
{"AgentMessage": {"items": [{"Text": "I'll create a hello world program..."}]}}
{"Reasoning": {"items": [{"content": {"Text": "First, I'll use apply_patch..."}}]}}
{"FunctionCall": {"name": "apply_patch", "arguments": "{...}", "call_id": "..."}}
{"FunctionCallOutput": {"call_id": "...", "output": "Successfully applied patch"}}
```

**回合项类型:**
- `UserMessage` - 用户输入
- `AgentMessage` - 模型的响应文本
- `Reasoning` - 模型的思考（用于 o1 风格模型）
- `WebSearch` - 网络搜索结果
- `FunctionCall` - 工具调用
- `FunctionCallOutput` - 工具结果
- `CustomToolCall` / `CustomToolCallOutput` - MCP 工具
- `GhostSnapshot` - 撤销检查点
- `LocalShellCall` - Shell 执行记录

### 5.3 上下文压缩

当令牌计数超过限制时，Codex 压缩上下文：

**配置:**
- `model_auto_compact_token_limit` - 触发阈值
- `model_max_output_tokens` - 模型的最大输出
- `compact_prompt` - 自定义压缩指令

**过程:**
```
1. 检测令牌限制临近
   └─> 检查 model_auto_compact_token_limit

2. 选择要压缩的项目
   ├─> 保留最近的回合（最后 N 个）
   ├─> 总结中间回合
   └─> 保留重要的函数调用

3. 向模型发送压缩请求
   ├─> 包含 compact_prompt 指令
   ├─> 模型生成摘要
   └─> 用摘要替换冗长的回合

4. 更新 rollout
   ├─> 将回合标记为 "compacted"
   ├─> 插入带摘要的 CompactedItem
   └─> 使用减少的令牌继续会话
```

### 5.4 幽灵快照与撤销

Codex 使用 Git 实现撤销系统：

**幽灵提交过程:**
```
1. 在进行更改之前
   ├─> 检查工作区是否为 Git 仓库
   ├─> 使用当前状态创建临时提交
   │   ├─> 暂存所有更改（包括未跟踪的文件）
   │   ├─> 使用消息"ghost snapshot"提交
   │   └─> 存储提交 SHA
   └─> 在 rollout 中作为 GhostSnapshot 项跟踪

2. 在任务执行期间
   └─> 模型进行更改（apply_patch、exec_command 等）

3. 用户请求撤销
   ├─> 检索幽灵提交 SHA
   ├─> 运行：git reset --hard <ghost-sha>
   ├─> 如果需要，恢复未跟踪的文件
   └─> 发出 UndoCompletedEvent

4. 清理
   └─> 幽灵提交可以稍后被垃圾收集
```

**配置:**
- 如果不是 Git 仓库则禁用
- 跟踪 `preexisting_untracked_files` 以避免删除用户文件

---

## 6. 安全与沙箱系统

### 6.1 审批策略

四种模式控制命令的审批方式：

```typescript
type ApprovalPolicy =
  | "untrusted"           // 执行前总是询问
  | "on-failure"          // 先尝试沙箱，失败时询问
  | "on-request"          // 模型决定何时询问
  | "never"               // 完全自主
```

**不受信任模式（Untrusted）:**
- 非 Git 仓库的默认设置
- 每个命令都需要用户审批
- 显示完整命令和风险评估

**失败时模式（On-Failure）:**
- Git 仓库的默认设置
- 尝试在沙箱中执行
- 如果沙箱阻止，询问用户并提供解释

**请求时模式（On-Request）:**
- 模型可以明确请求审批
- 设置 `justification` 字段解释原因
- 用户看到模型的推理

**从不模式（Never）:**
- 完全自主操作
- 适用于 CI/CD 环境
- 谨慎使用

### 6.2 沙箱实现

#### macOS: Seatbelt

使用 Apple 的 Sandbox.framework：

```c
// Chromium 启发的沙箱配置文件
// https://source.chromium.org/chromium/chromium/src/+/main:sandbox/policy/mac/common.sb
sandbox_init(profile, flags, &error);
```

**配置文件组件:**
- 默认拒绝所有
- 允许在任何地方读取
- 允许写入特定根目录（工作区、TMPDIR）
- 基于 `network_access` 标志的网络
- 阻止敏感路径（`/etc/sudoers`、`/System/Library`）

**配置:**
```rust
struct SandboxPolicy {
    mode: "read-only" | "workspace-write" | "danger-full-access",
    writable_roots: Vec<PathBuf>,
    network_access: bool,
    exclude_tmpdir_env_var: bool,  // 不允许写入 TMPDIR
    exclude_slash_tmp: bool,       // 不允许写入 /tmp
}
```

#### Linux: Landlock + seccomp

双层方法：

**Landlock（文件系统访问）:**
```rust
landlock::Ruleset::new()
    .add_rule(Path::new("/"), AccessType::Read)
    .add_rule(Path::new("/home/user/project"), AccessType::ReadWrite)
    .apply();
```

**seccomp（系统调用）:**
```rust
seccomp::Context::new()
    .allow_syscall(Syscall::read)
    .allow_syscall(Syscall::write)
    .deny_syscall(Syscall::ptrace)
    .apply();
```

#### Windows: 受限令牌

使用 Windows 安全令牌：

```rust
CreateRestrictedToken(
    current_token,
    flags,
    sids_to_disable,
    privileges_to_delete,
    &restricted_token
);
```

### 6.3 风险评估

当启用 `experimental_sandbox_command_assessment` 时：

```rust
struct SandboxCommandAssessment {
    risk_level: "low" | "medium" | "high",
    risk_categories: Vec<RiskCategory>,
    explanation: String,
}

enum RiskCategory {
    DataDeletion,          // rm, shred 等
    DataExfiltration,      // curl, wget, scp
    PrivilegeEscalation,   // sudo, su
    SystemModification,    // apt install, systemctl
    ResourceExhaustion,    // :(){ :|:& };:
    Compliance,            // 许可证违规
}
```

**评估过程:**
1. 解析命令和参数
2. 检查已知危险模式
3. 分析敏感位置的文件路径
4. 考虑网络操作
5. 评估综合风险
6. 向用户展示并说明

**危险模式:**
- `rm -rf /`
- `sudo` 命令
- 出站网络连接
- 软件包安装
- 内核模块加载

---

## 7. JSONRPC 协议

### 7.1 传输层

**连接:**
- **主要:** 通过 HTTPS 的服务器发送事件（SSE）
- **端点:**
  - `https://chatgpt.com/backend-api/codex`
  - `https://api.openai.com/v1/responses/chat/completions`

**头部:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>`
- `Accept: text/event-stream`（用于 SSE）
- `Mcp-Session-Id: <uuid>`（用于 MCP）
- `Last-Event-Id: <id>`（SSE 恢复）

### 7.2 客户端请求（客户端 → 服务器）

| 方法 | 用途 | 参数 |
|------|------|------|
| `initialize` | 启动新会话 | `clientInfo`, `capabilities` |
| `newConversation` | 开始新聊天 | `prompt`, `images?`, `model?` |
| `sendUserTurn` | 发送用户消息 | `message`, `session_id` |
| `listModels` | 获取可用模型 | - |
| `loginApiKey` | 使用 API 密钥认证 | `api_key` |
| `loginChatGpt` | 启动 ChatGPT OAuth | - |
| `logout` | 结束会话 | - |
| `fuzzyFileSearch` | 搜索文件 | `query`, `workspace` |
| `execOneOffCommand` | 运行单个命令 | `command`, `cwd` |
| `getTask` | 获取 Cloud 任务 | `task_id` |
| `listTasks` | 列出 Cloud 任务 | `environment` |
| `resumeSession` | 继续会话 | `session_id` |
| `compact` | 触发上下文压缩 | `session_id` |
| `review` | 启动审查模式 | `review_request` |
| `undo` | 撤销最后的更改 | `session_id` |

### 7.3 服务器通知（服务器 → 客户端）

| 通知 | 用途 | 数据 |
|------|------|------|
| `sessionConfigured` | 会话准备就绪 | `model`, `history_log_id`, `rollout_path` |
| `authStatusChange` | 认证状态改变 | `status`, `user_info` |
| `loginChatGptComplete` | OAuth 完成 | `success`, `error?` |
| `account/rateLimits/updated` | 速率限制信息 | `rate_limits` |
| `toolCall` | 模型调用工具 | `tool_name`, `arguments` |
| `error` | 发生错误 | `error_data` |

### 7.4 事件（双向流）

**来自服务器（模型操作）:**
```typescript
type EventMsg =
  | { type: "task_started", ... }
  | { type: "agent_message", content: string }
  | { type: "agent_reasoning", content: string }  // o1 模型
  | { type: "exec_command_begin", command: string[], cwd: string }
  | { type: "exec_command_output_delta", stream: "stdout"|"stderr", data: bytes }
  | { type: "exec_command_end", exit_code: number, wall_time_seconds: number }
  | { type: "patch_apply_begin", changes: FileChange[] }
  | { type: "patch_apply_end", success: boolean }
  | { type: "mcp_tool_call_begin", invocation: McpInvocation }
  | { type: "mcp_tool_call_end", invocation: McpInvocation, result: any }
  | { type: "exec_approval_request", command: string[], risk_assessment?: SandboxRisk }
  | { type: "apply_patch_approval_request", grant_root?: string }
  | { type: "web_search_begin", query: string }
  | { type: "web_search_end", results: WebSearchItem[] }
  | { type: "view_image_tool_call", file_path: string }
  | { type: "token_count", usage: TokenUsage }
  | { type: "task_complete", last_agent_message?: string }
  // ... 40+ 事件类型
```

---

## 8. 配置参考

### 8.1 完整配置选项

```toml
# ~/.codex/config.toml

[model]
# 主要模型提供商
provider = "openai"  # 或 "ollama"

# 模型选择
model = "gpt-4-turbo"
review_model = "gpt-4"  # 用于审查模式

# 令牌限制
model_max_output_tokens = 16384
model_auto_compact_token_limit = 100000

# 推理（用于 o1 模型）
model_supports_reasoning_summaries = true
model_reasoning_summary_format = "text"
model_reasoning_summary = true
model_verbosity = "concise"

[approval]
# 审批策略
approval_policy = "on-failure"  # untrusted | on-failure | on-request | never

[sandbox]
# 沙箱模式
sandbox_mode = "workspace-write"  # read-only | workspace-write | danger-full-access
network_access = false
exclude_tmpdir_env_var = false
exclude_slash_tmp = false

# Shell 环境处理
shell_environment_policy = "inherit"  # 或 "ignore_default"

[security]
# 风险评估
experimental_sandbox_command_assessment = true

[prompts]
# 自定义指令
developer_instructions = """
始终为新函数编写测试。
"""

# 用于上下文缩减的紧凑提示
compact_prompt = """
总结会话历史，保留：
- 做出的关键决策
- 修改的文件
- 未解决的问题
"""

# 外部指令文件
experimental_instructions_file = "/path/to/instructions.md"
experimental_compact_prompt_file = "/path/to/compact.md"

[auth]
# 强制特定登录方法
forced_login_method = "api_key"  # 或 "chatgpt"

# 工作区限制
forced_chatgpt_workspace_id = "ws_..."

# 凭据存储
cli_auth_credentials_store = "keychain"  # 或 "file"
mcp_oauth_credentials_store = "keychain"

[project]
# 项目文档
project_doc_max_bytes = 1000000
project_doc_fallback_filenames = ["README.md", "CONTRIBUTING.md"]

[ui]
# TUI 设置
hide_agent_reasoning = true
show_raw_agent_reasoning = false
file_opener = "code"  # 打开文件的命令
disable_paste_burst = false

[features]
# 功能标志（实验性）
unified_exec = true
rmcp_client = true
apply_patch_freeform = true
view_image_tool = true
web_search_request = true
enable_experimental_windows_sandbox = false

[logging]
# 日志记录行为
log_user_prompt = false
persistence = true

[telemetry]
# OpenTelemetry 设置
enabled = true
endpoint = "http://localhost:4318"
protocol = "otlp-http"  # 或 "otlp-grpc"

[search]
# 文件搜索配置
ignore_default_excludes = false
exclude = ["node_modules/", ".git/"]
include_only = []

[model_providers.ollama]
type = "ollama"
base_url = "http://localhost:11434"

[mcp.github]
type = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "${GITHUB_TOKEN}" }

[mcp.database]
type = "streamable-http"
url = "https://example.com/mcp"
oauth = { issuer = "https://auth.example.com" }
```

### 8.2 环境变量

```bash
# 认证
OPENAI_API_KEY=sk-...
CODEX_API_KEY=sk-...

# 遥测
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_HEADERS="x-api-key=..."
OTEL_EXPORTER_OTLP_COMPRESSION=gzip

# 行为
SKIP_GIT_REPO_CHECK=1  # 允许在 Git 仓库外运行
CODEX_STARTING_DIFF=1  # 在上下文中包含起始 diff

# MCP
GITHUB_TOKEN=ghp_...   # 用于 GitHub MCP 服务器
```

---

## 附录 A: Rust 模块映射

从字符串中的文件路径提取：

```
codex_core::
├── default_client         # API 客户端
├── event_mapping          # 事件处理器
├── project_doc            # 文档阅读
├── rollout::recorder      # 会话日志记录
├── spawn                  # 进程生成
├── tools::
│   ├── handlers::
│   │   ├── apply_patch    # 补丁工具
│   │   ├── shell          # Shell 工具
│   │   ├── read_file      # 文件读取
│   │   ├── list_dir       # 目录列表
│   │   ├── grep_files     # 文件搜索
│   │   ├── mcp            # MCP 集成
│   │   ├── mcp_resource   # MCP 资源
│   │   ├── plan           # 计划工具
│   │   ├── unified_exec   # 统一执行
│   │   ├── view_image     # 图像工具
│   │   └── test_sync      # 测试同步
│   ├── runtimes::
│   │   ├── apply_patch    # 补丁运行时
│   │   ├── shell          # Shell 运行时
│   │   └── unified_exec   # 执行运行时
│   ├── parallel           # 并行执行
│   ├── registry           # 工具目录
│   ├── router             # 工具路由
│   ├── orchestrator       # 工具编排
│   ├── sandboxing         # 沙箱化
│   ├── spec               # 工具规格
│   └── events             # 工具事件
├── tasks::
│   ├── ghost_snapshot     # 撤销快照
│   ├── undo               # 撤销逻辑
│   └── user_shell         # 用户命令
├── sandboxing::
│   └── assessment         # 风险评估
└── user_notification      # 用户消息

codex_protocol::
├── account                # 帐户管理
└── models                 # 数据模型

codex_app_server::
└── message_processor      # JSONRPC 处理

codex_exec::
└── event_processor_with_jsonl_output  # Exec 模式输出

codex_cloud_tasks::
└── env_detect             # 环境检测
```

---

## 附录 B: 完整事件类型列表

从重建的 TypeScript 定义中提取：

1. `task_started` - 任务开始
2. `task_complete` - 任务结束
3. `token_count` - 令牌使用信息
4. `agent_message` - 模型文本响应
5. `user_message` - 用户输入
6. `agent_message_delta` - 流式文本
7. `agent_reasoning` - 推理过程
8. `agent_reasoning_delta` - 流式推理
9. `agent_reasoning_raw_content` - 完整推理
10. `agent_reasoning_raw_content_delta` - 流式完整推理
11. `agent_reasoning_section_break` - 推理分隔符
12. `session_configured` - 会话初始化
13. `mcp_tool_call_begin` - MCP 工具开始
14. `mcp_tool_call_end` - MCP 工具完成
15. `web_search_begin` - 网络搜索开始
16. `web_search_end` - 网络搜索完成
17. `exec_command_begin` - 命令执行开始
18. `exec_command_output_delta` - 命令输出流
19. `exec_command_end` - 命令执行完成
20. `view_image_tool_call` - 图像附件
21. `exec_approval_request` - 命令需要用户审批
22. `apply_patch_approval_request` - 补丁需要用户审批
23. `deprecation_notice` - 功能弃用警告
24. `background_event` - 后台任务通知
25. `undo_started` - 撤销开始
26. `undo_completed` - 撤销完成
27. `stream_error` - 流式错误发生
28. `patch_apply_begin` - 补丁应用开始
29. `patch_apply_end` - 补丁应用完成
30. `turn_diff` - 回合变更的 diff
31. `get_history_entry_response` - 检索历史条目
32. `mcp_list_tools_response` - 列出 MCP 工具
33. `list_custom_prompts_response` - 列出自定义提示
34. `plan_update` - 计划更新
35. `turn_aborted` - 回合取消
36. `shutdown_complete` - 干净关闭
37. `entered_review_mode` - 激活审查模式
38. `exited_review_mode` - 退出审查模式
39. `raw_response_item` - 原始 API 响应
40. `item_started` - 响应项开始
41. `item_completed` - 响应项完成
42. `agent_message_content_delta` - 消息内容流
43. `reasoning_content_delta` - 推理流
44. `reasoning_raw_content_delta` - 原始推理流
45. `error` - 发生错误

---

## 总结

### 关键发现总结

1. **工具是虚拟的:**
   - 所有 Codex 工具（`apply_patch`、`read_file` 等）都是内部 Rust 函数
   - 它们作为 LLM 和系统操作之间的抽象层
   - 不是外部操作系统命令，而是 `core/src/tools/handlers/` 中的处理器

2. **架构:**
   - 客户端-服务器模式，本地 CLI + 远程 OpenAI API
   - 通过 HTTPS/SSE 的 JSONRPC 双向通信
   - 事件驱动架构，具有 40+ 事件类型

3. **安全性:**
   - 多层：审批策略 + 沙箱化 + 风险评估
   - 平台特定沙箱（Seatbelt/Landlock/Restricted Token）
   - 四种审批模式，从完全自主到总是询问

4. **上下文管理:**
   - rollout.jsonl 存储完整会话
   - 接近令牌限制时自动压缩
   - 幽灵提交启用撤销功能

5. **提示词:**
   - 声称使用"GPT-5"模型
   - 系统提示强调自主性和工具使用
   - 可通过配置注入自定义指令

---

**元数据:**
- **分析的字符串数:** 207,466
- **二进制大小:** 33.6 MB（仅可执行文件）
- **分析持续时间:** ~4 小时（估计）
- **置信度:** 高（85%+）工具执行模型和架构
- **源代码验证:** 不可能（闭源）

**联系方式:**
有关此分析的问题，请参阅原始逆向工程请求。
