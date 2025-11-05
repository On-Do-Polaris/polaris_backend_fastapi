"""
SKAX Physical Risk Analysis Agent
Main Orchestrator using LangGraph
"""
from config.settings import Config
from workflow import create_workflow_graph, print_workflow_structure


class SKAXPhysicalRiskAnalyzer:
    """
    SKAX 물리적 리스크 분석 메인 오케스트레이터
    """

    def __init__(self, config: Config):
        self.config = config

        # LangGraph 워크플로우 생성
        print("[초기화] LangGraph 워크플로우 생성 중...")
        self.workflow_graph = create_workflow_graph(config)
        print("[초기화] 워크플로우 생성 완료")

    def analyze(self, target_location: dict, analysis_params: dict) -> dict:
        """
        전체 물리적 리스크 분석 실행

        Args:
            target_location: 분석 대상 위치 정보
            analysis_params: 분석 파라미터

        Returns:
            분석 결과 딕셔너리
        """
        print("\n" + "=" * 70)
        print("SKAX 물리적 리스크 분석 시작 (LangGraph)")
        print("=" * 70)

        # 초기 상태 설정
        initial_state = {
            'target_location': target_location,
            'analysis_params': analysis_params,
            'climate_risk_scores': {},
            'completed_risk_analyses': [],
            'errors': [],
            'logs': [],
            'current_step': 'data_collection',
            'workflow_status': 'in_progress'
        }

        # 워크플로우 실행
        print("\n[실행] 워크플로우 실행 중...\n")

        try:
            # LangGraph 실행 (스트리밍 모드)
            final_state = None
            for state in self.workflow_graph.stream(initial_state):
                # 중간 상태 출력 (선택)
                if self.config.DEBUG:
                    print(f"  > 현재 단계: {state}")
                final_state = state

            # 최종 상태 추출
            if final_state:
                # 마지막 노드의 상태 가져오기
                last_node_key = list(final_state.keys())[-1]
                result = final_state[last_node_key]

                print("\n" + "=" * 70)
                print("워크플로우 실행 완료")
                print("=" * 70)

                # 결과 요약 출력
                self._print_summary(result)

                return result
            else:
                raise Exception("워크플로우 실행 결과가 없습니다.")

        except Exception as e:
            print(f"\n[에러] 워크플로우 실행 중 오류 발생: {e}")
            return {
                'workflow_status': 'failed',
                'errors': [str(e)]
            }

    def _print_summary(self, result: dict):
        """
        분석 결과 요약 출력
        """
        print("\n📊 분석 결과 요약:")
        print("-" * 70)

        # 워크플로우 상태
        status = result.get('workflow_status', 'unknown')
        print(f"상태: {status}")

        # 로그
        logs = result.get('logs', [])
        if logs:
            print(f"\n✓ 완료된 단계: {len(logs)}개")
            for log in logs:
                print(f"  - {log}")

        # 에러
        errors = result.get('errors', [])
        if errors:
            print(f"\n⚠ 에러: {len(errors)}개")
            for error in errors:
                print(f"  - {error}")

        # 통합 리스크 스코어
        integrated_risk = result.get('integrated_risk', {})
        if integrated_risk:
            integrated_score = integrated_risk.get('integrated_score', 0)
            risk_rating = integrated_risk.get('risk_rating', 'UNKNOWN')
            print(f"\n🎯 종합 리스크 스코어: {integrated_score:.2f} ({risk_rating})")

            # 상위 리스크
            top_risks = integrated_risk.get('top_risks', [])
            if top_risks:
                print(f"\n🔥 상위 리스크 Top 3:")
                for risk in top_risks[:3]:
                    print(f"  {risk['rank']}. {risk['risk_type']}: {risk['score']:.2f}")

        # 리포트
        report = result.get('report')
        if report:
            print(f"\n📄 리포트가 생성되었습니다.")

        print("-" * 70)

    def visualize(self, output_path: str = "workflow_graph.png"):
        """
        워크플로우 시각화

        Args:
            output_path: 출력 파일 경로
        """
        from workflow import visualize_workflow
        visualize_workflow(self.workflow_graph, output_path)

    def print_structure(self):
        """
        워크플로우 구조 출력
        """
        print_workflow_structure()


def main():
    """
    메인 실행 함수
    """
    # 설정 로드
    config = Config()

    # 분석기 초기화
    analyzer = SKAXPhysicalRiskAnalyzer(config)

    # 워크플로우 구조 출력
    print("\n")
    analyzer.print_structure()

    # 분석 대상 위치 설정 (예시)
    target_location = {
        'latitude': 37.5665,
        'longitude': 126.9780,
        'name': 'Seoul, South Korea'
    }

    # 분석 파라미터 설정
    analysis_params = {
        'time_horizon': '2050',
        'analysis_period': '2025-2050'
    }

    # 분석 실행
    results = analyzer.analyze(target_location, analysis_params)

    # 워크플로우 시각화 (선택)
    print("\n[시각화] 워크플로우 그래프 생성 중...")
    try:
        analyzer.visualize("workflow_graph.png")
    except Exception as e:
        print(f"시각화 생성 실패: {e}")

    return results


if __name__ == "__main__":
    main()
