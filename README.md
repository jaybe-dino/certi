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

## 헬스 체크

| 엔드포인트 | 용도 |
|-----------|------|
| `GET /` | 서비스 정보 |
| `GET /api/v1/health` | Liveness (의존성 미접속) |
| `GET /api/v1/health/ready` | Readiness (DB 연결 확인) |

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
