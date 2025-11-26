# uv 설치 가이드 (배포용)

## ✅ 해결책: uv cache clean

uv 0.9.7-0.9.12에서 setuptools 80.9.0 호환성 문제가 발생하면:

```bash
# 1. uv 캐시 클리어
uv cache clean

# 2. 패키지 재설치
uv pip install --reinstall-package plotly -r requirements.txt
```

## 배포 환경 설정

### Dockerfile
```dockerfile
FROM python:3.11.9-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Python 의존성
COPY requirements.txt .
RUN uv cache clean && \
    uv pip install --system -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### GitHub Actions / CI
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v1
  with:
    version: "0.9.12"

- name: Install dependencies
  run: |
    uv cache clean
    uv pip install --system -r requirements.txt
```

## 검증

```bash
# 패키지 설치 확인
uv pip list | grep -E "(plotly|pandas|langchain)"

# 워크플로우 테스트
python test_agent_workflow_mock.py
```

## 주의사항

1. **uv cache clean 필수**: 첫 설치 시 반드시 실행
2. **Python 3.11.9 사용**: requirements.txt가 이 버전 기준
3. **wkhtmltopdf 필요**: PDF 생성 기능용

## 현재 상태

- ✅ uv 0.9.12
- ✅ 168개 패키지 설치
- ✅ plotly, pandas 설치 완료
- ✅ 워크플로우 정상 작동
- ✅ PDF 생성 기능 포함
