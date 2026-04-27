<!--
SYNC IMPACT REPORT
==================
Version Change: TEMPLATE → 1.0.0 (MINOR bump - initial constitution ratification)
Modified Principles: All 5 principles newly defined from template placeholders
Added Sections:
  - I. Protected Master Branch (分支保护)
  - II. Feature Branch Workflow (特性分支工作流)
  - III. Dual Environment Deployment (双环境部署)
  - IV. Deployment Gatekeeping (部署门禁)
  - V. Minimum Invasive Changes (最小侵入性)
Removed Sections: None
Templates Requiring Updates:
  - ✅ plan-template.md: Constitution Check section aligns with principles I-V
  - ✅ spec-template.md: Branch naming conventions referenced
  - ⚠️ commands/*.md: No updates required (generic guidance)
  - ⚠️ AGENTS.md: Source of truth for branch rules; cross-reference maintained
Deferred Items: None
Ratification Date: 2026-04-02
-->

# 慧度生态 Constitution

## Core Principles

### I. Protected Master Branch (受保护主分支)

**MUST**: `master` 分支是唯一可部署到生产环境的分支，受保护且仅允许通过 Pull Request 合并代码。

**MUST NOT**: 严禁直接推送代码到 `master` 分支；严禁在 `master` 分支直接修改代码。

**Rationale**: 生产环境稳定性要求单一可信源，`master` 作为唯一部署目标避免环境漂移和未经审核的代码进入生产。

**Scope**: 适用于 ai-awesome-material-platform、XiaKe-Island、cang、V2medical-kb-system 所有子项目。

---

### II. Feature Branch Workflow (特性分支工作流)

**MUST**: 所有新功能和修复必须从 `master` 创建分支，遵循命名规范：
- 功能分支：`feature/xxx-需求名称`
- 修复分支：`fix/xxx-问题描述`

**MUST**: 开发完成后通过 GitHub 提交 PR 到 `master`，经代码审查后方可合并。

**NOTES**: `develop` 分支已废弃，不再使用。所有工作流简化为 master + feature/* 模式。

**Rationale**: 简化分支模型减少认知负担，PR 流程确保代码审查和质量门禁。

---

### III. Dual Environment Deployment (双环境部署)

**MUST**: 维护生产环境和开发环境两套独立部署：
- 生产环境：`/` 路径，端口 3000，构建输出 `dist/`
- 开发环境：`/dev/` 路径，端口 3002，构建输出 `dist-dev/`

**MUST**: 前端和后端服务在双环境中使用独立端口和配置，避免相互干扰。

**Rationale**: 开发测试与生产服务隔离，确保开发中的代码不会意外影响线上用户。

---

### IV. Deployment Gatekeeping (部署门禁)

**MUST**: 生产部署脚本 (`./deploy.sh`) 执行前强制校验：
- 当前分支必须是 `master`
- 工作区必须干净（无未提交更改）

**MUST**: 校验失败时部署脚本必须拒绝执行并给出明确错误信息。

**Rationale**: 防止开发分支或未完成的代码被误部署到生产环境，最后一道人工防线。

---

### V. Minimum Invasive Changes (最小侵入性)

**SHOULD**: 新功能开发遵循最小变更原则：
- 仅修改必要的文件
- 不引入新的架构模式除非有明确必要性
- 复用现有基础设施（如 SQLite 连接模式、API 客户端）

**SHOULD**: 积极清理技术债务，删除重复代码，减少维护面。

**Rationale**: 降低变更风险，保持代码库可维护性，避免过度工程化。

---

## Development Environment Standards (开发环境规范)

### Backend Service Ports

| 环境 | 服务 | 端口 | 启动命令 |
|------|------|------|----------|
| 生产 | 素材平台后端 | 3000 | `npm run build && npm start` |
| 开发 | 素材平台后端 | 3002 | `npm run dev` |
| 生产/开发 | 侠客岛服务 | 8000 | `python main.py` |
| 生产/开发 | Nginx | 80 | `docker restart material-platform-nginx` |

### Frontend Build Outputs

- 生产构建：`frontend/dist/` → 服务根路径 `/`
- 开发构建：`frontend/dist-dev/` → 服务 `/dev/` 路径

### Database

- **Type**: SQLite3
- **Location**: `backend/data/app.db`
- **Constraint**: 保持与现有数据库 schema 兼容，最小化变更

---

## Governance

### Amendment Procedure (修宪程序)

1. **Proposal**: 任何原则修改需通过 GitHub Issue 或 PR 提出
2. **Review**: 核心维护者审查，评估对现有工作流的影响
3. **Approval**: 涉及 MUST 原则变更需团队共识
4. **Documentation**: 更新 constitution.md 版本号和修订日期
5. **Propagation**: 检查并同步更新依赖模板（plan-template.md, spec-template.md 等）

### Versioning Policy (版本策略)

遵循语义化版本控制：
- **MAJOR**: 原则移除或重新定义，向后不兼容的治理变更
- **MINOR**: 新增原则或章节，实质性扩展指导范围
- **PATCH**: 措辞澄清、格式调整、非语义性完善

### Compliance Review (合规审查)

- 所有 PR 必须验证是否符合分支管理规范（Principle I & II）
- 部署前必须确认环境配置符合双环境规范（Principle III）
- 复杂变更需论证最小侵入性原则遵循情况（Principle V）

---

**Version**: 1.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02
