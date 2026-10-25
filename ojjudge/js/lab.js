/* ============================================================
 * OJJudge 对拍实验室 · 核心逻辑 + 界面
 *
 * 复刻桌面版对拍流程：生成器造随机数据 → 主程序与暴力/标程
 * 各跑一遍 → 比对输出。遇到分歧不中断，跑完全部轮一次性汇总。
 *
 * 支持两种运行模式：
 *  · JavaScript：浏览器内跑（Web Worker 带超时，file:// 下自动降级为内联执行），
 *    代码约定为一个函数 main(input)，收输入字符串、return 输出字符串。
 *  · C++ / Python / Java：交给服务端真编译器跑（/api/compile + /api/compare），
 *    代码约定为一个完整程序：stdin 读、stdout 写。
 * 随机数据的生成始终在浏览器里做（输入格式 + 范围），与语言无关。
 *
 * 界面语言（中文 / English）：动态文案统一走 T()，
 *  英文译文来自 js/i18n-dict.js 的 window.OJJudgeI18N_DICT；
 *  切换语言时由 i18n.js 派发 oj:langchange，本文件重绘动态区域。
 * ============================================================ */
(function () {
  "use strict";

  /* ---------- 界面语言工具 ---------- */
  function uiLang() {
    return (window.OJJudgeI18n && window.OJJudgeI18n.get()) === "en" ? "en" : "zh";
  }
  // 翻译一段中文界面文案；找不到译文时原样返回
  function T(zh) {
    if (!zh) return zh;
    if (uiLang() === "zh") return zh;
    if (window.OJJudgeI18n && window.OJJudgeI18n.translate) {
      return window.OJJudgeI18n.translate(zh);
    }
    return zh;
  }

  /* ---------- 语言定义 ---------- */
  var LANGS = [
    { id: "js", label: "JavaScript", mode: "client",
      hint: "写一个函数 main(input)：input 是本轮完整输入字符串，return 输出字符串。名字用 main / brute / solve 均可。" },
    { id: "cpp", label: "C++", mode: "server",
      hint: "写一个完整的 C++ 程序：从 stdin 读数据，把结果打到 stdout。评测时会把该组输入喂给 stdin 并比对 stdout。" },
    { id: "python", label: "Python", mode: "server",
      hint: "写一个完整的 Python 程序：用 sys.stdin 读数据，把结果 print 出来（结果会打到 stdout）。" },
    { id: "java", label: "Java", mode: "server",
      hint: "写一个完整的 Java 程序：public class Main，从 System.in 读数据，System.out.println 输出结果。" }
  ];

  function langMeta(id) {
    for (var i = 0; i < LANGS.length; i++) if (LANGS[i].id === id) return LANGS[i];
    return LANGS[0];
  }

  /* ---------- 预设挑战（每个都埋了一个真 bug，且各语言都有对应版本） ----------
   * js/cpp/python/java 四种语言的「主程序（带 bug）」与「暴力 / 标程（正确）」。
   * 同一个 bug 在不同语言里的等价形态：
   *   初值之坑     Kadane 初值设 0，全负数时返回 0
   *   比较方式之坑 按字符串/字典序比较，10 排在 9 前面
   *   精度之坑     乘积超 2^53 后用浮点算，悄悄丢精度
   *   语义之坑     负数取模余数带负号（数学上应为非负）
   *   溢出之坑     乘积塞进 32 位整数，绕回一圈
   *   浮点累加     和超过 2^53，每一步 + 都在丢精度
   */
  var PRESET_DEFS = [
    {
      id: "kadane",
      name: "挑战 1 · 最大子段和",
      bug: "初值之坑",
      desc: "主程序用 Kadane 求最大子段和，但初值设成了 0——全负数时返回 0，而真正的最大子段和是负数。暴力 O(n²) 枚举显然正确。",
      format: "{n}\n{n} 行: {a}",
      ranges: "n=1 8, a=-10 10",
      js: {
        main:
          "function main(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  let best = 0, cur = 0;          // 坑：初值设 0，全负数时会返回 0\n" +
          "  for (const v of a) {\n" +
          "    cur = Math.max(0, cur + v);\n" +
          "    best = Math.max(best, cur);\n" +
          "  }\n" +
          "  return String(best);\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  let best = -Infinity;\n" +
          "  for (let i = 0; i < n; i++) {\n" +
          "    let s = 0;\n" +
          "    for (let j = i; j < n; j++) { s += a[j]; if (s > best) best = s; }\n" +
          "  }\n" +
          "  return String(best);\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<long long> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    long long best = 0, cur = 0;   // 坑：初值设 0，全负数时会返回 0\n" +
          "    for (int i = 0; i < n; i++) { cur = max(0LL, cur + a[i]); best = max(best, cur); }\n" +
          "    cout << best << \"\\n\"; return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\n#include <vector>\n#include <climits>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<long long> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    long long best = LLONG_MIN;\n" +
          "    for (int i = 0; i < n; i++) { long long s = 0; for (int j = i; j < n; j++) { s += a[j]; if (s > best) best = s; } }\n" +
          "    cout << best << \"\\n\"; return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "best = 0; cur = 0        # 坑：初值设 0，全负数时会返回 0\n" +
          "for v in a:\n" +
          "    cur = max(0, cur + v)\n" +
          "    best = max(best, cur)\n" +
          "print(best)\n",
        brute:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "best = None\n" +
          "for i in range(n):\n" +
          "    s = 0\n" +
          "    for j in range(i, n):\n" +
          "        s += a[j]\n" +
          "        best = s if best is None else max(best, s)\n" +
          "print(best)\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    long[] a = new long[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextLong();\n" +
          "    long best = 0, cur = 0;   // 坑：初值设 0，全负数时会返回 0\n" +
          "    for (int i = 0; i < n; i++) { cur = Math.max(0, cur + a[i]); best = Math.max(best, cur); }\n" +
          "    System.out.println(best);\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    long[] a = new long[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextLong();\n" +
          "    long best = Long.MIN_VALUE;\n" +
          "    for (int i = 0; i < n; i++) { long s = 0; for (int j = i; j < n; j++) { s += a[j]; best = Math.max(best, s); } }\n" +
          "    System.out.println(best);\n" +
          "  }\n" +
          "}\n"
      }
    },
    {
      id: "sort",
      name: "挑战 2 · 数组排序",
      bug: "API 误用之坑",
      desc: "主程序按字符串（字典序）比较——10 会排在 9 前面。暴力用数值比较。数据里出现两位数时立刻现形。",
      format: "{n}\n{n} 行: {a}",
      ranges: "n=2 8, a=0 100",
      js: {
        main:
          "function main(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  a.sort();                       // 坑：默认字典序，10 排在 9 前面\n" +
          "  return a.join(\" \");\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  a.sort((x, y) => x - y);        // 正确的数值比较\n" +
          "  return a.join(\" \");\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\n#include <vector>\n#include <algorithm>\n#include <string>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<int> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    // 坑：按字符串比较，10 排在 9 前面\n" +
          "    sort(a.begin(), a.end(), [](int x, int y) { return to_string(x) < to_string(y); });\n" +
          "    for (int i = 0; i < n; i++) cout << a[i] << (i + 1 < n ? \" \" : \"\\n\");\n" +
          "    return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<int> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    sort(a.begin(), a.end());      // 正确的数值比较\n" +
          "    for (int i = 0; i < n; i++) cout << a[i] << (i + 1 < n ? \" \" : \"\\n\");\n" +
          "    return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "a.sort(key=str)                 # 坑：按字符串排，10 排在 9 前面\n" +
          "print(*a)\n",
        brute:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "a.sort()                         # 正确的数值比较\n" +
          "print(*a)\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    Integer[] a = new Integer[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n" +
          "    // 坑：按字符串比较，10 排在 9 前面\n" +
          "    Arrays.sort(a, Comparator.comparing(String::valueOf));\n" +
          "    for (int i = 0; i < n; i++) System.out.print(a[i] + (i + 1 < n ? \" \" : \"\\n\"));\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    Integer[] a = new Integer[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n" +
          "    Arrays.sort(a);               // 正确的数值比较\n" +
          "    for (int i = 0; i < n; i++) System.out.print(a[i] + (i + 1 < n ? \" \" : \"\\n\"));\n" +
          "  }\n" +
          "}\n"
      }
    },
    {
      id: "bigmod",
      name: "挑战 3 · 大数取模",
      bug: "精度之坑",
      desc: "主程序把乘积先转成浮点再取模——a、b 到 1e9 量级时乘积超出双精度精确整数范围（2^53），结果悄悄算错。暴力用整数精确计算。",
      format: "{a} {b} {p}",
      ranges: "a=100000000 1000000000, b=100000000 1000000000, p=2 1000000000",
      js: {
        main:
          "function main(input) {\n" +
          "  const [a, b, p] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String((a * b) % p);     // 坑：a*b 超 2^53，精度丢失\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const [a, b, p] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String((BigInt(a) * BigInt(b)) % BigInt(p)); // BigInt 精确\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    long long a, b, p; cin >> a >> b >> p;\n" +
          "    // 坑：先转 double，乘积超 2^53 后丢精度\n" +
          "    double prod = (double)a * (double)b;\n" +
          "    cout << (long long)(prod % (double)p) << \"\\n\";\n" +
          "    return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    long long a, b, p; cin >> a >> b >> p;\n" +
          "    cout << (a * b) % p << \"\\n\";   // long long 精确\n" +
          "    return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys\n" +
          "a, b, p = map(int, sys.stdin.read().split())\n" +
          "prod = float(a) * float(b)       # 坑：转成 float，超 2^53 丢精度\n" +
          "print(int(prod % p))\n",
        brute:
          "import sys\n" +
          "a, b, p = map(int, sys.stdin.read().split())\n" +
          "print(a * b % p)                 # 整数精确\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    long a = sc.nextLong(), b = sc.nextLong(), p = sc.nextLong();\n" +
          "    // 坑：先转 double，乘积超 2^53 后丢精度\n" +
          "    double prod = (double) a * (double) b;\n" +
          "    System.out.println((long) (prod % p));\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    long a = sc.nextLong(), b = sc.nextLong(), p = sc.nextLong();\n" +
          "    System.out.println((a * b) % p);   // long 精确\n" +
          "  }\n" +
          "}\n"
      }
    },
    {
      id: "mod-neg",
      name: "博物馆 1 · 负数取模",
      bug: "语义之坑",
      desc: "C++ / JS 的 % 余数符号跟着被除数走：-7 % 3 = -1，而数学上余数应是 2。暴力用 ((a%b)+b)%b 归一化成非负余数。只要 a 是负数，几乎必现。",
      format: "{a} {b}",
      ranges: "a=-10 10, b=2 5",
      js: {
        main:
          "function main(input) {\n" +
          "  const [a, b] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String(a % b);            // 坑：-7 % 3 = -1，余数带负号\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const [a, b] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String(((a % b) + b) % b); // 数学上的非负余数\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int a, b; cin >> a >> b;\n" +
          "    cout << a % b << \"\\n\";   // 坑：-7 % 3 = -1，余数带负号\n" +
          "    return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int a, b; cin >> a >> b;\n" +
          "    cout << ((a % b) + b) % b << \"\\n\";   // 数学上的非负余数\n" +
          "    return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys, math\n" +
          "a, b = map(int, sys.stdin.read().split())\n" +
          "print(int(math.fmod(a, b)))       # 坑：fmod 是 C 风格余数，-7 % 3 = -1\n",
        brute:
          "import sys\n" +
          "a, b = map(int, sys.stdin.read().split())\n" +
          "print((a % b) % b)                # 数学上的非负余数\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int a = sc.nextInt(), b = sc.nextInt();\n" +
          "    System.out.println(a % b);   // 坑：-7 % 3 = -1，余数带负号\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int a = sc.nextInt(), b = sc.nextInt();\n" +
          "    System.out.println(((a % b) + b) % b);   // 数学上的非负余数\n" +
          "  }\n" +
          "}\n"
      }
    },
    {
      id: "int-overflow",
      name: "博物馆 2 · 整数溢出",
      bug: "溢出之坑",
      desc: "把乘积塞进 32 位整数，乘积超过约 21 亿（2^31）就绕回一圈变成另一个数。暴力用 64 位（Python 用大整数）直接算。数据在 10 ~ 10^5 时约一半轮次现形。",
      format: "{a} {b}",
      ranges: "a=10 100000, b=10 100000",
      js: {
        main:
          "function main(input) {\n" +
          "  const [a, b] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String((a * b) | 0);      // 坑：按 32 位截断，超 2^31 绕回\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const [a, b] = input.trim().split(/\\s+/).map(Number);\n" +
          "  return String(a * b);            // JS 安全整数范围内精确\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    long long a, b; cin >> a >> b;\n" +
          "    int r = (int)(a * b);           // 坑：按 32 位截断，超 2^31 绕回\n" +
          "    cout << r << \"\\n\";\n" +
          "    return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    long long a, b; cin >> a >> b;\n" +
          "    cout << a * b << \"\\n\";        // long long 精确\n" +
          "    return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys\n" +
          "a, b = map(int, sys.stdin.read().split())\n" +
          "r = (a * b) & 0xFFFFFFFF            # 坑：按 32 位截断\n" +
          "if r >= 0x80000000: r -= 0x100000000\n" +
          "print(r)\n",
        brute:
          "import sys\n" +
          "a, b = map(int, sys.stdin.read().split())\n" +
          "print(a * b)                      # Python 大整数精确\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    long a = sc.nextLong(), b = sc.nextLong();\n" +
          "    int r = (int) (a * b);          // 坑：按 32 位截断，超 2^31 绕回\n" +
          "    System.out.println(r);\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    long a = sc.nextLong(), b = sc.nextLong();\n" +
          "    System.out.println(a * b);      // long 精确\n" +
          "  }\n" +
          "}\n"
      }
    },
    {
      id: "float-sum",
      name: "博物馆 3 · 浮点累加",
      bug: "精度之坑",
      desc: "用浮点 + 把几个 1e15 量级的大数累加，和一旦超过 2^53 ≈ 9×10^15，每一步都在悄悄丢精度。暴力用整数精确求和，一个数都不丢。",
      format: "{n}\n{n} 行: {x}",
      ranges: "n=3 6, x=4000000000000000 9000000000000000",
      js: {
        main:
          "function main(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  let s = 0;\n" +
          "  for (const v of a) s += v;       // 坑：和超过 2^53 后精度丢失\n" +
          "  return String(s);\n" +
          "}",
        brute:
          "function brute(input) {\n" +
          "  const t = input.trim().split(/\\s+/).map(Number);\n" +
          "  const n = t[0], a = t.slice(1, n + 1);\n" +
          "  let s = 0n;\n" +
          "  for (const v of a) s += BigInt(v);\n" +
          "  return String(s);                // BigInt 精确求和\n" +
          "}"
      },
      cpp: {
        main:
          "#include <iostream>\n#include <vector>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<long long> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    double s = 0;                   // 坑：和超过 2^53 后精度丢失\n" +
          "    for (int i = 0; i < n; i++) s += (double)a[i];\n" +
          "    cout << (long long)s << \"\\n\";\n" +
          "    return 0;\n" +
          "}\n",
        brute:
          "#include <iostream>\n#include <vector>\nusing namespace std;\n" +
          "int main() {\n" +
          "    ios::sync_with_stdio(false); cin.tie(0);\n" +
          "    int n; if (!(cin >> n)) return 0;\n" +
          "    vector<long long> a(n);\n" +
          "    for (int i = 0; i < n; i++) cin >> a[i];\n" +
          "    long long s = 0;                // 整数精确求和\n" +
          "    for (int i = 0; i < n; i++) s += a[i];\n" +
          "    cout << s << \"\\n\";\n" +
          "    return 0;\n" +
          "}\n"
      },
      python: {
        main:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "s = 0.0                           # 坑：和超过 2^53 后精度丢失\n" +
          "for v in a: s += v\n" +
          "print(int(s))\n",
        brute:
          "import sys\n" +
          "t = list(map(int, sys.stdin.read().split()))\n" +
          "n = t[0]; a = t[1:n+1]\n" +
          "s = 0                             # 整数精确求和\n" +
          "for v in a: s += v\n" +
          "print(s)\n"
      },
      java: {
        main:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    long[] a = new long[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextLong();\n" +
          "    double s = 0;                   // 坑：和超过 2^53 后精度丢失\n" +
          "    for (int i = 0; i < n; i++) s += (double) a[i];\n" +
          "    System.out.println((long) s);\n" +
          "  }\n" +
          "}\n",
        brute:
          "import java.util.*;\n" +
          "public class Main {\n" +
          "  public static void main(String[] args) {\n" +
          "    Scanner sc = new Scanner(System.in);\n" +
          "    int n = sc.nextInt();\n" +
          "    long[] a = new long[n];\n" +
          "    for (int i = 0; i < n; i++) a[i] = sc.nextLong();\n" +
          "    long s = 0;                    // 整数精确求和\n" +
          "    for (int i = 0; i < n; i++) s += a[i];\n" +
          "    System.out.println(s);\n" +
          "  }\n" +
          "}\n"
      }
    }
  ];

  /* 把各语言的代码挂到 preset 上（main / brute 兼容旧字段 = JavaScript 版） */
  var presets = PRESET_DEFS.map(function (p) {
    return {
      id: p.id, name: p.name, bug: p.bug, desc: p.desc,
      format: p.format, ranges: p.ranges,
      main: p.js.main, brute: p.js.brute,
      code: { js: p.js, cpp: p.cpp, python: p.python, java: p.java }
    };
  });

  function presetById(id) {
    for (var i = 0; i < presets.length; i++) if (presets[i].id === id) return presets[i];
    return null;
  }

  function presetCode(p, lang) {
    if (!p) return { main: "", brute: "" };
    var c = p.code && p.code[lang];
    if (c) return c;
    if (lang === "js") return { main: p.main, brute: p.brute };
    return { main: "", brute: "" };
  }

  /* ---------- 随机数据生成（与语言无关） ---------- */
  function parseRanges(text) {
    var ranges = {};
    if (!text) return ranges;
    String(text).split(/[,，;；]/).forEach(function (part) {
      part = part.trim();
      if (!part) return;
      var m = part.match(/^([A-Za-z_]\w*)\s*=\s*(.+)$/);
      if (!m) return;
      var nums = m[2].trim().split(/\s+/).map(Number).filter(function (n) { return !isNaN(n); });
      if (nums.length >= 2) ranges[m[1]] = [Math.min(nums[0], nums[1]), Math.max(nums[0], nums[1])];
      else if (nums.length === 1) ranges[m[1]] = [nums[0], nums[0]];
    });
    return ranges;
  }

  function randInt(lo, hi) { return lo + Math.floor(Math.random() * (hi - lo + 1)); }

  function genInput(format, ranges) {
    var bound = {};   // 同一输入内，独立出现的变量只生成一次并保持稳定
    function draw(v) {
      var r = ranges[v] || [1, 1000];
      return randInt(r[0], r[1]);
    }
    function boundVal(v) {
      if (!(v in bound)) bound[v] = draw(v);
      return bound[v];
    }
    var out = [];
    String(format).split(/\r?\n/).forEach(function (line) {
      var t = line.trim();
      if (!t) return;
      var rep = t.match(/^\{(\w+)\}\s*行[:：]?\s*(.*)$/);
      if (rep) {
        var n = boundVal(rep[1]);       // 重复次数取该变量的绑定值
        var rest = rep[2];
        for (var i = 0; i < n; i++) {
          out.push(rest.replace(/\{(\w+)\}/g, function (_, v) { return draw(v); })); // 每行重新随机
        }
      } else {
        out.push(t.replace(/\{(\w+)\}/g, function (_, v) { return boundVal(v); }));
      }
    });
    return out.join("\n") + "\n";
  }

  /* ---------- JavaScript 程序执行（浏览器内） ---------- */
  function compileProgram(code) {
    var f = new Function(code + "\n;return (typeof main==='function')?main:(typeof brute==='function')?brute:(typeof solve==='function')?solve:null;");
    var fn = f();
    if (typeof fn !== "function") throw new Error(T("找不到函数：请定义 main / brute / solve 之一"));
    return fn;
  }

  function runInline(code, input) {
    try {
      var out = compileProgram(code)(input);
      return { ok: true, out: out == null ? "" : String(out) };
    } catch (err) {
      return { ok: false, err: String((err && err.message) || err) };
    }
  }

  /* Worker 执行：带超时，死循环可判 TLE 而不卡死页面。
   * file:// 等环境下 Worker 可能静默失效——先用探针测试，
   * 失败则永久切回内联执行（无超时保护但保证可用）。 */
  var WORKER_SRC =
    "onmessage=function(e){var d=e.data;try{" +
    "var f=new Function(d.code+\";return (typeof main==='function')?main:(typeof brute==='function')?brute:(typeof solve==='function')?solve:null;\")();" +
    "var r=f(d.input);postMessage({id:d.id,ok:true,out:r==null?\"\":String(r)});}" +
    "catch(err){postMessage({id:d.id,ok:false,err:String(err&&err.message||err)});}}";

  var worker = null, workerDead = false, workerChecked = false, idc = 0;
  var workerPending = {};    // id -> resolve，主程序与暴力并行跑时按 id 分发响应

  function getWorker() {
    if (workerDead) return null;
    if (worker) return worker;
    try {
      worker = new Worker(URL.createObjectURL(new Blob([WORKER_SRC], { type: "text/javascript" })));
      /* onmessage 只挂一次：按 id 分发给对应的等待者，
         否则主程序与暴力程序并行发消息时会互相覆盖回调，导致一边永远超时。 */
      worker.onmessage = function (e) {
        var d = (e && e.data) || {};
        var cb = workerPending[d.id];
        if (!cb) return;
        delete workerPending[d.id];
        cb(d);
      };
      worker.onerror = function () {
        /* Worker 整体挂掉：把挂起的全部按内联降级处理 */
        var ids = Object.keys(workerPending);
        for (var i = 0; i < ids.length; i++) {
          var fn = workerPending[ids[i]];
          delete workerPending[ids[i]];
          if (fn) fn({ __fallback: true });
        }
        workerDead = true;
        worker = null;
      };
    } catch (e) { workerDead = true; worker = null; }
    return worker;
  }

  /* 探针：用一段必然成功的代码测试 Worker 是否真的可用 */
  function ensureRunner() {
    return new Promise(function (resolve) {
      if (workerChecked) { resolve(); return; }
      workerChecked = true;
      var w = getWorker();
      if (!w) { resolve(); return; }
      var id = ++idc, done = false;
      var to = setTimeout(function () {
        if (done) return;
        done = true;
        delete workerPending[id];
        try { w.terminate(); } catch (_) {}
        worker = null; workerDead = true;
        resolve();
      }, 800);
      workerPending[id] = function (d) {
        if (done) return;
        done = true; clearTimeout(to);
        if (!(d.ok && d.out === "ok")) { workerDead = true; worker = null; }
        resolve();
      };
      try { w.postMessage({ id: id, code: "function main(input){ return \"ok\"; }", input: "x" }); }
      catch (e) {
        if (done) return;
        done = true; clearTimeout(to);
        delete workerPending[id];
        workerDead = true; worker = null;
        resolve();
      }
    });
  }

  /* 单轮执行：主程序与暴力程序并行跑时，靠 id 分发各自的响应，
     不能用覆盖式的 w.onmessage（会互相吞掉回调，导致一边永远超时）。 */
  function runInWorker(code, input, timeoutMs) {
    return new Promise(function (resolve) {
      var w = getWorker();
      if (!w) { resolve(runInline(code, input)); return; }
      var id = ++idc, done = false;
      var to = setTimeout(function () {
        if (done) return;
        done = true;
        delete workerPending[id];
        /* 只超时本轮，不 terminate Worker——否则会连带杀掉并行的另一轮 */
        resolve({ ok: false, tle: true });
      }, timeoutMs);
      workerPending[id] = function (d) {
        if (done) return;
        done = true; clearTimeout(to);
        if (d && d.__fallback) { resolve(runInline(code, input)); return; }
        resolve(d);
      };
      try {
        w.postMessage({ id: id, code: code, input: input });
      } catch (e) {
        if (done) return;
        done = true; clearTimeout(to);
        delete workerPending[id];
        resolve(runInline(code, input));
      }
    });
  }

  /* ---------- 服务端编译 / 运行（C++ / Python / Java） ---------- */
  var apiBase = (typeof location !== "undefined" && location.origin && location.origin !== "null")
    ? location.origin : "";

  function apiPost(path, payload, timeoutMs) {
    var ctrl = (typeof AbortController !== "undefined") ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, timeoutMs || 30000) : null;
    var opt = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    };
    if (ctrl) opt.signal = ctrl.signal;
    return fetch(apiBase + path, opt).then(function (r) {
      if (timer) clearTimeout(timer);
      return r.json();
    }).catch(function (e) {
      if (timer) clearTimeout(timer);
      var msg = (e && e.name === "AbortError") ? T("请求超时") : (T("网络错误：") + ((e && e.message) || e));
      return { ok: false, error: msg };
    });
  }

  function apiGet(path, timeoutMs) {
    var ctrl = (typeof AbortController !== "undefined") ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, timeoutMs || 10000) : null;
    var opt = ctrl ? { signal: ctrl.signal } : {};
    return fetch(apiBase + path, opt).then(function (r) { return r.json(); })
      .catch(function (e) {
        if (timer) clearTimeout(timer);
        return { ok: false, tools: {} };
      });
  }

  var FILE_NAME = { cpp: "main.cpp", python: "main.py", java: "Main.java" };

  function compileProgramServer(lang, code) {
    return apiPost("/api/compile", {
      language: lang,
      files: [{ name: FILE_NAME[lang] || "main.txt", content: code }]
    }, 40000);
  }

  function disposeSessions(sessions) {
    (sessions || []).forEach(function (s) {
      apiPost("/api/dispose", { session: s }, 5000);
    });
  }

  /* ============================================================
   * 以下为界面逻辑（Node 环境下跳过）
   * ============================================================ */
  function $(id) { return document.getElementById(id); }

  function init() {
    var fmtEl = $("lab-format"), rangesEl = $("lab-ranges"),
        mainEl = $("lab-main"), bruteEl = $("lab-brute"),
        roundsEl = $("lab-rounds"), toEl = $("lab-timeout"),
        btn = $("lab-start"), logBox = $("lab-log"),
        sumBox = $("lab-summary"), probBox = $("lab-problems"),
        statusEl = $("lab-status"),
        langBox = $("lab-langs"), langHint = $("lab-langhint"),
        mainLabel = $("lab-main-label"), bruteLabel = $("lab-brute-label"),
        langNote = $("lab-langnote");

    var curLang = "js";
    var curPreset = null;
    var serverTools = {};        // 服务端可用工具链
    var envProbed = false;

    var LABELS = {
      js: {
        main: "主程序（JS 函数 main(input)）",
        brute: "暴力 / 标程（JS 函数）"
      },
      cpp: { main: "主程序（完整 C++ 程序）", brute: "暴力 / 标程（C++ 程序）" },
      python: { main: "主程序（完整 Python 程序）", brute: "暴力 / 标程（Python 程序）" },
      java: { main: "主程序（完整 Java 程序）", brute: "暴力 / 标程（Java 程序）" }
    };
    function clearResults() {
      logBox.innerHTML = "";
      sumBox.innerHTML = "";
      probBox.innerHTML = "";
      statusEl.textContent = "";
    }

    function esc(s) {
      return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    /* ---------- 状态栏：存生成函数，切语言时重绘 ---------- */
    var statusFn = null;
    function setStatus(fn) {
      statusFn = fn;
      statusEl.textContent = typeof fn === "function" ? fn() : String(fn);
    }

    /* ---------- 语言切换 ---------- */
    var lastApplied = { main: "", brute: "" };   // 上一次由预设写入的代码，用于判断用户是否手改过

    function applyLangToEditors() {
      var m = langMeta(curLang);
      if (langHint) langHint.textContent = T(m.hint);
      if (mainLabel) mainLabel.textContent = T(LABELS[curLang].main);
      if (bruteLabel) bruteLabel.textContent = T(LABELS[curLang].brute);
      if (curPreset) {
        var code = presetCode(curPreset, curLang);
        /* 只有当编辑器内容仍是"上次预设写入的那份"时才替换，用户手改过就保留 */
        var mainUntouched = mainEl.value === lastApplied.main;
        var bruteUntouched = bruteEl.value === lastApplied.brute;
        if (mainUntouched) mainEl.value = code.main;
        if (bruteUntouched) bruteEl.value = code.brute;
        lastApplied = { main: mainEl.value, brute: bruteEl.value };
      }
      if (langBox) {
        Array.prototype.forEach.call(langBox.querySelectorAll("[data-lang]"), function (b) {
          var id = b.getAttribute("data-lang");
          var meta = langMeta(id);
          b.classList.toggle("on", id === curLang);
          if (meta.mode === "server" && envProbed && !serverTools[id]) {
            b.classList.add("off");
            b.title = T("服务端未安装") + meta.label + T(" 工具链");
          } else {
            b.classList.remove("off");
            b.title = "";
          }
        });
      }
    }

    function switchLang(lang) {
      var meta = langMeta(lang);
      if (meta.mode === "server" && envProbed && !serverTools[lang]) {
        setStatus(function () { return T("服务端暂不可用 ") + meta.label + T(" 工具链，换个语言试试"); });
        return;
      }
      curLang = lang;
      applyLangToEditors();
      setStatus(function () { return T("当前语言：") + meta.label; });
    }

    if (langBox) {
      langBox.addEventListener("click", function (e) {
        var b = e.target.closest ? e.target.closest("[data-lang]") : null;
        if (b) switchLang(b.getAttribute("data-lang"));
      });
    }

    /* 探测服务端工具链：决定哪些语言可用 */
    function probeEnv() {
      if (!apiBase) { envProbed = true; applyLangToEditors(); return Promise.resolve(); }
      return apiGet("/api/env", 8000).then(function (d) {
        envProbed = true;
        serverTools = {};
        var tools = (d && d.tools) || {};
        Object.keys(tools).forEach(function (k) {
          var t = tools[k];
          serverTools[k] = !!(t && (typeof t === "object" ? t.ok : t));
        });
        applyLangToEditors();
        var avail = LANGS.filter(function (l) {
          return l.mode === "client" || serverTools[l.id];
        }).map(function (l) { return l.label; });
        if (langNote) {
          langNote.textContent = T("服务端可用：") + (avail.join(" / ") || T("仅浏览器内 JavaScript"));
        }
      });
    }

    /* ---------- 载入预设 ---------- */
    function loadPreset(p) {
      curPreset = p;
      fmtEl.value = p.format;
      rangesEl.value = p.ranges;
      fmtEl.setAttribute("data-loaded-preset", p.id);
      var code = presetCode(p, curLang);
      mainEl.value = code.main;
      bruteEl.value = code.brute;
      lastApplied = { main: code.main, brute: code.brute };
      if (typeof window !== "undefined") {
        window.__ojCurrentPreset = { id: p.id, name: p.name, bug: p.bug, lang: curLang };
        /* 链接即挑战：把当前挑战写进 URL hash，复制给别人打开自动预载 */
        try { history.replaceState(null, "", "#challenge=" + p.id); } catch (_) {}
      }
      clearResults();
      setStatus(function () { return T("已载入：") + T(p.name); });
    }

    /* 支持 lab.html#challenge=sort 直接预载指定挑战 */
    function presetFromHash() {
      if (typeof location === "undefined") return null;
      var m = String(location.hash || "").match(/challenge=([\w-]+)/);
      if (!m) return null;
      return presetById(m[1]);
    }

    document.querySelectorAll("[data-preset]").forEach(function (b) {
      b.addEventListener("click", function () {
        var p = presetById(b.getAttribute("data-preset"));
        if (p) { loadPreset(p); setStatus(function () { return T("已载入：") + T(p.name); }); }
      });
    });

    /* ---------- 日志与结果渲染 ---------- */
    var logRows = [];      // 保留原始数据，切语言时重绘
    var lastSum = null;     // {r, rounds, consistent, problems}
    var lastProblems = null;

    function logRound(r, st, rm, rb) {
      logRows.push({ r: r, st: st, rm: rm, rb: rb });
      var row = document.createElement("div");
      row.className = "lab-log-row st-" + st;
      var label = T({ OK: "一致", DIFF: "输出不一致", TLE: "超时", RE: "运行异常" }[st]);
      var detail = "";
      if (st === "OK") detail = " (" + esc(String(rm.out).trim().slice(0, 40)) + ")";
      else if (st === "DIFF") detail = T("主[") + esc(String(rm.out).trim().slice(0, 30)) + "] vs " + T("暴力[") + esc(String(rb.out).trim().slice(0, 30)) + "]";
      else if (st === "TLE") detail = T("主") + (rm.tle ? "TLE" : T("正常")) + " / " + T("暴力") + (rb.tle ? "TLE" : T("正常"));
      else if (st === "RE") detail = T("主") + (rm.ok ? T("正常") : T("异常")) + " / " + T("暴力") + (rb.ok ? T("正常") : T("异常"));
      row.innerHTML = '<span class="lab-log-r">' + T("第") + r + T("轮") + '</span><span class="lab-log-st">' + label + "</span><span class=\"lab-log-d\">" + detail + "</span>";
      logBox.appendChild(row);
      logBox.scrollTop = logBox.scrollHeight;
    }

    function updateSummary(r, rounds, consistent, problems) {
      lastSum = { r: r, rounds: rounds, consistent: consistent, problems: problems };
      sumBox.innerHTML =
        '<div class="lab-sum-bar">' + T("已跑 ") + "<b>" + r + "</b> / " + rounds + T(" 轮 · ") + T("一致 ") + "<b class='ok'>" + consistent +
        "</b>" + T(" 轮 · ") + T("发现问题 ") + "<b class='bad'>" + problems + "</b>" + T(" 处") + "</div>";
    }

    function finalSummary(rounds, consistent, problems) {
      lastSum = { final: true, rounds: rounds, consistent: consistent, problems: problems };
      var cls = problems ? "bad" : "ok";
      var text = problems
        ? T("对拍完成：共 ") + rounds + T(" 轮，一致 ") + consistent + T(" 轮，发现 ") + problems + T(" 处问题")
        : T("对拍完成：共 ") + rounds + T(" 轮全部一致，没有发现问题");
      sumBox.innerHTML = '<div class="lab-sum-final ' + cls + '">' + text + "</div>";
    }

    function renderProblems(problems) {
      lastProblems = problems;
      probBox.innerHTML = "";
      if (!problems.length) return;
      var h = document.createElement("h3");
      h.className = "lab-prob-title";
      h.textContent = T("问题明细（") + problems.length + T(" 组不一致 / 异常，点开可看输入与两边输出）");
      probBox.appendChild(h);
      problems.slice(0, 20).forEach(function (p) {
        var d = document.createElement("details");
        d.className = "lab-prob";
        var stLabel = p.m.tle || p.b.tle ? T("超时") : (!p.m.ok || !p.b.ok ? T("运行异常") : T("输出不一致"));
        d.innerHTML =
          "<summary>" + T("第 ") + p.r + T(" 轮 · ") + stLabel + "</summary>" +
          '<div class="lab-prob-body">' +
          '<div class="lab-io"><span class="lab-io-tag in">' + T("输入") + '</span><pre>' + esc(p.input) + "</pre></div>" +
          '<div class="lab-io"><span class="lab-io-tag m">' + T("主程序输出") + '</span><pre>' + esc(p.m.tle ? T("（超时，无输出）") : (p.m.ok ? p.m.out : T("（运行时错误：") + p.m.err + T("）"))) + "</pre></div>" +
          '<div class="lab-io"><span class="lab-io-tag b">' + T("暴力 / 标程输出") + '</span><pre>' + esc(p.b.tle ? T("（超时，无输出）") : (p.b.ok ? p.b.out : T("（运行时错误：") + p.b.err + T("）"))) + "</pre></div>" +
          "</div>";
        probBox.appendChild(d);
      });
    }

    function setRunning(on) {
      btn.disabled = on;
      btn.textContent = on ? T("对拍进行中…") : T("开始对拍");
    }

    function nextFrame() { return new Promise(function (res) { setTimeout(res, 0); }); }

    /* ---------- 浏览器内跑（JavaScript） ---------- */
    function runClientBattle(mainCode, bruteCode, rounds, timeout) {
      return ensureRunner().then(function () {
        var consistent = 0, problems = [];
        var chain = Promise.resolve();
        for (var r = 1; r <= rounds; r++) {
          (function (round) {
            chain = chain.then(function () {
              var input = genInput(fmtEl.value, parseRanges(rangesEl.value));
              return Promise.all([
                runInWorker(mainCode, input, timeout),
                runInWorker(bruteCode, input, timeout)
              ]).then(function (res) {
                var rm = res[0], rb = res[1], st;
                if (rm.tle || rb.tle) st = "TLE";
                else if (!rm.ok || !rb.ok) st = "RE";
                else if (String(rm.out).trim() === String(rb.out).trim()) { st = "OK"; consistent++; }
                else st = "DIFF";
                logRound(round, st, rm, rb);
                if (st === "DIFF" || st === "RE") problems.push({ r: round, input: input, m: rm, b: rb });
                updateSummary(round, rounds, consistent, problems.length);
                return nextFrame();
              });
            });
          })(r);
        }
        return chain.then(function () { return { consistent: consistent, problems: problems }; });
      });
    }

    /* ---------- 服务端跑（C++ / Python / Java） ---------- */
    function runServerBattle(lang, mainCode, bruteCode, rounds, timeout) {
      var consistent = 0, problems = [];
      var sessions = [];
      return compileProgramServer(lang, mainCode).then(function (cm) {
        if (!cm || !cm.ok) throw new Error((cm && cm.error) || T("主程序编译失败"));
        sessions.push(cm.session);
        return compileProgramServer(lang, bruteCode);
      }).then(function (cb) {
        if (!cb || !cb.ok) throw new Error((cb && cb.error) || T("暴力程序编译失败"));
        sessions.push(cb.session);
        var chain = Promise.resolve();
        for (var r = 1; r <= rounds; r++) {
          (function (round) {
            chain = chain.then(function () {
              var input = genInput(fmtEl.value, parseRanges(rangesEl.value));
              return apiPost("/api/compare", {
                a: sessions[0], b: sessions[1], stdin: input,
                timeout: timeout / 1000
              }, 2 * timeout + 20000).then(function (d) {
                if (!d || !d.ok) {
                  var rm = { ok: false, err: (d && d.error) || T("运行失败") };
                  logRound(round, "RE", rm, rm);
                  problems.push({ r: round, input: input, m: rm, b: rm });
                  updateSummary(round, rounds, consistent, problems.length);
                  return nextFrame();
                }
                var a = d.a || {}, b = d.b || {};
                var rm = { ok: !a.timedOut, out: a.stdout, err: a.stderr, tle: !!a.timedOut };
                var rb = { ok: !b.timedOut, out: b.stdout, err: b.stderr, tle: !!b.timedOut };
                var st;
                if (rm.tle || rb.tle) st = "TLE";
                else if (a.code !== 0 || b.code !== 0) st = "RE";
                else if (String(rm.out).trim() === String(rb.out).trim()) { st = "OK"; consistent++; }
                else st = "DIFF";
                logRound(round, st, rm, rb);
                if (st === "DIFF" || st === "RE") problems.push({ r: round, input: input, m: rm, b: rb });
                updateSummary(round, rounds, consistent, problems.length);
                return nextFrame();
              });
            });
          })(r);
        }
        return chain.then(function () {
          return { consistent: consistent, problems: problems, sessions: sessions };
        });
      }).catch(function (e) {
        disposeSessions(sessions);
        throw e;
      });
    }

    /* ---------- 开始对拍 ---------- */
    btn.addEventListener("click", function () {
      var meta = langMeta(curLang);
      var mainCode = mainEl.value, bruteCode = bruteEl.value;
      var rounds = parseInt(roundsEl.value, 10) || 100;
      var timeout = parseInt(toEl.value, 10) || 1500;

      if (meta.mode === "client") {
        try { compileProgram(mainCode); } catch (e) { setStatus(function () { return T("主程序有问题：") + e.message; }); return; }
        try { compileProgram(bruteCode); } catch (e) { setStatus(function () { return T("暴力程序有问题：") + e.message; }); return; }
      } else {
        if (!mainCode.trim() || !bruteCode.trim()) {
          setStatus(function () { return T("主程序 / 暴力程序都要填"); });
          return;
        }
      }

      clearResults();
      setRunning(true);
      setStatus(function () { return T("对拍进行中…"); });

      var runner = (meta.mode === "client")
        ? runClientBattle(mainCode, bruteCode, rounds, timeout)
        : runServerBattle(curLang, mainCode, bruteCode, rounds, timeout);

      runner.then(function (res) {
        setRunning(false);
        finalSummary(rounds, res.consistent, res.problems.length);
        renderProblems(res.problems);
        setStatus(function () { return T("完成"); });
        if (res.sessions) disposeSessions(res.sessions);
        if (typeof window !== "undefined") {
          window.__ojLastBattle = { rounds: rounds, consistent: res.consistent, problems: res.problems };
          if (window.OJJudgeShareCard && window.OJJudgeShareCard.onBattleDone) {
            window.OJJudgeShareCard.onBattleDone(window.__ojLastBattle, window.__ojCurrentPreset || null);
          }
        }
      }).catch(function (e) {
        setRunning(false);
        setStatus(function () { return T("出错：") + ((e && e.message) || e); });
        if (typeof window !== "undefined") {
          window.__ojLastBattle = { rounds: 0, consistent: 0, problems: [] };
        }
      });
    });

    /* 复制挑战链接：别人打开自动载入同一挑战 */
    var copyBtn = $("lab-copylink");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        if (typeof location === "undefined") return;
        var cur = (typeof window !== "undefined") ? window.__ojCurrentPreset : null;
        var url = location.href;
        if (!/#challenge=/.test(url)) url += "#challenge=" + ((cur && cur.id) || presets[0].id);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            setStatus(function () { return T("链接已复制，发给同学打开即自动载入这个挑战"); });
          }, function () {
            setStatus(function () { return T("复制失败，请手动复制地址栏链接"); });
          });
        } else {
          setStatus(function () { return T("当前浏览器不支持一键复制，请手动复制地址栏链接"); });
        }
      });
    }

    /* ---------- 界面语言切换：重绘动态区域 ---------- */
    function rerenderDynamic() {
      applyLangToEditors();
      // 状态栏
      if (statusFn) statusEl.textContent = typeof statusFn === "function" ? statusFn() : String(statusFn);
      // 日志
      logBox.innerHTML = "";
      var saved = logRows.slice();
      logRows.length = 0;
      saved.forEach(function (row) { logRound(row.r, row.st, row.rm, row.rb); });
      // 汇总
      if (lastSum) {
        if (lastSum.final) finalSummary(lastSum.rounds, lastSum.consistent, lastSum.problems);
        else updateSummary(lastSum.r, lastSum.rounds, lastSum.consistent, lastSum.problems);
      }
      // 问题明细
      if (lastProblems) renderProblems(lastProblems);
      // 语言提示
      if (envProbed) {
        var avail = LANGS.filter(function (l) {
          return l.mode === "client" || serverTools[l.id];
        }).map(function (l) { return l.label; });
        if (langNote) {
          langNote.textContent = T("服务端可用：") + (avail.join(" / ") || T("仅浏览器内 JavaScript"));
        }
      }
    }
    document.addEventListener("oj:langchange", function () { rerenderDynamic(); });

    /* 默认载入挑战 1，落地即玩；带 #challenge=hash 时按 hash 预载 */
    loadPreset(presetFromHash() || presets[0]);
    applyLangToEditors();
    probeEnv();
  }

  /* ---------- Node 导出（供自动化验证） ---------- */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      presets: presets, parseRanges: parseRanges, genInput: genInput,
      runInline: runInline, compileProgram: compileProgram,
      presetCode: presetCode, presetById: presetById,
      langMeta: langMeta, LANGS: LANGS
    };
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }
})();
