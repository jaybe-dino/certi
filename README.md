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
| 시설 등록 | `POST·GET /workspaces/{id}/facilities`, `GET·PATCH /facilities/{id}` | FR-04 |
| SPL/제출 | `GET /facilities/{id}/validate`, `POST /facilities/{id}/generate-spl`, `POST /facilities/{id}/mark-registered` | FR-04 |
| 컴플라이언스 | `POST·GET /workspaces/{id}/compliance-tasks`, `PATCH /compliance-tasks/{id}` | FR-09 |

### 도메인 엔진

- **무료 진단 엔진** (`services/diagnostic_service.py`) — 소규모 면제(매출 < $1M)·
  면제 제외 카테고리 판정 + 의무 체크리스트 (FR-01)
- **검증기** (`services/validation_service.py`) — 필수값·영문·FEI 형식 (§7.3)
- **SPL 생성기** (`services/spl_service.py`) — HL7 v3 Form 5066 (§2.2, §6.1)
- **마감 엔진** (`services/deadline_engine.py`) — 시설 +2년, 리스팅/변경 +120일,
  SAE +15영업일(주말·공휴일 제외), 상태 자동 산출 (§7.1)

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
