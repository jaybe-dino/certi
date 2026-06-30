# Certi — MoCRA Compliance Automation Platform

FDA MoCRA(Modernization of Cosmetics Regulation Act) 인증 자동화 플랫폼.
화장품 기업이 시설 등록(Form 5066)·제품 리스팅(Form 5067)·INCI 매핑·
컴플라이언스 마감 관리·FDA ESG NextGen 전자제출을 한 곳에서 처리하도록 한다.

> 기획서: `웹 개발 기획서 (Web Development Specification) Draft v1.0` 기준 개발.

## 모노레포 구조

```
certi/
├── apps/
│   ├── api/            # 백엔드 — FastAPI + SQLAlchemy(async) + PostgreSQL
│   └── web/            # 프론트엔드 — Next.js (예정)
├── docker-compose.yml  # 로컬 인프라: postgres + redis + api
└── .env.example        # 환경변수 템플릿
```

## 기술 스택 (기획서 §10)

| 영역 | 채택 |
|------|------|
| 백엔드 | Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · Alembic |
| DB | PostgreSQL 16 |
| 큐/캐시 | Redis |
| 프론트엔드 | React · Next.js · TypeScript *(예정)* |
| 인증 | JWT + 2FA *(예정)* |

## 빠른 시작

### Docker Compose (권장)

```bash
cp .env.example .env
docker compose up --build
# API:        http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### 로컬 직접 실행 (백엔드)

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# DB 마이그레이션 (PostgreSQL 필요)
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload
```

## 주요 API

전체 명세는 서버 실행 후 `http://localhost:8000/docs` (Swagger UI) 참고.

| 영역 | 엔드포인트 | FR |
|------|-----------|-----|
| 헬스 | `GET /`, `GET /api/v1/health`, `GET /api/v1/health/ready` | - |
| 인증 | `POST /api/v1/auth/register`·`/login`·`/refresh`, `GET /me` | FR-02 |
| 2FA | `POST /api/v1/auth/2fa/enroll`·`/verify`·`/disable` | FR-02 |
| 무료 진단 | `POST /api/v1/diagnostics` *(공개)* | FR-01 |
| 워크스페이스 | `POST·GET /api/v1/workspaces` | FR-14 |
| 온보딩 | `POST·GET /workspaces/{id}/responsible-persons`·`/us-agents`, `PATCH …` | FR-03, FR-12 |
| 시설 등록 | `POST·GET /workspaces/{id}/facilities`, `GET·PATCH /facilities/{id}` | FR-04 |
| 시설 SPL | `GET /facilities/{id}/validate`, `POST /facilities/{id}/generate-spl`·`/mark-registered` | FR-04 |
| 제품 등록 | `POST·GET /workspaces/{id}/products`, `POST /workspaces/{id}/products/bulk` (CSV) | FR-05, FR-06 |
| INCI/성분 | `POST·GET /products/{id}/ingredients`(+`/bulk`), `PATCH /ingredients/{id}` | FR-07 |
| 제품 SPL | `POST /products/{id}/facilities`, `POST /products/{id}/generate-spl` | FR-05 |
| 유해사례 | `POST /adverse-events`, `GET /products/{id}/adverse-events`, `GET …/severity-guide` | FR-10 |
| 컴플라이언스 | `POST·GET /workspaces/{id}/compliance-tasks`, `PATCH /compliance-tasks/{id}` | FR-09 |
| 문서 보관함 | `POST·GET /workspaces/{id}/documents` | FR-11 |
| 감사 로그 | `GET /workspaces/{id}/audit-logs` | FR-17 |

### 도메인 엔진

- **무료 진단 엔진** (`services/diagnostic_service.py`) — 소규모 면제(매출 < $1M)·
  면제 제외 카테고리 판정 + 의무 체크리스트 (FR-01)
- **INCI 매핑 엔진** (`services/inci_service.py`) — 정규화 일치/유사/미발견 →
  신뢰도(high/medium/low) + 검수 플래그 (FR-07, §7.2)
- **검증기** (`services/validation_service.py`) — 필수값·영문·FEI 형식 (§7.3)
- **SPL 생성기** (`services/spl_service.py`) — HL7 v3 Form 5066/5067 (§2.2, §6.1)
- **마감 엔진** (`services/deadline_engine.py`) — 시설 +2년, 리스팅/변경 +120일,
  SAE +15영업일(주말·공휴일 제외), 상태 자동 산출 (§7.1)
- **감사 로그** (`services/audit_service.py`) — append-only, 주요 제출·등록 액션 기록 (§9)

### 구현 현황 (FR)

✅ 완료: FR-01·02·03·04·05·06·07·09·10·11·12·17
⏳ 보류(외부 연동 필요): FR-08 ESG 제출, FR-13 결제 PG, FR-15 알림(문자/메일), FR-16 운영자 콘솔

## 배포 (Vercel + Railway)

프론트엔드는 **Vercel**, 백엔드+PostgreSQL은 **Railway**에 배포합니다.
단계별 가이드는 [`DEPLOYMENT.md`](./DEPLOYMENT.md) 참고.

- 백엔드: `apps/api/Dockerfile` + `railway.json` (배포 시 마이그레이션 자동 적용)
- 프론트: Vercel Root Directory `apps/web`, env `NEXT_PUBLIC_API_BASE_URL`
- `DATABASE_URL`은 `postgresql://`/`postgres://`여도 asyncpg로 자동 정규화
- CORS는 `BACKEND_CORS_ORIGINS`에 콤마구분 또는 JSON 배열로 지정

## 데이터 모델 (기획서 §5)

14개 테이블이 구현되어 있다: `organization`, `workspace`, `user`,
`facility`, `responsible_person`, `us_agent`, `product`, `ingredient`,
`product_facility`(연결), `submission`, `compliance_task`,
`adverse_event`, `document`, `audit_log`.

상태값/타입 enum은 `apps/api/app/models/enums.py` 참고 (기획서 §5.2).

## 개발 로드맵 (기획서 §11)

- **P0 사전** — ✅ 프로젝트 토대 + 데이터 모델 + 마이그레이션 (현재 단계)
- **P1 MVP** — 진단·인증·온보딩·시설/제품 등록·INCI·반자동 제출·캘린더·결제·감사로그
- **P2 확장** — 일괄 업로드·SAE·멤버·운영자 콘솔·ESG 완전 자동화
- **P3 엔터프라이즈** — OEM 멀티테넌트·AS2 대량·외부 API

## 테스트 / 린트

```bash
cd apps/api
pytest          # 스모크 테스트
ruff check .    # 린트
```
