# -*- coding: utf-8 -*-
"""按课程模板生成需求分析 / 系统设计阶段的 Excel 交付物。

输出：
    docs/交付物/功能分析表.xlsx
    docs/交付物/数据分析表.xlsx
    docs/交付物/数据库表结构.xlsx
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "交付物"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "宋体"
THIN = Side(style="thin", color="808080")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="D9E2F3")
LABEL_FILL = PatternFill("solid", fgColor="F2F2F2")


def style_cell(c, bold=False, fill=None, size=10, align="left", wrap=True):
    c.font = Font(name=FONT, size=size, bold=bold)
    c.alignment = Alignment(horizontal=align, vertical="center" if align == "center" else "top",
                            wrap_text=wrap)
    c.border = BORDER
    if fill:
        c.fill = fill


def est_height(text, width_chars, base=14.5):
    """width_chars 为 Excel 列宽单位，一个汉字约占 1.9 个单位。"""
    cpl = max(width_chars / 1.9, 8)
    lines = 0
    for part in str(text).split("\n"):
        eff = sum(1 if ord(ch) > 127 else 0.55 for ch in part)
        lines += max(1, int(eff / cpl) + 1)
    return min(max(base * lines + 6, 20), 320)


# ============================================================ 功能分析表
MODULES = [
    {
        "name": "用户与权限管理",
        "desc": "提供学生、驿站工作人员、管理员三类账号的统一认证与权限控制，支持学生自助注册、管理员维护账号与角色。",
        "rules": [
            "手机号全局唯一，一个手机号只能绑定一个账号。",
            "学生可自助注册；工作人员与管理员账号只能由管理员创建。",
            "密码使用 bcrypt 加密存储，长度不少于 8 位，必须同时包含字母与数字。",
            "连续 5 次密码错误锁定账号 15 分钟。",
            "账号被禁用后立即禁止登录，已签发令牌由 Redis 黑名单拦截。",
            "角色与权限绑定，前端菜单与后端接口双重校验。",
        ],
        "level": "学生、驿站工作人员、系统管理员",
        "pre": "系统已完成初始化，管理员账号已创建。",
        "basic": [
            "学生注册：手机号、学号、姓名、密码。",
            "登录：支持学号、工号或手机号 + 密码，返回访问令牌与刷新令牌。",
            "令牌刷新：访问令牌过期前静默续期。",
            "退出登录：令牌加入黑名单。",
            "查看与修改个人信息（姓名、学院、头像）。",
            "修改密码：校验原密码。",
            "管理员分页查询用户，按角色、状态、关键字筛选。",
            "管理员新增工作人员或管理员账号。",
            "管理员启用、禁用账号。",
        ],
        "aux": [
            "记住登录账号（仅本地保存账号，不保存密码）。",
            "忘记密码：由管理员重置，本期不做短信找回。",
            "用户列表导出 CSV。",
        ],
        "tips": [
            "登录成功提示“登录成功，正在进入系统”。",
            "账号或密码错误提示“账号或密码错误，请重试”。",
            "账号被禁用提示“账号已被禁用，请联系管理员”。",
            "两次密码不一致提示“两次输入的密码不一致”。",
            "修改成功提示“密码修改成功，请重新登录”。",
        ],
        "constraints": [
            "密码不得明文传输，生产环境必须使用 HTTPS。",
            "非管理员不得调用用户管理接口。",
            "管理员不能禁用自己。",
            "删除用户前检查是否存在未完成业务，改为禁用。",
        ],
        "input": "<手机号>、<学号/工号>、<姓名>、<密码>、<角色>、<学院>",
        "output": "<访问令牌>、<刷新令牌>、<用户信息>、<用户列表>",
        "check": "登录鉴权、角色权限隔离、密码安全",
        "nfr": "【性能需求】登录响应时间≤500ms，用户列表≤300ms。\n"
               "【安全需求】bcrypt 加密、JWT 鉴权、登录失败锁定、越权返回 403。",
        "stat": "各角色用户数量、日活跃用户数",
        "forms": "无",
    },
    {
        "name": "驿站与货架管理",
        "desc": "维护校园内多个驿站及其货架分区，提供格口容量与占用率数据，为快递入库分配提供依据。",
        "rules": [
            "驿站编码唯一，停用驿站不允许新增入库。",
            "货架编号在所属驿站内唯一。",
            "货架已用格口数由入库、出库自动维护，不允许手工修改。",
            "删除货架前必须保证已用格口数为 0。",
            "驿站容量为所有启用货架容量之和，仅用于展示与预警。",
        ],
        "level": "系统管理员（维护）、驿站工作人员（查看本站）",
        "pre": "管理员已登录，具备驿站管理权限。",
        "basic": [
            "驿站列表与详情查询。",
            "新增、修改驿站（名称、地址、电话、营业时间）。",
            "启用、停用驿站。",
            "货架列表，展示容量、已用格口与占用率。",
            "新增、修改货架（编号、分区、容量）。",
            "删除空闲货架。",
        ],
        "aux": [
            "按驿站筛选货架。",
            "按占用率排序。",
            "容量预警：占用率超过 90% 标红。",
        ],
        "tips": [
            "新增成功提示“驿站信息已保存”。",
            "编码重复提示“驿站编码已存在，请更换”。",
            "货架存在包裹时提示“该货架仍有包裹，无法删除”。",
            "驿站停用后入库提示“驿站已停用，暂不可入库”。",
        ],
        "constraints": [
            "驿站编码、货架编号唯一。",
            "删除货架前校验已用格口数。",
            "停用驿站不影响已存放包裹的取件。",
        ],
        "input": "<驿站编码>、<名称>、<地址>、<营业时间>、<货架编号>、<分区>、<容量>",
        "output": "<驿站列表>、<货架列表>、<占用率>、<容量预警>",
        "check": "容量计算准确性、驿站与货架状态联动",
        "nfr": "【性能需求】列表查询≤300ms。\n【安全需求】仅管理员可维护，工作人员只读本站数据。",
        "stat": "驿站数量、货架数量、总格口数、平均占用率",
        "forms": "无",
    },
    {
        "name": "快递入库管理",
        "desc": "快递到站后登记运单信息，匹配收件人、分配格口、生成取件码并通知收件人，是收件业务的起点。",
        "rules": [
            "运单号全局唯一，重复入库拒绝并展示原记录。",
            "收件人手机号必须为 11 位；未匹配到用户时登记为临时收件人。",
            "取件码为 6 位数字，驿站内唯一，有效期默认 7 天。",
            "包裹入库后状态为“在库”，同时记录入库时间与操作员。",
            "驿站无空闲格口时禁止入库。",
            "入库、占用格口、写通知、写日志必须在同一事务内完成。",
        ],
        "level": "驿站工作人员、系统管理员",
        "pre": "已登录且所属驿站处于营业状态。",
        "basic": [
            "单件入库：运单号、收件人手机号、快递公司、包裹类型、重量。",
            "支持扫码枪输入，回车提交。",
            "系统推荐空闲格口，支持手工改选。",
            "生成取件码并展示，支持复制。",
            "批量导入：上传 Excel 模板，逐条校验并返回成功/失败结果。",
            "入库记录分页查询与详情查看。",
            "调整货架格口。",
        ],
        "aux": [
            "展示最近 10 条入库记录。",
            "重复运单提示原入库时间与取件码。",
            "打印入库小票。",
        ],
        "tips": [
            "入库成功提示“入库成功，取件码：XXXXXX”。",
            "运单重复提示“该运单已入库，请勿重复登记”。",
            "格口不足提示“驿站格口已满，请扩容或转其他驿站”。",
            "手机号格式错误提示“请输入 11 位手机号”。",
        ],
        "constraints": [
            "运单号唯一约束兜底，重复提交返回原记录。",
            "取件码冲突时最多重试 5 次。",
            "包裹写入与格口计数在同一事务内，失败整体回滚。",
        ],
        "input": "<运单号>、<收件人手机号>、<快递公司>、<包裹类型>、<重量>、<驿站>、<货架>",
        "output": "<包裹记录>、<取件码>、<入库时间>、<批量导入结果>",
        "check": "运单唯一性校验、取件码生成、格口分配与事务一致性",
        "nfr": "【性能需求】单件入库≤400ms，批量 100 条≤10s。\n【安全需求】仅本站工作人员可操作，操作留痕。",
        "stat": "今日入库量、按快递公司分布、按驿站分布",
        "forms": "《快递入库登记表》",
    },
    {
        "name": "取件出库管理",
        "desc": "收件人凭取件码与手机号后四位到站取件，工作人员核验身份后完成出库、释放格口并记录取件信息。",
        "rules": [
            "取件码必须存在、未过期，且包裹状态为在库或超期。",
            "手机号后四位必须与收件人手机号一致。",
            "一件包裹只能成功出库一次。",
            "出库后释放格口，记录取件时间与操作员。",
            "超期件出库时记录超期天数。",
            "同一手机号 10 分钟内连续 5 次核验失败，暂停核验 10 分钟。",
        ],
        "level": "驿站工作人员、系统管理员",
        "pre": "包裹已完成入库，状态为在库或超期。",
        "basic": [
            "输入取件码查询包裹。",
            "核验手机号后四位。",
            "出库确认，展示包裹信息与取件人。",
            "写入取件记录。",
            "取件记录分页查询。",
            "退回登记。",
        ],
        "aux": [
            "扫码取件。",
            "待取件列表。",
            "超期件整行标红。",
        ],
        "tips": [
            "核验成功提示“核验通过，请交付包裹”。",
            "取件码无效提示“取件码无效或已过期，请人工查询”。",
            "手机号不匹配提示“手机号后四位不匹配，请核对”。",
            "包裹已出库提示“该包裹已于 X 时出库”。",
        ],
        "constraints": [
            "重复提交幂等：状态条件更新 + 取件记录唯一约束。",
            "并发出库使用行锁，防止重复扣减格口。",
            "格口计数使用 GREATEST 保护，不允许为负。",
        ],
        "input": "<取件码>、<手机号后四位>、<操作员>",
        "output": "<取件记录>、<包裹状态>、<超期天数>",
        "check": "双重核验、幂等控制、事务一致性",
        "nfr": "【性能需求】核验响应≤300ms。\n【安全需求】核验失败限流，取件记录可追溯。",
        "stat": "今日出库量、平均取件时长、超期件占比",
        "forms": "《取件登记表》",
    },
    {
        "name": "寄件管理",
        "desc": "学生在线下单寄件，驿站揽收称重、确认运费并登记轨迹，学生可随时查看寄件进度。",
        "rules": [
            "寄件订单号唯一，格式为 S + 日期 + 6 位序号。",
            "运费按首重 8 元、续重 2 元/kg 估算，实际以驿站称重为准。",
            "订单状态按待揽收→已揽收→已发出→已完成流转。",
            "仅待揽收状态可取消，取消后不可恢复。",
            "揽收时必须录入实际重量，才能进入已揽收状态。",
            "轨迹按发生时间倒序展示。",
        ],
        "level": "学生（下单与查看）、驿站工作人员（揽收与轨迹）",
        "pre": "学生已登录，已选择受理驿站。",
        "basic": [
            "填写寄件信息（收件人、电话、地址、物品、预估重量）。",
            "系统估算运费。",
            "生成寄件订单。",
            "订单列表与详情查询。",
            "驿站揽收称重，确认实际运费。",
            "登记发出与轨迹节点。",
            "确认订单完成。",
            "取消待揽收订单。",
        ],
        "aux": [
            "历史收件地址快速填充。",
            "按状态筛选订单。",
            "轨迹时间轴展示。",
        ],
        "tips": [
            "下单成功提示“寄件订单已创建，订单号：SXXXX”。",
            "状态不允许提示“当前订单状态不支持该操作”。",
            "揽收未填重量提示“请先录入实际重量”。",
            "取消成功提示“订单已取消”。",
        ],
        "constraints": [
            "状态机校验，非法流转返回 30001。",
            "称重完成前不允许登记发出。",
            "学生只能查看本人订单。",
        ],
        "input": "<收件人>、<电话>、<地址>、<物品>、<重量>、<驿站>",
        "output": "<订单号>、<运费>、<订单状态>、<轨迹列表>",
        "check": "运费计算、订单状态流转",
        "nfr": "【性能需求】下单≤500ms，轨迹查询≤300ms。\n【安全需求】学生仅可访问本人订单。",
        "stat": "寄件量、运费收入、按驿站分布",
        "forms": "《寄件订单》",
    },
    {
        "name": "异常件与超期管理",
        "desc": "对超期未取、破损、丢失、错分等异常包裹进行识别、登记与处理，支持退回闭环。",
        "rules": [
            "包裹入库超过 3 天未取，自动标记为超期。",
            "超期 7 天仍未取，转退回处理。",
            "异常登记必须填写异常类型与描述。",
            "异常处理状态分为待处理、处理中、已解决。",
            "退回后释放格口，包裹状态为已退回。",
            "超期判定任务每日 02:00 执行。",
        ],
        "level": "驿站工作人员、系统管理员",
        "pre": "包裹已入库且状态正常。",
        "basic": [
            "超期件列表与超期天数展示。",
            "异常登记（类型、描述）。",
            "异常处理状态更新。",
            "退回登记并释放格口。",
            "异常记录查询。",
        ],
        "aux": [
            "按超期天数排序。",
            "批量发送超期提醒。",
            "异常类型统计。",
        ],
        "tips": [
            "登记成功提示“异常件已登记”。",
            "已退回提示“该包裹已退回，不可重复操作”。",
            "处理完成提示“异常件已处理完成”。",
        ],
        "constraints": [
            "退回需二次确认。",
            "退回与释放格口在同一事务内。",
            "已退回包裹不允许再次出库。",
        ],
        "input": "<包裹>、<异常类型>、<描述>、<处理人>",
        "output": "<异常记录>、<包裹状态>、<超期天数>",
        "check": "超期判定准确性、异常处理闭环",
        "nfr": "【性能需求】批量超期任务≤5min。\n【安全需求】仅工作人员可操作，全程留痕。",
        "stat": "超期率、异常类型分布、退回量",
        "forms": "《异常件登记表》",
    },
    {
        "name": "通知与公告管理",
        "desc": "向收件人推送取件、超期、寄件状态通知，管理员发布校园驿站公告。",
        "rules": [
            "通知按用户维度写入，未读数量实时统计。",
            "通知渠道为站内信，短信通道以日志模拟。",
            "公告仅管理员可发布，下架后学生不可见。",
            "通知默认保留 90 天。",
        ],
        "level": "全部角色",
        "pre": "已登录。",
        "basic": [
            "通知列表与未读数量展示。",
            "单条标记已读。",
            "全部标记已读。",
            "公告列表与详情查看。",
            "管理员发布、编辑、下架公告。",
        ],
        "aux": [
            "按通知类型筛选。",
            "公告置顶。",
            "公告详情富文本展示。",
        ],
        "tips": [
            "发布成功提示“公告已发布”。",
            "下架成功提示“公告已下架”。",
            "无新通知提示“暂无新消息”。",
        ],
        "constraints": [
            "学生只能查看本人通知。",
            "公告正文过滤脚本与非法标签。",
        ],
        "input": "<通知类型>、<标题>、<内容>、<公告正文>",
        "output": "<通知列表>、<未读数量>、<公告列表>",
        "check": "通知触达、公告权限控制",
        "nfr": "【性能需求】未读数查询≤100ms（Redis 计数）。\n【安全需求】XSS 过滤，公告仅管理员可发布。",
        "stat": "通知发送量、已读率",
        "forms": "《公告》",
    },
    {
        "name": "统计报表",
        "desc": "汇总收发量、驿站工作量、超期率等指标，为驿站运营与课程答辩提供数据支撑。",
        "rules": [
            "统计口径按自然日，时区统一为 Asia/Shanghai。",
            "学生无权查看统计；工作人员仅可查看本站。",
            "统计结果缓存 5 分钟。",
            "趋势默认近 7 天，可切换近 30 天。",
        ],
        "level": "系统管理员（全局）、驿站工作人员（本站）",
        "pre": "已登录且角色为工作人员或管理员。",
        "basic": [
            "总览指标：在库、今日入库、今日出库、超期件。",
            "收发量趋势图（按日、按周）。",
            "驿站工作量对比。",
            "超期率与超期件分布。",
            "异常件统计。",
        ],
        "aux": [
            "时间范围切换。",
            "导出 Excel。",
        ],
        "tips": [
            "无数据提示“所选时间范围内暂无数据”。",
            "加载失败提示“数据加载失败，请重试”。",
        ],
        "constraints": [
            "统计接口只读，禁止修改业务数据。",
            "查询走覆盖索引，避免影响业务表性能。",
        ],
        "input": "<时间范围>、<驿站>",
        "output": "<指标卡>、<趋势图>、<对比表>",
        "check": "统计口径一致性、数据范围隔离",
        "nfr": "【性能需求】报表加载≤2s。\n【安全需求】按角色限定数据范围。",
        "stat": "上述指标本身",
        "forms": "《统计报表》",
    },
]


def build_function_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "功能项清单"
    headers = ["编号", "功能项名称", "备注"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=i, value=h)
        style_cell(c, bold=True, fill=HEAD_FILL, align="center")
    for i, m in enumerate(MODULES, 1):
        ws.cell(row=i + 1, column=1, value=i)
        ws.cell(row=i + 1, column=2, value=m["name"])
        ws.cell(row=i + 1, column=3, value="")
        for j in range(1, 4):
            style_cell(ws.cell(row=i + 1, column=j), align="center" if j == 1 else "left")
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 40
    ws.freeze_panes = "A2"

    for idx, m in enumerate(MODULES, 1):
        sh = wb.create_sheet(f"{idx}.{m['name']}")
        widths = {"A": 14, "B": 13, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12, "H": 12, "I": 12, "J": 12}
        for col, w in widths.items():
            sh.column_dimensions[col].width = w

        def put_row(r, label, value, label2=None, value2=None):
            a = sh.cell(row=r, column=1, value=label)
            style_cell(a, bold=True, fill=LABEL_FILL)
            sh.merge_cells(start_row=r, start_column=2, end_row=r, end_column=10)
            b = sh.cell(row=r, column=2, value=value)
            style_cell(b)
            for c_i in range(3, 11):
                style_cell(sh.cell(row=r, column=c_i))
            if label2:
                d = sh.cell(row=r, column=4, value=label2)
                style_cell(d, bold=True, fill=LABEL_FILL)

        # 标题
        sh.merge_cells("A1:J1")
        t = sh.cell(row=1, column=1, value=f"{idx}. {m['name']}")
        style_cell(t, bold=True, size=13, align="center")
        sh.row_dimensions[1].height = 28

        # 创建者 / 日期
        for r, label, person, date_label, date in [
            (2, "创建者", "项目组", "创建日期", "2026-10-26"),
            (3, "最后更新者", "项目组", "最后更新日期", "2026-10-26"),
        ]:
            a = sh.cell(row=r, column=1, value=label)
            style_cell(a, bold=True, fill=LABEL_FILL)
            sh.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
            b = sh.cell(row=r, column=2, value=person)
            style_cell(b)
            style_cell(sh.cell(row=r, column=3))
            d = sh.cell(row=r, column=4, value=date_label)
            style_cell(d, bold=True, fill=LABEL_FILL)
            sh.merge_cells(start_row=r, start_column=5, end_row=r, end_column=10)
            e = sh.cell(row=r, column=5, value=date)
            style_cell(e)
            for c_i in range(6, 11):
                style_cell(sh.cell(row=r, column=c_i))
            sh.row_dimensions[r].height = 22

        simple_rows = [
            (4, "业务说明", m["desc"]),
            (5, "业务规则", "\n".join(f"{i}.{x}" for i, x in enumerate(m["rules"], 1))),
            (6, "使用级别", m["level"]),
            (7, "先决条件", m["pre"]),
        ]
        for r, label, value in simple_rows:
            put_row(r, label, value)
            sh.row_dimensions[r].height = est_height(value, 109)

        # 功能要求块
        sh.cell(row=8, column=1, value="功能要求")
        sh.merge_cells("A8:A11")
        style_cell(sh.cell(row=8, column=1), bold=True, fill=LABEL_FILL)
        for r in range(9, 12):
            style_cell(sh.cell(row=r, column=1), fill=LABEL_FILL)
        blocks = [
            (8, "基本功能", m["basic"]),
            (9, "辅助功能", m["aux"]),
            (10, "提示信息", m["tips"]),
            (11, "处理约束", m["constraints"]),
        ]
        for r, label, items in blocks:
            b = sh.cell(row=r, column=2, value=label)
            style_cell(b, bold=True, fill=LABEL_FILL)
            sh.merge_cells(start_row=r, start_column=3, end_row=r, end_column=10)
            text = "\n".join(f"{i}.{x}" for i, x in enumerate(items, 1))
            c = sh.cell(row=r, column=3, value=text)
            style_cell(c)
            for c_i in range(4, 11):
                style_cell(sh.cell(row=r, column=c_i))
            sh.row_dimensions[r].height = est_height(text, 96)

        # 信息处理要求
        sh.cell(row=12, column=1, value="信息处理要求")
        sh.merge_cells("A12:A13")
        style_cell(sh.cell(row=12, column=1), bold=True, fill=LABEL_FILL)
        style_cell(sh.cell(row=13, column=1), fill=LABEL_FILL)
        for r, label, value in [(12, "输入信息", m["input"]), (13, "输出信息", m["output"])]:
            b = sh.cell(row=r, column=2, value=label)
            style_cell(b, bold=True, fill=LABEL_FILL)
            sh.merge_cells(start_row=r, start_column=3, end_row=r, end_column=10)
            c = sh.cell(row=r, column=3, value=value)
            style_cell(c)
            for c_i in range(4, 11):
                style_cell(sh.cell(row=r, column=c_i))
            sh.row_dimensions[r].height = est_height(value, 96)

        for r, label, value in [
            (14, "考核要素", m["check"]),
            (15, "非功能需求", m["nfr"]),
            (16, "统计要素", m["stat"]),
            (17, "表卡单据", m["forms"]),
        ]:
            put_row(r, label, value)
            sh.row_dimensions[r].height = est_height(value, 109)

        sh.sheet_view.showGridLines = True

    path = OUT / "功能分析表.xlsx"
    wb.save(path)
    print("saved", path)


# ============================================================ 数据分析表
DATA_CLASSES = [
    ("用户信息", "记录学生、驿站工作人员、管理员的基本信息与账号状态", "手机号唯一；学号唯一；密码加密存储；角色只能为三类之一",
     "学生注册、管理员录入", "系统存储", ["学号/工号", "姓名", "手机号", "密码", "角色", "学院", "账号状态"]),
    ("驿站信息", "校园快递服务点的档案信息", "驿站编码唯一；停用驿站不可入库",
     "管理员录入", "系统存储", ["驿站编码", "驿站名称", "地址", "联系电话", "营业时间", "总容量", "状态"]),
    ("货架信息", "驿站内货架及格口容量信息", "编号在驿站内唯一；已用格口不超过容量",
     "管理员/工作人员录入", "系统存储", ["货架编号", "所属驿站", "分区", "容量", "已用格口", "状态"]),
    ("包裹信息", "快递到站后的运单与存放信息", "运单号全局唯一；取件码站内唯一；状态受流转规则约束",
     "工作人员扫码/录入", "系统存储", ["运单号", "快递公司", "包裹类型", "重量", "收件人", "收件人手机号", "所属驿站", "货架", "状态", "取件码", "入库时间"]),
    ("取件记录", "包裹出库时的核验与签收信息", "一件包裹仅一条成功记录；取件码与手机后四位必填",
     "工作人员核验", "系统存储", ["所属包裹", "操作员", "取件码", "手机号后四位", "核验方式", "取件时间"]),
    ("寄件订单", "学生在线寄件的订单信息", "订单号唯一；状态按待揽收→已揽收→已发出→已完成流转",
     "学生下单", "系统存储", ["订单号", "寄件人", "受理驿站", "收件人", "收件电话", "收件地址", "物品名称", "重量", "运费", "状态"]),
    ("寄件轨迹", "寄件订单的物流节点记录", "按发生时间排序；节点必须属于该订单",
     "工作人员登记", "系统存储", ["所属订单", "节点名称", "节点状态", "描述", "操作人", "发生时间"]),
    ("通知信息", "系统向用户推送的消息", "按用户隔离；默认保留 90 天",
     "系统生成", "系统存储", ["接收人", "通知类型", "标题", "内容", "关联包裹/订单", "渠道", "是否已读", "发送时间"]),
    ("公告信息", "管理员发布的驿站公告", "仅管理员可发布；下架后不可见",
     "管理员发布", "系统存储", ["标题", "正文", "发布人", "状态", "发布时间"]),
    ("异常记录", "破损、丢失、错分等异常件的处理记录", "必须关联包裹；状态为待处理/处理中/已解决",
     "工作人员登记", "系统存储", ["所属包裹", "异常类型", "描述", "处理人", "处理状态", "完成时间"]),
    ("操作日志", "关键写操作的审计记录", "只增不改；记录操作人、IP 与时间",
     "系统生成", "系统存储", ["操作人", "模块", "动作", "目标对象", "参数快照", "IP 地址", "操作时间"]),
]

DATA_ITEMS = [
    ("学号/工号", "学生在校学号或教职工工号", "用户输入", "文本型", "唯一，长度≤20", "8—20 位数字或字母", "20", "用户信息"),
    ("姓名", "用户真实姓名", "用户输入", "文本型", "非空，长度≤50", "2—20 个汉字", "50", "用户信息"),
    ("手机号", "用户联系手机号，用于登录与取件核验", "用户输入", "文本型", "唯一，11 位", "1 开头 11 位数字", "11", "用户信息、包裹信息"),
    ("密码", "用户登录口令的哈希值", "用户输入", "文本型", "8—32 位，含字母和数字", "bcrypt 哈希后存储", "100", "用户信息"),
    ("角色", "用户所属角色", "系统生成", "列表型", "取值为学生/工作人员/管理员", "参见数据列表", "16", "用户信息"),
    ("学院", "学生所在学院或教职工部门", "用户输入", "文本型", "长度≤100", "", "100", "用户信息"),
    ("账号状态", "账号是否可用", "系统维护", "列表型", "正常/禁用", "1 正常，0 禁用", "1", "用户信息"),
    ("驿站编码", "驿站的唯一业务编码", "管理员录入", "文本型", "唯一，长度≤20", "ST- 开头", "20", "驿站信息"),
    ("驿站名称", "驿站对外名称", "管理员录入", "文本型", "非空", "", "50", "驿站信息"),
    ("驿站地址", "驿站详细地址", "管理员录入", "文本型", "非空，长度≤200", "", "200", "驿站信息"),
    ("营业时间", "驿站每日营业起止时间", "管理员录入", "时间型", "开始早于结束", "00:00—23:59", "8", "驿站信息"),
    ("总容量", "驿站所有货架格口总数", "系统汇总", "数值型", "≥0", "[0,9999]", "4", "驿站信息"),
    ("货架编号", "货架在驿站内的编号", "管理员/工作人员录入", "文本型", "驿站内唯一", "如 A-03", "20", "货架信息"),
    ("分区", "货架所属区域", "管理员/工作人员录入", "文本型", "长度≤20", "A—Z", "20", "货架信息"),
    ("格口容量", "货架可存放包裹的数量", "管理员/工作人员录入", "数值型", "≥1", "[1,200]", "3", "货架信息"),
    ("已用格口", "货架当前占用数量", "系统维护", "数值型", "0≤已用≤容量", "[0,容量]", "3", "货架信息"),
    ("运单号", "快递公司的物流单号", "工作人员录入/扫码", "文本型", "全局唯一", "6—40 位字母数字", "40", "包裹信息"),
    ("快递公司", "承运快递公司名称", "工作人员录入", "列表型", "取值参见数据列表", "顺丰/中通/圆通等", "30", "包裹信息"),
    ("包裹类型", "包裹的属性分类", "工作人员录入", "列表型", "普通/易碎/大件/文件", "参见数据列表", "16", "包裹信息"),
    ("重量", "包裹重量（kg）", "工作人员录入", "数值型", "0<重量≤100", "[0.01,100.00]，两位小数", "6,2", "包裹信息"),
    ("收件人手机号", "包裹面单上的收件电话", "工作人员录入", "文本型", "11 位", "1 开头 11 位数字", "11", "包裹信息"),
    ("取件码", "包裹入库后生成的取件凭证", "系统生成", "文本型", "站内唯一，6 位数字", "000000—999999", "6", "包裹信息"),
    ("包裹状态", "包裹当前所处状态", "系统维护", "列表型", "受状态机约束", "在库/已取件/超期/已退回/异常", "16", "包裹信息"),
    ("入库时间", "包裹完成入库的时间", "系统生成", "时间型", "不晚于当前时间", "YYYY-MM-DD HH:mm:ss", "19", "包裹信息"),
    ("取件时间", "包裹完成出库的时间", "系统生成", "时间型", "不早于入库时间", "YYYY-MM-DD HH:mm:ss", "19", "取件记录"),
    ("核验方式", "取件时的身份核验方式", "工作人员选择", "列表型", "取件码+手机号/人工", "参见数据列表", "16", "取件记录"),
    ("手机号后四位", "取件核验时输入的后四位", "工作人员录入", "文本型", "4 位数字", "0000—9999", "4", "取件记录"),
    ("订单号", "寄件订单的唯一编号", "系统生成", "文本型", "唯一", "S+yyyyMMdd+6 位序号", "32", "寄件订单"),
    ("收件人", "寄件的收件人姓名", "学生录入", "文本型", "非空", "", "50", "寄件订单"),
    ("收件地址", "寄件的收件地址", "学生录入", "文本型", "非空，长度≤200", "", "200", "寄件订单"),
    ("物品名称", "寄递物品名称", "学生录入", "文本型", "非空", "", "100", "寄件订单"),
    ("运费", "寄件应收运费（元）", "系统计算", "数值型", "≥0", "[0,9999.99]，两位小数", "8,2", "寄件订单"),
    ("订单状态", "寄件订单当前状态", "系统维护", "列表型", "受状态机约束", "待揽收/已揽收/已发出/已完成/已取消", "16", "寄件订单"),
    ("轨迹节点", "物流轨迹的节点名称", "工作人员录入", "文本型", "非空", "如驿站揽收、已发出", "50", "寄件轨迹"),
    ("发生时间", "轨迹节点的发生时间", "工作人员录入", "时间型", "不晚于当前时间", "", "19", "寄件轨迹"),
    ("通知类型", "通知的业务类别", "系统生成", "列表型", "取件/超期/寄件/系统", "参见数据列表", "16", "通知信息"),
    ("通知标题", "通知的简短标题", "系统生成", "文本型", "非空，长度≤100", "", "100", "通知信息"),
    ("通知内容", "通知的正文内容", "系统生成", "文本型", "长度≤500", "", "500", "通知信息"),
    ("是否已读", "用户是否已查看", "系统维护", "列表型", "未读/已读", "0 未读，1 已读", "1", "通知信息"),
    ("公告标题", "公告标题", "管理员录入", "文本型", "非空，长度≤100", "", "100", "公告信息"),
    ("公告正文", "公告详细内容", "管理员录入", "文本型", "长度≤5000", "过滤脚本标签", "5000", "公告信息"),
    ("异常类型", "异常件的分类", "工作人员选择", "列表型", "破损/丢失/错分/退回/其他", "参见数据列表", "16", "异常记录"),
    ("异常描述", "异常情况说明", "工作人员录入", "文本型", "非空，长度≤300", "", "300", "异常记录"),
    ("处理状态", "异常处理进度", "系统维护", "列表型", "待处理/处理中/已解决", "参见数据列表", "16", "异常记录"),
    ("操作模块", "日志所属业务模块", "系统生成", "文本型", "非空", "如 package、auth", "30", "操作日志"),
    ("操作动作", "具体操作名称", "系统生成", "文本型", "非空", "如 inbound、pickup", "50", "操作日志"),
    ("IP 地址", "客户端访问地址", "系统生成", "文本型", "IPv4 或 IPv6", "", "45", "操作日志"),
]

DATA_LISTS = [
    ("角色", ["学生 student", "驿站工作人员 staff", "系统管理员 admin"]),
    ("账号状态", ["正常（1）", "禁用（0）"]),
    ("包裹状态", ["在库 in_stock", "已取件 picked", "超期 overdue", "已退回 returned", "异常 exception"]),
    ("包裹类型", ["普通 normal", "易碎 fragile", "大件 large", "文件 doc"]),
    ("核验方式", ["取件码+手机号 code_phone", "人工核验 manual"]),
    ("寄件订单状态", ["待揽收 pending", "已揽收 accepted", "已发出 shipped", "已完成 completed", "已取消 cancelled"]),
    ("通知类型", ["取件 pickup", "超期 overdue", "寄件 shipment", "系统 system"]),
    ("通知渠道", ["站内信 inapp", "短信 sms（模拟）"]),
    ("异常类型", ["破损 damaged", "丢失 lost", "错分 wrong_station", "退回 returned", "其他 other"]),
    ("异常处理状态", ["待处理 open", "处理中 processing", "已解决 resolved"]),
    ("公告状态", ["已发布 1", "草稿/下架 0"]),
    ("快递公司", ["顺丰速运", "中通快递", "圆通速递", "韵达快递", "京东物流", "邮政 EMS"]),
    ("驿站状态", ["营业 1", "停用 0"]),
    ("货架状态", ["可用 1", "停用 0"]),
]


def build_data_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "数据类"
    headers = ["序号", "数据类名称", "数据描述", "限制与约束", "数据来源", "数据存储", "数据组成"]
    widths = [6, 16, 42, 42, 18, 12, 70]
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(row=1, column=i, value=h)
        style_cell(c, bold=True, fill=HEAD_FILL, align="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    for r, (name, desc, limit, source, store, parts) in enumerate(DATA_CLASSES, 2):
        vals = [r - 1, name, desc, limit, source, store, "、".join(parts)]
        for c_i, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=c_i, value=v)
            style_cell(c, align="center" if c_i in (1, 6) else "left")
        ws.row_dimensions[r].height = max(est_height(desc, 42), est_height(limit, 42),
                                          est_height("、".join(parts), 70))
    ws.freeze_panes = "A2"

    ws2 = wb.create_sheet("数据项")
    headers2 = ["序号", "数据项名称", "数据描述", "数据来源", "数据类型", "限制与约束",
                "数据精度与取值范围", "字长", "引用此数据项的数据类", "备注"]
    widths2 = [6, 18, 40, 16, 10, 36, 30, 8, 26, 12]
    for i, (h, w) in enumerate(zip(headers2, widths2), 1):
        c = ws2.cell(row=1, column=i, value=h)
        style_cell(c, bold=True, fill=HEAD_FILL, align="center")
        ws2.column_dimensions[get_column_letter(i)].width = w
    for r, (name, desc, source, dtype, limit, rng, length, refs) in enumerate(DATA_ITEMS, 2):
        vals = [r - 1, name, desc, source, dtype, limit, rng, length, refs, ""]
        for c_i, v in enumerate(vals, 1):
            c = ws2.cell(row=r, column=c_i, value=v)
            style_cell(c, align="center" if c_i in (1, 5, 8) else "left")
        ws2.row_dimensions[r].height = est_height(desc, 40)
    ws2.freeze_panes = "A2"

    ws3 = wb.create_sheet("数据列表")
    headers3 = ["序号", "数据项名称", "数据列表取值", "备注"]
    widths3 = [6, 20, 46, 30]
    for i, (h, w) in enumerate(zip(headers3, widths3), 1):
        c = ws3.cell(row=1, column=i, value=h)
        style_cell(c, bold=True, fill=HEAD_FILL, align="center")
        ws3.column_dimensions[get_column_letter(i)].width = w
    row = 2
    for idx, (name, values) in enumerate(DATA_LISTS, 1):
        start = row
        for v in values:
            c = ws3.cell(row=row, column=3, value=v)
            style_cell(c)
            row += 1
        ws3.cell(row=start, column=1, value=idx)
        ws3.cell(row=start, column=2, value=name)
        style_cell(ws3.cell(row=start, column=1), align="center")
        style_cell(ws3.cell(row=start, column=2))
        if row - 1 > start:
            ws3.merge_cells(start_row=start, start_column=1, end_row=row - 1, end_column=1)
            ws3.merge_cells(start_row=start, start_column=2, end_row=row - 1, end_column=2)
    ws3.freeze_panes = "A2"

    path = OUT / "数据分析表.xlsx"
    wb.save(path)
    print("saved", path)


if __name__ == "__main__":
    build_function_xlsx()
    build_data_xlsx()
