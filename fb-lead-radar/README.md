# Facebook Lead Radar

基于 [Agent-Reach](https://github.com/Panniantong/Agent-Reach) 构建的 Facebook 线索雷达工具。

**只做线索收集和评分，不做任何自动外联。** 所有私信/评论/加好友操作由人工完成。

---

## 快速开始（3 分钟）

### Windows 用户

双击 `run.bat` 即可启动。

### macOS / Linux 用户

```bash
cd fb-lead-radar
./run.sh
```

### 手动运行

```bash
cd fb-lead-radar

# 创建虚拟环境（首次运行）
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 安装依赖（首次运行）
pip install -e ../Agent-Reach

# 检查状态
python lead_radar.py doctor

# 用示例数据试一下
python lead_radar.py manual --file sample_posts.txt --show
```

---

## 两种使用模式

### 模式一：手动导入（推荐先用这个）

**适合：** 刚开始用、还没配置 OpenCLI、想先看看效果

**操作流程：**
1. 在 Facebook 群里逛，看到有需求的帖子
2. 把帖子内容复制到 `input_posts.txt` 里（用 `---` 分隔多条）
3. 运行 `python lead_radar.py manual --file input_posts.txt`
4. 看 `reports/` 里的每日报告，挑 Top 10 去私信

**帖子文件格式：**

```
name: Sarah Johnson
url: https://www.facebook.com/groups/xxx/posts/xxx
group: Shopify Sellers Unite
comments: 5

Hey everyone! I've been building my Shopify store... （帖子内容）

---

name: Mike Chen
url: https://www.facebook.com/groups/xxx/posts/yyy
group: Ecommerce Growth Hacks
comments: 23

I'm getting good traffic but zero sales... （第二条帖子）
```

可以复制 `input_posts_template.txt` 改着用。

### 模式二：自动搜索 Facebook

**适合：** 每天要搜很多群，想省时间

**前置条件：**
- 你自己的电脑（Windows/macOS/Linux 桌面版）
- Chrome 浏览器
- 已在 Chrome 中登录 Facebook（**建议用小号**）

**配置步骤（5 分钟）：**

1. **安装 Node.js**（如果还没有）
   - 下载：https://nodejs.org/ （LTS 版本就行）
   - 装完后打开命令行输入 `node --version`，有版本号就装好了

2. **安装 OpenCLI**
   ```bash
   npm install -g @jackwener/opencli
   ```

3. **安装 Chrome 扩展**
   - 打开：https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
   - 点「添加至 Chrome」

4. **验证安装**
   ```bash
   opencli doctor
   ```
   看到 `Extension: connected` 就成功了。

5. **登录 Facebook**
   - 在 Chrome 里打开 facebook.com 并登录
   - 建议用专门的小号，不要用主号

6. **运行搜索**
   ```bash
   python lead_radar.py search --top 10
   ```

---

## 命令大全

```bash
# 检查环境状态
python lead_radar.py doctor

# 手动导入帖子文件
python lead_radar.py manual --file input_posts.txt
python lead_radar.py manual --file input_posts.txt --show   # 同时在终端显示预览
python lead_radar.py manual --file input_posts.txt --top 20 # 输出 Top 20

# 快速评分单条帖子
python lead_radar.py score-one --text "帖子内容..."
python lead_radar.py score-one --text "帖子内容..." --name "张三" --comments 5

# 自动搜索 Facebook（需配置 OpenCLI）
python lead_radar.py search
python lead_radar.py search --top 20
python lead_radar.py search --per-keyword 15
```

---

## 评分规则（总分 10 分）

| 维度 | 分值 | 加分项 | 减分项 |
|------|------|--------|--------|
| 需求明确度 | 0-2 | need help、review my store、no sales、building phase | 需求模糊、随便问问 |
| 能力匹配度 | 0-2 | 产品页、主页、布局、视觉、短视频、第一印象 | 广告投放、代运营、保销量、SEO 保证 |
| 客户真实度 | 0-2 | 有网站链接、真实产品、详细描述、第一人称 | 信息太少、无具体产品 |
| 竞争程度 | 0-2 | 评论少（≤3条）、刚发布 | 评论多（>20条）、服务商刷屏 |
| 小单成交性 | 0-2 | 新店、建设期、具体小需求、只想修一部分 | 要完整团队、长期运营、整站代管 |

**联系建议：**
- **YES** (≥7分)：建议联系，高质量线索
- **MAYBE** (5-7分)：可以试试，看你时间
- **NO** (<5分 or 被跳过)：不建议联系

---

## 需求分类

| 类型 | 说明 |
|------|------|
| store_review | 店铺求点评 |
| no_sales | 有流量没转化 |
| building_phase | 店铺建设中 |
| shopify_designer_needed | 找 Shopify 设计师 |
| product_page_help | 产品页需要帮助 |
| product_visuals_needed | 需要产品视觉素材 |
| promo_video_needed | 需要推广短视频 |
| digital_product_store | 数字产品店 |
| handmade_or_craft_store | 手工/手作店 |
| unclear_or_low_quality | 需求不明确/低质量 |

---

## 自动跳过的线索

以下情况直接跳过，不进入评分：

- 🚫 纯广告帖 / 服务商发帖（"我提供..."、"DM me" 等）
- 🚫 要账号代管 / 整店运营的
- 🚫 要保证销量 / 保证 ROI 的
- 🚫 明显 scam（被动收入、快速致富等）
- 🚫 帖子内容过短，没有具体需求
- 🚫 评论区被大量服务商刷屏的

---

## 私信建议

### ✅ 应该做的
- 短，像真人说话
- 只问一个问题
- 先让对方发店铺/产品
- 把范围拉到 small first fix
- 强调自己不是大 agency

### ❌ 不要做的
- 一上来提 USDT
- 说自己是 Shopify expert
- 承诺 generate sales
- 说 guaranteed results
- 长篇大论

### 示例话术

```
I can take a quick look from a product page / first impression angle.
What are you selling?
```

```
I'm not a big Shopify agency, but I can help with product page layout,
homepage sections, and promo visuals. Send the store link and I'll tell you
the first thing I'd fix.
```

```
Product page layout is what I do. Send your store link and I'll tell you
the first thing I'd change.
```

---

## 项目结构

```
fb-lead-radar/
├── run.bat                   # Windows 一键启动
├── run.sh                    # macOS/Linux 一键启动
├── lead_radar.py             # 主入口 CLI
├── models.py                 # 数据模型
├── scoring.py                # 评分引擎
├── keywords.py               # 关键词配置
├── facebook_search.py        # Facebook 搜索适配器 (OpenCLI)
├── manual_import.py          # 手动导入解析
├── report_generator.py       # 报告生成器 (Markdown + CSV)
├── sample_posts.txt          # 示例帖子数据
├── input_posts_template.txt  # 输入模板
├── README.md                 # 你正在看的
└── reports/                  # 输出报告目录
    ├── daily_facebook_leads_YYYY-MM-DD.md
    └── daily_facebook_leads_YYYY-MM-DD.csv
```

---

## 常见问题

**Q: 为什么不用 Facebook Graph API？**
A: Graph API 的 Groups 权限审批非常严格，普通开发者拿不到。用浏览器登录态是目前最实用的方案。

**Q: 会被封号吗？**
A: 只要你只是正常浏览和搜索，不批量操作、不发垃圾信息，风险很低。但建议用小号，不要用主号。

**Q: 可以加更多关键词吗？**
A: 可以，编辑 `keywords.py` 里的 `KEYWORDS` 列表即可。

**Q: 评分规则可以调整吗？**
A: 可以，所有评分逻辑都在 `scoring.py` 里，可以根据你的业务特点修改权重和规则。

**Q: Facebook 搜索用不了怎么办？**
A: 先用手动导入模式。把你在 Facebook 群里看到的帖子复制下来评分，一样能用。

**Q: 报告存在哪里？**
A: `reports/` 目录下，每天一个 Markdown 文件和一个 CSV 文件。

---

## 红线（绝对不做）

- ❌ 不自动私信
- ❌ 不自动评论
- ❌ 不自动加好友
- ❌ 不自动发帖
- ❌ 不绕过平台规则
- ❌ 不批量骚扰用户
- ❌ 不读取非公开信息

这个工具只是帮你节省找线索的时间，最终联系由你手动完成。

---

## License

MIT
