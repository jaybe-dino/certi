# 배포 가이드 — Vercel(프론트) + Railway(백엔드)

이 저장소는 모노레포입니다. 프론트엔드(`apps/web`)는 Vercel에, 백엔드(`apps/api`)는
Railway에 배포합니다.

```
┌─────────────┐      HTTPS       ┌──────────────────────┐
│   Vercel    │  ───────────────▶ │       Railway        │
│  apps/web   │   API 호출         │  apps/api + Postgres │
│ (Next.js)   │ ◀─────────────── │     (Docker)         │
└─────────────┘   JSON 응답       └──────────────────────┘
```

---

## 1단계 · 백엔드 → Railway

1. [railway.app](https://railway.app) 로그인 → **New Project** → **Deploy from GitHub repo** → 이 저장소 선택
2. 생성된 서비스 → **Settings**
   - **Root Directory**: `apps/api`  ← 모노레포라 필수
   - Build는 `apps/api/railway.json`/`Dockerfile`로 자동 인식됩니다.
3. **Database 추가**: 프로젝트에서 **New** → **Database** → **Add PostgreSQL**
4. 백엔드 서비스 → **Variables** 에 아래 추가:

   | 변수 | 값 |
   |------|-----|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway 참조 변수) |
   | `SECRET_KEY` | 길고 무작위한 문자열 |
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `false` |
   | `BACKEND_CORS_ORIGINS` | `https://<your-app>.vercel.app` (2단계 후 Vercel 도메인) |

   > `start.sh`가 배포 시 `alembic upgrade head`로 마이그레이션을 자동 적용합니다.
   > `DATABASE_URL`이 `postgresql://`이어도 앱이 asyncpg 드라이버로 자동 정규화합니다.
5. 배포 완료 후 발급된 공개 도메인 확인 (예: `https://certi-api-production.up.railway.app`)
   - 헬스체크: `GET /api/v1/health` → `{"status":"ok",...}`

## 2단계 · 프론트엔드 → Vercel

1. [vercel.com/new](https://vercel.com/new) → 이 저장소 import
2. **Root Directory**: `apps/web`  ← 필수. Framework는 Next.js 자동 감지
3. **Environment Variables**:

   | 변수 | 값 |
   |------|-----|
   | `NEXT_PUBLIC_API_BASE_URL` | 1단계의 Railway 백엔드 URL (끝에 `/` 없이) |

4. **Deploy** → `https://<your-app>.vercel.app` 발급

## 3단계 · CORS 연결 마무리

1. Vercel 도메인이 나오면, Railway 백엔드의 `BACKEND_CORS_ORIGINS` 를 그 도메인으로 갱신
   - 여러 개면 콤마로: `https://app.vercel.app,https://www.도메인.com`
2. Railway가 자동 재배포 → 프론트에서 API 호출 정상 동작

---

## 로컬에서 한 번에 실행 (배포 전 확인)

```bash
# 백엔드 + DB
cp .env.example .env
docker compose up --build        # API: localhost:8000

# 프론트엔드 (다른 터미널)
cd apps/web
cp .env.example .env.local
npm install && npm run dev        # Web: localhost:3000
```

## 참고

- **마감 자동 갱신**: 현재는 조회 시점에 상태를 재계산합니다. 주기적 일괄 갱신이 필요하면
  Railway Cron 또는 별도 워커로 확장할 수 있습니다(향후 FR-08 ESG 폴링과 함께).
- **Redis/큐**: 비동기 제출·알림 도입 시 Railway에 Redis 플러그인을 추가하고
  `REDIS_URL` 환경변수를 연결하세요.
