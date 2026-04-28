# Feature Specification: 输入结构化 Skill

**Feature Branch**: `002-input-structure-skill`
**Created**: 2026-04-27
**Status**: Draft
**Input**: User description: "将用户提供的 PDF/PPT/DOCX/TXT 补充材料转换为结构化 Markdown，供产品 Agent 下游消费。纯格式转换，不做意图理解、不做证据归类。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 产品 Agent 解析客户提供的 PDF 补充材料 (Priority: P1)

产品 Agent 收到用户的写作需求（自然语言）以及一份或多份 PDF 补充材料。在进入规格化（specify）步骤之前，产品 Agent 调用输入结构化 Skill，将 PDF 转换为按页组织的结构化 Markdown，连同用户的原始需求文本一并返回，供下游直接消费。

**Why this priority**: PDF 是医学写作场景中最常见的客户材料格式（临床报告、文献、指南）。支持 PDF 解析是 Skill 的核心价值。

**Independent Test**: 提供一份 5 页的 PDF 文件和一个一句话写作需求，Skill 返回包含用户原文 + PDF 逐页结构化内容的 Markdown。

**Acceptance Scenarios**:

1. **Given** 用户输入"写一篇关于仑卡奈单抗的科普文章"并附上一份 3 页 PDF，**When** 产品 Agent 调用输入结构化 Skill，**Then** 返回的 Markdown 中「用户写作需求」章节包含完整原始语句，「补充材料」章节包含 PDF 每页的文本内容和页码标注
2. **Given** PDF 中包含标题层级，**When** Skill 解析该 PDF，**Then** 输出保留标题层级结构，以 Markdown heading 表示
3. **Given** PDF 某页为纯扫描件（无可提取文本层），**When** Skill 解析该页，**Then** 使用 PaddleOCR 进行文字识别，输出提取到的文本并标注 `[第X页 — OCR 识别]`，不中断整体解析
4. **Given** PDF 中包含表格（文本层或扫描件），**When** Skill 解析，**Then** 表格内容转换为 Markdown table 格式（`| 列1 | 列2 |`），保留表头行
5. **Given** PDF 中包含图表（柱状图/折线图/流程图等），**When** Skill 解析，**Then** 提取图表原图并保存为 PNG 到 `assets/` 子目录，Markdown 中以相对路径 `![图题](./assets/文件名_pX_figN.png)` 引用，并提取图题文本

---

### User Story 2 - 产品 Agent 解析客户提供的 PPT/DOCX/TXT 材料 (Priority: P2)

客户可能以 PPT（产品宣讲、会议演示）、DOCX（医学报告、文献综述）或 TXT（纯文本笔记）格式提供补充材料。Skill 需统一处理这些格式，输出结构化 Markdown。

**Why this priority**: PDF 之外的高频格式。PPT 和 DOCX 的结构化信息（标题层级、备注、段落）对下游产品 Agent 理解材料有重要价值。

**Independent Test**: 提供一份含 5 张幻灯片的 PPT 文件，Skill 返回 Markdown，包含每张幻灯片的标题、正文、备注。

**Acceptance Scenarios**:

1. **Given** 用户上传一份 10 页 PPT，**When** Skill 解析，**Then** 输出每张幻灯片的标题、正文内容和备注，以 `### Slide N — 标题` 格式组织
2. **Given** 用户上传一份包含多级标题的 DOCX，**When** Skill 解析，**Then** 输出保留标题层级（Heading 1/2/3 → #/##/###）和段落结构
3. **Given** 用户上传一份 TXT 文件，**When** Skill 解析，**Then** 输出按空行自然分段，无空行时原样保留全文
4. **Given** 用户同时上传 PDF + PPT + DOCX 三种格式的材料，**When** Skill 解析，**Then** 所有材料按文件名分别展示，顺序与输入顺序一致

---

### User Story 3 - 纯文本输入时跳过解析 (Priority: P3)

用户可能只写了写作需求而不提供任何补充文件。此时 Skill 直接透传用户需求，不报错、不额外处理。

**Why this priority**: 无材料场景是合法的用户路径，必须保证不阻塞下游流程。

**Independent Test**: 仅传入用户自然语言描述（无文件），Skill 返回仅含「用户写作需求」章节的有效 Markdown。

**Acceptance Scenarios**:

1. **Given** 用户只输入了写作需求（无补充文件），**When** 产品 Agent 调用输入结构化 Skill，**Then** 返回的 Markdown 仅包含「用户写作需求」章节，「补充材料」章节标注「无」
2. **Given** 用户上传了一个被支持但为空（0 字节）的文件，**When** Skill 解析，**Then** 标注 `[文件名 — 空文件]`，不抛异常

---

### Edge Cases

- **不支持的文件格式**（如 .xlsx、.jpg、.mp4）：输出 `[文件名 — 不支持的格式：.xxx]`，不中断流程
- **文件不存在或无法读取**：输出 `[文件名 — 无法读取：原因]`，继续处理其余文件
- **PDF 有密码保护**：输出 `[文件名 — 加密PDF，无法解析]`
- **扫描件 OCR 超时（单页 >30s）**：跳过该页，标注 `[第X页 — OCR 超时]`，继续处理后续页面
- **扫描件 OCR 质量过低（置信度 <60%）**：标注 `[第X页 — OCR 识别质量低]`，仍输出已识别文本
- **表格结构复杂（合并单元格/嵌套表格）**：尽力转换为 Markdown table，无法转换部分以缩进文本保留
- **PPT/DOCX 包含大量嵌入图片**：提取图片并保存到 `assets/`，提取替代文本作为图题；无替代文本时仅标注 `[图片 — Slide N]`
- **图表原图损坏或无法提取**：标注 `[图表 — 第X页，无法提取原图]`，仍输出图题文本
- **单文档图片数量过多（>50张）**：全部提取保存，但主 Markdown 中只内联前 20 张，其余以文件列表形式附录在末尾
- **超大文件（>50MB）**：输出 `[文件名 — 文件过大，跳过解析]`
- **同一文件被多次传入**：去重处理，每个文件只解析一次
- **文件名含特殊字符**：正常处理，不因文件名异常而崩溃

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Skill 必须接收用户的自然语言描述和零到多个文件路径作为输入
- **FR-002**: Skill 必须输出统一的结构化 Markdown，包含「用户写作需求」和「补充材料」两个章节
- **FR-003**: Skill 必须能从 PDF 文件中按页提取文本，标注页码（`### 第N页`）
- **FR-004**: Skill 必须能从 PPT 文件中按幻灯片提取标题、正文、备注
- **FR-005**: Skill 必须能从 DOCX 文件中按段落提取文本，保留标题层级（Heading → Markdown heading）
- **FR-006**: Skill 必须能从 TXT 文件中提取文本，按空行自然分段
- **FR-007**: 处理多个文件时，Skill 必须按输入顺序组织输出，每个文件独立展示
- **FR-008**: 单个文件解析失败不得中断其他文件的解析
- **FR-009**: Skill 不得对内容做意图理解、摘要、证据归类或任何形式的语义处理
- **FR-010**: Skill 必须对不支持/损坏/加密/过大/不存在的文件给出明确的跳过说明
- **FR-011**: Skill 必须使用 PaddleOCR 对无文本层的扫描件 PDF 页面进行文字识别
- **FR-012**: Skill 必须将 PDF 中的表格转换为 Markdown table 格式（`| col | col |` + `|---|---|` 分隔行）
- **FR-013**: Skill 必须识别 PDF 中的图表（figure/chart），提取并保存原图为 PNG 到 `assets/` 子目录，Markdown 中以相对路径 `![图题](./assets/文件名_pX_figN.png)` 引用
- **FR-014**: Skill 必须将提取的图片文件组织在输出根目录的 `assets/` 子目录中，命名格式为 `{源文件名}_p{页码}_fig{序号}.png`，避免冲突

### Key Entities

- **StructuredInput**: Skill 的顶层输出。包含：用户原始需求文本、补充材料列表（有序）、解析时间戳、`assets/` 图片资源目录
- **ParsedMaterial**: 单个文件的解析结果。包含：文件名、原始格式、页码/幻灯片数/段落数等规模信息、结构化文本内容（含图片相对路径引用）
- **ParsedImage**: 从文档中提取的图表图片。包含：源文件名、所在页码、图片序号、图题文本、保存路径（`assets/{源文件}_p{页码}_fig{序号}.png`）
- **ParseError**: 单个文件解析失败时的记录。包含：文件名、失败原因、是否阻塞整体流程（始终为否）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 给定一份 10 页以内的有文本层 PDF，Skill 在 5 秒内（墙钟时间，含文件读写，不含模型首次加载）完成解析返回结果
- **SC-001a**: 给定一份 10 页以内的纯扫描件 PDF，Skill 在 60 秒内（墙钟时间，含文件读写，不含 PaddleOCR 模型首次加载）完成 OCR 解析返回结果
- **SC-002**: 给定一份 20 张幻灯片以内的 PPT，Skill 在 3 秒内（墙钟时间，含文件读写）完成解析返回结果
- **SC-003**: Skill 支持的文件格式覆盖 PDF、PPT（.pptx）、DOCX（.docx）、TXT（.txt）四种
- **SC-004**: 一次传入 5 个不同类型的文件，即使其中 2 个解析失败，其余 3 个的正常解析结果不受影响
- **SC-005**: 无文件传入时，Skill 不报错，返回仅含用户需求原文的有效 Markdown
- **SC-006**: PDF 中的表格转换为 Markdown table 后，行列结构保持正确（行数、列数与原表格一致）

## Assumptions

- 产品 Agent 在调用 Skill 前已完成文件上传/接收，Skill 接收的是本地文件路径
- PPT 解析仅支持 .pptx 格式，不支持旧版 .ppt 格式（可通过外部工具预转换）
- DOCX 解析仅支持 .docx 格式，不支持旧版 .doc 格式
- 有文本层的 PDF 直接提取文本；纯扫描件 PDF 通过 PaddleOCR 进行文字识别
- 服务器已预装 PaddleOCR 及其中文模型，Skill 可直接调用
- TXT 文件默认 UTF-8 编码，非 UTF-8 编码尝试系统默认编码兜底
- Skill 是产品 Agent 内部的同步调用，不涉及网络通信或外部服务

---

## Clarifications

### Session 2026-04-28

- **Q1**: 纯扫描件 PDF（无可提取文本层）如何处理？ → **A**: 使用 PaddleOCR 进行文字识别。新增 FR-011，扫描件页面标注 `[第X页 — OCR 识别]`，OCR 超时（单页>30s）跳过，置信度<60% 标注低质量警告但仍输出文本
- **Q2**: PDF 中的图表（表格、柱状图、折线图、流程图等）如何处理？ → **A**: 表格转 Markdown table（FR-012），保持行列结构；图表/图形提取原图保存为 PNG 到 `assets/` 子目录（FR-013），Markdown 中 `![图题](./assets/...)` 相对路径引用（FR-014），保留图题文本，不生成语义描述以保持"纯格式转换"定位
- **Q3**: 图表原图是否需要保存下来作为写作证据？ → **A**: 是。使用 PyMuPDF/python-pptx 等库从源文档中提取嵌入图片，统一保存为 PNG，按 `{源文件名}_p{页码}_fig{序号}.png` 命名，供下游 Agent 引用
- **Q4**: 性能指标的测量范围是什么？ → **A**: 墙钟时间（wall-clock），含文件读写，不含 OCR/ML 模型首次加载。已更新 SC-001/001a/002 描述
- **Q5**: (speckit-analyze 修复) 交叉分析发现 4 个 MEDIUM 问题 → **A**: 全部修复：SC-004 引用错误已更正、去重边缘案例已加入 T027、FR-009 已在 T027 追加验证、性能基准已加入 T025
