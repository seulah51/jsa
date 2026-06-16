# JSA — 부서별 월별 자금계획 관리

부서별로 월간 자금 집행 계획을 등록·제출·마감 흐름으로 관리하는 Flask 웹 애플리케이션입니다.

## 주요 기능
- 부서/월별 자금계획 등록 (수동 입력 + **엑셀 일괄 업로드**)
- 배포용 엑셀 양식 다운로드 (필수 항목·중요 안내·금액 콤마 서식 포함)
- 등록여부/이월 체크, 잔액 자동 이월, 마감일 관리
- CSV(엑셀) 내보내기, 부서별 메일 알림
- 관리자: 부서 설정, 월 마감/해제

## 기술 스택
- Python / Flask, PostgreSQL (psycopg2)
- gunicorn, Railway 배포 (NIXPACKS)
- openpyxl (엑셀 양식 생성/업로드 파싱)

## 환경변수
| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 (필수) |
| `ADMIN_PASSWORD` | 관리자 비밀번호 |
| `SECRET_KEY` | 세션 암호화 키 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_USE_TLS` / `FROM_EMAIL` | 메일 알림 설정 |
