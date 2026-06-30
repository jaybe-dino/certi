# Certi Web (apps/web)

MoCRA 인증 자동화 플랫폼의 고객 포털 프론트엔드.
**Next.js 14 (App Router) + TypeScript + Tailwind CSS**.

## 화면

| 경로 | 화면 | 기획서 |
|------|------|--------|
| `/` | 랜딩 (가치제안·기능·CTA) | SCR-01 |
| `/diagnostics` | 무료 진단 (로그인 불필요) | SCR-02 |
| `/login` | 로그인 / 회원가입 (2FA 지원) | SCR-03 |
| `/dashboard` | 대시보드 (워크스페이스·캘린더·현황) | SCR-05 |

## 로컬 실행

```bash
cd apps/web
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE_URL 확인
npm install
npm run dev                       # http://localhost:3000
```

> 백엔드(API)가 `http://localhost:8000`에서 실행 중이어야 합니다.
> 루트에서 `docker compose up` 으로 API+DB를 먼저 띄우세요.

## 환경변수

| 변수 | 설명 |
|------|------|
| `NEXT_PUBLIC_API_BASE_URL` | 백엔드 API 기본 URL (예: `http://localhost:8000`, 배포 시 백엔드 도메인) |

## Vercel 배포

1. GitHub 저장소를 [vercel.com/new](https://vercel.com/new) 에서 import
2. **Root Directory** 를 `apps/web` 로 지정 (모노레포이므로 필수)
3. Framework Preset 은 자동으로 **Next.js** 감지됨
4. **Environment Variables** 에 `NEXT_PUBLIC_API_BASE_URL` = 배포된 백엔드 URL 추가
5. Deploy

> ⚠️ 프론트엔드만 Vercel에 올리면 백엔드 API가 필요합니다.
> 백엔드는 Railway/Render/Fly.io 등에 별도 배포한 뒤 그 URL을 위 환경변수에 넣으세요.
> 백엔드 CORS(`BACKEND_CORS_ORIGINS`)에 Vercel 도메인을 추가해야 합니다.
