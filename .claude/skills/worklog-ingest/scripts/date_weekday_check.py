#!/usr/bin/env python3
"""星期↔日期映射一致性检查（日期门，P0）。

用法:
    python3 date_weekday_check.py <file.md> [<file2.md> ...]
    python3 date_weekday_check.py --all          # 全仓 diaries/ + wiki/

覆盖 7 种写法（zh 5 种 + en 2 种）:
    1. frontmatter `date:` + `day: 周X`
    2. 标题「YYYY年M月D日（周X）」
    3. 「M/D（周X）」        （年份按 frontmatter date 或文件名推断, 兜底当前年）
    4. 「周X（M/D）」
    5. 「YYYY-MM-DD（周X）」
    6. frontmatter `date:` + `day: Saturday`（en locale）
    7. 「YYYY-MM-DD (Saturday)」（en，半角括号；括号词不是星期词则跳过不校验）

退出码: 0 = 干净 / 1 = 有不一致 / 2 = 用法错误 / 3 = 有文件读取失败(其余已检测, 与 punctuation_check.py 契约一致)。
写订正说明时引用旧错请改写成「误配」措辞（如「周六原误配 7/12」），
不要原样保留错误的「周X（M/D）」配对, 否则本检查会持续命中引用文本。
"""
import datetime
import glob
import os
import re
import sys

WD = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
WDN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WD_EN = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
         "friday": 4, "saturday": 5, "sunday": 6}
WDN_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WORKLOG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def infer_year(text, path):
    m = re.search(r"^date: (\d{4})-", text, re.M)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{4})-\d{2}-\d{2}", os.path.basename(path))
    if m:
        return int(m.group(1))
    return datetime.date.today().year  # 动态兜底：无任何年份上下文时取当前年（调用方须先 export 正确 TZ）


def check_file(path):
    errors = []
    # OSError 交给 main 按「文件读取失败」处理: 读不到 ≠ 日期不一致, 不得混入错误计数
    text = open(path, encoding="utf-8").read()
    year = infer_year(text, path)

    def check(y, m, d, wd_char, line_no, ctx):
        try:
            real = datetime.date(y, m, d).weekday()
        except ValueError:
            errors.append((path, line_no, f"非法日期 {y}-{m}-{d}", ctx))
            return
        if WD.get(wd_char) != real:
            errors.append((path, line_no,
                           f"{y}-{m:02d}-{d:02d} 实为{WDN[real]}, 文中写周{wd_char}", ctx))

    def check_en(y, m, d, word, line_no, ctx):
        real_idx = WD_EN.get(word.lower())
        if real_idx is None:
            return  # 括号词不是星期（如 (draft)）, 不属校验对象
        try:
            real = datetime.date(y, m, d).weekday()
        except ValueError:
            errors.append((path, line_no, f"非法日期 {y}-{m}-{d}", ctx))
            return
        if real_idx != real:
            errors.append((path, line_no,
                           f"{y}-{m:02d}-{d:02d} 实为 {WDN_EN[real]}, 文中写 {word}", ctx))

    mdate = re.search(r"^date: (\d{4})-(\d{2})-(\d{2})", text, re.M)
    mday = re.search(r"^day: 周(.)", text, re.M)
    if mdate and mday:
        check(int(mdate.group(1)), int(mdate.group(2)), int(mdate.group(3)),
              mday.group(1), 0, "frontmatter date/day")
    mday_en = re.search(r"^day: ([A-Za-z]+)\s*$", text, re.M)
    if mdate and mday_en:
        check_en(int(mdate.group(1)), int(mdate.group(2)), int(mdate.group(3)),
                 mday_en.group(1), 0, "frontmatter date/day (en)")

    for i, ln in enumerate(text.split("\n"), 1):
        for m in re.finditer(r"(\d{4})年(\d{1,2})月(\d{1,2})日（周(.)）", ln):
            check(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), i, ln[:80])
        for m in re.finditer(r"(?<![\d/])(\d{1,2})/(\d{1,2})（周(.)）", ln):
            mo, da = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12 and 1 <= da <= 31:
                check(year, mo, da, m.group(3), i, ln[:80])
        for m in re.finditer(r"周(.)（(\d{1,2})/(\d{1,2})）", ln):
            mo, da = int(m.group(2)), int(m.group(3))
            if 1 <= mo <= 12 and 1 <= da <= 31:
                check(year, mo, da, m.group(1), i, ln[:80])
        for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})（周(.)）", ln):
            check(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), i, ln[:80])
        for m in re.finditer(r"(\d{4})-(\d{1,2})-(\d{1,2}) \(([A-Za-z]+)\)", ln):
            check_en(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4), i, ln[:80])
    return errors


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--all":
        files = sorted(glob.glob(f"{WORKLOG}/diaries/**/*.md", recursive=True)) + \
                sorted(glob.glob(f"{WORKLOG}/wiki/**/*.md", recursive=True))
    else:
        files = argv[1:]
    all_errors = []
    missing = False
    for f in files:
        try:
            all_errors.extend(check_file(f))
        except OSError as e:
            sys.stderr.write(f"⚠️ 文件读取失败(跳过): {f}: {e}\n")
            missing = True
    if all_errors:
        print(f"✗ {len(all_errors)} 处星期↔日期不一致（改后重跑）")
        for path, ln, msg, ctx in all_errors:
            rel = os.path.relpath(path, WORKLOG)
            print(f"{rel}:{ln}: {msg}")
            if ctx:
                print(f"    {ctx}")
        return 1
    if missing:
        return 3
    print(f"✓ 星期↔日期映射干净（{len(files)} 文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
