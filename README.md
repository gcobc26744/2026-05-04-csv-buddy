# CSV Buddy：小型 CSV 清理 + 統計工具

我常常拿到一份 CSV，想要「先快速看一下有沒有缺值、欄位名亂不亂、數字大概落在哪」，但又不想打開大型工具或寫一堆一次性的程式。
所以今天做一個很小的 CLI：讀入 CSV → 做幾個常見清理 → 輸出乾淨版 CSV，順便印出一份簡單摘要。

這個專案刻意不使用第三方套件（pandas 之類），只用 Python 標準庫，當作練習 `csv`、`argparse`、以及把「資料清理」拆成可測的小步驟。

## 功能

- 讀入 CSV（支援自動偵測分隔符號：逗號或分號）
- 清理：
  - 去掉欄位名與資料中的前後空白
  - 欄位名標準化（轉小寫、空白改底線、移除奇怪字元）
  - 移除「整列都是空」的資料列
- 輸出：
  - 產生清理後的 CSV（預設寫到 `out/cleaned.csv`）
  - 依欄位印出缺值統計
  - 對「看起來像數字」的欄位（可解析成 float）印出 min/max/avg

## 資料夾結構

```
projects/2026-05-04-csv-buddy/
  src/
    csv_buddy.py
    main.py
  data/
    sample.csv
  docs/
    learning-notes.md
    retrospective.md
  out/
    (執行後產生)
```

## 怎麼跑

需求：Python 3.10+（我用 3.11 測）

1) 跑範例

```bash
cd projects/2026-05-04-csv-buddy
python src/main.py data/sample.csv
```

2) 指定輸出路徑

```bash
python src/main.py data/sample.csv --out out/my_cleaned.csv
```

3) 不輸出 CSV，只看摘要

```bash
python src/main.py data/sample.csv --no-write
```

## 驗證結果（我在本機跑的輸出）

用 `data/sample.csv` 跑 `--no-write` 時會看到：

```text
Input rows (excluding header): 4
Output rows (after dropping empty rows): 4

Missing values by column:
- name: 1
- age: 1
- city: 0
- spend: 1

Numeric column stats (min/max/avg):
- age: min=23.000 max=31.000 avg=27.667
- spend: min=80.000 max=200.000 avg=133.500
```

## 我在做什麼、為什麼這樣切

- 一開始想直接把所有事情塞在 `main.py`，但很快就覺得「清理、偵測分隔符、統計」其實是三種不同概念。
- 所以把核心邏輯放到 `src/csv_buddy.py`，`src/main.py` 只管參數與 I/O。
- 這樣之後如果想加單元測試（或換成讀 stdin / 寫 stdout）也比較好改。

比較細的學習記錄放在 `docs/learning-notes.md`，包含我踩到的一些 `csv` 小坑。

## 下一步想做

- 讓工具可以輸出 JSON 報告（方便丟到其他工具/流程）
- 增加「欄位型別推測」：日期、整數、布林之類
- 支援簡單規則（例如：某欄位不允許空值，違反就 return non-zero exit code）
