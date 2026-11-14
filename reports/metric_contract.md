# Metric contract – Nhóm G07 – T01 Coverage Planner

**Nhóm:** G07  
**Người chịu trách nhiệm:** Hồ Đăng Mạnh  
**Thử thách:** T01 – Coverage Planner

Bảng dưới đây xác định cách đánh giá, ngân sách lựa chọn và quy tắc ra quyết định trước khi chạy đánh giá.

| Mục | Khai báo của nhóm |
|---|---|
| Track | T01 – Coverage Planner |
| Primary metric (tên đúng như evaluator in ra) | `Weighted Coverage@K` |
| Tăng tốt hay giảm tốt? | `higher` – càng cao càng tốt |
| Đơn vị đánh giá | Coverage cell (ô tình huống mục tiêu); đánh giá trên tập clip được chọn |
| Công thức + numerator / denominator | Tổng trọng số các ô mục tiêu được phủ / tổng trọng số tất cả ô mục tiêu. `Numerator = Σ weight của các ô được phủ`; `Denominator = Σ weight của 15 ô = 48` |
| Cách ghép prediction ↔ GT | Ghép theo `clip_id`. Với mỗi clip, so sánh 4 thuộc tính `route`, `weather`, `light`, `object` từ tag đã kiểm chứng với từng ô mục tiêu. Ký hiệu `*` chấp nhận mọi giá trị. Không dùng IoU. |
| Candidate pool cố định | 120 clip trong `fixtures/t01_coverage/candidates.csv`. Tập holdout riêng gồm 25 clip trong `holdout_candidates.csv`. |
| Review budget B / K | K = 30 clip trên tập chính; K = 6 trên holdout. Dự kiến B = 20 mục trong review queue theo mã khung hiện tại; đồng thời phải có human review cho 3 ô rủi ro. |
| Seed | 42 |
| Threshold policy (chọn trên dev như thế nào) | **Đề xuất để nhóm chốt:** GO nếu dữ liệu hợp lệ, chọn đúng K clip không trùng ID, mức bao phủ ước tính từ metadata đạt ít nhất 80% và không bỏ sót ô hard theo kết quả review. HOLD nếu còn ô rủi ro cần xác minh hoặc quay bổ sung. REWORK nếu dữ liệu đầu vào, nguồn gốc hoặc đầu ra không hợp lệ. Không sử dụng GT ẩn để ra quyết định trong pipeline. |
| Eval split (không dùng để tune) | Tập ứng viên chính dùng để phát triển thuật toán. Holdout 25 clip dành cho kiểm tra sau khi đã chốt phương pháp, không dùng để chỉnh thuật toán hay ngưỡng. |
| Chỉ số lỗi xấu (miss / false alarm / false reject) | Weighted missing coverage = `1 - Weighted Coverage@K`; số ô hard chưa được phủ; số clip trùng kịch bản; chi phí trên mỗi ô được phủ. |
| Slices sẽ báo cáo (≥2) | (1) Ô khó `is_hard=1` và ô thường `is_hard=0`; (2) theo loại tuyến đường `urban`, `highway`, `alley`. |
| Cách báo độ bất định khi N nhỏ (Wilson CI / bootstrap) | Đề xuất Bootstrap 1.000 lần trên 15 ô mục tiêu với seed 42; báo khoảng 95%, kèm tử số, mẫu số và lưu ý số ô mục tiêu nhỏ. Đây là phân tích bổ sung, không phải metric mặc định của evaluator. |
14/11/2026, 17:30 (giờ Việt Nam) – Hồ Đăng Mạnh (Owner, nhóm G07)

## Quy tắc so sánh

Baseline và phương pháp PoC phải dùng cùng tập ứng viên, cùng K và seed 42. Nhóm sẽ báo cáo kết quả ở các ngân sách K = 10, 20 và 30 khi thực hiện phần mở rộng.

Chỉ số chính được tính theo định nghĩa có sẵn trong `src/metrics/tracks.py`, không sửa công thức sau khi biết kết quả đánh giá.

Nếu Baseline bằng 0, ghi rõ **“baseline = 0”** thay vì tính phần trăm cải thiện.

Không sử dụng Ground Truth ẩn trong `src/pipeline.py` và không điều chỉnh tham số theo kết quả holdout.