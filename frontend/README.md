# VN Bank Advisor - Frontend (Vite + React)

Giao diện dashboard, explorer và admin console cho hệ thống VN Bank Advisor. Repo này chỉ là frontend chạy bằng Vite.

## Yêu cầu môi trường
- Node.js 18+ (khuyến nghị dùng 20 LTS)
- npm 9+ (đi kèm Node)
- Cổng backend mặc định: `http://localhost:8000/api/v1`

## Cài đặt
```bash
cd frontend
npm install
```

## Chạy dev
- Dùng dữ liệu thật từ backend: `npm run dev`
- Dùng dữ liệu mock (không cần backend): `VITE_USE_MOCK=true npm run dev`

## Build production
```bash
cd frontend
npm run build
```
Kết quả nằm trong thư mục `dist/`.

## Cấu hình quan trọng
- Biến môi trường `VITE_USE_MOCK=true` để bật mock data (dashboard, chart).
- Cổng API mặc định hard-code trong `src/services/api.js` (`http://localhost:8000/api/v1`); sửa tại đây nếu backend đổi host/port.

## Cấu trúc chính
- `src/pages/` chứa các trang Dashboard, Explorer, Advisor, Admin.
- `src/components/` chứa layout, chart và UI con.
- `src/services/api.js` định nghĩa các call REST tới backend.

## Kiểm thử nhanh
- Dev: mở `http://localhost:5173`
- Build: `npm run build` (Vite sẽ kiểm tra lỗi biên dịch)

## Ghi chú
- Nếu push code, đừng commit thư mục `dist/` và `node_modules/` (đã được ignore).
