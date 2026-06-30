# Certi API

MoCRA 인증 자동화 플랫폼의 백엔드 API 서버.

## 디렉터리

```
app/
├── main.py            # FastAPI 앱 엔트리포인트
├── core/
│   ├── config.py      # pydantic-settings 기반 환경설정
│   └── database.py    # async SQLAlchemy 엔진 / 세션 / get_db 의존성
├── models/            # ORM 엔티티 (기획서 §5)
│   ├── base.py        # Base, UUIDMixin, TimestampMixin
│   ├── enums.py       # 상태/타입 enum (기획서 §5.2)
│   ├── organization.py# organization, workspace, user
│   ├── facility.py    # facility, responsible_person, us_agent, product_facility
│   ├── product.py     # product, ingredient
│   ├── submission.py  # submission (SPL/ESG)
│   ├── compliance.py  # compliance_task, adverse_event
│   └── document.py    # document, audit_log
├── schemas/           # Pydantic 입출력 스키마 (기능 추가 시)
└── api/
    ├── router.py      # v1 라우터 집계
    └── routes/        # 엔드포인트 모듈
```

## 마이그레이션 (Alembic)

```bash
# 새 마이그레이션 자동 생성
alembic revision --autogenerate -m "메시지"

# 최신 스키마 적용
alembic upgrade head

# 한 단계 롤백
alembic downgrade -1
```

DB URL은 `app/core/config.py`의 설정에서 주입된다 (`migrations/env.py`).
`POSTGRES_*` 환경변수 또는 `DATABASE_URL`로 지정한다.

## 환경변수

`.env`(루트) 또는 셸 환경에서 로드된다. `../../.env.example` 참고.

## 테스트

```bash
pytest -q          # 스모크 테스트 (DB 불필요)
ruff check app tests
```
