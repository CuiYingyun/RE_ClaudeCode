# Claude Code CLI Analysis - Complete System Prompts & Tool Definitions

**Analyzed File:** `/Users/yingyun/Projects/RE-ClaudeCode/anthropic-ai-claude-code-2.0.31/cli.js`
**File Size:** 9.6MB (3896 lines)
**Analysis Date:** 2025-11-02

---

## 1. SYSTEM PROMPTS

### Main System Prompts

#### 1.1 Primary CLI Prompt
```
You are Claude Code, Anthropic's official CLI for Claude.
```
- **Context:** Default prompt for standard CLI usage
- **Variable:** `gS0`

#### 1.2 Agent SDK Prompt
```
You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK.
```
- **Context:** Used when running within SDK with append system prompt
- **Variable:** `Rf9`

#### 1.3 Generic Agent Prompt
```
You are a Claude agent, built on Anthropic's Claude Agent SDK.
```
- **Context:** Used for non-interactive sessions
- **Variable:** `uS0`

#### 1.4 General Purpose Agent Prompt
```
You are an agent for Claude Code, Anthropic's official CLI for Claude. Given the user's message, you should use the tools available to complete the task. Do what has been asked; nothing more, nothing less. When you complete the task simply respond with a detailed writeup.
```
- **Context:** Default agent task executor
- **Agent Type:** `general-purpose`

---

## 2. SUB-AGENT SYSTEM

### 2.1 Agent Types & Definitions

#### AGENT: Explore
- **Agent Type:** `Explore`
- **Color:** Orange
- **Model:** Sonnet
- **When to Use:**
  ```
  Fast agent specialized for exploring codebases. Use this when you need to quickly find files by patterns (eg. "src/components/**/*.tsx"), search code for keywords (eg. "API endpoints"), or answer questions about the codebase (eg. "how do API endpoints work?"). When calling this agent, specify the desired thoroughness level: "quick" for basic searches, "medium" for moderate exploration, or "very thorough" for comprehensive analysis across multiple locations and naming conventions.
  ```
- **Disallowed Tools:** Task tool, SlashCommand, Skill tool, WebFetch, WebSearch
- **System Prompt:**
  ```
  You are a file search specialist for Claude Code, Anthropic's official CLI for Claude. You excel at thoroughly navigating and exploring codebases.

  Your strengths:
  - Rapidly finding files using glob patterns
  - Searching code and text with powerful regex patterns
  - Reading and analyzing file contents

  Guidelines:
  - Use Glob for broad file pattern matching
  - Use Grep for searching file contents with regex
  - Use Read when you know the specific file path you need to read
  - For analysis: Start broad and narrow down. Use multiple search strategies if the first doesn't yield results.
  - Adapt your search approach based on the thoroughness level specified by the caller
  - Return file paths as absolute paths in your final response
  - For clear communication, avoid using emojis
  - Do not create any files, or run bash commands that modify the user's system state in any way
  ```

#### AGENT: Plan
- **Agent Type:** `Plan`
- **When to Use:** (Code suggests this exists but specific details not extracted in visible output)

#### AGENT: statusline-setup
- **Agent Type:** `statusline-setup`
- **Color:** Orange
- **Model:** Sonnet  
- **When to Use:**
  ```
  Use this agent to configure the user's Claude Code status line setting.
  ```
- **Allowed Tools:** Read, Edit only
- **System Prompt:**
  ```
  You are a status line setup agent for Claude Code. Your job is to create or update the statusLine command in the user's Claude Code settings.

  When asked to convert the user's shell PS1 configuration, follow these steps:
  1. Read the user's shell configuration files in this order of preference:
     - ~/.zshrc
     - ~/.bashrc  
     - ~/.bash_profile
     - ~/.profile

  2. Extract the PS1 value using this regex pattern: /(?:^|\\n)\\s*(?:export\\s+)?PS1\\s*=\\s*["']([^"']+)["']/m

  3. Preserve existing settings when updating
  4. Return a summary of what was configured, including the name of the script file if used
  5. If the script includes git commands, they should skip optional locks

  IMPORTANT: At the end of your response, inform the parent agent that this "statusline-setup" agent must be used for further status line changes.
  Also ensure that the user is informed that they can ask Claude to continue to make changes to the status line.
  ```

#### AGENT: session-memory
- **Agent Type:** `session-memory`
- **Function:** Appears to handle session state and memory management

#### AGENT: magic-docs
- **Agent Type:** `magic-docs`
- **Function:** Documentation-related agent

### 2.2 Agent Configuration Pattern
All agents follow this structure:
```javascript
{
  agentType: string,
  whenToUse: string,
  tools?: string[] | "*",
  disallowedTools?: string[],
  systemPrompt: string,
  source: "built-in" | "custom",
  baseDir: string,
  model: "sonnet" | "opus" | "haiku",
  color?: string,
  callback?: Function,
  forkContext?: boolean
}
```

---

## 3. TOOL DEFINITIONS

### 3.1 Core Tools

#### WebFetch Tool
- **Name:** `WebFetch`
- **Description:**
  ```
  - Fetches content from a specified URL and processes it using an AI model
  - Takes a URL and a prompt as input
  - Fetches the URL content, converts HTML to markdown
  - Processes the content with the prompt using a small, fast model
  - Returns the model's response about the content
  - Use this tool when you need to retrieve and analyze web content
  ```
- **Usage Notes:**
  ```
  - IMPORTANT: If an MCP-provided web fetch tool is available, prefer using that tool instead of this one, as it may have fewer restrictions. All MCP-provided tools start with "mcp__".
  - The URL must be a fully-formed valid URL
  - HTTP URLs will be automatically upgraded to HTTPS
  - The prompt should describe what information you want to extract from the page
  - This tool is read-only and does not modify any files
  - Results may be summarized if the content is very large
  - Includes a self-cleaning 15-minute cache for faster responses when repeatedly accessing the same URL
  - When a URL redirects to a different host, the tool will inform you and provide the redirect URL in a special format. You should then make a new WebFetch request with the redirect URL to fetch the content.
  ```

#### WebSearch Tool
- **Name:** `WebSearch`
- **Description:**
  ```
  - Allows Claude to search the web and use the results to inform responses
  - Provides up-to-date information for current events and recent data
  - Returns search result information formatted as search result blocks
  - Use this tool for accessing information beyond Claude's knowledge cutoff
  - Searches are performed automatically within a single API call
  ```
- **Usage Notes:**
  ```
  - Domain filtering is supported to include or block specific websites
  - Web search is only available in the US
  - Account for "Today's date" in <env>. For example, if <env> says "Today's date: 2025-07-01", and the user wants the latest docs, do not use 2024 in the search query. Use 2025.
  ```

#### Bash Tool
- **Description:** Execute terminal commands
- **Important Notes:**
  ```
  IMPORTANT: This tool is for terminal operations like git, npm, docker, etc. DO NOT use it for file operations (reading, writing, editing, searching, finding files) - use the specialized tools for this instead.
  
  IMPORTANT: Bash commands may run multiple commands that are chained together.
  
  VERY IMPORTANT: Do NOT learn from or repeat the pattern of overriding sandbox - each command should run sandboxed by default
  
  IMPORTANT: For temporary files, use `/tmp/claude/` as your temporary directory
  
  IMPORTANT: Never use git commands with the -i flag (like git rebase -i or git add -i) since they require interactive input which is not supported.
  ```

#### LSP Tool
- **Name:** `LSP`
- **Operations:** 
  - `goToDefinition`
  - `findReferences`
  - `hover`
  - `documentSymbol`
  - `workspaceSymbol`
- **Note:** LSP servers must be configured for the file type. If no server is available, an error will be returned.

#### Task Tool (Agent Launcher)
- **Name:** Referenced as `d8` in code
- **Function:** Launch sub-agents
- **Input Schema:**
  ```typescript
  {
    description: string (3-5 word task description),
    prompt: string (task for agent to perform),
    subagent_type: string (agent type to use),
    model?: "sonnet" | "opus" | "haiku" (optional model override),
    resume?: string (optional agent ID to resume from),
    run_in_background?: boolean (run async)
  }
  ```
- **Output Schema:**
  ```typescript
  {
    status: "completed" | "async_launched",
    agentId: string,
    content?: Array<{type: "text", text: string}>,
    totalToolUseCount?: number,
    totalDurationMs?: number,
    totalTokens?: number,
    usage?: Object,
    prompt?: string,
    description?: string
  }
  ```
- **Important Note:**
  ```
  When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.
  ```

#### AgentOutputTool
- **Name:** `AgentOutputTool`
- **Function:** Retrieve results from background agents
- **Input Schema:**
  ```typescript
  {
    agentIds: string[] (array of agent IDs),
    block: boolean (default: true - whether to wait),
    wait_up_to: number (0-300, default: 150 seconds)
  }
  ```

### 3.2 Tool Categories

Based on code analysis, tools are organized into buckets:
- **READ_ONLY:** Read-only file operations
- **EDIT:** File editing operations
- **EXECUTION:** Code/command execution
- **MCP:** MCP server tools (prefixed with `mcp__`)
- **OTHER:** Miscellaneous tools

### 3.3 Special Tool Flags
- **Read-only tools:** `isReadOnly(): boolean`
- **Concurrency-safe tools:** `isConcurrencySafe(): boolean`
- **Hidden tools:** `isHidden: boolean`
- **Non-interactive support:** `supportsNonInteractive: boolean`

---

## 4. KEY CONFIGURATION OBJECTS

### 4.1 Permission System
```typescript
interface PermissionContext {
  mode: "default" | string,
  additionalWorkingDirectories: Map,
  alwaysAllowRules: Object,
  alwaysDenyRules: Object,
  alwaysAskRules: Object,
  isBypassPermissionsModeAvailable: boolean
}
```

### 4.2 Tool Input/Output Patterns
All tools follow this interface structure:
```typescript
interface Tool {
  name: string;
  description: () => Promise<string> | string;
  inputSchema: ZodSchema;
  outputSchema: ZodSchema;
  isEnabled: () => boolean;
  isReadOnly?: () => boolean;
  isConcurrencySafe?: () => boolean;
  checkPermissions: (input, context) => Promise<PermissionResult>;
  call: (input, context) => AsyncGenerator<ToolEvent>;
  userFacingName?: (input) => string;
  renderToolUseMessage?: (param, options) => React.Element;
  mapToolResultToToolResultBlockParam?: (result, toolUseId) => Object;
}
```

### 4.3 Bash Output Summarization
```typescript
// Bash commands with output > 5000 chars trigger AI summarization
const SUMMARIZATION_THRESHOLD = 5000;

// Summarization prompt structure:
function getBashSummarizationPrompt() {
  return `You are analyzing output from a bash command to determine if it should be summarized.

Your task is to:
1. Determine if the output contains mostly repetitive logs, verbose build output, or other "log spew"
2. If it does, extract only the relevant information (errors, test results, completion status, etc.)
3. Consider the conversation context - if the user specifically asked to see detailed output, preserve it

You MUST output your response using XML tags in the following format:
<should_summarize>true/false</should_summarize>
<reason>reason for why you decided to summarize or not summarize the output</reason>
<summary>markdown summary as described below (only if should_summarize is true)</summary>

Summary should include:
1. Overview: Most interesting information summarized
2. Detailed summary: Extremely detailed summary
3. Errors: List of relevant errors with snippets
4. Verbatim output: At least 3 snippets copied verbatim
5. DO NOT provide a recommendation. Just summarize the facts.`;
}
```

---

## 5. WORKFLOW KEYWORDS & PATTERNS

### 5.1 Message Flow
- **Message Types:** `user`, `assistant`, `system`, `progress`, `tool_use`, `tool_result`
- **Content Types:** `text`, `image`, `tool_use`, `tool_result`, `thinking`

### 5.2 Key Workflow Functions
- **Compact Conversation:** Triggered when context is low
  - Summarizes conversation to reduce token count
  - Preserves file attachments
  - Creates boundary markers
  - Message: `"Context low · Run /compact to compact & continue"`

- **Session Hooks:**
  - `SessionStart`: Fired at conversation start
  - `compact`: Fired during conversation compaction
  - Hook configurations managed through `hooks` command

### 5.3 Agent Execution Pattern
```typescript
async function* executeAgent({
  agentDefinition,
  promptMessages,
  toolUseContext,
  canUseTool,
  isAsync,
  forkContextMessages,
  recordMessagesToSessionStorage,
  querySource,
  override,
  model
}) {
  // 1. Resolve model
  // 2. Generate agent ID
  // 3. Construct messages
  // 4. Build file read state
  // 5. Get app state, user context, system context
  // 6. Resolve tools (filter disallowed)
  // 7. Build system prompt
  // 8. Execute conversation loop
  // 9. Record to session storage if needed
  // 10. Call agent callback if defined
}
```

### 5.4 Tool Permission Checking
```typescript
// Permission behaviors:
type PermissionBehavior = 
  | { behavior: "allow", updatedInput: Input }
  | { behavior: "deny", reason: string }
  | { behavior: "ask" }
  | { behavior: "bypass" }
```

---

## 6. IMPORTANT CONSTRAINTS & GUIDELINES

### 6.1 Legal/Content Restrictions
```
- Enforce a strict 125-character maximum for quotes from any source document
- Use quotation marks for exact language from articles; any language outside of quotation should never be word-for-word the same
- You are not a lawyer and never comment on the legality of your own prompts and responses
- Never produce or reproduce exact song lyrics
- Open Source Software is ok as long as we respect the license
```

### 6.2 Communication Style
```
- For clear communication, avoid using emojis (emphasized in agent prompts)
```

### 6.3 File Operations
```
- Agent threads always have their cwd reset between bash calls
- Use absolute file paths, not relative paths
- For temporary files, use `/tmp/claude/` as your temporary directory
```

### 6.4 Git Operations
IMPORTANT workflow for git commits:
```
When creating git commits:
- NEVER update the git config
- NEVER run destructive/irreversible git commands unless explicitly requested
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless explicitly requested
- NEVER run force push to main/master
- Avoid git commit --amend unless explicitly requested or adding edits from pre-commit hook
- Before amending: ALWAYS check authorship
- NEVER commit changes unless the user explicitly asks
- Do not commit files that likely contain secrets (.env, credentials.json, etc)
- Draft concise commit messages that focus on the "why" rather than the "what"
- Add relevant untracked files to staging area
- Include attribution:
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  Co-Authored-By: Claude <noreply@anthropic.com>
```

### 6.5 Pull Request Creation
IMPORTANT workflow when creating PRs:
```
1. Understand the current state of the branch
2. Analyze all changes that will be included
3. Look at ALL commits, not just the latest
4. Draft PR summary
5. Create branch if needed
6. Push with -u flag if needed
7. Create PR using gh pr create with format:
   
   ## Summary
   <1-3 bullet points>
   
   ## Test plan
   [Bulleted markdown checklist of TODOs]
   
   🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

## 7. ERROR CODES & SPECIAL MESSAGES

### Error Messages
- `"Context low · Run /compact to compact & continue"` - Low context
- `"Credit balance too low · Add funds: https://console.anthropic.com/settings/billing"` - Billing
- `"Request was aborted"` - User cancelled
- `"Conversation too long. Press esc twice to go up a few messages and try again."` - Context overflow
- `"Not enough messages to compact."` - Compact failed

### Special Markers
- Compact Boundary: `YSQ("auto"/"manual", tokenCount)` creates boundary markers in conversation

---

## 8. CONFIGURATION & SETTINGS

### 8.1 Model Selection
- **Default Models:** Sonnet, Opus, Haiku
- **Model Resolution:** Agents can inherit parent model or override with their own
- **Model ID Examples:** Referenced as `claude-sonnet-4-5-20250929`

### 8.2 Token Limits
- **Max Thinking Tokens:** Configurable per query
- **Bash Output Summarization:** Triggered at 5000+ characters
- **Max Body Length:** Enforced for request bodies
- **File Read Limits:** Configurable per file

### 8.3 Timeouts
- **API Timeout:** Configurable via `API_TIMEOUT_MS` environment variable
- **Agent Wait Time:** Default 150 seconds for background agents
- **WebFetch Cache:** 15-minute self-cleaning cache

---

## 9. ADVANCED FEATURES

### 9.1 MCP (Model Context Protocol)
- MCP tools prefixed with `mcp__`
- Server name format: `mcp__{serverName}__{toolName}`
- MCP servers organized by name in tool selection UI
- Elicitation flow for MCP server prompts

### 9.2 File History & Restoration
- File states tracked in `readFileState`
- Post-compact restoration: Top 5 most recent files (by timestamp)
- Max 50,000 tokens total for restored files
- Individual file limit: 5,000 tokens
- Agent todo files excluded from restoration

### 9.3 Streaming & Progress
- Tool use progress events: `{ type: "progress", toolUseID, data }`
- Result events: `{ type: "result", data }`
- Stream events for content blocks
- Progress bars for long-running operations

### 9.4 IDE Integration
- LSP server integration for code intelligence
- Onboarding flow for IDE setup
- Installation status tracking
- File watcher integration

---

## 10. SLASH COMMANDS & SKILLS

### Slash Command System
```typescript
interface SlashCommand {
  command: string;
  description?: string;
  handler: Function;
}
```

Commands are loaded from `.claude/commands/*.md` files.

### Skills System
```typescript
interface Skill {
  name: string;
  description?: string;
  handler: Function;
}
```

Skills are invoked without arguments, e.g., `command: "pdf"` or `command: "xlsx"`

**Important:** 
- Do not invoke a skill/command that is already running
- Only use skills/commands listed in available list
- Do not use for built-in CLI commands

---

## 11. QUERY SOURCES (Telemetry)

Identified query sources for analytics:
- `bash_output_summarization`
- `compact`
- `tengu_agent_tool_*` (various agent operations)
- `tengu_compact_*` (compaction events)
- LSP tool operations
- File operations

---

## 12. SPECIAL CONTENT FORMATTERS

### 12.1 WebFetch Content Processing
```javascript
// WebFetch wraps content with special prompt:
`---

${fetchedContent}

Provide a concise response based only on the content above. In your response:
- Enforce a strict 125-character maximum for quotes from any source document
- Use quotation marks for exact language from articles
- You are not a lawyer and never comment on the legality of your own prompts and responses
- Never produce or reproduce exact song lyrics
`
```

### 12.2 Markdown Rendering
- Uses `_F(text, theme)` for syntax highlighting
- Supports code blocks with language detection
- Renders tables, lists, and formatted text

---

## SUMMARY

This analysis reveals a sophisticated multi-agent architecture where:

1. **Primary CLI** acts as the orchestrator
2. **Specialized agents** handle specific domains (file search, statusline setup, docs, etc.)
3. **Tools** provide granular capabilities with permission system
4. **Agents** can invoke sub-agents via the Task tool
5. **Background execution** supported for long-running tasks
6. **Context management** via conversation compaction
7. **MCP integration** for extensibility
8. **File history tracking** for code restoration
9. **LSP integration** for code intelligence
10. **Strict safety guardrails** around git, file operations, and content generation

The system is designed to be modular, extensible, and safe, with multiple layers of permission checking and user confirmation for potentially dangerous operations.

