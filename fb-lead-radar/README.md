# Facebook Lead Radar

基于 [Agent-Reach](https://github.com/Panniantong/Agent-Reach) 构建的 Facebook 线索雷达工具。

**只做线索收集和评分，不做任何自动外联。** 所有私信/评论/加好友操作由人工完成。

## 功能

- 🔍 **Facebook 群帖关键词搜索**（通过 OpenCLI 复用 Chrome 登录态）
- 📊 **智能评分系统**（10 分制，5 个维度）
- 🏷️ **需求分类**（10 种需求类型自动识别）
- 📝 **每日 Top 10 报告**（Markdown + CSV 格式）
- ✋ **手动导入模式**（粘贴帖子内容/链接即可评分）
- 💬 **人工私信建议**（真人风格，不 AI 味）

## 红线（绝对不做）

- ❌ 不自动私信
- ❌ 不自动评论
- ❌ 不自动加好友
- ❌ 不自动发帖
- ❌ 不绕过平台规则
- ❌ 不批量骚扰用户
- ❌ 不读取非公开信息

## 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd fb-lead-radar

# 使用虚拟环境（已在上级目录创建）
source ../venv/bin/activate
```

### 2. 检查状态

```bash
python lead_radar.py doctor
```

会检查三个部分：
- Agent-Reach 及 Facebook 渠道状态
- OpenCLI 安装及连接状态
- Lead Radar 核心模块

### 3. 使用方式

#### 方式 A：手动导入（推荐先用这个）

适用于：
- 服务器/无桌面环境
- Facebook 搜索暂时不可用
- 你已经手动找到了一些帖子想快速评分

创建一个帖子文件 `my_posts.txt`，格式如下：

```
name: 发帖人名字
url: https://www.facebook.com/groups/xxx/posts/xxx
group: 群组名称
profile_url: https://www.facebook.com/xxx
time: 2 hours ago
comments: 5

帖子内容...可以很长
---
name: 另一个人
url: ...
group: ...

另一条帖子内容
```

然后运行：

```bash
python lead_radar.py manual --file my_posts.txt --show
```

报告会生成在 `reports/daily_facebook_leads_YYYY-MM-DD.md`。

#### 方式 B：自动搜索 Facebook（需要桌面环境）

**前置条件：**
- 桌面电脑（Windows/macOS/Linux 桌面版）
- Chrome 浏览器
- 已在 Chrome 中登录 Facebook（建议用小号）

**配置步骤：**

1. 安装 OpenCLI：
   ```bash
   npm install -g @jackwener/opencli
   ```

2. 安装 Chrome 扩展：
   - 打开 https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
   - 点「添加至 Chrome」

3. 验证安装：
   ```bash
   opencli doctor
   ```
   显示 `Extension: connected` 即为成功。

4. 运行搜索：
   ```bash
   python lead_radar.py search --top 10
   ```

### 4. 快速评分单条帖子

```bash
python lead_radar.py score-one --text "帖子内容..." --name "张三" --comments 5
```

## 评分规则（总分 10 分）

| 维度 | 分值 | 说明 |
|------|------|------|
| 需求明确度 | 0-2 | need help、review my store、no sales 等 |
| 能力匹配度 | 0-2 | 产品页/主页/视觉/短视频加分；广告投放/代运营减分 |
| 客户真实度 | 0-2 | 有网站链接、真实产品、详细描述加分 |
| 竞争程度 | 0-2 | 评论少、刚发布加分；服务商刷屏减分 |
| 小单成交性 | 0-2 | 新店、具体小需求加分；整站/长期/保销量减分 |

## 需求分类

1. `store_review` - 店铺求点评
2. `no_sales` - 有流量没转化
3. `building_phase` - 店铺建设中
4. `shopify_designer_needed` - 找 Shopify 设计师
5. `product_page_help` - 产品页需要帮助
6. `product_visuals_needed` - 需要产品视觉素材
7. `promo_video_needed` - 需要推广短视频
8. `digital_product_store` - 数字产品店
9. `handmade_or_craft_store` - 手工/手作店
10. `unclear_or_low_quality` - 需求不明确/低质量

## 自动跳过的线索

- 纯广告帖 / 服务商发帖
- 要账号代管的
- 要保证销量的
- 要广告投放 ROI 的
- 明显 scam / fake profile
- 评论区被大量服务商刷屏的
- 没有具体店铺/产品/需求的
- 需要复杂支付网关或敏感业务的

## 私信建议规则

- 短，像真人
- 只问一个问题
- 先让对方发店铺/产品
- 把范围拉到 small first fix
- 不要一上来提 USDT
- 不要说自己是 Shopify expert
- 不要承诺 generate sales
- 不要说 guaranteed results

示例话术：

> I can take a quick look from a product page / first impression angle. What are you selling?

> I'm not a big Shopify agency, but I can help with product page layout, homepage sections, and promo visuals. Send the store link and I'll tell you the first thing I'd fix.

## 项目结构

```
fb-lead-radar/
├── lead_radar.py          # 主入口 CLI
├── models.py              # 数据模型
├── scoring.py             # 评分引擎
├── keywords.py            # 关键词配置
├── facebook_search.py     # Facebook 搜索适配器
├── manual_import.py       # 手动导入解析
├── report_generator.py    # 报告生成器
├── sample_posts.txt       # 示例帖子数据
└── reports/               # 输出报告目录
```

## 与 Agent-Reach 的关系

本项目基于 Agent-Reach 的 Facebook channel 能力构建：
- Agent-Reach 负责安装、检测和路由 OpenCLI 后端
- Facebook Lead Radar 负责业务逻辑：关键词、评分、分类、报告

你可以把 Agent-Reach 看作底层能力层，Lead Radar 是上面的业务应用。

## 常见问题

**Q: Facebook 搜索用不了怎么办？**
A: 先用手动导入模式。把你在 Facebook 群里看到的帖子复制下来，用 `manual` 命令评分。手动导入模式不依赖任何外部工具。

**Q: 为什么不用 Facebook Graph API？**
A: Graph API 的 Groups 权限审批非常严格，普通开发者拿不到。OpenCLI 复用浏览器登录态是目前最实用的方案。

**Q: 会被封号吗？**
A: 只要你只是正常浏览和搜索，不批量操作、不发垃圾信息，风险很低。但建议用小号，不要用主账号。

**Q: 可以加更多关键词吗？**
A: 可以，编辑 `keywords.py` 里的 `KEYWORDS` 列表即可。

**Q: 评分规则可以调整吗？**
A: 可以，所有评分逻辑都在 `scoring.py` 里，可以根据你的业务特点修改权重和规则。

## License

MIT
