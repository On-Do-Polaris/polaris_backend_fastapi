risk_insight = {
    "극심한 고온": {
    "risk_id": "extreme_heat",
    "aal_data": {
      "WSDI": {
        "full_name": "Warm Spell Duration Index (열파 지속 지수)",
        "definition": "평년(1981-2010) 대비 일최고기온이 90백분위 이상인 날이 최소 6일 연속되는 기간의 연간 일수 합계",
        "unit": "일/년 (days)",
        "data_source": "KMA 극값지수",
        "calculation_method": "분위수 기반 동적 bin 설정 (Q80, Q90, Q95, Q99)",
        "high_value_means": "WSDI > Q99 (상위 1%)는 극한 폭염을 의미하며, 건물 냉방 부하 증가, 에너지 소비 급증, 인프라 열화 가속을 유발합니다.",
        "bin_descriptions": {
          "bin_0 (< Q80)": "일반 수준 - 폭염 지속일수가 낮아 정상 냉방 운영 가능. 손상률 0.1%로 미미한 리스크",
          "bin_1 (Q80-Q90)": "경미 폭염 - 냉방 부하 증가 시작, 에너지 비용 소폭 상승. 손상률 0.5%",
          "bin_2 (Q90-Q95)": "중간 폭염 - 냉방 설비 과부하 발생, 에너지 비용 상당 상승. 냉방 시스템 효율 저하. 손상률 1.5%",
          "bin_3 (Q95-Q99)": "심각 폭염 - 냉방 설비 한계 도달, 에너지 비용 급격히 상승. 일부 구역 냉방 불가. 손상률 2.8%",
          "bin_4 (≥ Q99)": "극한 폭염 - 냉방 시스템 완전 포화, 에너지 비용 폭등. 건물 가동 중단 위험. 손상률 3.5%"
        },
        "impacts_on": {
          "financial_risk": "냉방비 급증으로 OPEX 증가. WSDI > Q99 (상위 1% 극한 폭염) 시 손상률 3.5%, 일반 수준(<Q80) 대비 35배 증가. 에너지 비용이 평년 대비 최대 2배까지 상승 가능",
          "operational_risk": "고온으로 인한 설비 과부하, 직원 생산성 저하, 옥외 작업 제한",
          "reputation_risk": "기후 적응 능력 부족으로 TCFD 공시에서 물리적 리스크 대응 미흡 평가, ESG 등급 하락 가능성"
        },
        "used_in": [
          "Impact Analysis: 폭염 강도별 에너지 비용 증가율 추정, 냉방 부하 정량화",
          "Strategy Generation: 외기 냉방제어(Free Cooling) 시스템 도입, 고효율 인버터 냉방기 교체, 옥상 쿨루프(Cool Roof) 도료 시공, 피크시간대(14-17시) 설비 가동 조절 및 축냉식 냉방 전환, 건물 외벽 단열재 보강 및 이중창 설치",
          "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 WSDI 추이 분석, 재무 영향 정량화"
        ],
        "interaction_with_other_data": {
          "baseline_wsdi": "기준기간(1991-2020) WSDI 데이터로 분위수 임계값 계산, 미래 시나리오와 비교"
        }
      }
    },
    "risk_score_data": {
        "HCI": {
          "data_name": "복합 폭염 지수 (HCI)",
          "mapped_variables": [
            "TXx (연최고기온)",
            "TR25 (열대야)",
            "WSDIx (폭염지속기간)",
            "SU25 (폭염일수)"
          ],
          "scientific_evidence": "IPCC AR6 WGI & 기상청 SSP 시나리오 데이터 (ETCCDI 지표 가중 평균)",
          "contextual_meaning": "단순 기온(Magnitude)뿐만 아니라 지속기간(Duration)과 야간 열대야(Night-time Heat)를 결합하여, 건물이 열을 식히지 못하고 축적하는 '열 스트레스 강도'를 나타냅니다.",
          "threshold_interpretation": {
            "High (> 0.8)": "열돔(Heat Dome) 현상 발생. 야간에도 기온이 떨어지지 않아 24시간 냉방이 필요하며, HVAC 설비 과부하로 인한 고장 확률이 급증하는 구간.",
            "Moderate (0.2 ~ 0.4)": "일반적인 여름 더위. 주간 냉방으로 대응 가능하며 야간에는 자연 환기 효과를 기대할 수 있음."
          },
          "financial_impact_type": {
            "Category": "OPEX (운영비용) 및 설비 리스크",
            "Mechanism": "냉방 효율 저하(De-rating)로 인한 전력 소비량 증가 및 피크 요금제(Demand Charge) 적용 위험.",
            "Sensitivity": "ASHRAE 모델 기준, HCI 상승 시 전력 비용 약 3~5% 내외 증가 추정 (건물 용도별 상이)."
          },
          "mitigation_keyword": {
            "Engineering": "고효율 인버터 냉동기 교체, 외기 냉방 제어(Economizer) 도입",
            "Operational": "피크 시간대 설비 가동 조정(Load Shifting)"
          }
        },
        "UHI_Intensity": {
          "data_name": "도시 열섬 강도 (UHI)",
          "mapped_variables": [
            "impervious_surface_ratio (불투수면 비율)",
            "building_type (건물용도)"
          ],
          "scientific_evidence": "Oke (1982)의 도시 기후학 이론을 적용한 환경부 토지피복도 기반 분석",
          "contextual_meaning": "사업장 주변의 인공 구조물과 포장 상태로 인해, 기상청 예보 온도보다 실제 현장 온도가 얼마나 더 높게 형성되는지를 나타내는 '입지적 할증 계수'입니다.",
          "threshold_interpretation": {
            "High (상업/공업지구)": "주변 기온 대비 +2~3°C 상승 효과. 아스팔트 복사열로 인해 외기 도입(Free Cooling)이 불가능하여 냉방 에너지가 추가 소모됨.",
            "Low (녹지/교외)": "주변 기온과 유사하거나 낮음. 야간에 빠른 열 방출이 가능하여 냉방 부하가 낮음."
          },
          "financial_impact_type": {
            "Category": "Revenue (매출) 및 생산성 리스크",
            "Mechanism": "전력 수급 비상 시 도심지 상업 시설 우선 단전 위험 및 쾌적성 저하로 인한 방문객 이탈."
          },
          "mitigation_keyword": {
            "Engineering": "쿨루프(Cool Roof, 차열도료), 쿨페이브먼트(Cool Pavement)",
            "Nature-based": "옥상 조경 및 벽면 녹화"
          }
        },
        "Building_Vulnerability": {
          "data_name": "건물 에너지 효율 (Vulnerability)",
          "mapped_variables": [
            "building_age (건축연도)",
            "structure_type (구조)"
          ],
          "scientific_evidence": "국토교통부 녹색건축물 설계 기준 (2020) 및 건축물대장 데이터",
          "contextual_meaning": "건물의 '피부(Skin)'가 외부의 열기를 얼마나 잘 차단하고 내부 냉기를 유지하는지를 결정하는 단열 및 기밀 성능 수준입니다.",
          "threshold_interpretation": {
            "High Risk (구축/비단열)": "단열 기준 강화 이전 건물(통상 1990년대 이전). 창호 틈새로 냉기가 새어나가고 외벽이 뜨거워지는 '밑 빠진 독' 상태.",
            "Low Risk (신축/고효율)": "Low-E 유리 및 고단열재 적용으로 외부 열기 차단 성능 우수."
          },
          "financial_impact_type": {
            "Category": "Asset Value (자산가치) 하락 & CAPEX",
            "Mechanism": "에너지 비효율 건물에 대한 임대료 할인 압박(Brown Discount) 및 향후 '좌초 자산' 방지를 위한 대규모 리모델링(CAPEX) 지출 불가피.",
            "Implication": "탄소세(Carbon Tax) 도입 시 Scope 2 배출량에 따른 추가 재무 부담"
          },
          "mitigation_keyword": {
            "Engineering": "그린 리모델링(단열 보강, 창호 교체)",
            "Financial": "에너지 성능 개선 공사비 지원 사업 및 녹색 채권 활용"
          }
        }   
    }
  },
  "극심한 한파": {
    "risk_id": "extreme_cold",
    "aal_data": {
      "CSDI": {
        "full_name": "Cold Spell Duration Index (한파 지속 지수)",
        "definition": "평년(1981-2010) 대비 일최저기온이 10백분위 이하인 날이 최소 6일 연속되는 기간의 연간 일수 합계",
        "unit": "일/년 (days)",
        "data_source": "KMA 극값지수",
        "calculation_method": "분위수 기반 동적 bin 설정 (Q80, Q90, Q95, Q99)",
        "high_value_means": "CSDI > Q99 (상위 1%)는 극한 한파를 의미하며, 배관 동파 위험, 난방 부하 급증, 건물 구조 수축을 유발합니다.",
        "bin_descriptions": {
          "bin_0 (< Q80)": "일반 수준 - 한파 지속일수가 낮아 정상 난방 운영 가능. 배관 동파 위험 거의 없음. 손상률 0.05%",
          "bin_1 (Q80-Q90)": "경미 한파 - 난방 부하 증가, 난방비 소폭 상승. 외부 노출 배관 일부 동파 가능성. 손상률 0.3%",
          "bin_2 (Q90-Q95)": "중간 한파 - 난방 설비 과부하, 난방비 상당 상승. 보온 미비 배관 동파 위험 증가. 손상률 0.8%",
          "bin_3 (Q95-Q99)": "심각 한파 - 난방 시스템 한계 도달, 난방비 급격히 상승. 배관 동파 다발, 일부 구역 난방 불가. 손상률 1.8%",
          "bin_4 (≥ Q99)": "극한 한파 - 난방 시스템 완전 포화, 난방비 폭등. 광범위 배관 동파, 건물 가동 중단. 손상률 2.5%"
        },
        "impacts_on": {
          "financial_risk": "난방비 급증 및 배관 동파 수리비 발생. CSDI > Q99 (상위 1% 극한 한파) 시 손상률 2.5%, 일반 수준 대비 50배 증가. 난방 비용 평년 대비 최대 3배 상승 가능",
          "operational_risk": "배관 동파 시 용수 공급 중단, 난방 시스템 과부하로 인한 설비 고장",
          "reputation_risk": "한파 대응 실패로 TCFD 물리적 리스크 관리 역량 부족 노출, ESG 평가에서 기후 회복력 부족 지적 가능"
        },
        "used_in": {
          "Impact Analysis: 한파 강도별 난방비 증가율 및 배관 동파 확률 추정",
          "Strategy Generation: 외부 노출 배관 열선(Heat Trace) 설치 및 보온재 2중 시공, 지하 배관실 온도감지 센서 및 자동 예열 시스템 구축, 비상 전기난방기 배치 및 동파 대응 매뉴얼 수립, 보일러 예비기 설치 및 정기 점검 강화, 겨울철 배관 순환수 온도 최저 5°C 유지 자동제어",
          "Report Generation: TCFD 물리적 리스크 섹션에서 극한 한파 시나리오 분석, 운영 연속성 계획 공시"
        },
        "interaction_with_other_data": {
          "baseline_csdi": "기준기간 CSDI 데이터로 분위수 임계값 계산"
        }
      }
    },
    "risk_score_data": {
        "CCI": {
          "data_name": "복합 한파 지수 (CCI)",
          "mapped_variables": [
            "TNn (연최저기온)",
            "CSDIx (한파지속기간)",
            "FD0 (결빙일수)",
            "ID0 (겨울일수)"
          ],
          "scientific_evidence": "IPCC AR6 WGI & 기상청 SSP 시나리오 데이터 (ETCCDI 지표 가중 결합)",
          "contextual_meaning": "단순히 기온이 낮은 것(Magnitude)뿐만 아니라, 영하의 날씨가 얼마나 오래 지속되는지(Duration)와 수분이 결빙되는 빈도(Frequency)를 결합하여 시설물의 동결 심도를 예측하는 지표입니다.",
          "threshold_interpretation": {
            "High (> 0.8)": "극한 한파 구간. 한파가 20일 이상 지속되고 결빙이 반복되어, 배관 내 유체가 팽창, 파열(Burst)될 물리적 임계치를 초과할 가능성이 매우 높음.",
            "Moderate (0.2 ~ 0.4)": "통상적인 겨울 날씨. 일반적인 단열 기준으로 방어 가능하나, 노후 설비의 경우 주의가 필요함."
          },
          "financial_impact_type": {
            "Category": "CAPEX (설비 교체) 및 Revenue 손실",
            "Mechanism": "수도/소방 배관 동파로 인한 누수 피해 복구 비용 발생 및 생산 시설의 경우 용수 공급 중단으로 인한 조업 정지(Shutdown) 리스크.",
            "Sensitivity": "CCI 상승 시 난방 에너지 요구량(Heating Degree Days) 기반 비용 증가 및 동파 사고 확률 유의미하게 상승."
          },
          "mitigation_keyword": {
            "Engineering": "배관 열선(Heat Trace) 설치, 보온재 등급 상향, 드레인(Drain) 밸브 자동화",
            "Operational": "동절기 퇴수 조치 및 야간 최소 난방(Sleep Mode) 가동"
          },
          "Implication": "에너지 효율 등급 저하로 인한 부동산 자산 가치 하락(Brown Discount) 가능성."
        },
        "Building_Insulation": {
          "data_name": "건물 단열 취약성 (Vulnerability)",
          "mapped_variables": [
            "building_age (건축연도)",
            "structure_type (구조)"
          ],
          "scientific_evidence": "국토교통부 건축물 에너지절약설계기준 및 건축물대장 데이터",
          "contextual_meaning": "건물 외피(Envelope)가 내부의 열을 뺏기지 않고 유지하는 '열 저항성(R-value)'과 기밀 성능의 수준입니다.",
          "threshold_interpretation": {
            "High Risk (구축/비단열)": "단열 기준 강화 이전 건물(통상 1990년대 이전). 단열재 성능 저하와 구조적 틈새(Air Leakage)로 인해 난방 부하가 신축 대비 40% 이상 폭증하며, 결로 및 곰팡이 발생 위험이 큼.",
            "Low Risk (신축/고효율)": "고기밀 시공 및 강화된 단열 법규 적용으로 열 손실 최소화."
          },
          "financial_impact_type": {
            "Category": "OPEX (난방비) 급증 및 탄소세 리스크",
            "Mechanism": "열 관류율(U-value) 저하로 인한 LNG/전력 소비량 급증. 이는 Scope 1, 2 배출량을 증가시켜 탄소 규제 비용을 가중시킴."
          },
          "mitigation_keyword": {
            "Engineering": "이중창/삼중창 교체(Retrofit), 외단열 공법 적용",
            "Financial": "에너지 효율화 사업(ESCO)을 통한 개보수 자금 조달"
          }
        },
        "Urban_Intensity_Cold": {
          "data_name": "도시화 및 에너지 수요 집중도 (Exposure)",
          "mapped_variables": [
            "building_type (건물용도)",
            "urban_intensity (추정된 도시화강도)"
          ],
          "scientific_evidence": "건축물대장 용도 분류 및 도시 에너지 소비 패턴 분석",
          "contextual_meaning": "한파 발생 시 해당 구역의 에너지(가스, 전력) 수요가 얼마나 집중되는지를 나타내며, 이는 인프라 과부하에 따른 공급 불안정성을 시사합니다.",
          "threshold_interpretation": {
            "High (업무/상업 밀집)": "주간 난방 수요가 집중되는 구역. 전력/가스 공급망의 부하가 높아 공급 이상 발생 시 대체 수단이 없으면 운영 마비.",
            "Low (녹지/저밀도)": "에너지 수요 밀도가 낮아 공급망 부하가 적음."
          },
          "financial_impact_type": {
            "Category": "Operational Resilience (운영 회복력) 리스크",
            "Mechanism": "도시 가스압 저하 또는 지역난방 공급 온도 미달 시, 개별 전열기구 사용 급증으로 인한 화재 위험 및 예비 전력비 증가."
          },
          "mitigation_keyword": {
            "Engineering": "비상 발전기 및 유류 저장 탱크(Backup Fuel) 확보",
            "Operational": "난방 부하 분산 운전 및 재택 근무 전환 계획 수립"
          }
        }
    }
  },
"산불": {
    "risk_id": "wildfire",
    "aal_data": {
        "TA": {
      "full_name": "평균 기온 (Temperature Average)",
      "definition": "월평균 기온 (FWI 계산용)",
      "unit": "°C",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "기온이 높을수록 FWI 지수가 지수적으로 증가. TA 1°C 상승 시 FWI 8.3% 증가 (exp(0.08) 기반, 온도 계수 0.08)",
      "impacts_on": {
        "financial_risk": "산불 위험 증가로 보험료 상승, 산불 발생 시 자산 손실",
        "operational_risk": "고온으로 인한 산불 위험 증가, 옥외 작업 중단",
        "reputation_risk": "산불 대응 미흡 시 ESG 평가에서 환경 리스크 관리 부족 지적"
      },
      "used_in": [
        "Impact Analysis: 기온 상승에 따른 FWI 증가율 정량화",
        "Strategy Generation: 고온 시즌 방화대 조성, 감시 강화 우선순위",
        "Report Generation: TCFD 물리적 리스크 섹션에서 산불 리스크 시나리오 분석"
      ],
      "interaction_with_other_data": {
        "RHM": "고온 + 저습 조합 시 FWI 최대화",
        "WS": "고온 + 강풍 조합 시 산불 확산 속도 급증",
        "RN": "고온 + 무강수 조합 시 산림 건조 심화"
      },
      "calculation_formula": "temp_factor = exp(0.08 × (TA - 5))"
    },
    "RHM": {
      "full_name": "상대 습도 (Relative Humidity)",
      "definition": "월평균 상대 습도 (FWI 계산용)",
      "unit": "%",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "습도가 낮을수록 FWI 급증. 습도 10% 하락 (예: 90% → 80%) 시 FWI 41% 증가 (제곱근 효과)",
      "impacts_on": {
        "financial_risk": "저습으로 인한 산불 위험 증가, 보험료 상승",
        "operational_risk": "산불 위험으로 현장 작업 중단",
        "reputation_risk": "산불 대응 실패 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 습도별 FWI 변화율 추정",
        "Strategy Generation: 저습 시즌 방화 감시 강화",
        "Report Generation: TCFD 산불 리스크 분석에서 습도 영향 정량화"
      ],
      "interaction_with_other_data": {
        "TA": "저습 + 고온 조합 시 FWI 최대화",
        "WS": "저습 + 강풍 조합 시 산불 확산 속도 5배 증가"
      },
      "calculation_formula": "humidity_factor = (1 - RHM/100)^0.5"
    },
    "WS": {
      "full_name": "풍속 (Wind Speed)",
      "definition": "월평균 풍속 (FWI 계산용)",
      "unit": "m/s",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "풍속이 강할수록 FWI 지수적 증가. 풍속 10km/h 증가 시 FWI 65% 증가 (exp(0.5039) 기반, 캐나다 ISI 방식)",
      "impacts_on": {
        "financial_risk": "강풍 시 산불 확산 속도 급증, 피해 규모 확대로 손실 증가",
        "operational_risk": "강풍으로 인한 산불 진화 어려움",
        "reputation_risk": "산불 대응 실패 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 풍속별 FWI 증가율 및 산불 확산 속도 추정",
        "Strategy Generation: 강풍 시즌 방화대 확장 투자 우선순위",
        "Report Generation: TCFD 산불 리스크 분석에서 풍속 영향 정량화"
      ],
      "interaction_with_other_data": {
        "RHM": "강풍 + 저습 조합 시 산불 확산 속도 급증",
        "TA": "강풍 + 고온 조합 시 FWI 200 이상"
      },
      "calculation_formula": "wind_factor = exp(0.05039 × WS_kmh), WS_kmh = WS × 3.6"
    },
    "RN": {
      "full_name": "강수량 (Rainfall)",
      "definition": "월 강수량 (FWI 계산용)",
      "unit": "mm",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "무강수 시 FWI 급증. RN < 10mm 시 FWI 약 2배 증가",
      "impacts_on": {
        "financial_risk": "가뭄으로 인한 산불 위험 증가, 보험료 상승",
        "operational_risk": "산림 건조로 산불 진화 어려움",
        "reputation_risk": "산불 대응 미흡 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 강수량별 FWI 변화율 추정",
        "Strategy Generation: 무강수 시즌 방화 감시 강화",
        "Report Generation: TCFD 산불 리스크 분석에서 강수 패턴 변화 영향 정량화"
      ],
      "interaction_with_other_data": {
        "TA": "무강수 + 고온 조합 시 산림 건조 심화",
        "RHM": "무강수 + 저습 조합 시 FWI 최대화"
      },
      "calculation_formula": "rain_factor = exp(-0.0005 × RN)"
    },
    "FWI": {
      "full_name": "Fire Weather Index (산불 위험 지수)",
      "definition": "기온, 습도, 풍속, 강수량을 종합한 산불 위험 지수",
      "unit": "무차원 (지수)",
      "data_source": "TA, RHM, WS, RN 기반 계산",
      "calculation_method": "월별 기후 데이터로 FWI 계산 후 bin 분류",
      "calculation_formula": "FWI = (1 - RHM/100)^0.5 × exp(0.05039 × WS_kmh) × exp(0.08 × (TA - 5)) × exp(-0.0005 × RN) × 5",
      "high_value_means": "FWI > 50은 산불 고위험, FWI > 100은 산불 극한 위험으로 진화 거의 불가능을 의미합니다.",
      "bin_descriptions": {
        "bin_0 (FWI < 5.4, Low)": "낮은 산불 위험 - 정상적인 산림 관리 가능. 산불 발화 가능성 극히 낮음. 손상률 0.1%",
        "bin_1 (FWI 5.4-11.2, Moderate)": "중간 산불 위험 - 산불 발화 가능성 증가, 주의 단계. 일상적 감시로 충분. 손상률 1%",
        "bin_2 (FWI 11.2-21.3, High)": "높은 산불 위험 - 산불 발화 및 확산 위험 높음. 강화된 감시 필요, 야외 화기 사용 제한. 손상률 5%",
        "bin_3 (FWI 21.3-50, Very High)": "매우 높은 산불 위험 - 산불 빠른 확산 위험, 진화 어려움. 산림 접근 통제, 비상 대기. 손상률 12%",
        "bin_4 (FWI ≥ 50, Extreme)": "극한 산불 위험 - 산불 폭발적 확산, 진화 거의 불가능. 전면 통제, 자산 대피 고려. 손상률 25%"
      },
      "impacts_on": {
        "financial_risk": "산불 발생 시 자산 손실 및 영업 중단 손실. FWI ≥ 50 (Extreme) 시 손상률 25%, Moderate(11.2-21.3, 손상률 1%) 대비 25배 증가",
        "operational_risk": "산불 위험으로 현장 작업 전면 중단",
        "reputation_risk": "산불 대응 실패 시 ESG 평가에서 환경 리스크 관리 능력 부족 노출"
      },
      "used_in": [
        "Impact Analysis: FWI별 산불 발화 확률 및 재무 손실 추정",
        "Strategy Generation: 사업장 주변 30m 방화대(Firebreak) 조성 및 정기 제초, FWI > 21.3 시 자동 살수 시스템 가동, 고위험 시즌(3-5월, 11-12월) 24시간 감시 CCTV 및 열화상 카메라 설치, 산림 인접 건물 외벽 불연재 교체 및 스프링클러 설치, 비상 소화전 증설 및 소방차 진입로 확보",
        "Report Generation: TCFD 물리적 리스크 섹션에서 산불 리스크 시계열 분석, SSP 시나리오별 FWI 추이"
      ],
      "interaction_with_other_data": {
        "TA": "온도 상승 → FWI 지수적 증가",
        "RHM": "습도 하락 → FWI 급증",
        "WS": "풍속 증가 → FWI 지수적 증가",
        "RN": "강수 감소 → FWI 증가"
      }
    }
  },
    "risk_score_data": {
      "FWI": {
        "data_name": "산불위험지수 (FWI)",
        "mapped_variables": [
          "fwi (연평균/최대값)",
          "temperature",
          "relative_humidity",
          "wind_speed",
          "rainfall"
        ],
        "scientific_evidence": "Canadian Forest Service (CFS) FWI System & KMA SSP 시나리오 데이터_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "기온, 습도, 풍속, 강수량을 종합하여 숲의 연료(낙엽, 가지)가 얼마나 건조해져 불이 붙기 쉬운 상태인지를 나타내는 '기상학적 발화 잠재력'입니다.",
        "threshold_interpretation": {
          "Extreme (> 50)": "폭발적 확산 단계. 작은 불씨도 즉시 대형 산불로 번지며, 소방 인력에 의한 진화가 불가능하고 자연 소화를 기다려야 하는 수준.",
          "High (30 ~ 50)": "지표면 연료가 매우 건조하여 불길이 수관(나무 꼭대기)으로 옮겨붙을 위험이 높음."
        },
        "financial_impact_type": {
          "Category": "Asset Write-off (자산 전손) 및 보험 리스크",
          "Mechanism": "화재로 인한 시설물 전소(Total Loss) 위험. FWI가 높은 지역은 재산종합보험의 자연재해 담보(NatCat) 가입이 거절되거나 보험료율(Premium)이 급증할 수 있음.",
          "Sensitivity": "FWI 10 증가 시 대형 산불 발생 확률 기하급수적 증가."
        },
        "mitigation_keyword": {
          "Engineering": "외부 살수 설비(Drencher) 설치, 불연성 외장재 교체",
          "Operational": "건조 주의보 발령 시 화기 작업 전면 중단 및 감시 강화"
        }
      },
      "Forest_Distance": {
        "data_name": "산림 인접도 (Exposure)",
        "mapped_variables": [
          "forest_distance_m (산림거리)",
          "proximity_category (근접도범주)"
        ],
        "scientific_evidence": "환경부 산림 공간 데이터 및 V-World 지형 분석_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, erd.md]",
        "contextual_meaning": "산불 발생 시 화염의 직접적인 복사열(Radiant Heat)이나 강풍에 날리는 불똥(비산화, Embers)이 건물에 도달할 수 있는 물리적 거리입니다.",
        "threshold_interpretation": {
          "Critical (< 100m)": "화염 직접 접촉 가능권. 방화벽이나 이격 공간(Defensible Space) 없이는 소방차 진입조차 어려워 방어가 불가능함.",
          "Warning (100m ~ 500m)": "비산화(도깨비불) 위험권. 본 화재가 도달하기 전 불똥으로 인해 2차 화재가 발생할 수 있음."
        },
        "financial_impact_type": {
          "Category": "CAPEX (방호 설비) 요구",
          "Mechanism": "산림과 인접한 사업장은 화재 방어선 구축을 위한 대규모 토목 공사 비용(CAPEX)이 발생하며, 지자체의 산림 정비 명령 이행 비용 부담.",
          "Risk": "화재 발생 시 주변 산림 훼손에 대한 배상 책임(Liability) 리스크."
        },
        "mitigation_keyword": {
          "Engineering": "방화수림대 조성, 이격 공간(Defensible Space) 확보",
          "Nature-based": "사업장 경계 가연성 식생 제거(Fuel Management)"
        }
      },
      "Building_Vulnerability_Wildfire": {
        "data_name": "건물 화재 취약성 (Vulnerability)",
        "mapped_variables": [
          "structure_type (구조)",
          "building_age (건축연도)"
        ],
        "scientific_evidence": "건축물대장 구조 정보 및 화재안전기준(NFSC)_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, 01_공공데이터포털_API.md]",
        "contextual_meaning": "외부에서 날아온 불똥이나 복사열에 의해 건물 외장재가 얼마나 쉽게 착화되는지를 결정하는 구조적 특성입니다.",
        "threshold_interpretation": {
          "High Vulnerability (목조/샌드위치패널)": "가연성 외장재 사용으로 인해 외부 화재가 내부로 급격히 전이됨. (취약성 점수 대폭 가산)",
          "Low Vulnerability (철근콘크리트/불연재)": "내화 성능 확보로 화재 전이 지연 가능 (불연성 자재로 인한 감점 요인)."
        },
        "financial_impact_type": {
          "Category": "Business Interruption (운영 중단)",
          "Mechanism": "주요 설비 소실로 인한 장기 조업 중단 및 복구 기간 동안의 매출 손실(Revenue Loss).",
          "Cost": "화재 안전 진단 및 내진/내화 보강 공사 비용."
        },
        "mitigation_keyword": {
          "Engineering": "드라이비트 등 가연성 외장재 제거, 방화 셔터/댐퍼 점검",
          "Financial": "기업 휴지 보험(Business Interruption Insurance) 가입"
        }
      }
    }
  },
  "가뭄": {
    "risk_id": "drought",
    "aal_data": {
      "SPEI_12": {
      "full_name": "Standardized Precipitation-Evapotranspiration Index 12개월",
      "definition": "강수량과 증발산량을 고려한 12개월 누적 수분 가용성 지수. 음수는 가뭄, 양수는 습윤을 의미",
      "unit": "무차원 (표준화 지수)",
      "data_source": "KMA SPEI 데이터",
      "calculation_method": "월별 SPEI-12 값을 bin으로 분류 (>-1, -1~-1.5, -1.5~-2.0, ≤-2.0)",
      "high_value_means": "SPEI-12 ≤ -2.0 (극심 가뭄)은 용수 공급 제한, 토양 수분 고갈, 화재 위험 증가를 의미합니다.",
      "bin_descriptions": {
        "bin_0 (SPEI > -1, Normal to Wet)": "정상~습윤 - 수분 가용성 양호, 가뭄 영향 없음. 정상 용수 공급. 손상률 0.1%",
        "bin_1 (SPEI -1 ~ -1.5, Moderate Drought)": "중간 가뭄 - 토양 수분 감소, 용수 수요 증가. 용수비 소폭 상승. 손상률 2%",
        "bin_2 (SPEI -1.5 ~ -2.0, Severe Drought)": "심각 가뭄 - 토양 심각 건조, 용수 공급 제한 시작. 용수비 상당 상승, 일부 생산 조정. 손상률 8%",
        "bin_3 (SPEI ≤ -2.0, Extreme Drought)": "극심 가뭄 - 토양 완전 고갈, 용수 공급 심각 제한. 용수비 폭등, 생산 중단 위험. 손상률 20%"
      },
      "impacts_on": {
        "financial_risk": "가뭄으로 인한 용수비 증가, 생산 차질. SPEI-12 ≤ -2.0 (극심 가뭄) 시 손상률 20%, 중간 가뭄(-1.5~-1, 손상률 2%) 대비 10배 증가. 용수 비용 최대 3배 상승 가능",
        "operational_risk": "용수 공급 제한으로 냉각수 부족, 제조 공정 중단 위험",
        "reputation_risk": "물 사용 효율 저하로 ESG 평가에서 수자원 관리 역량 부족 지적, CDP Water 등급 하락 가능"
      },
      "used_in": [
        "Impact Analysis: 가뭄 심도별 용수 비용 증가 및 생산 차질 정량화",
        "Strategy Generation: 우수 집수 탱크(1000톤 이상) 설치 및 조경/화장실 용수 전환, 공정용수 재이용률 70% 이상 달성 (역삼투압 RO 시스템 도입), 지하수 관정 개발 및 비상 수원 확보, 용수 사용량 실시간 모니터링 시스템 구축, 절수형 냉각탑 교체 및 증발 손실 50% 저감",
        "Report Generation: TCFD 물리적 리스크 섹션에서 물 스트레스 대응 전략 공시, SSP 시나리오별 가뭄 영향 분석"
      ],
      "interaction_with_other_data": {
        "monthly_data": "월별 SPEI-12 값을 평탄화하여 월 기반 확률 계산"
      }
    }
  },
    "risk_score_data": {
        "SPEI": {
        "data_name": "표준화 강수-증발산 지수 (SPEI-12)",
        "mapped_variables": [
          "spei_12 (12개월 척도)",
          "annual_precipitation_mm (연강수량)",
          "potential_evapotranspiration (잠재증발산량)"
        ],
        "scientific_evidence": "Vicente-Serrano et al. (2010) & WMO 가뭄 감시 가이드라인 (1500mm 기준 적용)_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "단순 강수량 부족뿐만 아니라, 기온 상승으로 인해 땅과 식물에서 증발하는 수분량(Evapotranspiration)까지 고려한 '실질적 수자원 가용성' 지표입니다.",
        "threshold_interpretation": {
          "Extreme Drought (SPEI < -2.0)": "50~100년 빈도의 극한 가뭄. 댐 저수율 저하로 인해 지자체 차원의 강제 급수 제한(Water Rationing) 조치가 시행될 확률이 매우 높음.",
          "Normal to Mild (> -1.0)": "통상적인 기후 범위. 자체적인 용수 확보 노력으로 대응 가능한 수준."
        },
        "financial_impact_type": {
          "Category": "Revenue (매출) 손실 및 OPEX 증가",
          "Mechanism": "공업용수 공급 제한에 따른 공장 가동률 저하(Curtailment) 및 비상 용수(Water Trucking) 조달 비용 발생.",
          "Sensitivity": "반도체, 철강 등 다량의 냉각수/세척수가 필요한 산업군에서 매출 타격(Business Interruption)이 즉각적으로 발생함."
        },
        "mitigation_keyword": {
          "Engineering": "폐수 재활용 시스템(Water Recycling) 도입, 빗물 저류조 설치",
          "Operational": "대체 수원 확보 및 용수 사용 최적화 프로세스 구축"
        }
      },
      "Water_Dependency": {
        "data_name": "용수 의존도 (Exposure)",
        "mapped_variables": [
          "water_dependency (용수의존도_등급)",
          "main_purpose (건물주용도)"
        ],
        "scientific_evidence": "환경부 산업용수 수요관리 종합계획 및 건축물대장 용도 분류_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, fallback_values_comprehensive.md]",
        "contextual_meaning": "사업장 운영에 물이 얼마나 필수적인지를 나타내는 '운영 민감도'입니다. 물 공급이 끊겼을 때 비즈니스가 멈추는지(High), 단순히 불편한지(Low)를 구분합니다.",
        "threshold_interpretation": {
          "High (제조/발전/세차)": "물 공급 중단 = 조업 즉시 중단. 대체 수원 없이는 매출 0원이 되는 구조적 취약성 보유.",
          "Medium (업무/상업)": "화장실, 식수 등 생활용수 부족으로 인한 직원 근무 환경 악화 및 고객 불편 초래."
        },
        "financial_impact_type": {
          "Category": "Operational Continuity (운영 연속성) 리스크",
          "Mechanism": "물 부족 시 우선순위(생활용수 > 공업용수)에 따라 산업체가 가장 먼저 공급 제한을 받게 되므로, 고의존도 사업장은 규제 리스크에 직접 노출됨."
        },
        "mitigation_keyword": {
          "Engineering": "공정 개선을 통한 용수 원단위(Water Intensity) 저감",
          "Strategic": "사업 연속성 계획(BCP) 내 물 부족 시나리오 수립"
        }
      },
      "Geo_Subsidence_Risk": {
        "data_name": "지반 침하 취약성 (Vulnerability)",
        "mapped_variables": [
          "basement_floors (지하층수)",
          "building_age (건축연도)"
        ],
        "scientific_evidence": "Smit et al. (2012) - 가뭄에 의한 토양 수축 및 기초 손상 연구_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, 01_공공데이터포털_API.md]",
        "contextual_meaning": "장기 가뭄으로 토양 내 수분이 빠져나가 흙이 수축(Soil Shrinkage)할 때, 건물의 기초(Foundation)가 불균등하게 침하되거나 균열이 발생할 가능성입니다.",
        "threshold_interpretation": {
          "High Risk (노후 건물 + 지하층 보유)": "기초 콘크리트가 노후화된 상태에서 토양 수축 압력을 받으면 외벽 균열 및 지하 구조물 누수, 뒤틀림 발생 위험 높음.",
          "Low Risk (신축 + 지상 건물)": "최신 내진 설계 및 기초 보강으로 토양 변형에 대한 저항성 확보."
        },
        "financial_impact_type": {
          "Category": "Asset Value (자산가치) 하락 & CAPEX",
          "Mechanism": "건물 구조 안전 진단 등급 하락 및 기초 보강 공사(Underpinning)를 위한 대규모 자본 지출 발생.",
          "Implication": "물리적 손상으로 인한 건물의 잔존 수명(Useful Life) 단축."
        },
        "mitigation_keyword": {
          "Engineering": "건물 주변 토양 함수비 유지 관리, 기초 보강 공사",
          "Monitoring": "구조물 기울기 및 균열 계측 시스템 도입"
        }
      }
    }
  },
  "물부족": {
    "risk_id": "water_stress",
    "aal_data": {
      "TA": {
      "full_name": "평균 기온 (Temperature Average)",
      "definition": "월평균 기온 (ET0 계산용)",
      "unit": "°C",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "기온이 높을수록 증발산량(ET0) 증가 → 유효강수량(P_eff) 감소 → 수자원 가용량(TRWR) 감소",
      "impacts_on": {
        "financial_risk": "고온으로 인한 ET0 증가 → 수자원 부족 → 용수비 증가",
        "operational_risk": "수자원 감소로 냉각수 공급 제한, 생산 설비 가동 제약",
        "reputation_risk": "물 스트레스 대응 미흡 시 CDP Water 등급 하락, ESG 평가에서 수자원 관리 역량 부족 지적"
      },
      "used_in": [
        "Impact Analysis: 기온 상승에 따른 ET0 증가 및 수자원 가용량 감소 정량화",
        "Strategy Generation: 용수 재이용 시스템, 절수 설비 투자 우선순위",
        "Report Generation: TCFD 물리적 리스크 섹션에서 물 스트레스 시나리오 분석"
      ],
      "interaction_with_other_data": {
        "RHM": "고온 + 저습 → ET0 최대화 → 수자원 급감",
        "SI": "고온 + 고일사 → ET0 증가 → P_eff 감소",
        "RN": "고온 + 무강수 → P_eff 음수 가능 → TRWR 급감"
      },
      "calculation_formula": "Penman-Monteith 식에서 포화수증기압(es), 실제수증기압(ea), 기울기(Δ) 계산에 사용"
    },
    "RHM": {
      "full_name": "상대 습도 (Relative Humidity)",
      "definition": "월평균 상대 습도 (ET0 계산용)",
      "unit": "%",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "습도가 낮을수록 ET0 증가 → 수자원 가용량 감소",
      "impacts_on": {
        "financial_risk": "저습으로 인한 ET0 증가 → 수자원 부족 → 용수비 증가",
        "operational_risk": "수자원 감소로 생산 차질",
        "reputation_risk": "물 사용 효율 저하 → ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 습도 변화에 따른 ET0 및 수자원 가용량 추정",
        "Strategy Generation: 저습 시즌 용수 사용 최적화",
        "Report Generation: TCFD 물 스트레스 분석에서 습도 영향 정량화"
      ],
      "interaction_with_other_data": {
        "TA": "저습 + 고온 → ET0 최대화",
        "WS": "저습 + 강풍 → ET0 급증"
      },
      "calculation_formula": "실제수증기압 ea = es × (RHM / 100)"
    },
    "WS": {
      "full_name": "풍속 (Wind Speed)",
      "definition": "월평균 풍속 (ET0 계산용)",
      "unit": "m/s",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "풍속이 강할수록 ET0 증가 → 수자원 가용량 감소",
      "impacts_on": {
        "financial_risk": "강풍으로 인한 ET0 증가 → 수자원 부족 → 용수비 증가",
        "operational_risk": "수자원 감소로 냉각수 공급 제한",
        "reputation_risk": "물 스트레스 대응 미흡 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 풍속 변화에 따른 ET0 및 수자원 가용량 추정",
        "Strategy Generation: 용수 절감 기술 도입 우선순위",
        "Report Generation: TCFD 물 스트레스 분석에서 풍속 영향 정량화"
      ],
      "interaction_with_other_data": {
        "RHM": "강풍 + 저습 → ET0 급증",
        "SI": "강풍 + 고일사 → ET0 최대화"
      },
      "calculation_formula": "풍속 보정 u2 = WS × 4.87 / ln(67.8 × 10 - 5.42), Aerodynamic Term에 사용"
    },
    "SI": {
      "full_name": "일사량 (Solar Irradiance)",
      "definition": "월평균 일사량 (ET0 계산용)",
      "unit": "W/m²",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "일사량이 높을수록 ET0 증가 → 수자원 가용량 감소",
      "impacts_on": {
        "financial_risk": "고일사로 인한 ET0 증가 → 수자원 부족 → 용수비 증가",
        "operational_risk": "수자원 감소로 냉각수 공급 제한",
        "reputation_risk": "물 스트레스 대응 미흡 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 일사량 변화에 따른 ET0 및 수자원 가용량 추정",
        "Strategy Generation: 일사 패턴 고려한 용수 사용 최적화",
        "Report Generation: TCFD 물 스트레스 분석에서 일사량 영향 정량화"
      ],
      "interaction_with_other_data": {
        "TA": "고일사 + 고온 → ET0 최대화",
        "WS": "고일사 + 강풍 → ET0 급증"
      },
      "calculation_formula": "Rs ≈ SI × 0.0864 (MJ/m²/day) → 순복사량(Rn) 계산 → Radiation Term"
    },
    "RN": {
      "full_name": "강수량 (Rainfall)",
      "definition": "월 강수량",
      "unit": "mm",
      "data_source": "KMA 기후 데이터",
      "high_value_means": "무강수 시 유효강수량(P_eff) 음수 → TRWR 급감 → WSI 급등",
      "impacts_on": {
        "financial_risk": "무강수로 인한 P_eff 음수 → 수자원 고갈 → 용수비 급증",
        "operational_risk": "수자원 부족으로 생산 중단",
        "reputation_risk": "물 사용 제한 위반 시 법적 제재, ESG 평가 최하위"
      },
      "used_in": [
        "Impact Analysis: 강수 패턴 변화에 따른 수자원 가용량 및 WSI 추정",
        "Strategy Generation: 빗물 저장 시설 투자 우선순위",
        "Report Generation: TCFD 물 스트레스 분석에서 강수 변동성 영향 정량화"
      ],
      "interaction_with_other_data": {
        "TA": "무강수 + 고온 → P_eff 음수",
        "ET0": "무강수 + 고ET0 → P_eff 대폭 감소"
      },
      "calculation_formula": "P_eff = RN - ET0 (유효강수량)"
    },
    "BWS": {
      "full_name": "Baseline Water Stress (Aqueduct 4.0 물 스트레스 지수)",
      "definition": "WRI Aqueduct 4.0에서 제공하는 미래 물 스트레스 지수 (2030, 2050, 2080)",
      "unit": "무차원 (비율, 0~5 점수)",
      "data_source": "Aqueduct 4.0 (World Resources Institute)",
      "calculation_method": "WRI의 글로벌 물 스트레스 모델 기반. 미래 시나리오(SSP1-5)별 물 스트레스 예측치 제공",
      "high_value_means": "BWS ≥ 4.0 (Extremely High Water Stress)은 용수 공급이 수요의 80% 이상 소진되는 지역으로, 심각한 물 부족 위험을 의미합니다.",
      "impacts_on": {
        "financial_risk": "BWS ≥ 4.0 시 용수 공급 제한으로 생산 차질, 용수비 급등, 대체 수원 확보 비용 증가",
        "operational_risk": "물 스트레스 고위험 지역에서 냉각수/공정용수 공급 중단 → 설비 가동 중지",
        "reputation_risk": "물 스트레스 고위험 지역 입지로 CDP Water 최하위 등급, ESG 평가에서 수자원 리스크 관리 능력 부족 노출"
      },
      "used_in": [
        "Impact Analysis: 미래 물 스트레스 시나리오별 용수 공급 제약 정량화",
        "Strategy Generation: 고위험 지역 대체 수원 확보, 용수 재이용 시스템 투자 우선순위 결정",
        "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 물 스트레스 추이 분석, Aqueduct 4.0 BWS 데이터 인용"
      ],
      "interaction_with_other_data": {
        "Withdrawal": "BWS와 실제 용수이용량 조합 → 실제 물 스트레스 리스크 수준 판단",
        "Flow": "하천 유량 감소 시 BWS 악화 → 물 스트레스 증가",
        "WSI": "BWS는 미래 예측치, WSI는 현재 계산치 → 두 지표 비교로 물 스트레스 추세 파악"
      }
    },
    "Flow": {
      "full_name": "Daily River Flow (실시간 일유량)",
      "definition": "하천 관측소에서 측정한 일별 유량 데이터",
      "unit": "m³/s (초당 입방미터)",
      "data_source": "유량 관측소 (수자원공사, 환경부)",
      "calculation_method": "관측소별 일 유량 데이터 수집 → TRWR(Total Renewable Water Resources) 계산에 활용",
      "high_value_means": "유량이 낮을수록 가용 수자원 감소 → TRWR 하락 → WSI 상승. 극저유량(Q10 이하) 시 용수 공급 제한 가능",
      "impacts_on": {
        "financial_risk": "유량 감소 시 TRWR 하락 → WSI 상승 → 용수비 증가, 생산 차질",
        "operational_risk": "극저유량 시 취수 제한으로 냉각수/공정용수 공급 중단 → 설비 가동 중지",
        "reputation_risk": "유량 감소로 물 스트레스 악화 시 CDP Water 평가에서 수자원 관리 역량 부족 지적"
      },
      "used_in": [
        "Impact Analysis: 유량 변동에 따른 TRWR 및 WSI 변화 정량화, 극저유량 시나리오별 용수 공급 제약 분석",
        "Strategy Generation: 유량 모니터링 기반 용수 사용 최적화, 저유량 시즌 비상 용수 확보 계획 수립",
        "Report Generation: TCFD 물리적 리스크 섹션에서 유량 추세 분석, SSP 시나리오별 유량 감소 영향 정량화"
      ],
      "interaction_with_other_data": {
        "RN": "강수량 감소 → 유량 감소 → TRWR 하락",
        "ET0": "증발산량 증가 → 유효강수량 감소 → 유량 감소",
        "WSI": "유량 감소 → TRWR 하락 → WSI 상승",
        "BWS": "미래 유량 감소 예측은 BWS에 반영됨"
      }
    },
    "Withdrawal": {
      "full_name": "Water Withdrawal (용수이용량)",
      "definition": "지역별 연간 용수 취수량 (생활용수, 공업용수, 농업용수 포함)",
      "unit": "m³/year (연간 입방미터)",
      "data_source": "WAMIS (국가 수자원 관리 종합정보 시스템), Aqueduct 4.0 (미래 예측)",
      "calculation_method": "WAMIS: 과거 실측 용수이용량. Aqueduct 4.0: SSP 시나리오별 미래 용수 수요 예측",
      "high_value_means": "용수이용량이 높을수록 WSI 상승 → 물 스트레스 증가. Withdrawal > ARWR 시 수자원 고갈 위험",
      "impacts_on": {
        "financial_risk": "용수이용량 증가 → WSI 상승 → 용수비 급등, 용수 공급 제한 시 생산 차질로 매출 손실",
        "operational_risk": "용수이용량이 ARWR을 초과할 경우 강제 취수 제한 → 설비 가동 중단",
        "reputation_risk": "과도한 용수이용으로 CDP Water 평가에서 수자원 관리 미흡 판정, ESG 등급 하락, 지역 사회 반발"
      },
      "used_in": [
        "Impact Analysis: 용수이용량 증가율에 따른 WSI 변화 및 용수비 증가 정량화",
        "Strategy Generation: 용수 재이용률 목표 설정, 절수 설비 투자 ROI 계산, 용수이용량 감축 로드맵 수립",
        "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 용수 수요 증가 분석, 용수이용량 감축 목표 및 실적 공시"
      ],
      "interaction_with_other_data": {
        "WSI": "WSI = Withdrawal / ARWR → 용수이용량이 WSI의 분자. 용수이용량 10% 증가 시 WSI 10% 증가 (선형 관계)",
        "BWS": "Aqueduct 4.0 BWS 계산 시 미래 Withdrawal 예측치 사용",
        "Flow": "유량 감소 시 ARWR 하락 → 동일 Withdrawal에도 WSI 상승"
      }
    },
    "WSI": {
      "full_name": "Water Stress Index (물 스트레스 지수)",
      "definition": "용수이용량 / 가용 수자원 (ARWR)",
      "unit": "무차원 (비율)",
      "data_source": "WAMIS 용수이용량, 유량 관측소 데이터, Aqueduct 4.0 BWS (미래)",
      "calculation_method": "WSI = Withdrawal / ARWR, ARWR = TRWR × scale_factor × 0.63 (환경유지유량 차감)",
      "calculation_formula": "scale_factor = P_eff(year) / P_eff(baseline), P_eff = RN - ET0",
      "high_value_means": "WSI ≥ 0.8 (극심한 물 스트레스)은 용수 공급 제한, 생산 중단 위험을 의미합니다. WRI 기준 적용.",
      "bin_descriptions": {
        "bin_0 (WSI < 0.2, Low)": "낮은 물 스트레스 - 용수 가용량 풍부, 정상 공급. 용수비 안정. 손상률 1%",
        "bin_1 (WSI 0.2-0.4, Medium-Low)": "중하 물 스트레스 - 용수 수요 증가, 일부 계절 제약 가능. 용수비 소폭 상승. 손상률 3%",
        "bin_2 (WSI 0.4-0.8, Medium-High)": "중상 물 스트레스 - 용수 공급 제약 심화, 비상 절수 필요. 용수비 상당 상승, 생산 일부 조정. 손상률 8%",
        "bin_3 (WSI ≥ 0.8, High)": "높은 물 스트레스 - 용수 공급 심각 제한, 강제 절수 조치. 용수비 폭등, 생산 중단 위험. 손상률 15%"
      },
      "impacts_on": {
        "financial_risk": "WSI ≥ 0.8 시 용수 공급 제한으로 생산 차질, 용수비 급등. 손상률 15%, 낮은 물 스트레스(WSI < 0.2, 손상률 1%) 대비 15배 증가",
        "operational_risk": "용수 부족으로 냉각수 공급 중단 → 설비 가동 중지",
        "reputation_risk": "물 스트레스 대응 미흡 시 CDP Water 최하위 등급, ESG 평가에서 수자원 관리 능력 부족 노출, 투자자 신뢰 하락"
      },
      "used_in": [
        "Impact Analysis: WSI별 용수비 증가율 및 생산 차질 정량화",
        "Strategy Generation: 폐수 재이용 처리장(MBR 방식) 구축으로 용수 재이용률 80% 달성, 냉각수 순환율 95% 이상 향상 (블로다운 최소화), 중수도 시스템 도입 및 화장실/조경 용수 100% 전환, 스마트 용수계량 시스템으로 누수 실시간 탐지, 고위험 시기 용수 사용 제한 프로토콜 수립 (생산 라인별 우선순위)",
        "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 WSI 추이 분석, 물 스트레스 대응 전략 공시"
      ],
      "interaction_with_other_data": {
        "TA": "고온 → ET0 증가 → P_eff 감소 → scale_factor 하락 → WSI 상승",
        "RHM": "저습 → ET0 증가 → WSI 상승",
        "WS": "강풍 → ET0 증가 → WSI 상승",
        "SI": "고일사 → ET0 증가 → WSI 상승",
        "RN": "무강수 → P_eff 감소 → WSI 급등",
        "BWS": "미래 WSI 예측치 = Aqueduct 4.0 BWS",
        "Flow": "유량 감소 → TRWR 하락 → WSI 상승",
        "Withdrawal": "용수이용량 증가 → WSI 상승"
      }
    }      
  },
    "risk_score_data": {
      "Baseline_Water_Stress": {
        "data_name": "기초 물 스트레스 지수 (BWS)",
        "mapped_variables": [
          "baseline_water_stress (WRI_Aqueduct)",
          "water_supply_demand_balance (WAMIS_수급전망)"
        ],
        "scientific_evidence": "WRI Aqueduct Water Risk Atlas & 국가수자원관리종합정보시스템(WAMIS) 수급 통계_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, erd.md]",
        "contextual_meaning": "해당 지역의 '연간 가용 수자원 총량' 대비 '총 물 수요량(농업+공업+생활)'의 비율입니다. 기후와 무관하게, 지역 자체가 얼마나 '물 과소비' 상태인지(구조적 결핍)를 나타냅니다.",
        "threshold_interpretation": {
          "Extremely High (> 80%)": "가용 수자원의 80% 이상을 이미 끌어다 쓰고 있는 상태. 작은 가뭄에도 즉각적인 물 공급 대란이 발생하며, 신규 공장 증설 시 용수 확보 허가(Permit)가 반려될 가능성이 높음.",
          "High (40-80%)": "물 공급 경쟁이 치열한 상태. 갈수기에는 공업용수 취수 제한이 빈번함."
        },
        "financial_impact_type": {
          "Category": "Operational Cost & Regulatory Risk",
          "Mechanism": "물 가격(Water Tarif) 인상 및 취수 부담금 증가. 지자체의 '물 이용 부담금' 신설 또는 공업용수 사용 쿼터 축소로 인한 생산량 제한.",
          "Sensitivity": "반도체/디스플레이 등 세정 공정이 필수인 산업은 용수 공급 10% 감소 시 가동률 저하로 인한 고정비 부담 급증."
        },
        "mitigation_keyword": {
          "Engineering": "폐수 무방류 시스템(ZLD) 도입, 공정 냉각수 순환율 향상",
          "Strategic": "대체 수원(지하수, 해수담수화) 확보 및 물 리스크 헷징(Hedging) 계약"
        }
      },
      "Water_Dependency_Stress": {
        "data_name": "사업장 용수 의존도 (Exposure)",
        "mapped_variables": [
          "water_dependency (용수의존도_등급)",
          "main_purpose (건물주용도)"
        ],
        "scientific_evidence": "환경부 산업용수 수요관리 종합계획 및 건축물대장_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, fallback_values_comprehensive.md]",
        "contextual_meaning": "비즈니스 모델 자체가 물에 얼마나 의존적인지를 나타내는 지표입니다. 물 부족이 발생했을 때 '대체 불가능한 자원'인지 평가합니다.",
        "threshold_interpretation": {
          "High (발전/제조/데이터센터)": "냉각수나 공정수가 필수적인 시설. 단수 시 설비 과열(Overheating) 방지를 위해 강제 셧다운(Shutdown)이 불가피함.",
          "Low (물류/단순사무)": "생활용수 수준의 수요. 생수 공급 등으로 단기 대응 가능."
        },
        "financial_impact_type": {
          "Category": "Revenue at Risk (매출 리스크)",
          "Mechanism": "물 부족으로 인한 조업 중단 기간(Downtime) 동안의 매출 증발 및 납기 지연에 따른 배상금(Penalty) 발생.",
          "Implication": "ESG 평가 기관(MSCI, CDP Water)의 '물 관리' 등급 하락에 따른 투자 매력도 감소."
        },
        "mitigation_keyword": {
          "Engineering": "용수 사용 원단위(Intensity) 모니터링 및 누수 감지 센서 설치",
          "Operational": "워터 밸런스(Water Balance) 분석 및 절수 목표 수립"
        }
      },
      "Water_Storage_Capacity": {
        "data_name": "비상 용수 대응력 (Vulnerability)",
        "mapped_variables": [
          "has_water_storage (저수조유무)",
          "building_age (노후도)"
        ],
        "scientific_evidence": "건축물 설비 기준(저수조 설치 여부) 추정 및 노후 배관 효율 분석_231.물리적 리스크 스코어링 로직 정의_v0.3.docx]",
        "contextual_meaning": "외부 상수도 공급이 차단되었을 때, 자체적으로 버틸 수 있는 '버퍼(Buffer)' 용량 및 배관망의 효율성입니다.",
        "threshold_interpretation": {
          "High Vulnerability (저수조 없음 + 노후 배관)": "상수도 단수 즉시 물 공급이 중단되며(Zero Buffer), 노후 배관 누수로 인해 평시에도 수도 요금이 낭비되는 상태.",
          "Low Vulnerability (대용량 저수조 보유)": "수일간 자체 용수로 조업 유지 가능(Business Continuity 확보)."
        },
        "financial_impact_type": {
          "Category": "Business Continuity (사업 연속성) 비용",
          "Mechanism": "단수 발생 시 긴급 급수차(Water Truck) 섭외 비용 및 조업 중단 방어를 위한 예비비 지출.",
          "Opportunity": "노후 배관 교체 시 누수 저감으로 인한 즉각적인 수도 요금 절감 효과(ROI)."
        },
        "mitigation_keyword": {
          "Engineering": "비상용 저수조(Water Tank) 증설, 노후 급수관 갱생 공사",
          "Operational": "단수 시 비상 대응 매뉴얼(SOP) 수립 및 모의 훈련"
        }
    }
  },
},
"해수면 상승": {
    "risk_id": "sea_level_rise",
    "aal_data": {
        "ZOS": {
      "full_name": "Sea Surface Height (해수면 높이)",
      "definition": "해수면 높이 (미래 시나리오 기반)",
      "unit": "m",
      "data_source": "CMIP6 SSP 시나리오 데이터",
      "calculation_method": "SSP 시나리오별 미래 해수면 높이 추정",
      "high_value_means": "ZOS > 1.0m는 해안 지역 침수 위험을 의미하며, 해수 역류로 인한 지하 시설 침수 위험이 높습니다.",
      "bin_descriptions": {
        "bin_0 (침수 깊이 0-0.3m)": "경미 침수 - 지상층 일부 침수, 지하층 해수 역류 시작. 배수 가능. 손상률 2%",
        "bin_1 (침수 깊이 0.3-0.5m)": "중간 침수 - 지상 1층 침수 심화, 지하 주차장 침수. 전기 설비 위험. 손상률 8%",
        "bin_2 (침수 깊이 0.5-1.0m)": "심각 침수 - 1층 완전 침수, 지하 전체 침수. 전산/전기 설비 손상. 손상률 15%",
        "bin_3 (침수 깊이 ≥ 1.0m)": "극심 침수 - 2층까지 침수 위험, 지하 완전 수몰. 건물 구조 손상, 장기 복구. 손상률 35%"
      },
      "impacts_on": {
        "financial_risk": "해수면 상승으로 해안 자산 가치 하락, 침수 복구비 증가. 침수 깊이 ≥ 1.0m 시 손상률 35%, 경미 피해(0-0.3m, 손상률 2%) 대비 17.5배 증가. 침수 깊이 0.3m → 1.0m 증가 시 손상률 7.5배 (2% → 15%) 증가",
        "operational_risk": "해수 역류로 지하층 침수, 업무 중단",
        "reputation_risk": "해안 침수 대응 미흡 시 ESG 평가에서 기후 리스크 관리 능력 부족 노출, 투자자 우려 증가"
      },
      "used_in": [
        "Impact Analysis: ZOS별 침수 확률 및 자산 가치 하락 추정",
        "Strategy Generation: 해안 방조제 2.5m 높이 설치 및 월류 방지 게이트 구축, 지하층 방수벽 시공 및 역류 방지 밸브 설치, 중요 전기/통신 설비 2층 이상 이전, 해수 유입 감지 센서 및 자동 배수 펌프(500톤/시간) 설치, 해안 자산 재배치 로드맵 수립 (10년 이내)",
        "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 해수면 상승 영향 분석, 장기 적응 전략 공시"
      ],
      "interaction_with_other_data": {
        "baseline_zos": "과거 해수면 높이와 미래 시나리오 비교"
      }
    }    
  },
    "risk_score_data": {
      "SLR_Projection": {
        "data_name": "해수면 상승 예측치 (Hazard)",
        "mapped_variables": [
          "slr_cm (CMIP6_예측값)",
          "slr_increase_cm (기준년대비_상승량)"
        ],
        "scientific_evidence": "IPCC AR6 기반 CMIP6 전지구 모형 데이터 (SSP 시나리오별 예측)_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "기후변화로 인한 해수 열팽창과 빙하 융해로 인해 평균 해수면이 영구적으로 상승하는 정도입니다. (내륙 지역은 물리적 영향 없음으로 0.0 처리)",
        "threshold_interpretation": {
          "Critical (> 80cm)": "만조 시 해수면이 지반고에 근접하여 상시 침수 위협이 발생하며, 태풍 해일(Storm Surge) 발생 시 방어벽을 쉽게 월류(Overtopping)할 수 있는 단계.",
          "Warning (40~80cm)": "해안가 저지대의 배수 효율이 급격히 저하되어, 적은 강우량에도 배후지가 침수되는 '맑은 날의 홍수(Sunny Day Flooding)' 발생 가능."
        },
        "financial_impact_type": {
          "Category": "Asset Stranding (자산 좌초) 위협",
          "Mechanism": "부지의 영구 침수 예상 시 부동산 가치가 '0'으로 수렴하며, 담보 가치 하락으로 인한 대출 조기 상환 압박(Liquidity Risk) 발생.",
          "Sensitivity": "예상 상승치가 방조제 높이를 초과하는 시점(Tipping Point)부터 자산 가치 급락 시작."
        },
        "mitigation_keyword": {
          "Engineering": "해안 방벽(Seawall) 증축, 부지 성토(Land Elevation)",
          "Strategic": "장기적 자산 이전(Managed Retreat) 계획 수립"
        }
      },
      "Coastal_Proximity": {
        "data_name": "해안 근접도 (Exposure)",
        "mapped_variables": [
          "coastal_distance_m (해안거리)",
          "proximity_category (근접도범주)"
        ],
        "scientific_evidence": "V-World 해안선 벡터 데이터 및 공간 분석_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, erd.md]",
        "contextual_meaning": "물리적인 바다와의 거리입니다. 해수면 상승의 직접적인 침수 위험뿐만 아니라, 염해(Salt Damage)로 인한 설비 부식 가속화를 결정합니다.",
        "threshold_interpretation": {
          "Very High (< 100m)": "해안 최전방. 해수면 상승 및 파도 에너지의 직접 타격권이며, 염분으로 인한 철근 콘크리트 및 실외기 부식 속도가 내륙 대비 3배 이상 빠름.",
          "Medium (500m ~ 1km)": "직접 침수 위험은 낮으나, 해수면 상승으로 인한 지하수 염수 침투(Saltwater Intrusion) 영향권."
        },
        "financial_impact_type": {
          "Category": "Maintenance Cost (유지보수비) 증가",
          "Mechanism": "염해 방지를 위한 특수 도료 사용 및 설비 교체 주기 단축으로 인한 LCC(Life Cycle Cost) 증가.",
          "Cost": "해안 침식 방지 공사 분담금 발생 가능성."
        },
        "mitigation_keyword": {
          "Engineering": "내염성 자재 사용(Salt-resistant Materials), 주요 설비 옥내화",
          "Operational": "설비 세정 주기 단축"
        }
      },
      "Vertical_Vulnerability": {
        "data_name": "고도 및 지하공간 취약성 (Vulnerability)",
        "mapped_variables": [
          "elevation_m (해발고도)",
          "basement_floors (지하층수)"
        ],
        "scientific_evidence": "V-World DEM(수치표고모델) 및 건축물대장_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "해수면 상승 시 물이 들어올 수 있는 물리적 높이 한계선입니다. 해발고도가 낮을수록, 지하층이 깊을수록 '물 그릇' 효과로 인해 침수 피해가 증폭됩니다.",
        "threshold_interpretation": {
          "High Risk (해발 5m 미만 + 지하층 보유)": "미래 해수면 상승 시 만조 수위보다 낮아질 수 있는 위험 구간. 자연 배수가 불가능해지며 펌프 고장 시 즉각적 수몰 위험.",
          "Low Risk (해발 10m 이상)": "해수면 상승의 직접적 영향권에서 벗어난 안전 고도."
        },
        "financial_impact_type": {
          "Category": "Business Interruption & CAPEX",
          "Mechanism": "지하 기계실/전기실 침수 시 건물 기능 전체 마비. 이를 방지하기 위한 차수판 설치 및 배수 펌프 용량 증설 비용 발생.",
          "Implication": "침수 이력 발생 시 건물 보험료율 급등."
        },
        "mitigation_keyword": {
          "Engineering": "차수판(Flood Gate) 및 역류 방지 밸브 설치",
          "Administrative": "지하 공간 중요 자산의 지상층 이전(Relocation)"
        }
      }
    }
  },

   "하천 홍수": {
    "risk_id": "river_flood",
    "aal_data": {
      "RX1DAY": {
      "full_name": "Max 1-day Precipitation (일 최대 강수량)",
      "definition": "연중 1일 최대 강수량",
      "unit": "mm/day",
      "data_source": "KMA 극값지수",
      "calculation_method": "연도별 RX1DAY 값을 bin으로 분류 (고정 임계값 기반)",
      "high_value_means": "RX1DAY > 200mm는 대규모 하천 범람 위험을 의미하며, 건물 침수, 인프라 손상을 유발합니다.",
      "bin_descriptions": {
        "bin_0 (RX1DAY < Q80)": "일반 강우 - 하천 범람 위험 낮음. 정상 배수 가능. 손상률 1%",
        "bin_1 (RX1DAY Q80-Q90)": "중간 강우 - 하천 수위 상승, 일부 저지대 침수 가능성. 손상률 2%",
        "bin_2 (RX1DAY Q90-Q95)": "강한 강우 - 하천 범람 주의, 제방 월류 위험. 침수 대비 필요. 손상률 5%",
        "bin_3 (RX1DAY Q95-Q99)": "극심 강우 - 하천 범람 발생, 광범위 침수. 전산/자산 손실 위험 높음. 손상률 12%",
        "bin_4 (RX1DAY ≥ Q99)": "기록적 강우 - 대규모 하천 범람, 건물 1층 침수. 장기 복구, 물류 마비. 손상률 20%"
      },
      "impacts_on": {
        "financial_risk": "하천 범람 시 침수 복구비 및 자산 손실. RX1DAY > Q99 (상위 1% 강우) 시 손상률 20%, 상위 20% 강우(Q80-Q95, 손상률 2%) 대비 10배 증가. 대규모 홍수 시 복구 비용 수십억 원 규모",
        "operational_risk": "침수로 인한 전산장비 손실, 업무 중단, 물류 마비",
        "reputation_risk": "홍수 대응 실패로 TCFD 물리적 리스크 관리 능력 부족 노출, ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 강수량별 침수 확률 및 재무 손실 추정",
        "Strategy Generation: 하천 인접 부지 방수벽 1.5m 높이 설치, 건물 주변 배수로 확장 및 우수 저류조(500톤) 설치, 지하층 출입구 지수판(Flood Barrier) 및 역류 방지 밸브 설치, 전산실/전기실 1층 이상 이전 및 방수 처리, 홍수 조기경보 시스템 및 비상 대피 매뉴얼 구축",
        "Report Generation: TCFD 물리적 리스크 섹션에서 홍수 시나리오 분석, 적응 대책 공시"
      ],
      "interaction_with_other_data": {
        "baseline_rx1day": "과거 RX1DAY 추세를 미래 시나리오와 비교"
      }
    }
  },
    "risk_score_data": {
      "RX1DAY": {
        "data_name": "일 최대강수량 (RX1DAY)",
        "mapped_variables": [
          "rx1day (연최대1일강수량)",
          "rx5day (5일누적강수량)",
          "rain80 (호우일수)"
        ],
        "scientific_evidence": "KMA SSP 시나리오 데이터 & WMO ETCCDI 지표_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "하천 유역에 하루 동안 내리는 비의 최대 양입니다. 이 값이 하천의 설계빈도(Design Flood)를 초과하면 제방 월류(Overtopping) 위험이 발생합니다.",
        "threshold_interpretation": {
          "Extreme (> 300mm)": "100년 빈도 이상의 대홍수 수준. 주요 국가 하천의 제방 안전 범위를 위협하며, 저지대 제내지(Levee-protected area)의 광범위한 침수가 확실시됨.",
          "High (200~300mm)": "호우 경보 수준. 소하천 및 지류의 범람 위험이 급증함."
        },
        "financial_impact_type": {
          "Category": "Asset Damage (자산 손실) & Business Interruption",
          "Mechanism": "대규모 침수로 인한 원자재/재고 전손(Write-off) 및 복구 기간(수주~수개월) 동안의 매출 공백.",
          "Sensitivity": "침수 심도(Inundation Depth) 10cm 증가 시 복구 비용이 비선형적으로 급증."
        },
        "mitigation_keyword": {
          "Engineering": "차수벽(Flood Wall) 설치, 중요 자산의 수직 이전(2층 이상 배치)",
          "Operational": "침수 예상 시 설비 가동 중단(Shutdown) 및 주요 물품 대피 매뉴얼 가동"
        }
      },
      "River_Proximity": {
        "data_name": "하천 인접도 (Exposure)",
        "mapped_variables": [
          "river_distance_m (하천거리)",
          "floodplain_zone (홍수범람구역_여부)"
        ],
        "scientific_evidence": "환경부 하천망 데이터 및 V-World 지형 분석_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, 02_VWorld_API.md]",
        "contextual_meaning": "사업장과 하천 제방 사이의 물리적 거리입니다. 범람 발생 시 물이 도달하는 시간(Warning Time)과 유속(Velocity)을 결정하는 핵심 입지 요인입니다.",
        "threshold_interpretation": {
          "Very High (< 100m)": "제방 붕괴 시 즉시 침수되는 '고위험 구역'. 빠른 유속으로 인해 건물의 구조적 파손이나 토사 유입 피해가 동반될 가능성 높음.",
          "Safe (> 1km)": "하천 범람의 직접적인 영향권에서 벗어난 안전 지대."
        },
        "financial_impact_type": {
          "Category": "Insurance Risk (보험 리스크) & Land Value",
          "Mechanism": "풍수해보험 가입 거절(Uninsurable) 또는 요율 할증(Premium Hike) 대상 지역. 홍수위험지구 지정 시 토지 가치 하락 위험."
        },
        "mitigation_keyword": {
          "Engineering": "사업장 경계 방수벽 보강, 배수 펌프장 용량 증설",
          "Administrative": "지자체 하천 정비 계획 모니터링"
        }
      },
      "Basement_Vulnerability": {
        "data_name": "지하공간 취약성 (Vulnerability)",
        "mapped_variables": [
          "basement_floors (지하층수)",
          "first_floor_elevation (1층고도)"
        ],
        "scientific_evidence": "건축물대장 및 V-World DEM 고도 데이터_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, fallback_values_comprehensive.md]",
        "contextual_meaning": "홍수 발생 시 물이 가장 먼저 유입되고 배수가 불가능한 구조적 약점입니다. 전기/기계실 등 핵심 설비가 지하에 위치할 경우 리스크가 극대화됩니다.",
        "threshold_interpretation": {
          "Critical (지하층 보유 + 저지대)": "외부 수위 상승 시 수압으로 인해 지하층이 고립(Trap)되며, 펌프 용량 초과 시 '물탱크'처럼 변해 설비 전손 및 인명 피해 초래.",
          "Low Risk (필로티 구조/고지대)": "물리적 높이(Freeboard) 확보로 침수 피해 최소화."
        },
        "financial_impact_type": {
          "Category": "System Failure (시스템 마비) & Liability",
          "Mechanism": "수변전 설비 침수 시 건물 전체 정전(Blackout) 및 기능 마비. 인명 피해 발생 시 중대재해처벌법 등 법적 배상 책임(Liability) 발생.",
          "Cost": "침수 후 오염 제거(Clean-up) 및 설비 전면 교체 비용."
        },
        "mitigation_keyword": {
          "Engineering": "지하 주차장 입구 차수판(Flood Gate) 설치, 침수 감지 센서 및 자동 배수 시스템",
          "Strategic": "지하 중요 설비(UPS, 발전기)의 지상화(Relocation)"
        }
      }
    }   
  },
  "도시 홍수": {
     "risk_id": "urban_flood",
     "aal_data": {
      "RAIN80": {
      "full_name": "일 최대 80mm 이상 강우 발생 일수",
      "definition": "연중 일 강수량이 80mm 이상인 날의 일수",
      "unit": "일/년 (days)",
      "data_source": "KMA 극값지수",
      "calculation_method": "연도별 RAIN80 일수를 bin으로 분류",
      "high_value_means": "RAIN80 > 10일은 도시 침수 고빈도 지역을 의미하며, 하수도 역류, 저지대 침수 빈발을 나타냅니다.",
      "bin_descriptions": {
        "bin_0 (RAIN80 0일)": "호우 없음 - 도시 침수 위험 없음. 정상 배수. 손상률 0.1%",
        "bin_1 (RAIN80 1-2일)": "저빈도 호우 - 연 1-2회 침수 가능성. 일시적 침수, 빠른 배수. 손상률 3%",
        "bin_2 (RAIN80 3-4일)": "중빈도 호우 - 연 3-4회 침수. 하수도 역류 시작, 지하 침수 반복. 손상률 12%",
        "bin_3 (RAIN80 5-7일)": "고빈도 호우 - 연 5-7회 침수. 하수도 포화, 지하 상습 침수. 손상률 30%",
        "bin_4 (RAIN80 ≥ 8일)": "극고빈도 호우 - 연 8회 이상 침수. 배수 시스템 완전 포화, 만성적 침수 피해. 손상률 45%"
      },
      "impacts_on": {
        "financial_risk": "도시 침수 복구비 및 영업 중단 손실. RAIN80 ≥ 8일 (고빈도 홍수) 시 손상률 45%, 저빈도(1-2일, 손상률 3%) 대비 15배 증가. 호우일수 3-4일에서 5-7일로 증가 시 손상률 2.5배 증가. 반복적 침수 시 연간 수억 원 손실 가능",
        "operational_risk": "하수도 역류로 인한 위생 문제, 지하 시설 침수",
        "reputation_risk": "도시 침수 대응 미흡으로 ESG 평가에서 기후 회복력 부족 지적"
      },
      "used_in": [
        "Impact Analysis: RAIN80 빈도별 침수 확률 및 손실액 추정",
        "Strategy Generation: 건물 내 독립 배수 펌프(300톤/시간) 및 비상 발전기 설치, 지하층 출입구 자동 차수판(높이 1.2m) 설치, 하수도 역류 방지 밸브 및 우수 분리 배수 시스템 구축, 투수성 포장 도입 및 빗물 침투 면적 30% 이상 확보, 침수 감지 센서 및 실시간 알림 시스템 구축",
        "Report Generation: TCFD 물리적 리스크 섹션에서 도시 침수 대응 계획 공시"
      ],
      "interaction_with_other_data": {
        "baseline_rain80": "과거 RAIN80 추세 분석"
      }
    }   
  },
     "risk_score_data": {
        "RX1DAY_Urban": {
        "data_name": "도시 설계빈도 초과 강우량 (Hazard)",
        "mapped_variables": [
          "rx1day (연최대1일강수량)",
          "rx1hr_estimate (시간당최대강수량_추정)"
        ],
        "scientific_evidence": "KMA SSP 시나리오 데이터 & 환경부 하수도 설계 기준_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "도시의 우수관(Sewer System)이 감당할 수 있는 한계를 시험하는 '극한 강우 강도'입니다. 한국의 통상적인 도심지 배수 설계 용량(시간당 95mm 내외)과 비교하여 평가합니다.",
        "threshold_interpretation": {
          "Critical (> 200mm/day)": "도시 배수 시스템의 처리 용량을 초과하는 수준. 맨홀 역류 및 저지대 도로 침수가 발생하며, 지하 주차장으로 빗물이 급격히 유입되는 '폭포수 현상' 발생 위험.",
          "Warning (120~200mm/day)": "국지적인 내수 침수 발생 가능 구간."
        },
        "financial_impact_type": {
          "Category": "Business Interruption (조업 중단) & Liability",
          "Mechanism": "도로 침수로 인한 물류 마비 및 직원 출퇴근 불가로 인한 생산 차질. 지하 공간 침수 시 복구 비용(Clean-up) 및 건물 내 입주사 배상 책임 발생.",
          "Sensitivity": "시간당 100mm 이상 강우 시 지하 공간 침수 속도는 분당 수 cm에 달해 골든타임 확보 불가능."
        },
        "mitigation_keyword": {
          "Engineering": "차수판(Flood Gate) 자동화, 배수 펌프 비상 전원 확보",
          "Operational": "침수 경보 시 차량 이동 및 지하 공간 폐쇄 매뉴얼"
        }
      },
      "Impervious_Surface": {
        "data_name": "불투수면 비율 (Exposure)",
        "mapped_variables": [
          "impervious_surface_ratio (불투수면비율)",
          "urban_intensity (도시화강도)"
        ],
        "scientific_evidence": "환경부 토지피복도(Landcover) 기반 공간 분석_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "빗물이 땅으로 스며들지 못하고 표면으로 흘러넘치는 비율입니다. 아스팔트와 콘크리트로 덮인 도심지는 빗물을 '순간적으로' 저지대로 모이게 하는 가속 페달 역할을 합니다.",
        "threshold_interpretation": {
          "Very High (> 80%)": "완전 포장된 도심지(CBD). 빗물 유출 계수가 0.9에 육박하여, 동일 강우량일지라도 녹지 대비 침수 도달 시간이 절반 이하로 단축됨.",
          "Moderate (50~80%)": "주거 밀집 지역. 부분적인 녹지가 있으나 배수 불량 시 침수 위험 상존."
        },
        "financial_impact_type": {
          "Category": "Regulatory Compliance (규제 준수) 비용",
          "Mechanism": "지자체의 '물순환 회복 조례' 등에 따른 투수성 포장 교체 의무화 및 '빗물세(Stormwater Fee)' 도입 시 비용 부담 증가.",
          "Opportunity": "LID(저영향개발) 기법 적용 시 친환경 건축물 인증 가산점 획득."
        },
        "mitigation_keyword": {
          "Engineering": "투수성 블록 교체, 침투 도랑(Infiltration Trench) 설치",
          "Nature-based": "옥상 녹화 및 빗물 정원(Rain Garden) 조성"
        }
      },
      "Basement_Risk": {
        "data_name": "지하공간 침수 취약성 (Vulnerability)",
        "mapped_variables": [
          "basement_floors (지하층수)",
          "building_age (건축연도)"
        ],
        "scientific_evidence": "건축물대장 지하층 정보 & 행정안전부 지하공간 침수방지 가이드라인_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, fallback_values_comprehensive.md]",
        "contextual_meaning": "도시 홍수 시 가장 먼저 물이 차오르고 배수가 불가능한 '구조적 함정(Trap)'입니다. TCFD 평가에서 도시 홍수 취약성을 결정하는 가장 결정적인 가중치(Weight) 요소입니다.",
        "threshold_interpretation": {
          "Extreme Risk (지하층 보유 + 차수판 미설치)": "도로 노면수 유입 시 수압으로 인해 출입문 개방이 불가능해지며, 전기실/기계실 침수 시 건물 전체 기능(전력, 통신, 엘리베이터) 마비.",
          "Safe (지상 건물)": "내수 침수로 인한 직접적인 자산 손실 위험 낮음."
        },
        "financial_impact_type": {
          "Category": "Asset Total Loss (자산 전손) & Legal Risk",
          "Mechanism": "지하 주차 차량 및 고가 설비 침수 피해액 막대함. 인명 피해 발생 시 기업 평판(Reputation) 치명타 및 법적 제재.",
          "Cost": "침수 방지 시설 설치를 위한 CAPEX 및 침수 감지 센서 유지보수 비용."
        },
        "mitigation_keyword": {
          "Engineering": "물막이판(차수판) 및 역류방지밸브 설치 (필수)",
          "Strategic": "지하 중요 설비의 지상층 이전(Relocation) 또는 방수 격벽 설치"
        }
      }
    }   
  },

  "태풍": {
     "risk_id": "typhoon",
     "aal_data": {
        "lon": {
      "full_name": "태풍 중심 경도 (Longitude)",
      "definition": "태풍 중심의 경도 좌표 (베스트트랙 시점별 데이터)",
      "unit": "도 (degree)",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "사이트 경도와의 거리 계산에 사용. 거리가 가까울수록 태풍 영향 증가",
      "impacts_on": {
        "financial_risk": "태풍 직접 영향 시 건물 손상, 자산 손실",
        "operational_risk": "태풍 영향권 내 업무 중단",
        "reputation_risk": "태풍 대응 실패 시 ESG 평가에서 기후 회복력 부족 노출"
      },
      "used_in": [
        "Impact Analysis: 태풍 경로와 사이트 거리 기반 영향 확률 계산",
        "Strategy Generation: 태풍 대비 시설 보강 우선순위",
        "Report Generation: TCFD 물리적 리스크 섹션에서 태풍 노출도 분석"
      ],
      "interaction_with_other_data": {
        "lat": "lon + lat → 사이트와 태풍 중심 간 거리 계산 (km 단위 변환)",
        "gale_long/gale_short/gale_dir": "거리 + 강풍 타원 → 영향권 판정"
      },
      "calculation_formula": "dx_km = (site_lon - typhoon_lon) × 111km × cos(평균위도)"
    },
    "lat": {
      "full_name": "태풍 중심 위도 (Latitude)",
      "definition": "태풍 중심의 위도 좌표 (베스트트랙 시점별 데이터)",
      "unit": "도 (degree)",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "사이트 위도와의 거리 계산에 사용. 거리가 가까울수록 태풍 영향 증가",
      "impacts_on": {
        "financial_risk": "태풍 직접 영향 시 건물 손상, 자산 손실",
        "operational_risk": "태풍 영향권 내 업무 중단",
        "reputation_risk": "태풍 대응 실패 시 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 태풍 경로와 사이트 거리 기반 영향 확률 계산",
        "Strategy Generation: 태풍 대비 시설 보강 우선순위",
        "Report Generation: TCFD 물리적 리스크 섹션에서 태풍 노출도 분석"
      ],
      "interaction_with_other_data": {
        "lon": "lon + lat → 사이트와 태풍 중심 간 거리 계산",
        "storm_long/storm_short/storm_dir": "거리 + 폭풍 타원 → 영향권 판정"
      },
      "calculation_formula": "dy_km = (site_lat - typhoon_lat) × 111km"
    },
    "grade": {
      "full_name": "태풍 등급 (Typhoon Grade)",
      "definition": "태풍 강도 등급 (TD, TS, STS, TY)",
      "possible_values": ["TD (Tropical Depression, 열대저압부)", "TS (Tropical Storm, 열대폭풍)", "STS (Severe Tropical Storm, 강한열대폭풍)", "TY (Typhoon, 태풍)"],
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "TY (태풍) 등급은 최대 풍속 33m/s 이상으로 건물 구조 손상 위험이 높습니다.",
      "impacts_on": {
        "financial_risk": "TY 등급 태풍 직접 영향 시 건물 손상, 복구 비용 증가",
        "operational_risk": "TY 등급 태풍 시 업무 전면 중단, 장기 복구 기간",
        "reputation_risk": "강력한 태풍 대응 실패 시 ESG 평가에서 기후 회복력 미흡 노출"
      },
      "used_in": [
        "Impact Analysis: 태풍 등급별 피해 규모 추정",
        "Strategy Generation: 등급별 대응 매뉴얼 수립",
        "Report Generation: TCFD 물리적 리스크 섹션에서 태풍 강도 시나리오 분석"
      ],
      "interaction_with_other_data": {
        "storm_long/storm_short": "TY + 폭풍 타원 내 → bin_inst = 3 (최고 영향)",
        "gale_long/gale_short": "TS + 강풍 타원 내 → bin_inst = 1"
      },
      "calculation_formula": "bin_inst 결정: grade + 타원 영향권 → 0 (영향 없음) ~ 3 (TY급 영향)"
    },
    "gale_long": {
      "full_name": "강풍 타원 장반경 (Gale Ellipse Semi-major Axis)",
      "definition": "강풍 영향권 타원의 장반경 (풍속 15m/s 이상 영역)",
      "unit": "km",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "강풍 타원 내 진입 시 풍속 15m/s 이상, 간판/유리창 파손 위험",
      "impacts_on": {
        "financial_risk": "강풍 영향권 내 외벽 손상, 간판 파손",
        "operational_risk": "강풍으로 외부 작업 중단",
        "reputation_risk": "태풍 피해로 고객 불만, ESG 평가 영향"
      },
      "used_in": [
        "Impact Analysis: 강풍 영향권 면적 및 피해 확률 계산",
        "Strategy Generation: 강풍 대비 외벽 보강 우선순위",
        "Report Generation: TCFD 태풍 리스크 분석에서 강풍 영향 범위 정량화"
      ],
      "interaction_with_other_data": {
        "gale_short/gale_dir": "장반경 + 단반경 + 회전각 → 타원 정의",
        "grade": "강풍 타원 + TS/STS/TY → bin_inst = 1"
      },
      "calculation_formula": "is_inside_ellipse(dx, dy, gale_long, gale_short, gale_dir) → 타원 내부 판정"
    },
    "gale_short": {
      "full_name": "강풍 타원 단반경 (Gale Ellipse Semi-minor Axis)",
      "definition": "강풍 영향권 타원의 단반경",
      "unit": "km",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "강풍 타원 형태 정의에 사용",
      "impacts_on": {
        "financial_risk": "강풍 영향권 내 외벽 손상",
        "operational_risk": "강풍으로 외부 작업 중단",
        "reputation_risk": "태풍 피해로 ESG 평가 영향"
      },
      "used_in": [
        "Impact Analysis: 강풍 영향권 면적 계산",
        "Strategy Generation: 강풍 대비 시설 보강",
        "Report Generation: TCFD 태풍 리스크 분석"
      ],
      "interaction_with_other_data": {
        "gale_long/gale_dir": "타원 정의"
      },
      "calculation_formula": "타원 방정식: (x_rot/gale_long)² + (y_rot/gale_short)² ≤ 1"
    },
    "gale_dir": {
      "full_name": "강풍 타원 회전 방향 (Gale Ellipse Direction)",
      "definition": "강풍 영향권 타원의 회전 각도 (북쪽 기준 시계방향)",
      "unit": "도 (degree)",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "타원 회전 각도, 태풍 진행 방향 반영",
      "impacts_on": {
        "financial_risk": "강풍 영향권 내 외벽 손상",
        "operational_risk": "강풍으로 외부 작업 중단",
        "reputation_risk": "태풍 피해로 ESG 평가 영향"
      },
      "used_in": [
        "Impact Analysis: 강풍 영향권 판정",
        "Strategy Generation: 강풍 대비 시설 보강",
        "Report Generation: TCFD 태풍 리스크 분석"
      ],
      "interaction_with_other_data": {
        "gale_long/gale_short": "타원 정의"
      },
      "calculation_formula": "회전 변환: x_rot = dx × cos(θ) + dy × sin(θ), θ = gale_dir (라디안)"
    },
    "storm_long": {
      "full_name": "폭풍 타원 장반경 (Storm Ellipse Semi-major Axis)",
      "definition": "폭풍 영향권 타원의 장반경 (풍속 25m/s 이상 영역)",
      "unit": "km",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "폭풍 타원 내 진입 시 풍속 25m/s 이상, 건물 구조 손상 위험",
      "impacts_on": {
        "financial_risk": "폭풍 영향권 내 건물 구조 손상, 대규모 복구 비용",
        "operational_risk": "폭풍으로 업무 전면 중단",
        "reputation_risk": "폭풍 피해로 ESG 평가 대폭 하락"
      },
      "used_in": [
        "Impact Analysis: 폭풍 영향권 면적 및 피해 규모 추정",
        "Strategy Generation: 구조 보강 투자 우선순위",
        "Report Generation: TCFD 태풍 리스크 분석에서 폭풍 영향 범위 정량화"
      ],
      "interaction_with_other_data": {
        "storm_short/storm_dir": "장반경 + 단반경 + 회전각 → 타원 정의",
        "grade": "폭풍 타원 + TY → bin_inst = 3, STS → bin_inst = 2"
      },
      "calculation_formula": "is_inside_ellipse(dx, dy, storm_long, storm_short, storm_dir) → 타원 내부 판정"
    },
    "storm_short": {
      "full_name": "폭풍 타원 단반경 (Storm Ellipse Semi-minor Axis)",
      "definition": "폭풍 영향권 타원의 단반경",
      "unit": "km",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "폭풍 타원 형태 정의에 사용",
      "impacts_on": {
        "financial_risk": "폭풍 영향권 내 건물 구조 손상",
        "operational_risk": "폭풍으로 업무 전면 중단",
        "reputation_risk": "폭풍 피해로 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 폭풍 영향권 면적 계산",
        "Strategy Generation: 구조 보강 투자",
        "Report Generation: TCFD 태풍 리스크 분석"
      ],
      "interaction_with_other_data": {
        "storm_long/storm_dir": "타원 정의"
      },
      "calculation_formula": "타원 방정식: (x_rot/storm_long)² + (y_rot/storm_short)² ≤ 1"
    },
    "storm_dir": {
      "full_name": "폭풍 타원 회전 방향 (Storm Ellipse Direction)",
      "definition": "폭풍 영향권 타원의 회전 각도 (북쪽 기준 시계방향)",
      "unit": "도 (degree)",
      "data_source": "KMA 태풍 Best Track API",
      "high_value_means": "타원 회전 각도, 태풍 진행 방향 반영",
      "impacts_on": {
        "financial_risk": "폭풍 영향권 내 건물 구조 손상",
        "operational_risk": "폭풍으로 업무 전면 중단",
        "reputation_risk": "폭풍 피해로 ESG 평가 하락"
      },
      "used_in": [
        "Impact Analysis: 폭풍 영향권 판정",
        "Strategy Generation: 구조 보강 투자",
        "Report Generation: TCFD 태풍 리스크 분석"
      ],
      "interaction_with_other_data": {
        "storm_long/storm_short": "타원 정의"
      },
      "calculation_formula": "회전 변환: x_rot = dx × cos(θ) + dy × sin(θ), θ = storm_dir (라디안)"
    },
    "S_tc": {
      "full_name": "태풍 누적 노출 지수 (Typhoon Cumulative Exposure Index)",
      "definition": "연도별 태풍 영향의 누적 가중 지수",
      "unit": "무차원 (지수)",
      "data_source": "KMA 베스트트랙 API 기반 계산",
      "calculation_method": "시점별 bin_inst에 가중치(w_tc) 적용하여 연도별 누적",
      "calculation_formula": "S_tc(year) = Σ w_tc[bin_inst(storm, τ)], w_tc = [0, 1, 3, 7]",
      "high_value_means": "S_tc > 15는 연간 매우 강한 태풍 노출을 의미하며, 건물 구조 손상 위험이 높습니다.",
      "bin_descriptions": {
        "bin_0 (S_tc 0-5)": "약한 태풍 노출 - 태풍 영향 미미 또는 약한 강풍권만 통과. 경미한 외벽 손상 가능. 손상률 2%",
        "bin_1 (S_tc 6-10)": "중간 태풍 노출 - 태풍 간접 영향 또는 TS급 직접 통과. 외벽/지붕 일부 손상, 유리창 파손. 손상률 8%",
        "bin_2 (S_tc 11-15)": "강한 태풍 노출 - STS급 직접 통과 또는 TY급 인접. 지붕 파손, 외벽 손상, 간판 탈락. 손상률 18%",
        "bin_3 (S_tc > 15)": "매우 강한 태풍 노출 - TY급 직접 통과 또는 복수 강력 태풍. 건물 구조 손상, 대규모 복구 필요. 손상률 30%"
      },
      "impacts_on": {
        "financial_risk": "S_tc > 15 시 건물 손상으로 대규모 복구 비용 발생, 손상률 30%. 약한 노출(0-5, 손상률 2%) 대비 15배 증가. TY급 영향 시점은 TS급 대비 가중치 7배",
        "operational_risk": "S_tc > 15 시 업무 중단 장기화",
        "reputation_risk": "반복적 태풍 피해로 ESG 평가에서 기후 회복력 부족 노출, 투자자 신뢰 하락"
      },
      "used_in": [
        "Impact Analysis: S_tc별 피해 규모 및 복구 비용 추정",
        "Strategy Generation: 건물 외벽 내풍 설계 기준 풍속 50m/s로 상향 보강, 지붕 고정 볼트 증설 및 방수층 이중화, 유리창 강화유리 교체 및 보호필름 부착, 옥외 간판/시설물 철거 또는 내풍 구조 보강, 태풍 예보 시 비상 점검 체크리스트 및 신속 대응팀 운영",
        "Report Generation: TCFD 물리적 리스크 섹션에서 SSP 시나리오별 S_tc 추이 분석 (IPCC AR6 기반 1°C당 태풍 강도 4% 증가 반영)"
      ],
      "interaction_with_other_data": {
        "lon/lat": "거리 계산 → 타원 영향권 판정 → bin_inst → S_tc",
        "grade": "등급 + 타원 → bin_inst 결정",
        "gale_*/storm_*": "타원 영향권 → bin_inst → 가중치 적용",
        "climate_change": "기온 1°C 상승 시 태풍 강도 4% 증가 (IPCC AR6 기준). 2°C 온난화 시 태풍 강도 최대 8% 증가"
      }
    } 
  },
     "risk_score_data": {
        "TCI": {
        "data_name": "태풍 복합 위험도 (TCI)",
        "mapped_variables": [
          "max_wind_speed_ms (최대풍속)",
          "max_precipitation_mm (동반강수량)",
          "typhoon_days (영향일수)"
        ],
        "scientific_evidence": "기상청 태풍 베스트트랙 및 KMA SSP 시나리오 데이터 (풍속+강수+빈도 가중 결합)_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, real_data_verification.md]",
        "contextual_meaning": "단순히 바람만 센 것이 아니라, 건물 외장재를 파손시키는 '물리적 타격력(Wind)'과 내부 침수를 유발하는 '집중호우(Rain)'가 결합된 복합 파괴력 지수입니다.",
        "threshold_interpretation": {
          "Extreme (> 0.8)": "초강력 태풍(Super Typhoon)급 타격 예상. 최대 풍속 40m/s 이상으로 간판/지붕이 뜯겨나가고, 400mm 이상의 폭우로 저지대 완전 침수가 동반됨.",
          "Moderate (0.2 ~ 0.4)": "일반적인 중형 태풍. 시설물 고정 조치로 대응 가능한 수준."
        },
        "financial_impact_type": {
          "Category": "Asset Damage (파손) 및 Liability (배상책임)",
          "Mechanism": "외벽/유리창 파손으로 인한 복구 비용(CAPEX) 발생 및 비산물(Flying Debris)이 인근 차량/행인을 타격할 경우 법적 배상 책임 발생.",
          "Sensitivity": "풍속이 2배 증가하면 건물에 가해지는 풍압(Wind Pressure)은 4배(제곱)로 증가하여 구조적 손상 위험 급증."
        },
        "mitigation_keyword": {
          "Engineering": "강풍 대비 창호 보강(Shatter-proof Glass), 지붕/외장재 결속력 강화",
          "Operational": "태풍 내습 전 옥외 적재물 실내 이동 및 고정 상태 점검"
        }
      },
      "Coastal_Proximity_Wind": {
        "data_name": "해안 강풍 노출도 (Exposure)",
        "mapped_variables": [
          "coastal_distance_m (해안거리)",
          "proximity_category (근접도범주)"
        ],
        "scientific_evidence": "V-World 지형 데이터 및 기상청 태풍 백서_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, 02_VWorld_API.md]",
        "contextual_meaning": "태풍의 에너지가 지면 마찰로 약화되기 전, 가장 강력한 상태의 바람과 해일(Storm Surge)을 맞닥뜨리는 물리적 위치입니다.",
        "threshold_interpretation": {
          "Very High (< 5km)": "태풍 상륙 직후 최대 풍속 구간. 해일로 인한 해수 범람 위험이 동반되며, 염분(Salt Spray)이 섞인 강풍으로 설비 부식 가속화.",
          "Low (> 50km)": "내륙 깊숙이 위치하여 지형 마찰로 풍속이 30% 이상 감쇄된 상태."
        },
        "financial_impact_type": {
          "Category": "Insurance Premium (보험료) 및 Total Loss",
          "Mechanism": "해안가 사업장은 풍수해보험 요율이 가장 높게 책정되며, 폭풍해일 동반 시 자산 전손(Total Loss) 리스크 상존.",
          "Implication": "물류/항만 시설의 경우 선적 지연에 따른 공급망 차질(Supply Chain Disruption) 발생."
        },
        "mitigation_keyword": {
          "Engineering": "해안 방재림 조성, 내염성/내풍압 설계 적용",
          "Administrative": "재난 위기 경보 '심각' 단계 시 필수 인원 외 전원 대피"
        }
      },
      "Structural_Resistance": {
        "data_name": "건물 내풍 취약성 (Vulnerability)",
        "mapped_variables": [
          "structure_type (구조)",
          "building_height (층수/높이)",
          "building_age (건축연도)"
        ],
        "scientific_evidence": "건축물대장 및 건축구조기준(KDS 41 10 15)_231.물리적 리스크 스코어링 로직 정의_v0.3.docx, 01_공공데이터포털_API.md]",
        "contextual_meaning": "강한 바람 압력을 건물이 얼마나 버틸 수 있는가입니다. 특히 고층 건물은 상층부 풍속이 강하고, 경량 구조는 바람에 날아갈 위험이 큽니다.",
        "threshold_interpretation": {
          "High Vulnerability (목조/경량철골 OR 초고층)": "경량 구조는 강풍에 지붕/벽체가 뜯겨나갈 위험(Vulnerability +30점). 초고층(10층 이상)은 강한 풍압과 진동으로 외벽 유리 파손 및 거주성 저하 우려.",
          "Low Vulnerability (저층 철근콘크리트)": "구조적 강성(Rigidity)이 높아 강풍 피해 미미."
        },
        "financial_impact_type": {
          "Category": "Maintenance & Retrofit Cost",
          "Mechanism": "노후된 외장재 탈락으로 인한 2차 피해 복구비 및 고층 건물 진동 제어(TMD 등)를 위한 설비 투자 비용.",
          "Risk": "샌드위치 패널 등 경량 자재 사용 공장은 파손 시 조업 복구까지 장기간 소요."
        },
        "mitigation_keyword": {
          "Engineering": "지붕 트러스 보강, 고층 건물 풍동 실험(Wind Tunnel Test) 기반 외장 설계",
          "Financial": "시설물 배상 책임 보험 한도 증액"
        }
      }
    }   
  },
}