# Bionic EPUB Generator 计划

## 1. 项目目标

开发一个本地命令行工具，把普通的 DRM-free EPUB 转换成适合 Kobo 阅读的仿生阅读版本。

工具会对英文正文中的单词开头部分加粗，例如：

```text
reading    ->    reading
understand ->    understand
```

实际 EPUB 中使用 HTML 标签表达加粗，而不是生成字体文件：

```html
<strong>read</strong>ing
<strong>under</strong>stand
```

原 EPUB 不被修改，工具输出一个新的 EPUB 文件。

## 2. 产品形态

### 第一阶段：CLI

CLI 是第一版的主要界面，适合个人使用、批量处理和快速迭代规则。

预期用法：

```powershell
bionic-epub input.epub -o output-bionic.epub
```

常用选项：

```powershell
bionic-epub input.epub -o output.epub --strength light
bionic-epub input.epub -o output.epub --strength strong --process-headings
bionic-epub input.epub --preview
```

### 第二阶段：可选本地 UI

只有在 CLI 的转换效果稳定后，才考虑增加本地网页 UI。UI 只负责文件选择、参数选择、文本预览和下载，不能复制核心转换逻辑。

## 3. MVP 范围

第一版必须完成：

- 接受一个 EPUB 输入文件
- 输出一个新的 EPUB 文件
- 保留原有章节、图片、字体、目录和元数据
- 处理 XHTML/HTML 正文中的英文单词
- 对每个单词的前缀加粗
- 提供轻度、标准、强度三种加粗级别
- 支持自定义输出路径
- 输出清晰的错误信息
- 不覆盖输入文件
- 检查生成文件是否仍然是有效 EPUB

第一版暂不包含：

- DRM 破解或 DRM 书籍处理
- 在线上传和云端转换
- 原生 Windows GUI
- OCR 或扫描版书籍识别
- 自动翻译
- 修改原 EPUB 的排版主题
- 多语言复杂断词规则

## 4. 转换规则

### 4.1 默认单词规则

建议使用基于单词长度的规则，而不是固定加粗字符数：

| 单词长度 | 默认加粗部分 |
| --- | --- |
| 1-3 | 全部 |
| 4-5 | 前 2 个字符 |
| 6-7 | 前 3 个字符 |
| 8 个及以上 | 前 40% 至 50% |

加粗比例应该通过 `strength` 配置控制，具体数值在测试样本文本上校准。

### 4.2 应跳过的内容

默认不处理：

- HTML 标签和属性
- URL 和邮箱地址
- 纯数字
- 代码片段
- 空白字符
- 已经位于 `<strong>`、`<b>`、标题或特殊注释中的内容，除非用户显式开启

需要保留：

- 原有标点
- 连字符和撇号
- 斜体、链接、脚注和其他内嵌 HTML 结构
- 原始空格和换行语义

### 4.3 HTML 处理原则

不能通过简单的全文字符串替换处理 EPUB。应使用 HTML/XML 解析器遍历文本节点，只修改文本内容，避免破坏标签嵌套和链接结构。

建议优先使用 `<strong>`，并通过 CSS 保持 Kobo 上的常规粗体表现。如果测试发现某些阅读器对嵌套标签处理不稳定，再评估使用专用 CSS class。

## 5. 技术方案

建议使用 Python 实现：

- `zipfile`：读取和重新打包 EPUB
- `lxml`：解析和修改 XHTML/XML
- `argparse` 或 `typer`：构建 CLI
- `pytest`：自动化测试
- `epubcheck`：生成文件的 EPUB 规范检查

建议项目结构：

```text
bio_generator/
├── plan.md
├── pyproject.toml
├── README.md
├── src/
│   └── bionic_epub/
│       ├── __init__.py
│       ├── cli.py
│       ├── converter.py
│       ├── tokenizer.py
│       ├── epub_io.py
│       ├── html_transformer.py
│       └── validator.py
├── tests/
│   ├── fixtures/
│   ├── test_tokenizer.py
│   ├── test_html_transformer.py
│   ├── test_epub_io.py
│   └── test_cli.py
└── examples/
```

## 6. EPUB 处理流程

1. 检查输入文件存在，扩展名为 `.epub`。
2. 解压到临时目录。
3. 读取 `META-INF/container.xml`，找到 OPF 文件。
4. 根据 OPF manifest 找到 XHTML/HTML 内容文档。
5. 遍历正文文本节点，按规则生成加粗前缀。
6. 将修改后的 XHTML 写回临时目录。
7. 按 EPUB 要求重新打包，确保 `mimetype` 是 ZIP 中的第一个文件且未压缩。
8. 输出到用户指定路径。
9. 对输出文件执行结构检查和可选的 EPUBCheck。
10. 打印输出路径、处理章节数和处理单词数。

## 7. CLI 设计

初步命令：

```text
bionic-epub convert INPUT -o OUTPUT [OPTIONS]
bionic-epub preview INPUT [OPTIONS]
bionic-epub validate INPUT
bionic-epub --version
```

建议选项：

```text
--strength {light,standard,strong}
--ratio FLOAT
--process-headings
--process-toc
--language LANG
--overwrite
--keep-temp
--verbose
```

默认行为应当偏保守：只处理正文、使用标准强度、拒绝覆盖已有输出文件。

## 8. 预览功能

CLI 的 `preview` 命令不需要生成完整 EPUB，可以输出一小段转换前后的文本：

```text
Before: The quick brown fox jumps over the lazy dog.
After:  The quick brown fox jumps over the lazy dog.
```

预览功能用于快速比较不同 `strength` 和 `ratio` 参数，降低反复导入 Kobo 的成本。

## 9. 测试策略

### 单元测试

覆盖：

- 不同长度的英文单词
- 大小写单词
- 标点和引号
- 连字符单词
- 撇号单词
- 数字、URL、邮箱和代码
- 已有粗体和斜体标签
- 链接和脚注中的文本
- 空文本节点

### EPUB 集成测试

准备至少三类 fixture：

1. 简单单章节 EPUB
2. 包含图片、CSS、字体和目录的小说 EPUB
3. 包含脚注、链接、嵌套标签和特殊字符的复杂 EPUB

需要验证：

- 输出文件可以正常解压
- `mimetype` 和 `container.xml` 正确
- OPF 和目录仍然可用
- 图片和字体未改变
- XHTML 可以重新解析
- 原 EPUB 的哈希或文件内容未被修改
- 输出文件能通过 EPUBCheck（如果本机已安装）

### 人工验收

将生成结果导入 Kobo，检查：

- 章节可以正常打开
- 翻页、目录、脚注和链接正常
- 粗体效果清楚但不过度干扰阅读
- 原有字体和主题没有明显变化
- 横屏、竖屏和不同字号下没有异常排版

## 10. 开发里程碑

### Milestone 1：规则原型

- 实现单词切分和前缀比例计算
- 完成 tokenizer 单元测试
- 用纯文本确认三种强度的视觉效果

### Milestone 2：HTML 转换

- 解析 XHTML 文本节点
- 保留原有标签和实体
- 完成嵌套标签测试

### Milestone 3：EPUB 读写

- 找到 EPUB 内容文档
- 修改并重新打包 EPUB
- 完成结构校验

### Milestone 4：CLI

- 加入参数解析
- 加入错误处理和进度输出
- 支持 preview、convert、validate

### Milestone 5：Kobo 验收

- 使用真实的 DRM-free EPUB 测试
- 调整默认加粗比例
- 修复阅读器兼容性问题
- 编写 README 使用说明

### Milestone 6：评估 UI

只有当以下需求出现时才增加 UI：

- 需要频繁调整参数
- 需要直观预览排版
- 需要让非技术用户使用
- 需要批量拖拽文件

## 11. 完成标准

MVP 完成的判断标准：

- 一条 CLI 命令可以生成新的 EPUB
- 生成后的 EPUB 可以导入 Kobo 并正常阅读
- 原始章节、图片、目录、脚注和链接未被破坏
- 转换规则有自动化测试
- 常见错误会给出可理解的提示
- README 中包含安装、使用和限制说明

## 12. 设计结论

项目的核心产品是可靠的 EPUB 转换引擎，CLI 是第一版最合适的交互方式。UI 不作为核心依赖，而作为未来对预览和参数调节的补充。因此应先把命令行、转换算法和 Kobo 兼容性做好，再根据实际使用频率决定是否增加 UI。
