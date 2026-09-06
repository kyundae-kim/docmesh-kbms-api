# fastapi-template

Keycloak 기반 인증/인가, PostgreSQL 연동, 계층형 의존성 주입 구조를 갖춘 FastAPI 프로젝트 템플릿입니다.  
`uv` 패키지 매니저 환경에서 동작합니다.

## 문서

| 문서 | 설명 |
| --- | --- |
| [docs/prd.md](docs/prd.md) | 주요 기능, 프로젝트 구조, API 엔드포인트, 기술 스택 |
| [docs/config.md](docs/config.md) | 환경 변수, YAML 서비스 설정, 환경 파일 예시 |
| [docs/test.md](docs/test.md) | 단위 테스트·통합 테스트 실행 방법 및 검증 항목 |

## 빠른 시작

```bash
# 의존성 설치
uv sync

# 개발 서버 실행
uv run fastapi dev
```

## Reference

- [uv - fastapi](https://docs.astral.sh/uv/guides/integration/fastapi/)
- [fastapi - deployment](https://fastapi.tiangolo.com/deployment/docker/)

