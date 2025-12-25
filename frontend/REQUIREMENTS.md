YÊU CẦU HỆ THỐNG
----------------

1) Node.js 18 trở lên (khuyến nghị 20 LTS)
2) npm 9 trở lên
3) Backend mặc định chạy tại `http://localhost:8000/api/v1`
4) Cổng dev Vite mặc định: 5173

CÁCH CHẠY
---------

- Cài đặt: `npm install`
- Dev dùng backend thật: `npm run dev`
- Dev dùng mock: `VITE_USE_MOCK=true npm run dev`
- Build production: `npm run build` (tạo thư mục `dist/`)

LƯU Ý PUSH CODE
---------------

- Không commit `node_modules/`, `dist/`, file `.env*`, log build.
- API base URL chỉnh trong `src/services/api.js` nếu backend đổi host/port.
