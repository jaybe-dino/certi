import Link from "next/link";

const FEATURES = [
  { title: "무료 진단", desc: "매출·카테고리·판매형태로 MoCRA 의무/면제를 자동 판정", fr: "FR-01" },
  { title: "시설 등록", desc: "Form 5066 위저드 + SPL 자동 생성", fr: "FR-04" },
  { title: "제품 리스팅", desc: "Form 5067 + INCI 자동 매핑", fr: "FR-05·07" },
  { title: "컴플라이언스 캘린더", desc: "갱신·리스팅·SAE 마감 자동 산출 및 알림", fr: "FR-09" },
];

export default function Home() {
  return (
    <div className="space-y-16">
      <section className="grid items-center gap-8 py-10 md:grid-cols-2">
        <div>
          <span className="inline-block rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            FDA MoCRA 인증 자동화
          </span>
          <h1 className="mt-4 text-4xl font-bold leading-tight text-slate-900">
            화장품 MoCRA 규제,
            <br />
            <span className="text-brand-600">자동으로 끝내세요.</span>
          </h1>
          <p className="mt-4 text-slate-600">
            시설 등록·제품 리스팅·INCI 매핑·마감 관리·전자제출까지 한 곳에서.
            먼저 1분 무료 진단으로 우리 회사의 의무 여부를 확인해 보세요.
          </p>
          <div className="mt-6 flex gap-3">
            <Link
              href="/diagnostics"
              className="rounded-lg bg-brand-600 px-5 py-3 font-medium text-white hover:bg-brand-700"
            >
              무료 진단 시작
            </Link>
            <Link
              href="/login"
              className="rounded-lg border border-slate-300 px-5 py-3 font-medium text-slate-700 hover:bg-slate-100"
            >
              로그인 / 가입
            </Link>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold text-slate-500">진행 현황 (예시)</p>
          <div className="mt-4 space-y-3">
            {[
              ["시설 등록", "완료", "bg-green-100 text-green-700"],
              ["제품 리스팅", "진행 중", "bg-amber-100 text-amber-700"],
              ["연간 갱신", "D-42", "bg-brand-50 text-brand-700"],
            ].map(([label, badge, cls]) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3"
              >
                <span className="text-sm text-slate-700">{label}</span>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
                  {badge}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-slate-900">핵심 기능</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <p className="text-xs font-medium text-brand-600">{f.fr}</p>
              <h3 className="mt-1 font-semibold text-slate-900">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
