# Group Report — Day 06 Data Lab (Field-to-Release PoC)

> Điền đầy đủ, cụ thể, không viết chung chung. Mọi con số phải lấy từ file do script sinh ra
> (`reports/metrics_*.json`, `reports/table1_baseline_vs_poc.md`) — không gõ tay, không làm tròn mất đơn vị.
> 3–5 trang (hoặc README + report.md tương đương).

## 00 · Header

| Mục | Giá trị |
|---|---|
| Group ID | G07 |
| Hình thức thực hiện | Cá nhân – 01 học viên thực hiện toàn bộ dự án |
| Challenge | T01 · Coverage Planner – Lựa chọn tập clip bao phủ các tình huống giao thông theo trọng số |
| Họ và tên | Hồ Đăng Mạnh |
| Mã học viên | 2A202603092 |
| Số lượng thành viên | 01 |
| Vai trò | Lead/Integrator; Data & Fixtures; Core Algorithm; QA/Metric; Human Review; Report; GitHub Management |
| Công việc thực hiện | Cấu hình dự án, triển khai thuật toán Greedy Coverage Planner, xử lý dữ liệu, xây dựng bài kiểm thử, đánh giá Baseline và PoC, kiểm tra Holdout, ghi nhận Human Review, tổng hợp báo cáo và quản lý GitHub |
| Git URL | https://github.com/manhdepzai123/K5-Day6-L2-HODANGMANH-2A202603092-DataGovernanceAndPrivacy |
| Branch | main |
| Commit đã tạo trên máy | 9a7c7c2 |
| Tag `demo-180m` | Chưa xác nhận |
| Tag `final-24h` | Chưa xác nhận |
| Deadline (giờ Việt Nam) | 12:00, 15/11/2026 |
| Kết quả kiểm thử | Pytest hoàn tất 100%; Preflight: 0 FAIL, 2 WARN |
| Trạng thái quyết định | HOLD – RISK_REVIEW_UNRESOLVED |



## 01 · Problem statement

### 1. Ai bị ảnh hưởng / ai chịu hậu quả khi hệ thống sai?

Hệ thống Coverage Planner hỗ trợ lựa chọn các đoạn video giao thông phục vụ thu thập dữ liệu, kiểm thử và phát triển mô hình trí tuệ nhân tạo trong lĩnh vực thị giác máy tính.

Những đối tượng có thể bị ảnh hưởng khi hệ thống lựa chọn dữ liệu không chính xác gồm:

- Người thu thập dữ liệu: Có thể phải ghi hình bổ sung do hệ thống lựa chọn thiếu các tình huống cần thiết.
- Người phát triển mô hình AI: Có nguy cơ sử dụng bộ dữ liệu thiếu tính đa dạng, dẫn đến khả năng tổng quát hóa kém trong những điều kiện giao thông phức tạp.
- Người kiểm thử và đánh giá chất lượng: Có thể đưa ra nhận định thiếu chính xác nếu các tình huống khó chưa được bao phủ đầy đủ.
- Người tham gia giao thông: Có thể chịu rủi ro gián tiếp nếu một hệ thống AI được triển khai thực tế mà chưa được kiểm chứng đầy đủ trên những tình huống quan trọng.

Trong phạm vi bài thực hành, các rủi ro này được phân tích ở mức giả định. Chưa có bằng chứng đánh giá tác động trực tiếp đến an toàn giao thông.

### 2. Điểm nghẽn cụ thể

Bài toán T01 yêu cầu lựa chọn một tập clip giao thông có khả năng bao phủ tốt các tình huống mục tiêu trong điều kiện ngân sách thu thập bị giới hạn.

Dữ liệu thực hành gồm:

- 120 clip ứng viên.
- 15 ô tình huống mục tiêu với tổng trọng số bằng 48.
- 4 ô tình huống khó cần ưu tiên.
- Ngân sách lựa chọn tối đa K = 30 clip.
- Ngân sách Human Review B = 20 clip.
- Một số metadata có giá trị unknown, cần kiểm tra thủ công.

Phương pháp lựa chọn ngẫu nhiên có thể bỏ sót các tình huống quan trọng, lựa chọn nhiều kịch bản tương tự và làm tăng tổng chi phí.

Giải pháp được triển khai là thuật toán Greedy Weighted Coverage, ưu tiên những clip giúp tăng tổng trọng số tình huống được bao phủ, đồng thời kiểm soát việc trùng ID và hỗ trợ Human Review.

Trong kết quả thực nghiệm K = 30:

- Random Baseline đạt Weighted Coverage proxy = 0.3750.
- Greedy PoC đạt Weighted Coverage proxy = 0.8125.
- Greedy PoC bao phủ 13/15 ô tình huống.
- Greedy PoC bao phủ 4/4 ô tình huống khó theo metadata.
- Tổng chi phí lựa chọn của Greedy PoC là 138.0 phút, so với 232.0 phút của Baseline.

Các chỉ số trên được tính từ metadata, chưa phải kết quả đánh giá chính thức bằng Ground Truth đã xác minh.

### 3. Đầu vào → Đầu ra

Đầu vào:

- `fixtures/t01_coverage/candidates.csv`: Danh sách 120 clip ứng viên và các thuộc tính mô tả.
- `fixtures/t01_coverage/targets.csv`: Danh sách 15 tình huống mục tiêu, trọng số và nhãn tình huống khó.
- `fixtures/t01_coverage/manifest.csv`: Thông tin nguồn gốc và mã SHA-256 phục vụ kiểm tra tính toàn vẹn dữ liệu.
- `configs/lab.yaml`: Cấu hình G07, T01, seed = 42, offline = true và strict_provenance = true.

Quy trình xử lý:

Đọc dữ liệu → Kiểm tra provenance → Tính độ bao phủ có trọng số → Chọn clip bằng Greedy → Xếp hạng ưu tiên → Human Review → Tổng hợp Coverage → Ra quyết định GO / HOLD / REWORK.

Đầu ra:

- `out/poc/pick.csv`: Danh sách 30 clip được chọn, không trùng clip ID.
- `out/poc/coverage.csv`: Kết quả bao phủ các ô tình huống.
- `out/poc/capture_plan.csv`: Kế hoạch thu thập bổ sung những tình huống chưa được bao phủ.
- `out/poc/review_queue.csv`: Danh sách 20 clip cần kiểm duyệt.
- `out/poc/risk_cells_review_queue.csv`: Danh sách 3 ô rủi ro ưu tiên kiểm tra.
- `out/poc/decision.json`: Quyết định cuối cùng và lý do.
- `out/poc/decision_log.csv`: Nhật ký quyết định.
- `out/poc/audit_log.jsonl`: Nhật ký kiểm toán.
- `reports/table1_proxy_only.md`: Bảng so sánh Baseline và PoC dựa trên metadata.
- `reports/g07_t01_proxy_coverage.png`: Biểu đồ so sánh kết quả.

### 4. Tiêu chí GO / HOLD / REWORK

Các tiêu chí được ghi nhận trong hợp đồng đánh giá của bài thực hành. Cần đối chiếu thời điểm chốt `reports/metric_contract.md` để xác nhận chính sách đã được thiết lập trước khi xem kết quả đánh giá.

GO – Có thể đề xuất chấp thuận khi:

- Chọn đúng K = 30 clip hợp lệ, không trùng clip ID.
- Weighted Coverage proxy đạt tối thiểu 0.80 theo ngưỡng đã khai báo.
- Không bỏ sót các ô tình huống khó bắt buộc.
- Hoàn thành yêu cầu Human Review.
- Không còn trường hợp cần chuyển cấp xử lý hoặc thay thế chưa được xác minh.
- Dữ liệu đầu vào có provenance hợp lệ.

HOLD – Tạm dừng chấp thuận khi:

- Còn quyết định Human Review chưa được giải quyết.
- Chưa có đủ bằng chứng xác minh clip hoặc tình huống rủi ro.
- Các thông tin quan trọng còn thiếu hoặc chưa chắc chắn.
- Cần xác minh thêm trước khi đưa ra quyết định cuối cùng.

REWORK – Yêu cầu xử lý lại khi:

- Chọn sai số lượng clip so với ngân sách.
- Xuất hiện clip ID trùng hoặc không hợp lệ.
- Đầu ra không đáp ứng yêu cầu cấu trúc.
- Thuật toán hoặc quy trình xử lý vi phạm điều kiện bắt buộc.
- Dữ liệu provenance không hợp lệ thì phải dừng xử lý và khắc phục trước khi tiếp tục.

Kết quả hiện tại:

- Trạng thái: HOLD.
- Reason code: RISK_REVIEW_UNRESOLVED.
- Người chịu trách nhiệm: Hồ Đăng Mạnh.
- Weighted Coverage proxy: 0.8125.
- Human Review: 20 clip và 3 ô rủi ro đã được ghi nhận, nhưng các trường hợp escalate chưa được xác minh bằng video gốc.

Do đó, chưa đủ điều kiện chuyển quyết định thành GO.

### 5. Giả định cần DPO / Legal / Domain Owner xác nhận

- Bộ dữ liệu hiện tại là dữ liệu synthetic phục vụ thực hành, không đại diện đầy đủ cho tình huống giao thông thực tế.
- Metadata được sử dụng để ước tính độ bao phủ, chưa được xác minh bằng Ground Truth.
- Dữ liệu video thực tế có thể chứa thông tin cá nhân như khuôn mặt, biển số xe hoặc vị trí.
- Cần xác nhận quyền thu thập, sử dụng, chia sẻ và thời hạn lưu trữ dữ liệu thực tế.
- Cần có sự kiểm tra của người có chuyên môn trước khi sử dụng kết quả để hỗ trợ quyết định triển khai hệ thống AI thực tế.
- Kết quả kiểm thử tự động và checklist không đủ để tuyên bố tuân thủ GDPR hoặc pháp luật bảo vệ dữ liệu cá nhân tại Việt Nam.

Người thực hiện chịu trách nhiệm về cấu hình, mã nguồn, đánh giá và báo cáo trong phạm vi bài thực hành. Việc phê duyệt sử dụng dữ liệu thật hoặc triển khai thực tế cần có xác nhận của các bên có thẩm quyền.

## 02 · Data & provenance

### 2.1. Nguồn dữ liệu và phân chia tập dữ liệu

| Split | N | Nguồn / link | License | Synthetic? |
|---|---|---|---|---|
| Dev / Candidate | 120 clip | `fixtures/t01_coverage/candidates.csv` | CC0-1.0 theo thông tin manifest của bộ dữ liệu synthetic | Có |
| Eval / Heldout | 25 clip | `fixtures/t01_coverage/holdout_candidates.csv` | CC0-1.0 theo thông tin manifest của bộ dữ liệu synthetic | Có |
| Target Coverage | 15 ô tình huống | `fixtures/t01_coverage/targets.csv` | CC0-1.0 theo thông tin manifest của bộ dữ liệu synthetic | Có |
| Verified Ground Truth | Chưa được cung cấp | Dữ liệu nhãn xác minh dành cho bộ phận đánh giá | Chưa xác nhận | Chưa xác nhận |

Nguồn dữ liệu gốc của bài thực hành:

https://github.com/VinUni-AI20k/K5-Day6-L2-DataGovernanceAndPrivacy

Repository bài thực hiện cá nhân:

https://github.com/manhdepzai123/K5-Day6-L2-HODANGMANH-2A202603092-DataGovernanceAndPrivacy

Dữ liệu được sử dụng là bộ dữ liệu mô phỏng phục vụ thực hành, không phải video giao thông thực tế.

Bộ dữ liệu gồm 120 clip ứng viên, 25 clip Holdout và 15 ô tình huống mục tiêu. Trong 15 ô có 4 tình huống khó cần được ưu tiên khi lựa chọn.

Tổng trọng số của 15 ô mục tiêu là 48.

### 2.2. Schema & Class Mapping

File `candidates.csv` chứa các trường dữ liệu:

| Trường | Ý nghĩa |
|---|---|
| `clip_id` | Mã định danh duy nhất của clip |
| `route` | Loại tuyến đường |
| `weather` | Điều kiện thời tiết |
| `light` | Điều kiện ánh sáng |
| `object` | Đối tượng giao thông |
| `risk` | Mức độ rủi ro |
| `cost_min` | Chi phí tính theo phút |
| `duration_s` | Thời lượng clip tính bằng giây |

File `targets.csv` chứa:

| Trường | Ý nghĩa |
|---|---|
| `cell_id` | Mã ô tình huống cần bao phủ |
| `route` | Loại tuyến đường mục tiêu |
| `weather` | Điều kiện thời tiết mục tiêu |
| `light` | Điều kiện ánh sáng mục tiêu |
| `object` | Đối tượng mục tiêu |
| `weight` | Trọng số ưu tiên của tình huống |
| `is_hard` | Đánh dấu tình huống khó |

Class Mapping:

- Route: `urban`, `highway`, `alley`.
- Weather: các điều kiện như `clear`, `rain`, `fog`.
- Light: `day`, `dusk`, `night`.
- Object: các loại đối tượng như `car`, `motorbike`, `pedestrian`.
- Risk: các mức độ như `high`, `med`, `low`.

Một số thuộc tính có thể mang giá trị `unknown`, thể hiện metadata chưa đầy đủ hoặc chưa xác định.

Thuật toán Greedy Coverage Planner đối chiếu các thuộc tính `route`, `weather`, `light`, `object` giữa clip ứng viên và ô tình huống mục tiêu.

Những thuộc tính không xác định không được tự động coi là bằng chứng chắc chắn để xác nhận độ bao phủ.

### 2.3. Seed và cách chia dữ liệu

Random Seed: 42.

Cấu hình thực hành:

- Group ID: G07.
- Track: T01.
- Input: `fixtures/t01_coverage`.
- Offline: true.
- Strict Provenance: true.
- Ngân sách lựa chọn tập chính: K = 30.
- Ngân sách Human Review: B = 20.
- Ngân sách lựa chọn Holdout: K = 6.

Tập Dev và Holdout được cung cấp dưới dạng hai file riêng biệt:

- Dev: `candidates.csv` gồm 120 clip.
- Holdout: `holdout_candidates.csv` gồm 25 clip.

Chưa có bằng chứng xác nhận chính xác quy tắc tách dữ liệu ban đầu theo scene, group hoặc segment. Vì vậy, báo cáo không khẳng định đã sử dụng cách chia theo các tiêu chí đó.

Tập Holdout được sử dụng để kiểm tra kết quả trên tập ứng viên riêng, không sử dụng để điều chỉnh lại ngưỡng hoặc thuật toán sau khi đã chốt quy trình đánh giá.

Kết quả kiểm tra Holdout:

- Số clip được chọn: 6.
- Số clip ID khác nhau: 6.
- Số tình huống được bao phủ ước tính: 6/15.
- Phương pháp đánh giá: metadata-proxy.
- Chưa có kết quả xác minh bằng Ground Truth.

### 2.4. Kiểm tra Manifest và SHA-256

Manifest verified (SHA-256): CÓ.

File manifest của bộ T01:

`fixtures/t01_coverage/manifest.csv`

Lệnh kiểm tra đã thực hiện:

`python -m tools.preflight`

Kết quả kiểm tra trên Repository GitHub mới:

- Python: 3.11.9.
- T01: hashes match.
- T02–T14: hashes match.
- Offline guard: OK.
- Preflight: 0 FAIL, 2 WARN.
- Không phát hiện Hugging Face token được Git theo dõi.
- File `.env` không được Git theo dõi.

Hai cảnh báo:

1. `data/real` chưa có. Đây là thư mục dữ liệu thật tùy chọn, không sử dụng trong bài T01 hiện tại.
2. `models_optional` chưa có. Đây là thư mục mô hình bổ sung cho T07/T14, không bắt buộc đối với T01.

Trong quá trình chuyển dự án sang GitHub trên Windows, một số file bị chuyển đổi ký tự xuống dòng LF sang CRLF, dẫn đến sai lệch mã SHA-256.

Người thực hiện đã khôi phục nội dung 1.211 file fixtures từ Git Index, sau đó chạy lại Preflight và Pytest.

Kết quả sau khắc phục: các manifest T01–T14 đều khớp, Pytest hoàn thành 100% và không còn lỗi kiểm thử.

Lệnh kiểm tra riêng theo mẫu yêu cầu:

`python -m tools.verify_manifests`

Lệnh này chưa có kết quả chạy riêng được xác nhận trong hồ sơ hiện tại. Bằng chứng xác minh SHA-256 đang sử dụng là kết quả `tools.preflight`.

### 2.5. Dữ liệu thật và phương pháp xây dựng Ground Truth

Dữ liệu thật đã sử dụng: Không.

Trong lần thực nghiệm này, toàn bộ dữ liệu được sử dụng là synthetic, phục vụ mô phỏng lựa chọn clip và đánh giá độ bao phủ.

Ground Truth chính thức: Chưa được cung cấp hoặc chưa có quyền truy cập trong môi trường thực hành hiện tại.

Do đó:

- Chưa thực hiện đánh giá chính thức dựa trên nhãn video đã được xác minh.
- Không sử dụng dữ liệu Ground Truth ẩn để huấn luyện hoặc điều chỉnh thuật toán.
- Không tự tạo nhãn xác minh để thay thế Ground Truth.
- Không coi kết quả metadata-proxy là kết quả đánh giá chính thức.

Nếu được cung cấp dữ liệu thật, quy trình xây dựng Ground Truth dự kiến gồm:

1. Kiểm tra quyền sử dụng, nguồn gốc, giấy phép và yêu cầu bảo vệ dữ liệu cá nhân.
2. Xây dựng quy tắc gán nhãn thống nhất cho tuyến đường, thời tiết, ánh sáng và đối tượng giao thông.
3. Sử dụng người có chuyên môn kiểm tra và xác minh nhãn từ video gốc.
4. Xử lý các trường hợp nhãn chưa thống nhất và ghi lại lịch sử quyết định.
5. Tạo tập nhãn xác minh riêng, không sử dụng làm đầu vào để tối ưu thuật toán.
6. Đánh giá Weighted Coverage@K trên Ground Truth đã được xác minh.

Kết luận:

Dữ liệu T01 đã vượt qua kiểm tra tính toàn vẹn SHA-256 và đáp ứng yêu cầu chạy offline trong môi trường thực hành.

Tuy nhiên, kết quả hiện tại mới phản ánh độ bao phủ ước tính theo metadata synthetic. Chưa có đủ bằng chứng để kết luận độ bao phủ thực tế theo Ground Truth hoặc mức độ an toàn khi triển khai hệ thống ngoài thực tế.

## 03 · Research & design

### 3.1. Tài liệu tham khảo và lý do chọn kỹ thuật

1. Chvátal (1979) – Greedy Set Cover  
   URL: https://doi.org/10.1287/moor.4.3.233  
   Lý do: Chọn thuật toán Greedy để ưu tiên clip có mức tăng độ bao phủ theo trọng số cao nhất trong ngân sách K = 30.

2. BDD100K – CVPR 2020  
   URL: https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.html  
   Lý do: Tham khảo phương pháp bảo đảm tính đa dạng của dữ liệu giao thông, đặc biệt ở các tình huống khó.

3. Google Data Cards Playbook  
   URL: https://sites.research.google/datacardsplaybook/  
   Lý do: Tham khảo cách quản lý nguồn gốc dữ liệu, kiểm tra chất lượng và lưu bằng chứng đánh giá.

Ngày kiểm tra nguồn: 14/11/2026.

### 3.2. Sơ đồ Data Flow

Input (`candidates.csv`, `targets.csv`, `manifest.csv`) → Kiểm tra SHA-256 → Greedy Weighted Coverage → Chọn 30 clip → Rank/QC → Human Review (20 clip và 3 ô rủi ro) → Quyết định GO/HOLD/REWORK → Xuất báo cáo và Audit Log.

### 3.3. Thành phần Offline

- Môi trường: Windows, Python 3.11.9, VS Code.
- Thuật toán: Greedy Weighted Coverage.
- Cấu hình: `offline=true`, `seed=42`.
- Model/Weights: Không sử dụng mô hình học sâu hoặc trọng số riêng.
- Checksum: SHA-256 xác minh dữ liệu qua manifest.
- License: CC0-1.0 theo manifest dữ liệu synthetic.
- Kiểm tra: Preflight 0 FAIL, 2 WARN.

### 3.4. Trade-offs đã cân nhắc

- Greedy dễ triển khai, chạy nhanh nhưng không bảo đảm nghiệm tối ưu toàn cục.
- Ưu tiên độ bao phủ có thể làm tăng chi phí lựa chọn ở một số trường hợp.
- Metadata giúp xử lý nhanh nhưng có thể sai hoặc thiếu, cần Human Review.
- Hai tình huống C13 và C15 chưa được bao phủ, cần thu thập bổ sung.
- PoC đạt Weighted Coverage proxy 0.8125, cao hơn Baseline 0.3750 tại K = 30.
- Quyết định hiện tại: HOLD vì còn các trường hợp review chưa được xác minh.

## 04 · Baseline vs PoC

- Baseline: Random Selection (`src.examples.random_baseline`), seed = 42, commit `acf1a65`.
- PoC: Greedy Weighted Coverage (`src.pipeline`), seed = 42, commit `9a7c7c2`.
- Điều kiện so sánh: Cùng 120 clip ứng viên, ngân sách K = 30 và seed = 42. Chưa so sánh hai phương pháp trên cùng tập Holdout.

### Bảng 1 · Baseline vs PoC & hard slices

| Metric (unit) | Baseline | PoC | Δ & chú thích |
|---|---:|---:|---|
| Primary: Weighted Coverage@30 (proxy) | 0.3750 | 0.8125 | +0.4375; càng cao càng tốt |
| Hard-slice Coverage (N = 4) | 1/4 | 4/4 | +3 ô hard |
| Review@B (B = 20) | Không áp dụng | 20/20 đã ghi nhận, còn escalate | Chưa xác minh hoàn tất |
| Miss / False Positive | Chưa có GT | Chưa có GT | Chưa thể đánh giá |
| Runtime / 100 items (ms) | 2384.78 | 2031.39 | -353.38 ms; PoC nhanh hơn 14.82% |

CPU: Intel Core i7-11800H @ 2.30 GHz.

Nguồn: `reports/table1_proxy_only.md` và kết quả đo thời gian bằng PowerShell `Measure-Command`.

Kết luận: PoC đạt độ bao phủ 81.25%, cao hơn Baseline 37.50%. Cả 4 tình huống khó được bao phủ theo metadata.

Lưu ý: Runtime được đo trên toàn chương trình và chuẩn hóa từ 120 clip. Các kết quả Coverage là metadata-proxy, chưa phải kết quả chính thức từ `src.compare` và verified Ground Truth.

## 05 · Evaluation protocol

- Primary metric: Weighted Coverage@K = Tổng trọng số các ô được phủ / Tổng trọng số 15 ô mục tiêu (48). Đơn vị đánh giá là ô tình huống. TP: ô được xác nhận bao phủ đúng; FP: ô báo phủ nhưng GT không xác nhận; FN: ô mục tiêu chưa được phủ. Kết quả metadata-proxy hiện tại: 39/48 = 0.8125 (81.25%). Càng cao càng tốt.

- Threshold / Budget: Ngưỡng GO dự kiến ≥ 0.80, không thiếu ô hard và không còn review chưa giải quyết. K = 30 clip, Human Review B = 20, Holdout K = 6, seed = 42. Thời điểm chốt: chưa xác nhận chính xác; cần đối chiếu `reports/metric_contract.md`.

- Độ bất định: Dự kiến Bootstrap 1.000 lần trên 15 ô mục tiêu để ước tính khoảng tin cậy 95%. Chưa thực hiện nên chưa có CI hoặc variance. Do N = 15 nhỏ, cần thận trọng khi diễn giải kết quả.

- Lệnh đánh giá chính thức:

```powershell
python -m src.evaluate --track t01 --pred out/poc/pick.csv --out reports/metrics_poc.json
```

- Trạng thái đánh giá: Chưa có verified Ground Truth nên chưa chạy đánh giá chính thức. Kết quả 0.8125 chỉ là metadata-proxy, không thay thế kết quả từ evaluator.

## 06 · Result slices

| Slice | N | Baseline | PoC | Ghi chú |
|---|---|---|---|---|
| Hard-slice | 4 ô | 1/4 | 4/4 | PoC bao phủ đủ 4 ô khó |
| Non-hard | 11 ô | 6/11 | 9/11 | PoC còn thiếu 2 ô |
| Tổng Coverage | 15 ô | 7/15 | 13/15 | K = 30, đánh giá theo metadata |

### Failure case 1: Thiếu tình huống trong dữ liệu

- C13: `urban/fog/night/pedestrian`, trọng số 5.
- C15: `alley/rain/dusk/pedestrian`, trọng số 4.
- Nguyên nhân: Không có clip ứng viên phù hợp với hai tình huống trên theo metadata.
- Giải pháp: Thu thập bổ sung dữ liệu cho C13 và C15.
- Minh chứng: `out/poc/coverage.csv`, `out/poc/capture_plan.csv`.

### Failure case 2: Metadata không đầy đủ

- `clip_112`: `weather=unknown`, `risk=high`.
- `clip_015`: `object=unknown`, `risk=med`.
- Nguyên nhân: Thiếu thông tin metadata để xác minh chính xác độ bao phủ.
- Giải pháp: Chuyển Human Review với quyết định `escalate`, chờ xác minh bằng video gốc.
- Minh chứng: `out/poc/review_queue_reviewed.csv`.

### Latency / Compute

- Hệ điều hành: Windows.
- CPU: Intel Core i7-11800H @ 2.30 GHz.
- Python: 3.11.9.
- Số clip đầu vào: 120.
- Baseline: 2861.73 ms/lần chạy, tương đương 23.85 ms/item.
- PoC: 2437.67 ms/lần chạy, tương đương 20.31 ms/item.
- PoC nhanh hơn khoảng 14.82% trong lần đo.
- Phương pháp đo: PowerShell `Measure-Command`, bao gồm thời gian khởi động Python.

Lưu ý: Coverage là kết quả metadata-proxy, chưa được xác minh bằng Ground Truth. Runtime được tính từ một lần chạy toàn chương trình của mỗi phương pháp.

## 07 · Human & decision

- Review queue: `out/poc/review_queue.csv`, ngân sách B = 20. Ưu tiên clip có metadata `unknown`, mức rủi ro cao và trọng số bao phủ lớn. Kiểm tra bổ sung 3 ô rủi ro C09, C10, C08.

- Override & Audit log: Người kiểm duyệt có thể chấp thuận, từ chối hoặc chuyển cấp xử lý. Khi thay thế clip phải ghi rõ lý do, bằng chứng và `override_value` hợp lệ. Nhật ký kiểm toán lưu tại `out/poc/audit_log.jsonl`; kết quả review lưu trong `review_queue_reviewed.csv` và `risk_cells_reviewed.csv`.

- Decision policy:
  - GO: Chọn đúng 30 clip không trùng ID, Coverage ≥ 0.80, không thiếu ô hard và hoàn tất kiểm duyệt.
  - HOLD: Còn trường hợp chưa xác minh hoặc cần bổ sung bằng chứng.
  - REWORK: Sai số lượng clip, trùng ID hoặc vi phạm yêu cầu dữ liệu và quy trình.

- Kết quả thực tế:
  - Decision: `HOLD`.
  - Reason code: `RISK_REVIEW_UNRESOLVED`.
  - Owner: Hồ Đăng Mạnh.
  - Weighted Coverage proxy: 0.8125.
  - Human Review: 20/20 clip và 3/3 ô rủi ro đã ghi nhận, đều còn trạng thái `escalate`.

- Kết luận: Chưa tự động release vì thiếu bằng chứng xác minh video gốc. Giữ trạng thái HOLD cho đến khi các vấn đề kiểm duyệt được giải quyết.

## 08 · Reproduce & tests

### Lệnh tái lập kết quả

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe -m src.main --config configs/lab.yaml --output out/poc --run-name poc --offline --seed 42

.\.venv\Scripts\python.exe -m tools.t01_report_proxy

.\.venv\Scripts\python.exe -m tools.preflight

.\.venv\Scripts\python.exe -m pytest -q
```

Lệnh đánh giá chính thức khi có verified Ground Truth:

```powershell
.\.venv\Scripts\python.exe -m src.evaluate --track t01 --pred out/poc/pick.csv --out reports/metrics_poc.json
```

Chưa chạy đánh giá chính thức vì chưa có Ground Truth xác minh.

### Kết quả kiểm thử

- Pytest: Hoàn thành 100%, không có FAILED hoặc ERROR; có các bài kiểm thử passed và skipped.
- Preflight: 0 FAIL, 2 WARN.
- SHA-256: Các manifest T01–T14 đều khớp.
- Offline mode: Hoạt động bình thường.
- Kết quả PoC: Chọn 30 clip không trùng ID, Weighted Coverage proxy = 0.8125.

### Môi trường thực hiện

| Thành phần | Thông tin |
|---|---|
| Người thực hiện | Hồ Đăng Mạnh |
| Máy tính | Laptop cá nhân |
| Hệ điều hành | Windows |
| CPU | Intel Core i7-11800H @ 2.30 GHz |
| Python | 3.11.9 |
| IDE | Visual Studio Code |
| Seed | 42 |
| Git branch | main |
| Git commit SHA (rút gọn) | 9a7c7c2 |
| Git repository | https://github.com/manhdepzai123/K5-Day6-L2-HODANGMANH-2A202603092-DataGovernanceAndPrivacy |

## 09 · Limitations & ethics

- Rủi ro pháp lý / PII / License: Dữ liệu hiện tại là synthetic, license CC0-1.0 theo manifest. Nếu sử dụng video thực tế, cần kiểm tra thông tin cá nhân (khuôn mặt, biển số xe), quyền sử dụng dữ liệu và bảo mật thông tin.

- Điều chưa biết / False alarms / Scale 10×: Chưa có verified Ground Truth nên chưa đánh giá chính xác False Positive và False Negative. Metadata có thể chứa nhãn `unknown`. Khi tăng dữ liệu từ 120 lên 1.200 clip, cần tối ưu thời gian xử lý, bộ nhớ và khả năng kiểm duyệt.

- Tuân thủ pháp luật: Kết quả kiểm tra tự động không chứng minh hệ thống đã tuân thủ GDPR hoặc pháp luật Việt Nam. Việc sử dụng dữ liệu thật cần được DPO, bộ phận pháp lý và người phụ trách chuyên môn xác nhận.

- Kế hoạch cải tiến:
  1. Thu thập bổ sung dữ liệu cho hai tình huống C13 và C15.
  2. Xác minh 20 clip và 3 ô rủi ro đang ở trạng thái `escalate`.
  3. Đánh giá bằng verified Ground Truth khi được cung cấp.
  4. Tối ưu thuật toán Greedy và kiểm thử với tập dữ liệu lớn hơn.
  5. Hoàn thiện nhật ký kiểm toán và quy trình bảo vệ dữ liệu.

Kết luận: PoC hiện đạt Weighted Coverage proxy = 0.8125 nhưng vẫn giữ quyết định HOLD do chưa đủ bằng chứng xác minh.

## 10 · Team contribution

Bài thực hành Day 06 – T01 do Hồ Đăng Mạnh thực hiện cá nhân.

### Bảng 2 · Individual contribution evidence

| Học viên | Git author/email | Module / vai trò | Commit SHA / diff chứng minh | Trình bày? |
|---|---|---|---|---|
| Hồ Đăng Mạnh – 2A202603092 | manh hồ / mho60471@gmail.com | Lead/Integrator; Data & Fixtures; Core Algorithm; QA/Metric; Human Review; Report | `9a7c7c2` – `configs/lab.yaml`, `src/pipeline.py`, `tests/test_t01_g07.py`, `tools/t01_holdout.py`, `tools/t01_report_proxy.py` và báo cáo proxy | Có, cá nhân thực hiện và trình bày |

Ghi chú: Dự án do một học viên thực hiện. Báo cáo `group_report.md` đang được cập nhật; cần commit phiên bản hoàn chỉnh trước khi nộp.

## 11 · References

| URL                                                                                                                                                                                                                                                                                                        | Ngày xem   | Ý nghĩa                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------- |
| [https://github.com/VinUni-AI20k/K5-Day6-L2-DataGovernanceAndPrivacy](https://github.com/VinUni-AI20k/K5-Day6-L2-DataGovernanceAndPrivacy)                                                                                                                                                                 | 14/11/2026 | Nguồn bài thực hành Day 06, dữ liệu synthetic và yêu cầu T01 Coverage Planner.    |
| [https://doi.org/10.1287/moor.4.3.233](https://doi.org/10.1287/moor.4.3.233)                                                                                                                                                                                                                               | 14/11/2026 | Chvátal (1979), cơ sở tham khảo thuật toán Greedy Set Cover để tối ưu độ bao phủ. |
| [https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.html](https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_BDD100K_A_Diverse_Driving_Dataset_for_Heterogeneous_Multitask_Learning_CVPR_2020_paper.html) | 14/11/2026 | BDD100K, tham khảo tính đa dạng của dữ liệu giao thông và các tình huống khó.     |
| [https://sites.research.google/datacardsplaybook/](https://sites.research.google/datacardsplaybook/)                                                                                                                                                                                                       | 14/11/2026 | Hướng dẫn quản trị dữ liệu, minh bạch nguồn gốc và đánh giá giới hạn dữ liệu.     |

Ghi chú: Ngày 14/11/2026 là ngày tổng hợp nguồn khi soạn báo cáo; người thực hiện cần xác nhận ngày thực sự tham khảo.

---

## Bảng 3 · Checklist chốt khi nộp

- [ ] Link GitHub đã có, nhưng chưa cập nhật README, chưa tạo hai tag `demo-180m`, `final-24h` và chưa xác nhận Push thành công.
- [ ] Đã có lệnh chạy PoC và Pytest offline. Lệnh đánh giá chính thức chưa chạy do thiếu verified Ground Truth.
- [ ] Đã có bảng so sánh Baseline/PoC dạng metadata-proxy, hai failure case, Human Review và Decision Log. Cần đưa bằng chứng review vào hồ sơ nộp và bổ sung metrics chính thức khi có GT.
- [ ] Đã xác nhận license CC0-1.0 theo manifest, nguồn dữ liệu synthetic, Dev = 120, Holdout = 25, seed = 42 và môi trường offline. Chưa có số lượng GT/eval chính thức.
- [ ] Hồ Đăng Mạnh thực hiện cá nhân, đã có commit `9a7c7c2` trên máy. Cần cập nhật `reports/team_contributions.csv`, bổ sung commit báo cáo hoàn chỉnh và Push lên GitHub.

### Kết luận

Dự án G07 – T01 đã hoàn thiện phần thuật toán, kiểm thử và đánh giá metadata-proxy. Preflight đạt 0 FAIL, 2 WARN. Quyết định hiện tại là HOLD do Human Review chưa được xác minh.
