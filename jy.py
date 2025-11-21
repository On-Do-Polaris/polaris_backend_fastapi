import sys
import yaml


def transform_node(node):
    # dict인 경우
    if isinstance(node, dict):
        # 1) openapi 버전 수정
        if "openapi" in node:
            val = str(node["openapi"])
            if val.startswith("3.1."):
                node["openapi"] = "3.0.3"

        # 2) anyOf + null → nullable 변환
        if "anyOf" in node and isinstance(node["anyOf"], list):
            anyof_list = node["anyOf"]

            # null type 있는지 찾기
            null_indices = [
                i for i, item in enumerate(anyof_list)
                if isinstance(item, dict) and item.get("type") == "null"
            ]

            if len(null_indices) == 1 and len(anyof_list) == 2:
                null_idx = null_indices[0]
                other_idx = 1 - null_idx
                other = anyof_list[other_idx]

                # 케이스 1: $ref + null
                if isinstance(other, dict) and "$ref" in other:
                    # 기존 키(제목/설명 등)를 유지하기 위해 저장
                    saved = {
                        k: v for k, v in node.items()
                        if k not in ("anyOf", "allOf", "nullable")
                    }
                    node.clear()
                    node["allOf"] = [{"$ref": other["$ref"]}]
                    node["nullable"] = True
                    # saved에 있는 title/description 등 다시 덮어쓰기 (이미 있는 키는 유지)
                    for k, v in saved.items():
                        if k not in node:
                            node[k] = v

                # 케이스 2: type + null
                elif isinstance(other, dict) and "type" in other:
                    saved = {
                        k: v for k, v in node.items()
                        if k not in ("anyOf", "type", "format", "items",
                                     "enum", "properties", "allOf", "oneOf",
                                     "nullable")
                    }
                    node.clear()
                    # other의 스키마 구조 복사 (type, format, items 등)
                    for k, v in other.items():
                        node[k] = v
                    node["nullable"] = True
                    # saved의 title/description 등 다시 추가
                    for k, v in saved.items():
                        if k not in node:
                            node[k] = v

                # 변환 후에도 더 깊이 탐색
                for v in list(node.values()):
                    transform_node(v)
                return  # 여기서 끝

        # dict의 나머지 자식들도 순회
        for v in list(node.values()):
            transform_node(v)

    # 리스트인 경우
    elif isinstance(node, list):
        for item in node:
            transform_node(item)


def main():
    if len(sys.argv) != 3:
        print("사용법: python fix_openapi.py input.yaml output.yaml")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    transform_node(data)

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

    print(f"완료: {output_path} 로 저장됨")


if __name__ == "__main__":
    main()
