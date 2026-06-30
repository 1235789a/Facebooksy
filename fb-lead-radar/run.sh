#!/bin/bash
# Facebook Lead Radar - macOS/Linux 启动脚本

clear
echo "============================================================"
echo "   Facebook Lead Radar - 本地运行启动器"
echo "============================================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[错误] 没有找到 Python3，请先安装 Python 3.10+"
    echo "macOS: brew install python3"
    echo "Linux: sudo apt install python3"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "[1/3] 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[2/3] 正在安装依赖..."
    pip install -e ../Agent-Reach
else
    source venv/bin/activate
fi

echo "[3/3] 启动 Lead Radar..."
echo ""

while true; do
    clear
    echo "============================================================"
    echo "   Facebook Lead Radar - 主菜单"
    echo "============================================================"
    echo ""
    echo "  [1] 检查环境状态 (doctor)"
    echo "  [2] 手动导入帖子评分"
    echo "  [3] 快速评分单条帖子"
    echo "  [4] 自动搜索 Facebook (需 OpenCLI)"
    echo "  [5] 打开报告目录"
    echo "  [0] 退出"
    echo ""
    read -p "请选择操作 [0-5]: " choice

    case $choice in
        1)
            clear
            python lead_radar.py doctor
            echo ""
            read -p "按回车返回菜单..."
            ;;
        2)
            clear
            echo "============================================================"
            echo "  手动导入模式"
            echo "============================================================"
            echo ""
            echo "请把帖子内容保存到 input_posts.txt 文件中"
            echo ""
            echo "格式示例："
            echo "  name: 发帖人"
            echo "  url: https://..."
            echo "  group: 群组名"
            echo "  comments: 5"
            echo "  （空行）"
            echo "  帖子内容..."
            echo "  ---"
            echo "  （下一条）"
            echo ""
            if [ -f "input_posts.txt" ]; then
                echo "检测到 input_posts.txt，按回车开始评分..."
                read
                python lead_radar.py manual --file input_posts.txt --show
            else
                echo "没有找到 input_posts.txt"
                echo "正在用示例数据演示..."
                read
                python lead_radar.py manual --file sample_posts.txt --show
            fi
            echo ""
            read -p "按回车返回菜单..."
            ;;
        3)
            clear
            echo "============================================================"
            echo "  快速评分单条帖子"
            echo "============================================================"
            echo ""
            echo "请粘贴帖子内容（输入完成后按回车，再按 Ctrl+D 结束）："
            echo ""
            text=""
            while IFS= read -r line; do
                text="$text$line"$'\n'
            done
            echo ""
            python lead_radar.py score-one --text "$text"
            echo ""
            read -p "按回车返回菜单..."
            ;;
        4)
            clear
            python lead_radar.py search --top 10
            echo ""
            read -p "按回车返回菜单..."
            ;;
        5)
            mkdir -p reports
            if command -v open &> /dev/null; then
                open reports
            elif command -v xdg-open &> /dev/null; then
                xdg-open reports
            else
                echo "报告目录: $(pwd)/reports"
                read -p "按回车返回菜单..."
            fi
            ;;
        0)
            echo ""
            echo "再见！"
            deactivate
            exit 0
            ;;
        *)
            echo "无效选择，请重试"
            sleep 1
            ;;
    esac
done
