
## 当前逆向分析任务说明
- 目标文件：单体混淆版 `cli.js`（TypeScript 编译产物，Node.js 运行）。  
- 需求概览：  
  1. 全面梳理 Agentic coding 工具的主要工作流程，列出所有中间节点及其作用。  
  2. 识别工具列表，记录各工具的提示语（prompt）与典型应用场景。  
  3. 解析上下文管理机制（会话状态、权限、任务缓存等）。  
  4. 提取全部可用 prompt，并推测意图与触发情境。  
- 参考资料：  
  - 通用工作流：https://docs.claude.com/en/docs/claude-code/common-workflows  
  - 插件系统：https://docs.claude.com/en/docs/claude-code/plugins  
  - 技能系统：https://docs.claude.com/en/docs/claude-code/skills  
  - 子代理功能：https://docs.claude.com/en/docs/claude-code/sub-agents  
- 先对主流程框架建模，再归档工具 & prompt 细节，保持笔记集中存放于 `Codex_analysis/`。


## Workspace Safety Rules
- 所有新增文件和修改后的版本都必须落在 `Codex_analysis/` 目录下；提交前请确认路径正确。  
- 严禁访问或引用 `CC_analysis/` 目录中的任何内容，避免引入不合规资料。