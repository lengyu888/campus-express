# -*- coding: utf-8 -*-
"""生成《校园快递收发系统》设计文档所需图表。

运行：
    python scripts/gen_diagrams.py
输出：
    docs/assets/*.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

INK = "#1F2937"
DARK = "#1F4E79"
BLUE = "#2E75B6"
LIGHT = "#EAF2FA"
PALE = "#F7FAFD"
GRAY = "#6B7280"
LGRAY = "#E5E7EB"
GREEN = "#2F7D5B"
GREEN_L = "#EDF7F1"
AMBER = "#B7791F"
AMBER_L = "#FDF6E7"
RED = "#B03A2E"
RED_L = "#FBEDEC"


# ---------------------------------------------------------------- 基础图元
def fig_ax(w, h):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)          # y 轴向下，便于按“从上到下”排版
    ax.axis("off")
    return fig, ax


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=210, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("saved", path)


def tw(s, fs):
    """粗略估算文本宽度（英寸），中文按 1 个字宽计。"""
    w = 0
    for ch in s:
        w += 0.55 if ord(ch) < 128 else 1.0
    return w * fs / 72.0


def fit(s, fs, width, min_fs=5.0):
    lines = s.split("\n")
    longest = max(lines, key=len) if lines else s
    while tw(longest, fs) > width and fs > min_fs:
        fs -= 0.3
    return fs


def rbox(ax, cx, cy, w, h, text="", fs=9, fc="white", ec=BLUE, lw=1.0,
         color=INK, bold=False, radius=0.06, z=2, align="center"):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z)
    ax.add_patch(p)
    if text:
        fs = fit(text, fs, w - 0.12)
        ax.text(cx, cy, text, ha=align, va="center", fontsize=fs, color=color,
                fontweight="bold" if bold else "normal", zorder=z + 1,
                linespacing=1.45)
    return p


def stadium(ax, cx, cy, w, h, text, fs=9, fc=LIGHT, ec=DARK):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                       boxstyle=f"round,pad=0,rounding_size={h/2}",
                       linewidth=1.1, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold", zorder=3)


def para(ax, cx, cy, w, h, text, fs=9, fc=GREEN_L, ec=GREEN):
    d = 0.16
    pts = [(cx - w / 2 + d, cy - h / 2), (cx + w / 2, cy - h / 2),
           (cx + w / 2 - d, cy + h / 2), (cx - w / 2, cy + h / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, lw=1.0, zorder=2))
    fs = fit(text, fs, w - 0.3)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3)


def diamond(ax, cx, cy, w, h, text, fs=8.6, fc=AMBER_L, ec=AMBER):
    pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, lw=1.1, zorder=2))
    fs = fit(text, fs, w * 0.62)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK,
            zorder=3, linespacing=1.3)


def arrow(ax, p1, p2, color=GRAY, lw=1.0, style="-|>", ls="-", shrink=2):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=9,
                        linewidth=lw, color=color, linestyle=ls,
                        shrinkA=shrink, shrinkB=shrink, zorder=1.5)
    ax.add_patch(a)


def poly_arrow(ax, pts, color=GRAY, lw=1.0, ls="-"):
    for i in range(len(pts) - 2):
        ax.add_line(Line2D([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                           color=color, lw=lw, linestyle=ls, zorder=1.5))
    arrow(ax, pts[-2], pts[-1], color=color, lw=lw, ls=ls)


def label(ax, x, y, text, fs=8, color=GRAY, bold=False, ha="center", va="center"):
    ax.text(x, y, text, ha=ha, va=va, fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", zorder=5)


# ---------------------------------------------------------------- 1 总体架构
def architecture():
    W, H = 8.4, 7.6
    fig, ax = fig_ax(W, H)
    bands = [
        ("用户层", 0.65, 0.72, ["学生 / 教职工", "驿站工作人员", "系统管理员"]),
        ("接入层", 1.62, 0.62, ["Nginx 静态资源与反向代理 / Vite Dev Server"]),
        ("前端层", 2.49, 0.86, ["Vue 3 SPA", "学生端", "驿站工作台", "管理端"]),
        ("接口层", 3.60, 0.70, ["FastAPI Router /api/v1", "JWT 鉴权", "Pydantic 校验"]),
    ]
    for name, y, h, items in bands:
        rbox(ax, W / 2, y + h / 2, 7.7, h, "", fc=PALE, ec=LGRAY, lw=0.8, z=1)
        ax.add_patch(Rectangle((0.35, y), 0.62, h, facecolor=LIGHT, edgecolor="none", zorder=1.2))
        ax.text(0.66, y + h / 2, name, ha="center", va="center", fontsize=9,
                color=DARK, fontweight="bold", rotation=90, zorder=2)
        n = len(items)
        avail = 6.85
        gap = 0.12
        bw = (avail - gap * (n - 1)) / n
        for i, it in enumerate(items):
            cx = 1.12 + bw / 2 + i * (bw + gap)
            rbox(ax, cx, y + h / 2, bw, h - 0.18, it, fs=9.2, fc="white",
                 ec=BLUE, lw=0.9)

    # 业务层
    y, h = 4.58, 1.62
    rbox(ax, W / 2, y + h / 2, 7.7, h, "", fc=PALE, ec=LGRAY, lw=0.8, z=1)
    ax.add_patch(Rectangle((0.35, y), 0.62, h, facecolor=LIGHT, edgecolor="none", zorder=1.2))
    ax.text(0.66, y + h / 2, "业务层", ha="center", va="center", fontsize=9,
            color=DARK, fontweight="bold", rotation=90, zorder=2)
    mods = ["M1 用户权限", "M2 驿站货架", "M3 快递入库", "M4 取件出库",
            "M5 寄件管理", "M6 异常超期", "M7 通知公告", "M8 统计报表"]
    bw, bh = 1.58, 0.56
    for i, m in enumerate(mods):
        row, col = divmod(i, 4)
        cx = 1.12 + bw / 2 + col * (bw + 0.13)
        cy = y + 0.42 + row * (bh + 0.16) + bh / 2
        rbox(ax, cx, cy, bw, bh, m, fs=8.6, fc="white", ec=BLUE, lw=0.9)

    # 数据层
    y, h = 6.44, 0.72
    rbox(ax, W / 2, y + h / 2, 7.7, h, "", fc=PALE, ec=LGRAY, lw=0.8, z=1)
    ax.add_patch(Rectangle((0.35, y), 0.62, h, facecolor=LIGHT, edgecolor="none", zorder=1.2))
    ax.text(0.66, y + h / 2, "数据层", ha="center", va="center", fontsize=9,
            color=DARK, fontweight="bold", rotation=90, zorder=2)
    items = ["SQLAlchemy 2.0 + Alembic", "MySQL 8.0（Docker）", "Redis 7（Docker）"]
    bw = 2.2
    for i, it in enumerate(items):
        cx = 1.12 + bw / 2 + i * (bw + 0.16)
        rbox(ax, cx, y + h / 2, bw, h - 0.18, it, fs=8.8, fc="white", ec=BLUE, lw=0.9)

    # 层间箭头
    for y1, y2 in [(1.37, 1.62), (2.24, 2.49), (3.35, 3.60), (4.30, 4.58), (6.20, 6.44)]:
        arrow(ax, (W / 2, y1), (W / 2, y2), color=BLUE, lw=1.1, style="<|-|>", shrink=0)
    save(fig, "fig_architecture.png")


# ---------------------------------------------------------------- 2 模块结构图
def module_tree():
    W, H = 7.4, 8.7
    fig, ax = fig_ax(W, H)
    rbox(ax, W / 2, 1.05, 2.60, 0.48, "校园快递收发系统", fs=11, fc=LIGHT,
         ec=DARK, lw=1.3, bold=True)

    modules = [
        ("M1 用户与权限管理", ["登录与令牌刷新", "用户信息管理", "角色与权限控制", "个人中心"]),
        ("M2 驿站与货架管理", ["驿站信息维护", "货架分区维护", "格口容量监控"]),
        ("M3 快递入库管理", ["到站登记", "批量导入", "格口分配", "取件码生成"]),
        ("M4 取件出库管理", ["取件核验", "出库签收", "取件记录", "退回登记"]),
        ("M5 寄件管理", ["寄件下单", "运费估算", "揽收称重", "轨迹跟踪"]),
        ("M6 异常件与超期管理", ["超期判定", "异常件登记", "退回处理"]),
        ("M7 通知与公告管理", ["取件通知", "超期提醒", "公告发布"]),
        ("M8 统计报表", ["收发量统计", "驿站工作量", "超期率分析"]),
    ]

    col_x = [2.02, 5.66]
    trunk_x = [0.34, 3.94]
    row_y = [1.95, 3.69, 5.43, 7.17]
    bus_y = 1.46
    mw, mh = 2.92, 0.52

    ax.add_line(Line2D([W / 2, W / 2], [1.29, bus_y], color=GRAY, lw=1.0, zorder=1.4))
    ax.add_line(Line2D([trunk_x[0], trunk_x[1]], [bus_y, bus_y], color=GRAY, lw=1.0, zorder=1.4))

    for idx, (name, subs) in enumerate(modules):
        col = idx % 2
        row = idx // 2
        cx, tx, cy = col_x[col], trunk_x[col], row_y[row]

        ax.add_line(Line2D([tx, tx], [bus_y, cy], color=GRAY, lw=1.0, zorder=1.3))
        ax.add_line(Line2D([tx, cx - mw / 2], [cy, cy], color=GRAY, lw=1.0, zorder=1.3))
        rbox(ax, cx, cy, mw, mh, name, fs=10.2, fc=LIGHT, ec=DARK, lw=1.2, bold=True)

        ax.add_line(Line2D([cx, cx], [cy + mh / 2, cy + 0.76], color=LGRAY, lw=1.4, zorder=0.8))
        cw, ch = 1.36, 0.38
        positions = []
        if len(subs) == 4:
            positions = [(-0.71, 0.57), (0.71, 0.57), (-0.71, 1.01), (0.71, 1.01)]
        elif len(subs) == 3:
            positions = [(-0.71, 0.57), (0.71, 0.57), (0.0, 1.01)]
        for (dx, dy), sub in zip(positions, subs):
            rbox(ax, cx + dx, cy + dy, cw, ch, sub, fs=8.4, fc="white", ec=BLUE, lw=0.8)

    save(fig, "fig_module_tree.png")


# ---------------------------------------------------------------- 3 E-R 图
def er_diagram():
    W, H = 8.6, 9.9
    fig, ax = fig_ax(W, H)
    def entity(cx, cy, name, attrs, w=1.62):
        h = 0.32 + 0.27 * len(attrs) + 0.10
        rbox(ax, cx, cy, w, h, "", fc="white", ec=DARK, lw=1.2, radius=0.04)
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, 0.32, facecolor=LIGHT,
                               edgecolor=DARK, lw=1.2, zorder=2.1))
        ax.text(cx, cy - h / 2 + 0.16, name, ha="center", va="center", fontsize=9.4,
                color=DARK, fontweight="bold", zorder=3)
        for i, a in enumerate(attrs):
            ax.text(cx - w / 2 + 0.08, cy - h / 2 + 0.32 + 0.135 + i * 0.27, a,
                    ha="left", va="center", fontsize=7.2, color=INK, zorder=3)
        return (cx, cy, w, h)

    def rel(cx, cy, text, w=0.88, h=0.42):
        diamond(ax, cx, cy, w, h, text, fs=7.9, fc=AMBER_L, ec=AMBER)
        return (cx, cy, w, h)

    def edge(ent, tx, ty):
        cx, cy, w, h = ent
        dx, dy = tx - cx, ty - cy
        sx = (w / 2) / abs(dx) if dx else 1e9
        sy = (h / 2) / abs(dy) if dy else 1e9
        k = min(sx, sy)
        return (cx + dx * k, cy + dy * k)

    def connect(e1, e2, r, c1, c2):
        p1 = edge(e1, r[0], r[1])
        p2 = edge(r, e1[0], e1[1])
        p3 = edge(r, e2[0], e2[1])
        p4 = edge(e2, r[0], r[1])
        for a, b in [(p1, p2), (p3, p4)]:
            ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], color=GRAY, lw=1.0, zorder=1.5))
        # 基数标注：靠近实体一侧，沿连线偏移
        for p, q, txt in [(p1, p2, c1), (p4, p3, c2)]:
            mx, my = p[0] + (q[0] - p[0]) * 0.22, p[1] + (q[1] - p[1]) * 0.22
            dx, dy = q[0] - p[0], q[1] - p[1]
            ln = (dx * dx + dy * dy) ** 0.5 or 1
            ox, oy = -dy / ln * 0.13, dx / ln * 0.13
            ax.text(mx + ox, my + oy, txt, ha="center", va="center", fontsize=8.0,
                    color=RED, fontweight="bold", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.10", fc="white", ec="none", alpha=0.85))

    E = {}
    E["user"] = entity(1.60, 5.50, "用户", ["PK user_id", "student_no", "name", "phone", "role"])
    E["station"] = entity(4.90, 8.40, "驿站", ["PK station_id", "code", "name", "address", "capacity"])
    E["shelf"] = entity(7.75, 7.90, "货架", ["PK shelf_id", "FK station_id", "code", "capacity"], w=1.50)
    E["pkg"] = entity(4.90, 5.70, "快递包裹", ["PK package_id", "tracking_no", "FK recipient_id", "FK station_id", "status"], w=1.78)
    E["notice"] = entity(1.60, 8.50, "通知", ["PK notice_id", "FK user_id", "type", "is_read"], w=1.50)
    E["pickup"] = entity(7.75, 5.05, "取件记录", ["PK pickup_id", "FK package_id", "operator_id", "picked_at"], w=1.62)
    E["exc"] = entity(7.75, 2.55, "异常记录", ["PK exception_id", "FK package_id", "type", "status"], w=1.62)
    E["order"] = entity(1.60, 2.00, "寄件订单", ["PK order_id", "order_no", "FK sender_id", "status"], w=1.62)
    E["track"] = entity(4.90, 2.00, "寄件轨迹", ["PK track_id", "FK order_id", "node", "created_at"], w=1.62)

    R = {}
    R["recv"] = rel(3.22, 5.62, "收件")
    R["cfg"] = rel(6.38, 8.16, "配置")
    R["store"] = rel(4.90, 7.05, "存放")
    R["shelve"] = rel(6.38, 6.98, "上架")
    R["sign"] = rel(6.40, 5.36, "签收")
    R["exc"] = rel(6.35, 4.08, "登记")
    R["notify"] = rel(1.60, 7.06, "接收")
    R["send"] = rel(1.60, 3.66, "发起")
    R["gentr"] = rel(3.26, 2.00, "生成")

    connect(E["user"], E["pkg"], R["recv"], "1", "N")
    connect(E["station"], E["shelf"], R["cfg"], "1", "N")
    connect(E["station"], E["pkg"], R["store"], "1", "N")
    connect(E["shelf"], E["pkg"], R["shelve"], "1", "N")
    connect(E["pkg"], E["pickup"], R["sign"], "1", "1")
    connect(E["pkg"], E["exc"], R["exc"], "1", "N")
    connect(E["user"], E["notice"], R["notify"], "1", "N")
    connect(E["user"], E["order"], R["send"], "1", "N")
    connect(E["order"], E["track"], R["gentr"], "1", "N")

    # 图例
    ax.add_patch(Rectangle((0.32, 0.72), 0.26, 0.18, facecolor=LIGHT, edgecolor=DARK, lw=1.0, zorder=2))
    label(ax, 0.66, 0.81, "实体", fs=7.8, ha="left")
    diamond(ax, 1.32, 0.81, 0.36, 0.22, "联系", fs=6.2)
    label(ax, 1.62, 0.81, "联系（1:N / 1:1）", fs=7.8, ha="left")
    label(ax, 0.32, 9.62, "说明：实体框内仅列关键属性，完整字段见 5.4 节；"
                          "公告、操作日志通过 user_id 关联用户，图中从略。",
          fs=7.2, ha="left", color=GRAY)
    save(fig, "fig_er.png")


# ---------------------------------------------------------------- 4 入库流程图
def flow_inbound():
    W, H = 6.8, 9.9
    fig, ax = fig_ax(W, H)
    cx = 2.55
    rx = 5.15

    stadium(ax, cx, 0.48, 1.15, 0.40, "开始", fs=9)
    rbox(ax, cx, 1.20, 3.55, 0.50, "驿站工作人员登录，进入入库登记", fs=9)
    para(ax, cx, 1.95, 3.55, 0.50, "扫描或手工输入运单号", fs=9)
    diamond(ax, cx, 2.95, 2.55, 0.86, "运单号已存在？", fs=8.8)

    rbox(ax, rx, 2.95, 2.55, 0.62, "提示“该运单已入库”\n并展示原记录", fs=8.4)
    stadium(ax, rx, 4.02, 1.05, 0.38, "结束", fs=9)

    rbox(ax, cx, 4.05, 3.55, 0.50, "按收件人手机号匹配系统用户", fs=9)
    diamond(ax, cx, 4.95, 2.55, 0.82, "匹配到用户？", fs=8.8)
    rbox(ax, rx, 4.95, 2.55, 0.62, "登记为临时收件人\n取件时核对手机号", fs=8.4)

    rbox(ax, cx, 6.00, 3.75, 0.52, "选择驿站，系统推荐空闲格口", fs=9)
    diamond(ax, cx, 6.95, 2.55, 0.84, "驿站有空闲格口？", fs=8.6)
    rbox(ax, rx, 6.95, 2.55, 0.62, "提示容量不足\n转人工处理", fs=8.4)
    stadium(ax, rx, 8.02, 1.05, 0.38, "结束", fs=9)

    rbox(ax, cx, 8.05, 3.75, 0.52, "分配格口并生成 6 位取件码\n（站内唯一，冲突则重新生成）", fs=8.6)
    rbox(ax, cx, 8.90, 3.75, 0.52, "保存包裹记录（状态=在库）\n写入操作日志并发送取件通知", fs=8.6)
    stadium(ax, cx, 9.60, 1.15, 0.40, "结束", fs=9)

    def down(a, b):
        arrow(ax, (cx, a), (cx, b), color=INK, lw=1.0, shrink=0)

    down(0.68, 0.95)
    down(1.45, 1.70)
    down(2.20, 2.52)
    down(3.38, 3.80)
    down(4.30, 4.54)
    down(5.36, 5.74)
    down(6.26, 6.53)
    down(7.37, 7.79)
    down(8.31, 8.64)
    down(9.16, 9.40)

    # 右分支
    arrow(ax, (cx + 1.28, 2.95), (rx - 1.28, 2.95), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2, 2.78, "是", fs=8, color=RED)
    arrow(ax, (rx, 3.26), (rx, 3.83), color=INK, lw=1.0, shrink=0)

    arrow(ax, (cx + 1.28, 4.95), (rx - 1.28, 4.95), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2 + 0.1, 4.78, "否", fs=8, color=RED)
    poly_arrow(ax, [(rx, 5.26), (rx, 5.64), (cx + 1.88, 5.64), (cx + 1.88, 6.00)],
               color=INK, lw=1.0)

    arrow(ax, (cx + 1.28, 6.95), (rx - 1.28, 6.95), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2, 6.78, "否", fs=8, color=RED)
    arrow(ax, (rx, 7.26), (rx, 7.83), color=INK, lw=1.0, shrink=0)

    label(ax, cx + 0.16, 3.40, "否", fs=8, color=RED)
    label(ax, cx + 0.16, 5.40, "是", fs=8, color=RED)

    # 主流程“是/否”标注
    label(ax, cx - 0.2, 7.40, "是", fs=8, color=RED, ha="right")
    save(fig, "fig_flow_inbound.png")


# ---------------------------------------------------------------- 5 取件流程图
def flow_pickup():
    W, H = 7.8, 10.1
    fig, ax = fig_ax(W, H)
    cx, rx, ex = 2.50, 5.30, 7.12

    stadium(ax, cx, 0.46, 1.15, 0.40, "开始", fs=9)
    rbox(ax, cx, 1.18, 3.90, 0.52, "收件人出示取件码与手机号后四位", fs=9)
    para(ax, cx, 1.95, 3.60, 0.50, "工作人员录入取件码", fs=9)
    rbox(ax, cx, 2.70, 3.60, 0.50, "按取件码查询包裹记录", fs=9)
    diamond(ax, cx, 3.64, 2.70, 0.88, "取件码存在且\n未失效？", fs=8.6)

    rbox(ax, rx, 3.64, 2.35, 0.62, "提示取件码无效\n引导至人工查询", fs=8.2)
    stadium(ax, ex, 3.64, 0.95, 0.38, "结束", fs=8.6)

    diamond(ax, cx, 5.28, 2.70, 0.82, "手机号后四位匹配？", fs=8.4)
    rbox(ax, rx, 5.28, 2.35, 0.62, "提示核验失败\n累计失败次数并留痕", fs=8.2)
    stadium(ax, ex, 5.28, 0.95, 0.38, "结束", fs=8.6)

    diamond(ax, cx, 6.60, 2.70, 0.82, "包裹为在库/超期？", fs=8.4)
    rbox(ax, rx, 6.60, 2.35, 0.62, "提示“已出库/已退回”\n展示流转记录", fs=8.2)
    stadium(ax, ex, 6.60, 0.95, 0.38, "结束", fs=8.6)

    rbox(ax, cx, 7.62, 3.75, 0.52, "写取件记录，状态置为“已取件”\n清除取件码，释放货架格口", fs=8.6)
    diamond(ax, cx, 8.55, 2.55, 0.80, "是否为超期件？", fs=8.6)
    rbox(ax, rx, 8.55, 2.35, 0.50, "记录超期天数\n计入统计", fs=8.2)

    rbox(ax, cx, 9.25, 3.55, 0.46, "推送取件成功通知", fs=9)
    stadium(ax, cx, 9.85, 1.15, 0.40, "结束", fs=9)

    def down(a, b):
        arrow(ax, (cx, a), (cx, b), color=INK, lw=1.0, shrink=0)

    for a, b in [(0.66, 0.92), (1.44, 1.70), (2.20, 2.45), (2.95, 3.20),
                 (4.08, 4.87), (5.69, 6.19), (7.01, 7.36), (7.88, 8.15),
                 (8.95, 9.02), (9.48, 9.65)]:
        down(a, b)

    arrow(ax, (cx + 1.35, 3.64), (rx - 1.175, 3.64), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2 - 0.05, 3.44, "否", fs=8, color=RED)
    arrow(ax, (rx + 1.175, 3.64), (ex - 0.475, 3.64), color=INK, lw=1.0, shrink=0)

    arrow(ax, (cx + 1.35, 5.28), (rx - 1.175, 5.28), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2 - 0.05, 5.08, "否", fs=8, color=RED)
    arrow(ax, (rx + 1.175, 5.28), (ex - 0.475, 5.28), color=INK, lw=1.0, shrink=0)

    arrow(ax, (cx + 1.35, 6.60), (rx - 1.175, 6.60), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2 - 0.05, 6.40, "否", fs=8, color=RED)
    arrow(ax, (rx + 1.175, 6.60), (ex - 0.475, 6.60), color=INK, lw=1.0, shrink=0)

    label(ax, cx + 0.16, 4.10, "是", fs=8, color=RED)
    label(ax, cx + 0.16, 5.72, "是", fs=8, color=RED)
    label(ax, cx + 0.16, 7.02, "是", fs=8, color=RED)

    arrow(ax, (cx + 1.28, 8.55), (rx - 1.175, 8.55), color=INK, lw=1.0, shrink=0)
    label(ax, (cx + rx) / 2, 8.35, "是", fs=8, color=RED)
    poly_arrow(ax, [(rx + 1.175, 8.55), (6.72, 8.55), (6.72, 9.25), (cx + 1.78, 9.25)],
               color=INK, lw=1.0)
    label(ax, cx + 0.16, 8.95, "否", fs=8, color=RED)
    save(fig, "fig_flow_pickup.png")


# ---------------------------------------------------------------- 6/7 N-S 图
def ns_frame(ax, x, y, w, h, title):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=DARK, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y), w, 0.34, facecolor=LIGHT, edgecolor=DARK, lw=1.3, zorder=3))
    ax.text(x + 0.12, y + 0.17, title, ha="left", va="center", fontsize=9.6,
            color=DARK, fontweight="bold", zorder=4)


def ns_seq(ax, x, y, w, h, text, fs=8.4, fc="white"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=GRAY, lw=0.8, zorder=3))
    fs = fit(text, fs, w - 0.18)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, zorder=4, linespacing=1.4)


def ns_select(ax, x, y, w, h, cond, left, right, fs=8.2):
    """选择结构：上方条件行，下方左右两分支。"""
    hh = 0.30
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=GRAY, lw=0.8, zorder=3))
    ax.add_line(Line2D([x, x + w], [y + hh, y + hh], color=GRAY, lw=0.8, zorder=4))
    ax.add_line(Line2D([x + w / 2, x + w / 2], [y + hh, y + h], color=GRAY, lw=0.8, zorder=4))
    ax.text(x + w / 2, y + hh / 2, cond, ha="center", va="center", fontsize=fs,
            color=AMBER, fontweight="bold", zorder=4)
    ax.text(x + w / 4, y + hh + 0.14, "是", ha="center", va="center", fontsize=7.4, color=RED, zorder=4)
    ax.text(x + w * 3 / 4, y + hh + 0.14, "否", ha="center", va="center", fontsize=7.4, color=RED, zorder=4)
    fs2 = fit(left, fs, w / 2 - 0.14)
    ax.text(x + w / 4, y + hh + (h - hh) / 2, left, ha="center", va="center",
            fontsize=fs2, color=INK, zorder=4, linespacing=1.35)
    fs3 = fit(right, fs, w / 2 - 0.14)
    ax.text(x + w * 3 / 4, y + hh + (h - hh) / 2, right, ha="center", va="center",
            fontsize=fs3, color=INK, zorder=4, linespacing=1.35)


def ns_loop(ax, x, y, w, h, cond, body, fs=8.4):
    hh = 0.30
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=GRAY, lw=0.8, zorder=3))
    ax.add_patch(Rectangle((x, y), w, hh, facecolor=AMBER_L, edgecolor=GRAY, lw=0.8, zorder=3.1))
    ax.text(x + w / 2, y + hh / 2, cond, ha="center", va="center", fontsize=fs,
            color=AMBER, fontweight="bold", zorder=4)
    ax.text(x + w / 2, y + hh + (h - hh) / 2, body, ha="center", va="center",
            fontsize=fs, color=INK, zorder=4, linespacing=1.35)


def ns_inbound():
    rows = [
        ("seq", 0.46, "输入运单号（扫码 / 手工录入）"),
        ("select", 0.92, "运单号已存在？", "提示重复并展示原记录，结束", "继续登记"),
        ("seq", 0.46, "按手机号匹配收件人；未匹配则登记为临时收件人"),
        ("seq", 0.46, "选择驿站，查询可用格口"),
        ("select", 0.92, "存在空闲格口？", "分配格口", "提示容量不足，转人工处理，结束"),
        ("loop", 0.80, "当取件码与站内有效码冲突时", "重新生成 6 位随机取件码"),
        ("seq", 0.46, "保存包裹记录，状态置为“在库”"),
        ("seq", 0.46, "写入操作日志"),
        ("seq", 0.46, "发送取件通知（站内信 + 短信模拟）"),
    ]
    body_h = sum(r[1] for r in rows)
    W, H = 7.2, 1.55 + body_h
    fig, ax = fig_ax(W, H)
    x, w = 0.55, 6.1
    y = 0.72
    ns_frame(ax, x, y, w, body_h + 0.62, "快递入库登记")

    xx, ww = x + 0.18, w - 0.36
    cy = y + 0.50
    for r in rows:
        if r[0] == "seq":
            ns_seq(ax, xx, cy, ww, r[1], r[2])
            cy += r[1]
        elif r[0] == "select":
            ns_select(ax, xx, cy, ww, r[1], r[2], r[3], r[4])
            cy += r[1]
        else:
            ns_loop(ax, xx, cy, ww, r[1], r[2], r[3])
            cy += r[1]
    save(fig, "fig_ns_inbound.png")


def ns_pickup():
    rows = [
        ("seq", 0.46, "录入取件码，查询包裹记录"),
        ("select", 0.92, "取件码存在且未过期？", "继续核验", "提示取件码无效，引导人工查询，结束"),
        ("select", 0.92, "手机号后四位一致？", "继续核验", "提示核验失败，记录失败次数，结束"),
        ("select", 0.92, "包裹状态为在库或超期？", "办理出库", "提示已出库/已退回，展示流转记录，结束"),
        ("seq", 0.46, "写取件记录（核验方式、操作员、时间）"),
        ("seq", 0.46, "包裹状态置为“已取件”，清除取件码"),
        ("seq", 0.46, "释放货架格口"),
        ("select", 0.80, "是否为超期件？", "记录超期天数", "不计超期"),
        ("seq", 0.46, "推送取件成功通知"),
    ]
    body_h = sum(r[1] for r in rows)
    W, H = 7.2, 1.55 + body_h
    fig, ax = fig_ax(W, H)
    x, w = 0.55, 6.1
    y = 0.72
    ns_frame(ax, x, y, w, body_h + 0.62, "取件核验与出库")

    xx, ww = x + 0.18, w - 0.36
    cy = y + 0.50
    for r in rows:
        if r[0] == "seq":
            ns_seq(ax, xx, cy, ww, r[1], r[2])
            cy += r[1]
        elif r[0] == "select":
            ns_select(ax, xx, cy, ww, r[1], r[2], r[3], r[4])
            cy += r[1]
        else:
            ns_loop(ax, xx, cy, ww, r[1], r[2], r[3])
            cy += r[1]
    save(fig, "fig_ns_pickup.png")


# ---------------------------------------------------------------- 8 部署图
def deployment():
    W, H = 8.4, 6.2
    fig, ax = fig_ax(W, H)
    rbox(ax, 1.20, 2.62, 1.50, 0.80, "浏览器\n学生 / 驿站 / 管理员", fs=8.2, fc="white", ec=GRAY)

    rbox(ax, 5.30, 3.15, 6.00, 5.10, "", fc=PALE, ec=GRAY, lw=1.2, radius=0.10)
    label(ax, 2.32, 0.48, "宿主机（开发机 / 服务器）", fs=8.8, color=DARK, bold=True, ha="left")

    rbox(ax, 5.35, 3.00, 5.50, 3.80, "", fc="white", ec=BLUE, lw=1.1, radius=0.08)
    label(ax, 2.62, 1.00, "Docker Engine", fs=8.4, color=BLUE, bold=True, ha="left")

    rbox(ax, 3.55, 2.62, 1.45, 1.00, "frontend\nnginx:alpine\n:80", fs=8.0, fc=LIGHT, ec=DARK)
    rbox(ax, 5.30, 2.62, 1.45, 1.00, "backend\npython:3.12\nuvicorn :8000", fs=8.0, fc=LIGHT, ec=DARK)
    rbox(ax, 7.05, 2.62, 1.30, 1.00, "MySQL 8.0\n:3306", fs=8.2, fc=LIGHT, ec=DARK)
    rbox(ax, 7.05, 3.80, 1.30, 0.70, "Redis 7\n:6379", fs=8.2, fc=LIGHT, ec=DARK)

    ax.add_line(Line2D([2.72, 7.95], [4.50, 4.50], color=BLUE, lw=1.3, ls=(0, (5, 3)), zorder=3))
    label(ax, 5.10, 4.72, "campus-net（bridge 网络）", fs=7.8, color=BLUE)

    label(ax, 2.62, 5.40, "数据卷：mysql_data（数据库文件）、redis_data（缓存持久化）",
          fs=7.6, color=GRAY, ha="left")

    arrow(ax, (1.95, 2.62), (2.825, 2.62), color=INK, lw=1.2, style="-|>", shrink=0)
    label(ax, 2.38, 2.41, "HTTP :80", fs=7.2, color=GRAY)
    arrow(ax, (4.275, 2.62), (4.575, 2.62), color=INK, lw=1.2, style="-|>", shrink=0)
    label(ax, 4.42, 2.43, "/api", fs=7.2, color=GRAY)
    arrow(ax, (6.025, 2.62), (6.40, 2.62), color=INK, lw=1.2, style="-|>", shrink=0)
    label(ax, 6.21, 2.43, "SQL", fs=7.2, color=GRAY)
    arrow(ax, (5.30, 3.12), (6.40, 3.72), color=INK, lw=1.2, style="-|>", shrink=0)
    label(ax, 5.86, 3.55, "缓存", fs=7.2, color=GRAY)

    save(fig, "fig_deploy.png")




# ---------------------------------------------------------------- 9 业务流程图（泳道）
def swimlane(name, lanes, steps, start_lane, end_lane, filename):
    header_h = 0.55
    top = 0.30
    row0 = 1.65
    step_h = 0.85
    node_h = 0.50
    W = 0.30 + sum(w for _, w in lanes) + 0.15
    H = row0 + (len(steps) - 1) * step_h + 1.15

    fig, ax = fig_ax(W, H)
    xs = [0.30]
    for _, w in lanes:
        xs.append(xs[-1] + w)
    cx = [(xs[i] + xs[i + 1]) / 2 for i in range(len(lanes))]

    # 表头与泳道
    ax.add_patch(Rectangle((xs[0], top), xs[-1] - xs[0], header_h,
                           facecolor="#404040", edgecolor="#404040", lw=1.0, zorder=1))
    for i, (title, _) in enumerate(lanes):
        ax.text(cx[i], top + header_h / 2, title, ha="center", va="center",
                fontsize=10, color="white", fontweight="bold", zorder=2)
    ax.add_patch(Rectangle((xs[0], top + header_h), xs[-1] - xs[0], H - top - header_h,
                           facecolor="white", edgecolor="black", lw=1.0, zorder=0.5))
    for x in xs[1:-1]:
        ax.add_line(Line2D([x, x], [top + header_h, H - 0.1], color="#606060", lw=0.8, zorder=0.8))

    def ny(i):
        return row0 + i * step_h

    def nw(i):
        return min(lanes[i][1] - 0.35, 2.65)

    stadium(ax, cx[start_lane], 1.02, 1.0, 0.36, "开始", fs=9)
    prev = None
    for i, (lane, text) in enumerate(steps):
        rbox(ax, cx[lane], ny(i), nw(lane), node_h, text, fs=8.6,
             fc="white", ec="black", lw=0.9, radius=0.03)
        if prev is not None:
            pl, py = prev
            if pl == lane:
                arrow(ax, (cx[pl], py + node_h / 2), (cx[lane], ny(i) - node_h / 2),
                      color="black", lw=0.9, shrink=0)
            else:
                mid = py + node_h / 2 + 0.14
                poly_arrow(ax, [(cx[pl], py + node_h / 2), (cx[pl], mid),
                                (cx[lane], mid), (cx[lane], ny(i) - node_h / 2)],
                           color="black", lw=0.9)
        prev = (lane, ny(i))

    arrow(ax, (cx[start_lane], 1.20), (cx[steps[0][0]], ny(0) - node_h / 2),
          color="black", lw=0.9, shrink=0)
    stadium(ax, cx[end_lane], ny(len(steps) - 1) + 0.92, 1.0, 0.36, "结束", fs=9)
    arrow(ax, (cx[end_lane], ny(len(steps) - 1) + node_h / 2),
          (cx[end_lane], ny(len(steps) - 1) + 0.74), color="black", lw=0.9, shrink=0)

    save(fig, filename)


def business_flows():
    recv_lanes = [("收件人", 2.25), ("驿站工作人员", 2.55), ("系统", 2.85)]
    recv_steps = [
        (1, "快递到站，核对件数"),
        (1, "扫描或输入运单号"),
        (2, "校验运单号，匹配收件人"),
        (1, "确认驿站与空闲格口"),
        (2, "生成取件码，状态置为在库"),
        (2, "推送取件通知"),
        (0, "查收通知，到站取件"),
        (1, "录入取件码与手机号后四位"),
        (2, "核验身份，写入取件记录"),
        (2, "释放格口，推送成功通知"),
        (0, "取件离站"),
    ]
    swimlane("收件", recv_lanes, recv_steps, 1, 0, "fig_flow_business_recv.png")

    send_lanes = [("学生", 2.25), ("驿站工作人员", 2.55), ("系统", 2.85)]
    send_steps = [
        (0, "在线填写寄件信息"),
        (2, "估算运费，生成寄件订单"),
        (0, "到驿站交寄"),
        (1, "揽收、称重"),
        (2, "确认运费，订单置为已揽收"),
        (1, "登记发出"),
        (2, "写轨迹，订单置为已发出"),
        (0, "查看订单与轨迹"),
        (1, "确认签收，完成订单"),
        (2, "推送完成通知"),
    ]
    swimlane("寄件", send_lanes, send_steps, 0, 2, "fig_flow_business_send.png")


if __name__ == "__main__":
    architecture()
    module_tree()
    er_diagram()
    flow_inbound()
    flow_pickup()
    ns_inbound()
    ns_pickup()
    deployment()
    business_flows()
