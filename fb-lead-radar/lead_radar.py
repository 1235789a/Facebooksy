#!/usr/bin/env python3
"""
Facebook Lead Radar - 基于 Agent-Reach 的 Facebook 线索收集与评分工具

只做线索收集和评分，不做任何自动私信/评论/加好友/发帖。
所有外联操作由人工完成。
"""

import argparse
import sys
import os

from keywords import KEYWORDS
from scoring import score_lead, rank_leads
from report_generator import save_report, save_csv
from models import Lead
from facebook_search import (
    check_facebook_status,
    search_multiple_keywords,
    is_opencli_available,
)
from manual_import import import_from_text, parse_manual_post


def cmd_doctor(args):
    """检查各组件状态"""
    print("=" * 60)
    print("Facebook Lead Radar - 状态检查")
    print("=" * 60)
    print()

    print("[1/3] Agent-Reach...")
    try:
        from agent_reach.doctor import check_all
        from agent_reach.config import Config
        config = Config()
        results = check_all(config)
        fb = results.get("facebook", {})
        print(f"  Facebook 渠道: {fb.get('status', 'unknown')}")
        print(f"  说明: {fb.get('message', '')}")
    except Exception as e:
        print(f"  Agent-Reach 检查失败: {e}")

    print()
    print("[2/3] OpenCLI...")
    if is_opencli_available():
        print("  ✅ 已安装")
        fb_status = check_facebook_status()
        print(f"  Facebook 状态: {fb_status.get('status', 'unknown')}")
        if fb_status.get("status") != "ready":
            print()
            print("  修复步骤:")
            for step in fb_status.get("fix_steps", []):
                print(f"    {step}")
        else:
            print("  ✅ Facebook 渠道可用")
    else:
        print("  ❌ 未安装")
        print("  安装: npm install -g @jackwener/opencli")

    print()
    print("[3/3] Lead Radar 核心模块...")
    modules_ok = True
    for mod in ["scoring", "report_generator", "models", "keywords", "manual_import"]:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except Exception as e:
            print(f"  ❌ {mod}: {e}")
            modules_ok = False

    print()
    print("=" * 60)
    if modules_ok:
        print("✅ 核心模块全部就绪")
    else:
        print("❌ 部分模块有问题")
    print()
    print("提示:")
    print("  - Facebook 自动搜索需要桌面 Chrome + OpenCLI 扩展 + 已登录 Facebook")
    print("  - 如果是服务器/无桌面环境，可以使用手动导入模式 (manual 命令)")
    print("  - 手动导入: python lead_radar.py manual --file posts.txt")


def cmd_search(args):
    """搜索 Facebook 并生成每日报告"""
    print("=" * 60)
    print("Facebook Lead Radar - 自动搜索模式")
    print("=" * 60)
    print()

    fb_status = check_facebook_status()
    if fb_status.get("status") != "ready":
        print("❌ Facebook 渠道不可用")
        print()
        print("原因:", fb_status.get("reason", "未知"))
        print()
        print("修复步骤:")
        for step in fb_status.get("fix_steps", []):
            print(f"  {step}")
        print()
        print("或者使用手动导入模式:")
        print("  python lead_radar.py manual --file posts.txt")
        sys.exit(1)

    keywords = KEYWORDS[:args.num_keywords] if args.num_keywords else KEYWORDS
    print(f"将搜索 {len(keywords)} 个关键词...")
    print()

    leads = search_multiple_keywords(keywords, per_keyword_max=args.per_keyword)
    print(f"\n共找到 {len(leads)} 条原始结果")

    if not leads:
        print("没有找到任何结果。可能原因:")
        print("  1. 关键词太冷门")
        print("  2. Facebook 登录态失效")
        print("  3. 网络问题")
        sys.exit(0)

    print("正在评分和排序...")
    scored_leads = []
    skipped = 0
    for lead in leads:
        scored = score_lead(lead)
        if scored.should_skip:
            skipped += 1
            continue
        scored_leads.append(scored)

    print(f"  跳过 {skipped} 条（广告/服务商/低质量等）")
    print(f"  有效线索 {len(scored_leads)} 条")

    top_leads = rank_leads(scored_leads, top_n=args.top_n)
    print(f"\n输出 Top {len(top_leads)}")

    output_dir = args.output
    md_path = save_report(top_leads, output_dir=output_dir)
    csv_path = save_csv(top_leads, output_dir=output_dir)

    print(f"\n✅ 报告已生成:")
    print(f"  Markdown: {md_path}")
    print(f"  CSV:      {csv_path}")


def cmd_manual(args):
    """手动导入帖子并评分"""
    print("=" * 60)
    print("Facebook Lead Radar - 手动导入模式")
    print("=" * 60)
    print()

    leads = []

    if args.file:
        print(f"从文件导入: {args.file}")
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        leads = import_from_text(text)
    elif args.text:
        print("从文本导入...")
        leads = import_from_text(args.text)
    elif args.post_text:
        print("单条帖子导入...")
        lead = parse_manual_post(
            post_text=args.post_text,
            lead_name=args.lead_name or "",
            post_url=args.post_url or "",
            group_name=args.group_name or "",
            profile_url=args.profile_url or "",
            post_time=args.post_time or "",
            comment_count=args.comment_count,
        )
        leads = [lead]
    else:
        print("请提供输入:")
        print("  --file FILE       从文件导入（支持多条，用 --- 分隔）")
        print("  --text TEXT       直接输入文本")
        print("  --post-text TEXT  单条帖子内容")
        sys.exit(1)

    print(f"导入 {len(leads)} 条帖子")
    print()

    if not leads:
        print("没有有效帖子")
        sys.exit(0)

    print("正在评分...")
    scored_leads = []
    skipped = 0
    for lead in leads:
        scored = score_lead(lead)
        if scored.should_skip and not args.include_skipped:
            skipped += 1
            continue
        scored_leads.append(scored)

    print(f"  跳过 {skipped} 条（广告/服务商/低质量等）")
    print(f"  有效线索 {len(scored_leads)} 条")

    top_leads = rank_leads(scored_leads, top_n=args.top_n)

    output_dir = args.output
    md_path = save_report(top_leads, output_dir=output_dir)
    csv_path = save_csv(top_leads, output_dir=output_dir)

    print(f"\n✅ 报告已生成:")
    print(f"  Markdown: {md_path}")
    print(f"  CSV:      {csv_path}")

    if args.show:
        print()
        print("=" * 60)
        print("Top 线索预览")
        print("=" * 60)
        for idx, lead in enumerate(top_leads[:3], 1):
            print(f"\n#{idx} [{lead.contact_recommendation}] {lead.total_score}/10 - {lead.detected_need_type}")
            print(f"  发帖人: {lead.lead_name or '未知'}")
            print(f"  适合点: {lead.why_good_fit[:80]}...")
            print(f"  建议话术: {lead.suggested_manual_reply[:80]}...")


def cmd_score_one(args):
    """快速评分单条帖子"""
    if not args.text:
        print("请提供帖子内容: --text '帖子内容'")
        sys.exit(1)

    lead = parse_manual_post(
        post_text=args.text,
        lead_name=args.name or "",
        post_url=args.url or "",
        group_name=args.group or "",
        comment_count=args.comments,
    )

    scored = score_lead(lead)

    print()
    print("=" * 60)
    print("评分结果")
    print("=" * 60)
    print()

    if scored.should_skip:
        print(f"❌ 跳过原因: {scored.skip_reason}")
        print()
        print("建议: 不联系")
        return

    print(f"综合评分: {scored.total_score} / 10")
    print(f"需求类型: {scored.detected_need_type}")
    print(f"痛点信号: {scored.pain_signal}")
    print(f"业务类型猜测: {scored.business_type_guess}")
    print(f"建议联系: {scored.contact_recommendation}")
    print()
    print(f"为什么适合: {scored.why_good_fit}")
    print(f"风险/不适合: {scored.why_risk}")
    print()
    print(f"建议切入角度: {scored.suggested_angle}")
    print()
    print("建议话术:")
    print(f"  \"{scored.suggested_manual_reply}\"")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Facebook Lead Radar - 线索收集与评分工具（只读，不自动外联）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python lead_radar.py doctor                  # 检查环境状态
  python lead_radar.py search --top 10         # 自动搜索 Facebook（需 OpenCLI）
  python lead_radar.py manual --file posts.txt # 手动导入帖子文件
  python lead_radar.py score-one --text "..."  # 快速评分单条帖子

重要声明:
  本工具只读取和搜索公开/账号可见的信息。
  不做自动私信、自动评论、自动加好友、自动发帖。
  不绕过平台规则，不批量骚扰用户。
  所有外联操作由人工完成。
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="检查环境状态")
    p_doctor.set_defaults(func=cmd_doctor)

    # search
    p_search = subparsers.add_parser("search", help="自动搜索 Facebook（需 OpenCLI）")
    p_search.add_argument("--top", type=int, default=10, dest="top_n",
                          help="输出 Top N 条（默认 10）")
    p_search.add_argument("--per-keyword", type=int, default=10, dest="per_keyword",
                          help="每个关键词取多少条（默认 10）")
    p_search.add_argument("--num-keywords", type=int, default=None, dest="num_keywords",
                          help="只用前 N 个关键词（测试用）")
    p_search.add_argument("--output", default="reports",
                          help="输出目录（默认 reports/）")
    p_search.set_defaults(func=cmd_search)

    # manual
    p_manual = subparsers.add_parser("manual", help="手动导入帖子并评分")
    p_manual.add_argument("--file", help="从文件导入（支持多条，用 --- 分隔）")
    p_manual.add_argument("--text", help="直接输入文本内容")
    p_manual.add_argument("--post-text", dest="post_text", help="单条帖子内容")
    p_manual.add_argument("--lead-name", dest="lead_name", help="发帖人名字")
    p_manual.add_argument("--post-url", dest="post_url", help="帖子链接")
    p_manual.add_argument("--profile-url", dest="profile_url", help="主页链接")
    p_manual.add_argument("--group-name", dest="group_name", help="群组名称")
    p_manual.add_argument("--post-time", dest="post_time", help="发帖时间")
    p_manual.add_argument("--comment-count", type=int, dest="comment_count",
                          help="评论数（影响竞争评分）")
    p_manual.add_argument("--top", type=int, default=10, dest="top_n",
                          help="输出 Top N 条（默认 10）")
    p_manual.add_argument("--output", default="reports",
                          help="输出目录（默认 reports/）")
    p_manual.add_argument("--show", action="store_true", help="在终端显示预览")
    p_manual.add_argument("--include-skipped", action="store_true", dest="include_skipped",
                          help="包含被跳过的线索")
    p_manual.set_defaults(func=cmd_manual)

    # score-one
    p_score = subparsers.add_parser("score-one", help="快速评分单条帖子")
    p_score.add_argument("--text", required=True, help="帖子内容")
    p_score.add_argument("--name", help="发帖人名字")
    p_score.add_argument("--url", help="帖子链接")
    p_score.add_argument("--group", help="群组名称")
    p_score.add_argument("--comments", type=int, help="评论数")
    p_score.set_defaults(func=cmd_score_one)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
