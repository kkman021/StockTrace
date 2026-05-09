# 主動式 ETF 偵測雷達
## 完整產品規劃文件 (Product Planning Document)

**版本**：v1.0
**文件性質**：產品規劃 + 系統分析 + 技術設計 三合一
**狀態**：SA 封版 / TD 封版 / 可進入實作

---

## 變更紀錄

| 版本 | 變更內容 |
|---|---|
| v1.0 | 整合 SA v1.3 Final、TD v1.0，新增產品目標、問題定義、前沿規劃 |

---

## 目錄

**Part 1 — 產品定義**
1. [問題定義](#1-問題定義)
2. [系統目標](#2-系統目標)
3. [使用情境](#3-使用情境)

**Part 2 — 系統分析（SA）**

4. [系統邊界與核心概念](#4-系統邊界與核心概念)
5. [資料來源規格](#5-資料來源規格)
6. [爬蟲策略規格](#6-爬蟲策略規格)
7. [ETF 名單管理規格](#7-etf-名單管理規格)
8. [分析邏輯規格](#8-分析邏輯規格)
9. [加碼共識評分模型](#9-加碼共識評分模型)
10. [減碼共識評分模型](#10-減碼共識評分模型)
11. [門檻參數設定規格](#11-門檻參數設定規格)
12. [回測模組規格](#12-回測模組規格)
13. [通知模組規格](#13-通知模組規格)
14. [運作時序設計](#14-運作時序設計)
15. [輸出規格](#15-輸出規格)

**Part 3 — 技術設計（TD）**

16. [技術棧總覽](#16-技術棧總覽)
17. [系統架構圖](#17-系統架構圖)
18. [Container 規格](#18-container-規格)
19. [資料庫設計](#19-資料庫設計)
20. [API 設計](#20-api-設計)
21. [Celery 任務設計](#21-celery-任務設計)
22. [爬蟲模組設計](#22-爬蟲模組設計)
23. [前端模組設計](#23-前端模組設計)
24. [設定與環境變數規格](#24-設定與環境變數規格)
25. [目錄結構](#25-目錄結構)

**Part 4 — 前沿規劃**

26. [開發里程碑](#26-開發里程碑)
27. [未來版本 Roadmap](#27-未來版本-roadmap)
28. [技術擴充方向](#28-技術擴充方向)
29. [使用情境延伸](#29-使用情境延伸)
30. [已知限制與邊界條件](#30-已知限制與邊界條件)
31. [決策紀錄（ADR）](#31-決策紀錄adr)

---

# Part 1 — 產品定義

---

## 1. 問題定義

### 1.1 背景

台灣資本市場近年出現越來越多**主動式 ETF**，與傳統指數型 ETF 不同，這類產品背後有真實的基金經理人在做選股決策，且依法規**每日公告持股明細**。

這意味著：

> 每一位基金經理人每天都在「公開投票」——他們今天加碼了什麼、減碼了什麼，全部記錄在公開資料裡。

然而，這些資料散落在各投信官網，格式各異，缺乏彙整。一般投資人即使知道這些資料存在，也沒有工具能快速從中提取有意義的訊號。

### 1.2 核心問題

**問題一：資料碎片化**

14 檔以上的主動式 ETF 分散在元大、國泰、富邦等不同投信官網，沒有統一的查詢入口。投資人若要手動比對，每日需要訪問十幾個網頁，耗時且容易遺漏。

**問題二：單點資訊的侷限性**

看單一 ETF 的持股變動，無法判斷這是個別經理人的特殊判斷，還是市場上普遍存在的共識。一個訊號的可信度，需要多個獨立來源的佐證。

**問題三：被動變動的干擾**

ETF 因申購 / 贖回導致的規模變動，或因配股導致的股數增加，會製造大量「看起來像加碼」的假訊號。沒有正確的數學還原，原始持股數字根本無法直接使用。

**問題四：訊號時效性**

經理人的集體行為有時間價值。若無自動化工具，等人工發現並彙整時，市場可能已經反應。

### 1.3 這個系統不解決的問題

> 本系統**不預測股價**，不提供買賣建議，不保證訊號的獲利性。

系統的本質是**量化統計工具**——它告訴你「有多少位獨立的專業經理人，在同一時間做出相似的決策」，至於這個決策是否正確，仍需使用者自行判斷。

---

## 2. 系統目標

### 2.1 核心命題

> 當多位獨立決策的基金經理人**同步增持**同一標的時，這種「集體投票」行為本身即為有效的市場訊號。訊號強度隨**共識廣度**（參與家數）與**共識深度**（資金規模）的增加而提升。反之，多位經理人同步減持同一標的，則為**風險警示訊號**。

### 2.2 系統目標

| 目標 | 說明 |
|---|---|
| **自動化資料彙整** | 每日自動抓取所有追蹤 ETF 的持股公告，無需人工介入 |
| **排除被動干擾** | 正確還原規模變動與除權息影響，只鎖定真正的主動加減碼行為 |
| **量化共識強度** | 透過廣度分數與深度分數，將「多少人在看好這檔股票」數字化 |
| **連續性追蹤** | 偵測持續性的集體行為，過濾單日雜訊 |
| **風險雙向偵測** | 同時追蹤加碼訊號與減碼警示，提供多空視角 |
| **可驗證性** | 提供回測功能，讓使用者能評估訊號的歷史有效性 |
| **參數可調性** | 所有門檻參數可在 runtime 調整，不需重啟系統 |

### 2.3 成功定義

系統上線後，以下條件達成即視為成功：

| 指標 | 目標 |
|---|---|
| 資料完整率 | 追蹤 ETF 的每日持股資料，成功率 ≥ 95% |
| 報告時效 | 每日 08:30 前完成開盤前共識排行產出 |
| 訊號延遲 | 18:30 資料入庫後，30 分鐘內完成分析與通知推播 |
| 系統穩定性 | 每月非計劃停機時間 < 2 小時 |
| 回測可用性 | 系統運行 3 個月後，回測功能具備統計意義（樣本數 ≥ 60 個交易日）|

---

## 3. 使用情境

### 情境 A：每日開盤前決策輔助

```
08:20  使用者起床,手機收到 Web Notification
       「📡 ETF 雷達｜今日開盤前摘要
        高度共識:2454、2330（共2檔）
        風險警示:2317（共1檔）」

08:25  打開系統,查看 2454 聯發科的詳情
       廣度 71%｜深度 83%｜連續 4 日
       10 檔 ETF 同步加碼

08:28  結合自己的基本面判斷,決定今日是否操作
09:00  開盤
```

### 情境 B：持倉風險監控

```
某日 18:45  收到即時通知
            「⚠️ 風險警示:鴻海（2317）
             減碼廣度 64%｜連續 3 日
             9 檔 ETF 同步減碼,建議檢視持倉」

使用者查看系統,確認減碼趨勢
結合近期新聞,決定是否調整持倉比例
```

### 情境 C：回測驗證門檻設定

```
使用者懷疑 60% 的廣度門檻太低,雜訊太多
進入回測模組,設定:
  廣度門檻:70%
  深度門檻:60%
  連續天數:3 日
  持有天數:10 日
  回測期間:過去 3 個月

產出統計摘要:
  平均報酬率:+3.2%
  勝率:67%

與 60% 門檻的回測結果比較,決定是否調整
```

### 情境 D：新增追蹤 ETF

```
某新主動式 ETF 上市
使用者進入 ETF 名單管理
填入代號、名稱、持股公告網址
系統從下一個 18:30 排程開始納入追蹤
第一日建立基準,第二日起正常計算
```

---

# Part 2 — 系統分析（SA）

---

## 4. 系統邊界與核心概念

### 4.1 系統邊界

- **納入範圍**：台灣掛牌、具每日持股公告義務的主動式 ETF
- **排除範圍**：指數型 ETF（被動追蹤，無主動決策意圖）、債券型 ETF
- **分析標的**：台股上市櫃股票（ETF 持股標的）
- **時間粒度**：日頻（T 日 vs T-1 日持股差異）
- **使用者**：單人工具，無多帳號 / 權限控管需求

### 4.2 「主動加碼」的定義（定義 C 簡化版）

**計算公式（三步驟，順序不可顛倒）：**

```
Step 1: 配股還原後昨日股數 = 昨日股數 × (1 + 配股率)
Step 2: 規模還原後基準股數 = Step1 × (今日ETF規模 / 昨日ETF規模)
Step 3: 主動加減碼股數     = 今日實際股數 - Step2
```

> **加碼判斷**：Step3 > 0
> **減碼判斷**：Step3 < 0

**計算範例：**

| 項目 | 數值 |
|---|---|
| 昨日持股 | 100,000 股 |
| 配股率 | 10%（0.1） |
| ETF 規模比（今/昨） | 1.05 |
| Step1 | 100,000 × 1.1 = 110,000 |
| Step2（基準線） | 110,000 × 1.05 = 115,500 |
| 今日實際股數 | 116,000 |
| **主動加碼股數** | **+500 股** |

### 4.3 「加碼金額」與「加碼強度」

```
加碼金額 = 主動加碼股數 × 當日收盤價
加碼強度 = 主動加碼股數 / 昨日股數（調整後）
```

---

## 5. 資料來源規格

### 5.1 資料可及性限制

> 投信依法規每日收盤後公告一次持股明細（通常 16:00–18:00），**無盤中即時持股資料**。

| 執行時間 | 工作內容 |
|---|---|
| **每日 08:30 前** | 讀取昨日公告，產出開盤前共識報告 |
| **每日 18:30 後** | 抓取今日最新持股公告，更新資料庫 |

### 5.2 主要資料來源

| 資料類型 | 來源 | 免費？ |
|---|---|---|
| ETF 每日持股明細 | 各投信官網 | 是 |
| ETF 持股公告（校驗） | MOPS 公開資訊觀測站 | 是 |
| 個股每日收盤價 / 開盤價 | 證交所 OpenAPI | 是 |
| 除權息資料 | 證交所 OpenAPI | 是 |
| ETF 每日 AUM | 各投信官網（自動爬取） | 是 |

### 5.3 持股公告必要欄位

| 欄位 | 說明 |
|---|---|
| `etf_id` | ETF 代號 |
| `date` | 公告日期 |
| `stock_id` | 持股股票代號 |
| `shares_held` | 持股股數 |
| `weight_pct` | 持股比例（%） |
| `aum` | ETF 當日規模（元） |

---

## 6. 爬蟲策略規格

### 6.1 分層架構

```
Layer 1（預設）：httpx 輕量爬取
    ↓ 驗證失敗
Layer 2（備援）：Playwright CLI 無頭瀏覽器
```

### 6.2 失敗判定條件

```
觸發 fallback 條件（滿足任一）：
  - 持股筆數為 0
  - 關鍵欄位（shares_held）缺失率 > 50%
  - 回應內容含登入頁 / 錯誤頁特徵字串
  - HTTP 狀態碼非 200
```

### 6.3 自動模式升級機制

```
規則：連續 5 次觸發 fallback → crawler_mode 自動升級為 "playwright"
重置：中間只要有一次輕量爬取成功 → fallback_count 歸零
降級：不自動降回，需透過管理介面手動重設
```

### 6.4 AUM 缺值備援（三層）

```
優先：當日爬取值
  ↓ 失敗
第一備援：前一個交易日的 AUM
  ↓ 仍缺
第二備援：管理介面最後一筆手動輸入
  ↓ 完全無資料
標記:「AUM 缺失」,不納入深度分數,仍納入廣度分數
```

---

## 7. ETF 名單管理規格

### 7.1 設計原則

- 單人工具，無帳號 / 權限控管
- **停用 ≠ 刪除**：歷史資料完整保留
- 名單變動下一次排程執行時生效

### 7.2 資料結構

| 欄位 | 型別 | 說明 |
|---|---|---|
| `etf_id` | string | ETF 代號 |
| `etf_name` | string | ETF 名稱 |
| `issuer` | string | 投信公司名稱 |
| `disclosure_url` | string | 持股公告頁面網址 |
| `aum_url` | string \| null | AUM 獨立頁面網址 |
| `aum_source` | enum | `inline` / `separate` |
| `crawler_mode` | enum | `light` / `playwright` |
| `fallback_count` | integer | 連續 fallback 計數（0–5） |
| `is_active` | boolean | 是否啟用追蹤 |
| `added_date` | date | 加入日期 |
| `last_success_date` | date \| null | 最後成功爬取日期 |
| `notes` | string \| null | 備註 |

### 7.3 N 的動態計算規則

```
N = 當日 is_active = true
    AND 當日持股資料爬取成功
    的 ETF 數量
```

---

## 8. 分析邏輯規格

### 8.1 完整計算流程

```
INPUT:
  今日 / 昨日持股公告 × N 檔 ETF
  今日收盤價、除權息公告
  各 ETF 今日 / 昨日 AUM

PROCESS:
  for each ETF:
    1. 查詢今日持股標的是否有除權事件
    2. 執行三步驟主動加減碼計算
    3. 分別記錄加碼標的與減碼標的

AGGREGATE:
  加碼方向 → 計算廣度分數 + 深度分數
  減碼方向 → 計算廣度分數

OUTPUT:
  加碼共識排行表 + 減碼風險警示列表
```

### 8.2 邊界情況處理

| 情況 | 處理方式 |
|---|---|
| 今日新增持股（新建倉） | 標記「新建倉」，視為 100% 主動買入 |
| 今日清倉 | 視為 100% 主動賣出，計入減碼 |
| 除權日 | Step1 先還原配股，再執行 Step2 |
| 減資 | 反向調整，與配股同邏輯 |
| AUM 缺值 | 依三層備援補值 |
| 公告延遲 | 標記「資料待補」，T+1 補算 |

---

## 9. 加碼共識評分模型

### 9.1 雙軌評分

| 指標 | 公式 | 意義 |
|---|---|---|
| **廣度分數** | M / N | 有多少比例的經理人看好 |
| **深度分數** | Σ(加碼金額) / Σ(所有ETF的AUM) | 有多少比例的資金在看好 |

### 9.2 訊號解讀矩陣

| 廣度 | 深度 | 標記 |
|---|---|---|
| ≥ 廣度門檻 | ≥ 深度門檻 | 高度共識 |
| ≥ 廣度門檻 | < 深度門檻 | 廣泛共識 |
| < 廣度門檻 | ≥ 深度門檻 | 深度佈局 |
| < 廣度門檻 | < 深度門檻 | 無標記 |

### 9.3 高度共識判定（AND 關係）

```
廣度分數 ≥ 廣度門檻
AND 深度分數 ≥ 深度門檻
AND 連續加碼天數 ≥ 連續門檻
```

---

## 10. 減碼共識評分模型

### 10.1 設計定位

> 用途是**風險警示**，不作放空依據。只計廣度，不計深度。

### 10.2 評分與判定

```
減碼廣度分數 = R / N

風險警示條件:
  減碼廣度分數 ≥ 減碼廣度門檻
  AND 連續減碼天數 ≥ 減碼連續門檻
```

### 10.3 警示等級

| 條件 | 標記 |
|---|---|
| 廣度 ≥ 門檻 AND 連續 ≥ 門檻 | 風險警示 |
| 廣度 ≥ 門檻 AND 連續 < 門檻 | 觀察中 |

---

## 11. 門檻參數設定規格

### 11.1 加碼共識門檻

| 參數 | 預設值 | 允許範圍 |
|---|---|---|
| `breadth_threshold` | 60% | 10% – 90% |
| `depth_threshold` | 60% | 10% – 90% |
| `consecutive_days` | 3 日 | 1 – 10 日 |
| `sliding_window` | 5 日 | 3 – 20 日 |

### 11.2 減碼共識門檻（獨立設定）

| 參數 | 預設值 | 允許範圍 |
|---|---|---|
| `reduction_breadth_threshold` | 60% | 10% – 90% |
| `reduction_consecutive_days` | 3 日 | 1 – 10 日 |

> 參數調整後歷史訊號紀錄不重算。回測是獨立沙盒，參數完全獨立指定。

---

## 12. 回測模組規格

### 12.1 前提說明

> 系統剛上線時無歷史資料，**建議累積至少 3 個月後再使用回測功能**。

### 12.2 回測參數

| 參數 | 說明 |
|---|---|
| `backtest_start` / `end` | 回測時間範圍 |
| `breadth_threshold` | 獨立設定，與系統目前設定無關 |
| `depth_threshold` | 同上 |
| `consecutive_days` | 同上 |
| `holding_days` | 持有天數（使用者自訂） |
| `target_stocks` | 指定標的（選填，留空則全部） |

### 12.3 買入價規則

```
買入價 = 訊號觸發日（T）次日（T+1）開盤價
```

### 12.4 輸出 A：統計摘要表

每檔標的輸出：觸發次數、平均報酬率、勝率、最大 / 最小報酬率、觸發時平均廣度 / 深度分數。

### 12.5 輸出 B：個別走勢圖

```
X 軸：訊號前 10 日 + 持有天數（以 T=0 為基準對齊）
Y 軸：以 T+1 開盤價為 0%，顯示累計報酬率
線條：每次觸發一條細線（半透明）+ 一條粗平均線（橘色）
標記：T=0 觸發點、持有結束點（垂直虛線）
```

---

## 13. 通知模組規格

### 13.1 架構

```python
class NotificationChannel:
    def send(self, event: NotificationEvent) -> bool: ...

# v1.0 實作
class WebNotificationChannel(NotificationChannel): ...

# 未來擴充
class LineNotificationChannel(NotificationChannel): ...
class TelegramNotificationChannel(NotificationChannel): ...
class EmailNotificationChannel(NotificationChannel): ...
```

### 13.2 推播時機

| 時間點 | 內容 |
|---|---|
| **18:30 後（即時）** | 當日新觸發的加碼訊號 + 減碼風險警示 |
| **08:30（開盤前摘要）** | 昨日所有有效訊號摘要 + 連續加碼排行 Top 5 |

### 13.3 訊號觸發條件完整對照

| 訊號 | 觸發條件 | 通知時機 |
|---|---|---|
| 高度共識 | 廣度 ≥ 門檻 AND 深度 ≥ 門檻 AND 連續 ≥ 門檻 | 即時 + 早盤摘要 |
| 廣泛共識 | 廣度 ≥ 門檻 AND 連續 ≥ 2日 | 早盤摘要 |
| 深度佈局 | 深度 ≥ 門檻 AND 廣度 < 門檻 | 早盤摘要 |
| 風險警示 | 減碼廣度 ≥ 門檻 AND 連續 ≥ 門檻 | 即時 + 早盤摘要 |
| 觀察中 | 減碼廣度 ≥ 門檻 AND 連續 < 門檻 | 早盤摘要 |

---

## 14. 運作時序設計

```
08:30  ── 開盤前摘要推播（daily_summary）
09:00  ── 台股開盤
13:30  ── 台股收盤
16:00  ── 投信開始公告今日持股
18:30  ── 第一次資料擷取 + 分析 + 即時推播
19:30  ── 第二次嘗試（僅補抓未成功的 ETF）
21:00  ── 最終嘗試（仍缺則標記「資料待補」）
T+1日  ── 補算機制:補抓前日缺失資料,不重新推播
```

---

## 15. 輸出規格

### 15.1 每日加碼共識排行表

`stock_id` / `stock_name` / `etf_count` / `breadth_score` / `depth_score` / `total_amount` / `consecutive_days` / `signal_tag`

### 15.2 每日減碼風險警示列表

`stock_id` / `stock_name` / `etf_count` / `reduction_breadth` / `consecutive_days` / `signal_tag`

---

# Part 3 — 技術設計（TD）

---

## 16. 技術棧總覽

| 層級 | 選型 | 用途 |
|---|---|---|
| **部署** | Docker Compose v2 | 多 container 編排 |
| **後端** | FastAPI（Python） | REST API |
| **前端** | Vue 3 | 介面 |
| **資料庫** | PostgreSQL 16 | 持股明細、共識分數、訊號紀錄 |
| **任務佇列** | Celery 5 | 爬蟲、分析、通知非同步執行 |
| **排程** | Celery Beat | 定時觸發任務 |
| **Broker** | Redis 7 | Celery Broker + 結果後端 |
| **爬蟲（輕量）** | httpx | Layer 1 |
| **爬蟲（重量）** | Playwright CLI | Layer 2 |
| **ORM** | SQLAlchemy 2 | 資料庫存取層 |
| **資料處理** | pandas 2 | 持股差異計算 |

---

## 17. 系統架構圖

### 17.1 Container 架構

```
+-----------------------------------------------------------+
|                   Docker Compose Network                  |
|                                                           |
|  +---------+   +---------+   +-------------------------+  |
|  |   web   |   | worker  |   |        crawler          |  |
|  | FastAPI |   | Celery  |-->| FastAPI (internal)      |  |
|  | Vue 3   |   | Worker  |   | Playwright CLI / httpx  |  |
|  +----+----+   +----+----+   +-------------------------+  |
|       |             |                                     |
|  +----v----+   +----v----+   +-------------------------+  |
|  |   db    |   |  redis  |   |          beat           |  |
|  | Postgres|   |  Redis  |   | Celery Beat (scheduler) |  |
|  +---------+   +---------+   +-------------------------+  |
+-----------------------------------------------------------+
```

### 17.2 資料流

```
Celery Beat → 每日 18:30 觸發爬蟲任務
  ↓
Celery Worker → HTTP POST /crawl/{etf_id}
  ↓
Crawler Container → httpx / Playwright 爬取
  ↓
回傳持股資料 JSON → Worker 寫入 PostgreSQL
  ↓
觸發分析任務 → 計算加碼 / 減碼共識分數
  ↓
寫入訊號紀錄 → 通知模組 → Web Notification 推播
```

---

## 18. Container 規格

### 18.1 docker-compose.yml 結構

見 repo 根目錄 `docker-compose.yml`。

### 18.2 各 Container 職責

| Container | 職責 | 對外 Port |
|---|---|---|
| `web` | FastAPI REST API + Vue 3 靜態檔 | `${WEB_PORT}:8000` |
| `worker` | Celery Worker | 無 |
| `beat` | Celery Beat 定時排程 | 無 |
| `crawler` | Playwright + httpx 爬蟲 HTTP API | `crawler:8001`（內部） |
| `db` | PostgreSQL | 內部 5432 |
| `redis` | Celery Broker + 結果後端 | 內部 6379 |

---

## 19. 資料庫設計

### 19.1 Table 總覽

```
etf_list              ETF 追蹤名單
holding_records       每日持股明細
consensus_scores      每日共識分數
signal_records        訊號觸發紀錄
backtest_runs         回測執行紀錄
backtest_results      回測結果明細
system_config         系統參數設定
crawl_logs            爬蟲執行日誌
```

詳細 DDL 參見 `migrations/versions/0001_initial.py`。

---

## 20. API 設計

### 20.1 Web Container（Port 8000）

```
# ETF 名單管理
GET    /api/etf
POST   /api/etf
GET    /api/etf/{etf_id}
PATCH  /api/etf/{etf_id}
POST   /api/etf/{etf_id}/reset-crawler
POST   /api/etf/{etf_id}/aum

# 共識報告
GET    /api/consensus
GET    /api/consensus/reduction
GET    /api/consensus/{date}
GET    /api/consensus/stock/{stock_id}

# 訊號紀錄
GET    /api/signals
GET    /api/signals/stream          # SSE 即時推播

# 門檻參數
GET    /api/config
PATCH  /api/config

# 回測
POST   /api/backtest
GET    /api/backtest
GET    /api/backtest/{run_id}
GET    /api/backtest/{run_id}/summary
GET    /api/backtest/{run_id}/chart/{stock_id}

# 維護用
POST   /api/admin/crawl
POST   /api/admin/crawl/{etf_id}
POST   /api/admin/analyze/{date}
```

### 20.2 Crawler Container（Port 8001，內部）

```
POST   /crawl     執行單一 ETF 爬取
GET    /health    健康檢查
```

---

## 21. Celery 任務設計

### 21.1 任務清單

```python
crawl_single_etf(etf_id, date)      # 爬取單一 ETF，呼叫 crawler API
crawl_all_etfs(date)                # 並行觸發所有 ETF 爬蟲
analyze_consensus(date)             # 計算加碼 + 減碼共識分數
detect_signals(date)                # 比對門檻，寫入訊號紀錄
send_notifications(date, type)      # 推播通知
generate_morning_summary()          # 產出開盤前摘要
run_backtest(run_id)                # 執行回測計算
```

### 21.2 Celery Beat 排程

詳見 `services/worker/celeryconfig.py`。

### 21.3 任務執行鏈

```python
crawl_all_etfs.s(date) | analyze_consensus.s() | detect_signals.s() | send_notifications.s()
```

---

## 22. 爬蟲模組設計

```python
class CrawlerStrategy:
    async def fetch(self, url: str) -> str: ...

class LightCrawler(CrawlerStrategy):
    async def fetch(self, url):
        async with httpx.AsyncClient() as client:
            return (await client.get(url, timeout=30)).text

class PlaywrightCrawler(CrawlerStrategy):
    async def fetch(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page    = await browser.new_page()
            await page.goto(url, wait_until='networkidle')
            content = await page.content()
            await browser.close()
            return content
```

---

## 23. 前端模組設計

### 23.1 頁面結構

```
/                     每日共識儀表板
/reduction            減碼風險警示
/etf                  ETF 名單管理
/config               門檻參數設定
/backtest             回測模組
/backtest/{run_id}    回測結果詳情
```

### 23.2 Web Notification 實作

```javascript
await Notification.requestPermission()

const es = new EventSource('/api/signals/stream')
es.onmessage = (event) => {
  const signal = JSON.parse(event.data)
  new Notification(signal.summary, {
    body: `廣度 ${(signal.breadth_score * 100).toFixed(0)}% | 連續 ${signal.consecutive_days} 日`,
    icon: '/icons/radar.png',
    tag:  signal.stock_id,
  })
}
```

---

## 24. 設定與環境變數規格

```bash
# 資料庫
POSTGRES_DB=etf_radar
POSTGRES_USER=radar
POSTGRES_PASSWORD=your_password_here
DATABASE_URL=postgresql://radar:your_password_here@db:5432/etf_radar

# Redis
REDIS_URL=redis://redis:6379/0

# Web
WEB_PORT=8080

# 門檻預設值（首次啟動寫入 system_config）
DEFAULT_BREADTH_THRESHOLD=0.6
DEFAULT_DEPTH_THRESHOLD=0.6
DEFAULT_CONSECUTIVE_DAYS=3
DEFAULT_SLIDING_WINDOW=5
DEFAULT_REDUCTION_BREADTH_THRESHOLD=0.6
DEFAULT_REDUCTION_CONSECUTIVE_DAYS=3
```

> 所有門檻參數在 runtime 從 `system_config` 動態讀取，**不需重啟 container 即可生效**。

---

## 25. 目錄結構

實際 repo 結構，請見根目錄。骨架已建立完成。

---

# Part 4 — 前沿規劃

---

## 26. 開發里程碑

### Milestone 1：基礎建設（預估 2–3 週）

> 目標：系統可以跑起來，資料可以進來

- [ ] Docker Compose 環境建立（6 個 container）
- [ ] PostgreSQL schema 建立（8 張 table）
- [ ] FastAPI 基礎架構（路由、ORM、設定讀取）
- [ ] 第一隻 ETF 爬蟲 Parser 完成（手動驗證）
- [ ] Celery Worker / Beat 排程驗證

### Milestone 2：核心分析引擎（預估 2–3 週）

> 目標：系統可以產出共識分數

- [ ] 主動加減碼計算邏輯實作
- [ ] 除權息還原邏輯
- [ ] AUM 三層備援機制
- [ ] 廣度 / 深度分數計算
- [ ] 連續性追蹤（滑動窗口）
- [ ] 訊號判定與寫入 signal_records
- [ ] 加碼 + 減碼共識完整流程端對端測試

### Milestone 3：介面與通知（預估 2 週）

> 目標：系統可以用，可以收到通知

- [ ] Vue 3 前端架構建立
- [ ] 每日共識儀表板頁面
- [ ] 減碼風險警示頁面
- [ ] ETF 名單管理頁面
- [ ] 門檻參數設定頁面
- [ ] SSE 即時推播實作
- [ ] Web Notification 整合

### Milestone 4：回測模組（預估 2 週）

> 目標：可以驗證訊號有效性

- [ ] 回測參數輸入介面
- [ ] 回測計算邏輯（含除權息還原）
- [ ] 統計摘要表輸出
- [ ] 個別走勢圖（細線 + 平均線）
- [ ] 回測結果詳情頁面

### Milestone 5：穩定化（預估 1–2 週）

> 目標：系統穩定運行，異常可被發現

- [ ] 所有投信 ETF Parser 完成
- [ ] 爬蟲自動升級機制驗證
- [ ] 補算機制驗證
- [ ] 錯誤處理與日誌完善
- [ ] 資料完整率監控

---

## 27. 未來版本 Roadmap

### v1.1：通知渠道擴充

- LINE Notify / LINE Bot 推播
- Telegram Bot 推播
- 使用者可在設定頁面選擇啟用的渠道

### v1.2：減碼方向回測

- 回測模組擴充支援減碼共識的歷史驗證
- 輸出格式與加碼回測一致

### v1.3：警示強化

- 加碼 + 減碼同時出現在同一標的（訊號衝突）的偵測與提示
- 訊號強度歷史趨勢圖（某標的的廣度分數走勢）

### v2.0：多人協作

- 帳號系統（多使用者）
- 個人化觀察清單
- 各使用者可設定獨立的門檻參數

### v2.1：資料深度擴充

- 納入法人買賣超資料（三大法人）作為輔助訊號
- 與 ETF 共識訊號交叉比對，提升訊號可信度

### v2.2：訊號品質評分

- 系統累積足夠歷史後，自動計算各訊號等級的歷史勝率
- 在儀表板上顯示「歷史勝率 XX%」作為參考

---

## 28. 技術擴充方向

### 28.1 資料庫層

**TimescaleDB 升級**
當持股資料量成長到數百萬筆後，可考慮將 PostgreSQL 升級為 TimescaleDB（時間序列擴充），大幅提升時間範圍查詢效能。

**Redis 快取層**
對高頻讀取的 API（如每日共識排行），加入 Redis 快取，減少資料庫查詢壓力。

### 28.2 爬蟲層

**Parser 自動更新偵測**
當投信官網改版導致 Parser 失效時，系統能自動偵測（連續多日 records_count 異常下降）並發出維護警告，而非靜默失敗。

**平行化爬蟲**
目前 14 檔 ETF 串行爬取，可改為並行（asyncio.gather），將 18:30 爬取窗口從約 15 分鐘壓縮至 2–3 分鐘。

### 28.3 分析層

**規模加權共識分數進化版**
目前深度分數使用「加碼金額 / 總 AUM」，未來可引入「流通股本比例」（加碼股數佔該股票流通股數的比例），更精準反映資金影響力。

**異常偵測**
對廣度分數做時間序列異常偵測，自動識別出「突然從 0% 飆升到 70%」這類異常跳升的訊號，與「緩慢累積」的訊號分開標記。

---

## 29. 使用情境延伸

### 29.1 產業輪動觀察

當系統追蹤的 ETF 數量夠多時，可以統計：

> 「本週加碼共識最集中的是哪幾個產業？」

把共識標的按照產業分類彙整，觀察資金是否在進行產業輪動，協助使用者掌握大方向。

### 29.2 個股深度頁面

針對單一標的，整合：
- 歷史廣度分數走勢圖
- 各 ETF 的持股比例變化
- 累計加碼金額趨勢
- 歷史訊號觸發紀錄

讓使用者能對特定關注標的做深度追蹤。

### 29.3 訊號日曆

以日曆視圖呈現每日的高度共識標的數量，讓使用者能快速識別「市場共識密集的日期」，回顧當時的市場背景。

### 29.4 對比分析

選取兩個不同時間段，比較同一標的的共識分數變化：

> 「2454 在 Q1 的平均廣度是 45%，Q2 升到 68%，說明經理人對聯發科的看法在這段期間明顯轉向。」

---

## 30. 已知限制與邊界條件

| 限制 | 影響 | 處理方式 |
|---|---|---|
| 持股公告每日僅一次 | 無法盤中即時分析 | 接受，採滾動日頻設計 |
| 各投信公告格式不統一 | 爬蟲需個別維護 | 每檔 ETF 獨立 Parser |
| 收盤價 ≠ 實際買入均價 | 加碼金額存在日內誤差 | 接受此近似 |
| 規模還原假設等比例再投入 | 基準線略有偏差 | 接受此簡化假設 |
| 減碼動機無法區分 | 無法判斷是看壞或獲利了結 | 定位為風險警示，不作放空依據 |
| 回測深度 = 系統運行天數 | 剛上線時樣本不足 | 累積 3 個月後才具統計意義 |
| 回測不含交易成本 | 實際報酬略低於理論值 | 標注「理論績效」 |
| Web Notification 需瀏覽器開啟 | 系統未開啟時收不到通知 | v1.1 擴充 LINE / Telegram |
| 共識不等於正確 | 集體決策也可能集體錯誤 | 系統僅量化共識，不預測股價 |

---

## 31. 決策紀錄（ADR）

| # | 問題 | 決策 | 理由 |
|---|---|---|---|
| OI-01 | ETF 名單管理 | 介面手動維護，N = 當日有效資料數 | 單人工具，手動維護成本低 |
| OI-02 | AUM 資料來源 | 自動爬取，預設合併持股爬蟲，三層備援 | 免費、自動，備援確保計算不中斷 |
| OI-03 | 門檻設定與回測 | 參數可調，回測獨立沙盒，買入價採 T+1 開盤 | 貼近真實可操作時間點 |
| OI-04 | 減碼共識 | 只計廣度，用於風險警示，門檻獨立設定 | 減碼動機複雜，深度分數意義不明確 |
| OI-05 | 技術棧 | FastAPI + Vue 3 + PostgreSQL + Celery + Redis | Python 生態一致，非同步友善 |
| OI-06 | 推播通知渠道 | 抽象介面 + Web Notification 第一實作，雙時間點 | 可擴充，Web Notification 零依賴 |
| TD-01 | 部署方式 | Docker Compose，6 個 container | 職責分離，各自獨立重啟 |
| TD-02 | Crawler 溝通方式 | 獨立 container，HTTP API | 清晰、可測試、標準介面 |
| TD-03 | 爬蟲工具 | httpx（Layer 1）+ Playwright（Layer 2），連續5次自動升級 | 平衡效能與可靠性，自我學習 |

---

*文件版本 v1.0 — 產品規劃完整封版。SA + TD 所有決策已歸檔，可進入實作階段。*
