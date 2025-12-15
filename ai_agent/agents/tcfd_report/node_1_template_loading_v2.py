"""
파일명: template_loading_node.py
최종 수정일: 2025-12-15
버전: v01

개요:
    기존 지속가능경영보고서(ESG / TCFD)를 분석하여
    '보고서 템플릿 메타데이터(report_template_profile)'를 생성하는 Node.

    이 Node는 '보고서 내용을 작성하지 않는다'.
    오직 기존 보고서로부터 다음 요소만을 추출한다:
        - 문체(tone)
        - 문서 구조(section structure)
        - 섹션별 서술 방식(section style)
        - KPI 및 시나리오 템플릿
        - TCFD / ESG 공시 구조
        - 재사용 가능한 문단 패턴

    본 Node의 출력은 이후 모든 보고서 생성·검증 단계에서
    공통 참조되는 템플릿 메타데이터로 사용된다.

파이프라인 내 위치:
    - Node 1 (Template Loading)
    - 파이프라인 시작 단계에서 실행됨
    - 이후 모든 Agent / Node가 본 Node의 결과를 참조함

참조하는 하위 Agent / Node:
    - scenario analysis
    - impact analysis
    - strategy section
    - validator
    - composer
    - finalizer

주요 기능:
    1. RAG 기반으로 기존 지속가능경영보고서의 문단 구조 및 공시 스타일 참조 수집
    2. LLM 분석을 통해 재사용 가능한 보고서 템플릿 패턴(JSON) 추출
    3. INIT / REPAIR 두 가지 분석 모드 지원
    4. 고정된 JSON Schema 기준으로 누락 필드 자동 보정
    5. RAG 기반 citation 정보 반환

분석 모드 설명:
    - INIT (분석가모드 1 - 최고 퀄리티):
        * 파이프라인 최초 실행 시 사용
        * 기존 보고서의 형식을 최대한 세분화하여 구조적으로 추출
        * EXHAUSTIVE 수준의 분석: 5-10개 패턴 추출 (기본 분석은 1-3개)
        * 12개 필수 필드 모두 RICH하게 채움 (최소 10개 이상의 reusable_paragraphs 등)
        * 철학: "INIT이 완벽하면 REPAIR는 필요 없다"

    - REPAIR (분석가모드 2 - 예외적 재분석):
        * Validation Agent가 템플릿 문제를 감지했을 때만 실행 (드물게 발생)
        * 기존 템플릿(JSON)을 입력으로 받아 검증 피드백에 따라 전면 재분석 수행
        * INIT보다 더 공격적으로 세분화 (INIT 실패 시 대안적 접근 시도)
        * 이전 템플릿은 참고용으로만 활용, 피드백 중심으로 재설계

설계 원칙:
    - 본 Node는 결과의 적합성을 스스로 판단하지 않는다.
    - INIT / REPAIR 중 어떤 모드로 실행할지는
      검증 단계(validator 또는 상위 제어 로직)에서 결정한다.
    - 본 Node는 주어진 모드와 입력에 따라
      동일한 방식으로 실행되는 순수 실행 노드이다.

변경 이력:
    - v0.1 (2025-12-15):
        * INIT / REPAIR 이중 프롬프트 구조 도입
        * 분석가모드 1 / 분석가모드 2 분리
        * 템플릿 재분석 및 보정 흐름 정의
"""

import json
from typing import Dict, Any, List, Optional
from ...utils.rag_helpers import RAGEngine


class TemplateLoadingNode:
    """
    Node 1: Template Loading

    역할:
        - 기존 지속가능경영보고서를 분석하여
          보고서 '형식 자체'를 구조화된 JSON으로 추출

    실행 모드:
        - mode="init":
            최초 실행 시 사용
        - mode="repair":
            Validation 실패 후 재실행 시 사용

    주의:
        본 클래스는 실행 흐름을 제어하지 않는다.
        어떤 mode로 실행할지는 외부(Validation Agent / Orchestrator)에서 결정한다.
    """

    def __init__(self, llm_client):
        """
        Node 초기화

        Args:
            llm_client:
                invoke / ainvoke 메서드를 지원하는 LLM 클라이언트
        """
        self.llm = llm_client

        # 벤치마크 보고서 기반 RAG 엔진
        self.rag = RAGEngine(source="benchmark")

        # 본 Node가 반드시 반환해야 하는 고정 JSON Schema
        # LLM 응답 실패 시 사용되는 fallback 기본값 포함
        self.required_fields = {
            "tone": {
                "formality": "formal",
                "audience": "stakeholders",
                "voice": "professional"
            },
            "section_structure": {
                "default": {"pages": 1, "priority": "medium"}
            },
            "section_style": {},
            "formatting_rules": {
                "headings": "default style",
                "lists": "bullet points"
            },
            "report_years": [2024],
            "esg_structure": {
                "E": ["Climate Change"],
                "S": ["Human Rights"],
                "G": ["Board Structure"]
            },
            "tcfd_structure": {
                "governance": {},
                "strategy": {},
                "risk_management": {},
                "metrics_targets": {}
            },
            "materiality": {
                "high": {"issues": [], "threshold": "unknown"}
            },
            "benchmark_KPIs": {},
            "scenario_templates": {},
            "hazard_template_blocks": {},
            "reusable_paragraphs": [
                "템플릿 생성 실패: LLM 응답을 파싱할 수 없습니다."
            ]
        }

    async def execute(
        self,
        company_name: str,
        past_reports: List[str],
        mode: str = "init",
        previous_template: Optional[Dict[str, Any]] = None,
        validation_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Node 실행 진입점

        Args:
            company_name:
                분석 대상 회사명
            past_reports:
                기존 지속가능경영보고서 원문 텍스트 리스트
            mode:
                "init" 또는 "repair"
            previous_template:
                repair 모드일 경우 이전 템플릿 JSON
            validation_feedback:
                Validation Agent가 반환한 수정 요구 사항

        Returns:
            {
                "report_template_profile": 정규화된 템플릿 JSON,
                "style_references": RAG 기반 참조 문단,
                "citations": 참조 출처 정보
            }
        """

        # 1. RAG 기반 스타일/구조 참조 수집
        style_references = await self._load_rag_references(company_name)
        citations = self.rag.get_citations(style_references)

        # 2. 실행 모드에 따른 프롬프트 생성
        prompt = self._build_prompt(
            company_name=company_name,
            past_reports=past_reports,
            rag_docs=style_references,
            mode=mode,
            previous_template=previous_template,
            validation_feedback=validation_feedback
        )

        # 3. LLM 실행
        raw_response = await self.llm.ainvoke(prompt)

        # 4. JSON 정규화 및 누락 필드 보정
        template_profile = self._sanitize_response(raw_response)

        # 5. Node 결과 반환
        return {
            "report_template_profile": template_profile,
            "style_references": style_references,
            "citations": citations
        }

    async def _load_rag_references(self, company_name: str) -> List[Dict[str, Any]]:
        """
        RAG 엔진을 사용하여 다음 항목에 대한 참조 문단 수집:
            - 보고서 문단 구조
            - TCFD 공시 방식
            - ESG KPI 서술 스타일
        """
        query_text = f"""
        {company_name} 지속가능경영보고서 문단 구조,
        TCFD 공시 방식,
        ESG KPI 서술 스타일
        """
        return self.rag.query(query_text=query_text, top_k=20)

    # -------------------------------------------------
    # Prompt Builder
    # -------------------------------------------------
    def _build_prompt(
        self,
        company_name: str,
        past_reports: List[str],
        rag_docs: List[Dict[str, Any]],
        mode: str,
        previous_template: Optional[Dict[str, Any]],
        validation_feedback: str
    ) -> str:
        """
        실행 모드에 따라 INIT 또는 REPAIR 프롬프트를 생성
        """

        reports_text = "\n\n----- REPORT -----\n\n".join(past_reports)
        rag_json = json.dumps(rag_docs, ensure_ascii=False, indent=2)

        if mode == "init":
            return self._build_init_prompt(company_name, reports_text, rag_json)

        if mode == "repair":
            return self._build_repair_prompt(previous_template, validation_feedback)

        raise ValueError(f"Unknown mode: {mode}")

    # -------------------------------------------------
    # INIT Prompt (분석가모드 1)
    # -------------------------------------------------
    def _build_init_prompt(self, company_name, reports_text, rag_json) -> str:
        """
        최초 템플릿 생성을 위한 최고 퀄리티 구조 분석 프롬프트

        ⚠️ 철학: "INIT이 완벽하면 REPAIR는 필요 없다"
        - 처음부터 최대한 세분화된 분석 수행
        - REPAIR 수준의 공격성으로 템플릿 추출
        - Validation 통과를 목표로 설계
        """
        return f"""
<ROLE>
You are an ELITE ESG report structure reconstruction expert.
This is your ONLY chance to create a PERFECT template.
Your output will be used to generate TCFD reports for investors.
</ROLE>

<OBJECTIVE>
Extract the MOST COMPREHENSIVE, machine-reusable sustainability report template
for "{company_name}".

⚠️ CRITICAL: This template must be SO DETAILED that:
1. Any AI agent can generate reports WITHOUT ambiguity
2. Validation will pass WITHOUT needing REPAIR
3. All 12 required fields are RICHLY populated
</OBJECTIVE>

<INPUTS>
<RAG_REFERENCES>
Industry best practices and reference reports:
{rag_json}
</RAG_REFERENCES>

<PAST_REPORTS>
Company's historical sustainability reports:
{reports_text}
</PAST_REPORTS>
</INPUTS>

<CRITICAL_ANALYSIS_REQUIREMENTS>

1. EXHAUSTIVE DECOMPOSITION (최우선)
   - Break down EVERY section into granular sub-structures
   - Extract ALL implicit hierarchies and patterns
   - Identify nested relationships (section → subsection → paragraph patterns)
   - Capture variations (e.g., different ways to present KPIs)

2. MULTI-DIMENSIONAL STYLE EXTRACTION
   For EACH section:
   - Tone: formal/informal, technical/accessible, quantitative/qualitative
   - Structure: intro → body → conclusion patterns
   - Rhetoric: how does the company justify actions? (data-driven, narrative, mixed)
   - Formatting: headings, lists, tables, emphasis patterns
   - Length: typical word counts, page allocations

3. COMPREHENSIVE KPI TEMPLATES
   Extract ALL metrics with:
   - Name, unit, scope, calculation method
   - Historical trends presentation style
   - Target-setting patterns (baseline → target → progress)
   - Visualization preferences (tables, charts, infographics)

4. REUSABLE PARAGRAPH PATTERNS (minimum 10)
   Extract:
   - Opening statements for each section
   - Transition phrases between topics
   - Data presentation formats ("AAL increased from X% to Y%")
   - Conclusion/commitment statements
   - Stakeholder engagement language

5. SCENARIO ANALYSIS TEMPLATES
   Extract:
   - Which scenarios are used (SSP, RCP, NGFS, etc.)
   - How scenarios are introduced and compared
   - Table/chart formats for scenario presentation
   - Language patterns for uncertainty ("under SSP5-8.5, AAL may reach...")

6. HAZARD-SPECIFIC BLOCKS
   For EACH physical risk type:
   - Description patterns
   - Metrics used (AAL, damage %, frequency)
   - Impact framing (financial, operational, reputational)
   - Mitigation strategy language

7. MATERIALITY & PRIORITIZATION LOGIC
   - How does the company rank issues?
   - What thresholds define "high/medium/low" materiality?
   - How are trade-offs discussed?

8. GOVERNANCE & COMPLIANCE LANGUAGE
   - Board oversight description patterns
   - Regulatory framework references
   - Assurance and verification language

</CRITICAL_ANALYSIS_REQUIREMENTS>

<STRATEGIC_IMPERATIVES>
✅ BE EXHAUSTIVE: Extract 5-10 patterns where a basic analysis finds 1-3
✅ BE SPECIFIC: "Professional tone" → "Formal, data-driven tone addressing institutional investors"
✅ BE HIERARCHICAL: Nested JSON structures for complex patterns
✅ BE COMPLETE: ALL 12 fields must be populated with RICH content
✅ BE ANTICIPATORY: Include patterns that MIGHT be needed, not just what's explicitly visible

⚠️ DO NOT be conservative or minimalist
⚠️ DO NOT leave fields empty unless NO data exists after thorough analysis
⚠️ DO NOT summarize - extract STRUCTURAL patterns

Think: "This template will be used by AI agents who need EXACT patterns to follow."
</STRATEGIC_IMPERATIVES>

<OUTPUT_SCHEMA>
Required 12 keys (ALL must be populated):
1. tone: {{detailed breakdown of voice, audience, formality}}
2. section_structure: {{hierarchy, page allocations, dependencies}}
3. section_style: {{intro/body/conclusion patterns PER section}}
4. formatting_rules: {{headings, lists, emphasis, spacing, tables}}
5. report_years: [covered years]
6. esg_structure: {{E/S/G categories and subcategories}}
7. tcfd_structure: {{governance/strategy/risk_mgmt/metrics hierarchies}}
8. materiality: {{prioritization logic and thresholds}}
9. benchmark_KPIs: {{metric templates with units, scopes, formats}}
10. scenario_templates: {{scenario types and presentation patterns}}
11. hazard_template_blocks: {{risk-specific description/metric/impact patterns}}
12. reusable_paragraphs: [minimum 10 example paragraphs]
</OUTPUT_SCHEMA>

<OUTPUT_RULES>
- Output ONE raw JSON object with ALL 12 keys
- Each field must be DETAILED (not placeholder text)
- Use nested objects/arrays for complex patterns
- NO explanations, NO apologies, NO markdown - PURE JSON ONLY
</OUTPUT_RULES>

JSON_ONLY:
"""

    # -------------------------------------------------
    # REPAIR Prompt (분석가모드 2 - 강화된 재분석)
    # -------------------------------------------------
    def _build_repair_prompt(self, previous_template, feedback) -> str:
        """
        Validation 실패 후 템플릿 전면 재분석 프롬프트

        ⚠️ 전략: "최소 수정" → "피드백 기반 전면 재분석"
        - INIT보다 더 공격적으로 세분화
        - 이전 템플릿은 참고용, 피드백에 맞춰 재설계
        - 검증 실패 원인을 근본적으로 해결
        """
        return f"""
<ROLE>
You are a SENIOR ESG report structure reconstruction specialist.
Your INIT attempt failed validation.
Now you must AGGRESSIVELY re-analyze and REDESIGN the template.
</ROLE>

<CONTEXT>
Previous template (FAILED):
{json.dumps(previous_template, ensure_ascii=False, indent=2)}

Validation feedback (WHY IT FAILED):
{feedback}
</CONTEXT>

<CRITICAL_MISSION>
The previous template was REJECTED.
You must NOW:

1. DEEPER DECOMPOSITION than INIT mode
   - Break down sections into MORE granular sub-structures
   - Extract patterns INIT mode missed
   - Identify implicit hierarchies

2. ADDRESS ALL FEEDBACK POINTS
   - Fix EVERY issue mentioned in validation feedback
   - Go BEYOND the feedback: anticipate related issues
   - Ensure NO validation failure can occur again

3. ALTERNATIVE STRUCTURAL APPROACHES
   - If INIT used hierarchy A, try hierarchy B
   - If INIT extracted 3 patterns, extract 5-7 patterns
   - If INIT was conservative, be COMPREHENSIVE

4. ENHANCED GRANULARITY
   - More detailed section_style breakdowns
   - More specific formatting_rules
   - More examples in reusable_paragraphs
   - More KPI templates with variations

5. STRICT SCHEMA COMPLIANCE
   - ALL 12 required fields must be populated
   - NO empty objects unless truly no data exists
   - RICH nested structures where applicable
</CRITICAL_MISSION>

<STRATEGIC_DIRECTIVES>
⚠️ DO NOT just "fix" the previous template.
⚠️ DO NOT preserve failed structures.
✅ DO perform fresh, aggressive analysis.
✅ DO create richer, more detailed patterns.
✅ DO ensure validation success.

Think: "If INIT was thorough, REPAIR must be EXHAUSTIVE."
</STRATEGIC_DIRECTIVES>

<OUTPUT_RULES>
- Output ONE raw JSON object with ALL 12 keys.
- Each field must be MORE detailed than INIT attempt.
- No explanations, no apologies.
- Pure JSON only.
</OUTPUT_RULES>

JSON_ONLY:
"""

    # -------------------------------------------------
    # JSON Sanitizer
    # -------------------------------------------------
    def _sanitize_response(self, llm_response: Any) -> Dict[str, Any]:
        """
        LLM 응답을 JSON으로 변환하고,
        필수 필드 누락 시 강제로 보정
        """
        # LangChain AIMessage 객체 처리
        if hasattr(llm_response, 'content'):
            llm_response = llm_response.content

        if isinstance(llm_response, str):
            # JSON 블록만 추출 (설명문 제거)
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                llm_response = json_match.group(0)

            try:
                llm_response = json.loads(llm_response)
            except Exception as e:
                # 파싱 실패 시 로깅 및 빈 템플릿 반환
                print(f"⚠️ JSON 파싱 실패: {e}")
                print(f"원본 응답 (처음 500자): {str(llm_response)[:500]}")
                llm_response = {}

        sanitized = {}
        for key, default in self.required_fields.items():
            value = llm_response.get(key, default)
            if value in [None, ""]:
                value = default
            sanitized[key] = value

        return sanitized

