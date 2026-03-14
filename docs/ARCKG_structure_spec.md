# ARCKG Structure & Naming Convention Specification

## 1. 개요

ARCKG(ARC Knowledge Graph)는 ARC 문제 풀이를 위한 순수 상징적(symbolic) 지식 그래프다.
그래프는 **node**와 **edge**로 구성되며, 계층 구조를 가지고 있고 이 계층이 물리적인 **폴더/파일 구조**로 표현된다.

---

## 2. 계층 구조

총 5개의 계층이 있다. Memory는 루트 폴더 역할이며 계층 카운팅에 포함하지 않는다.

```
Memory (루트)
└── TASK (T)
    └── PAIR (P)
        └── GRID (G)
            └── OBJECT (O)
                └── PIXEL (X)
```

각 계층의 기호: `T`, `P`, `G`, `O`, `X`

---

## 3. Node와 Edge

### 3.1 Node = 폴더

해당 component의 존재를 나타낸다. 폴더 안에는 하위 node들(inclusion)과 같은 레벨 node들 사이의 relation edge들이 담긴다.

node의 전체 구성:
```
node = property (0차 relation, 자기 자신을 대표하는 값)
     + 하위 node들 (폴더로 표현, inclusion)
     + 같은 레벨 간 relation edge들 (.json으로 표현)
```

### 3.2 Edge = .json 파일

edge에는 두 가지 종류가 있다.

| 종류 | 방향 | 물리적 표현 | 설명 |
|------|------|------------|------|
| Property | self-pointing | `E_[nodename].json` | node 자신의 속성 (0차 relation) |
| Relation | horizontal | `E_[comp1]-[comp2].json` | 두 entity를 비교한 결과 (1차 이상) |

Inclusion(vertical)은 폴더 포함 관계로 표현되며 별도 파일로 저장되지 않는다.

---

## 4. Relation의 정의 (재귀적 확장)

relation은 두 entity를 비교한 결과이며, 비교 대상에 따라 차수가 결정된다.

```
0차 (property) = 자기 자신의 속성
1차 relation   = compare(node.property, node.property)
2차 relation   = compare(1차 relation, 1차 relation)
N차 relation   = compare((N-1)차 relation, (N-1)차 relation)
```

> property는 node 자신과의 비교이므로 0차 relation으로 볼 수 있다.
> 즉 property와 relation은 동일한 compare 연산의 특수 케이스다.

### 비교 결과 필드

모든 relation의 result는 다음 3개 필드를 포함한다.

```json
"result": {
  "type": "COMM | DIFF",
  "score": "n/total",
  "category": { ... }
}
```

- `type`: 전체 비교 결과 (COMM 또는 DIFF)
- `score`: 일치 항목 수 / 전체 항목 수
- `category`: 각 하위 항목별 재귀적 비교 결과

**2차 이상의 relation**에서 비교 대상은 1차 result의 `type`, `score`, `category` 3개 필드 전체다. score가 같더라도 category 구성이 다를 수 있으므로 세 필드 모두 독립적으로 비교된다.

scalar 값(comp1, comp2)을 비교하는 leaf 수준에서는 5개 항목이 존재한다: `type`, `score`, `category`, `comp1`, `comp2`

---

## 5. 저장 위치 규칙

> **비교 대상 두 entity의 최소 공통 조상(LCA) node 폴더에 저장한다.**

이 규칙은 차수(0차, 1차, 2차, ...)와 관계없이 동일하게 적용된다.

예시:
- PAIR_0 안의 두 GRID를 비교한 relation → PAIR_0 폴더에 저장
- PAIR_0의 edge와 PAIR_1의 edge를 비교한 2차 relation → TASK 폴더에 저장

---

## 6. 네이밍 규칙

### 6.1 Node 이름 (폴더)

```
N_[기호][번호]
```

예시:
```
N_T083ede33    (Task level, 전체 task ID)
N_P0, N_P1    (PAIR level)
N_G0, N_G2    (GRID level)
N_O1          (OBJECT level)
N_X6          (PIXEL level)
```

Test pair는 번호 대신 알파벳 사용: `Pa`, `Pb`, `Pc` ...

### 6.2 Edge 이름 (파일)

**모든 edge 파일은 `E_`로 시작한다.**

#### 0차 (property)
```
E_[nodename].json
```
```
E_P0G0X6.json
E_P0G0O1.json
```

#### 1차 (node vs node)
```
E_[comp1]-[comp2].json
```
직속 하위 레벨:
```
E_P0-P1.json
E_P0G0-P1G0.json
```
더 깊은 레벨:
```
E_P0G0O1-P1G0O1.json
E_P0G0O1X3-P1G0O1X7.json
```

#### 2차 (edge vs edge)
edge 입력은 `()`로 감싼다.
```
E_(E_[comp1]-[comp2])-(E_[comp3]-[comp4]).json
```
```
E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9).json
E_(E_P0G0O1-P0G0O2)-(E_P1G0O1-P1G0O2).json
```

#### 3차 (2차 edge vs 2차 edge)
```
E_(E_(E_[...]- E_[...])-(E_[...]-E_[...]))-(E_(E_[...]-E_[...])-(E_[...]-E_[...])).json
```
```
E_(E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9))-(E_(E_P0G1X10-P0G1X11)-(E_P1G1X12-P1G1X13)).json
```

**규칙 요약:**
- `E_`는 항상 "이 파일은 relation이다"를 의미
- `()`는 입력이 복합체(edge)일 때 감싸는 구분자
- 단순 node 입력은 괄호 없이 그대로
- `E_`의 중첩 깊이 = relation의 차수

---

## 7. 비교 예시 (0차 ~ 3차)

아래 픽셀 데이터를 사용한다.

```
P0G0X6:  color=1, row=6, col=6
P0G0X7:  color=1, row=6, col=7
P1G0X8:  color=3, row=7, col=6
P1G0X9:  color=3, row=7, col=7
P0G1X10: color=1, row=3, col=2
P0G1X11: color=5, row=3, col=4
P1G1X12: color=1, row=5, col=2
P1G1X13: color=5, row=5, col=4
```

---

### 7.1 0차 (property)

**E_P0G0X6.json**
```json
{
  "color": 1,
  "coordinate": {
    "row_index": 6,
    "col_index": 6
  }
}
```

**E_P0G0X7.json**
```json
{
  "color": 1,
  "coordinate": {
    "row_index": 6,
    "col_index": 7
  }
}
```

**E_P1G0X8.json**
```json
{
  "color": 3,
  "coordinate": {
    "row_index": 7,
    "col_index": 6
  }
}
```

**E_P1G0X9.json**
```json
{
  "color": 3,
  "coordinate": {
    "row_index": 7,
    "col_index": 7
  }
}
```

**E_P0G1X10.json**
```json
{
  "color": 1,
  "coordinate": {
    "row_index": 3,
    "col_index": 2
  }
}
```

**E_P0G1X11.json**
```json
{
  "color": 5,
  "coordinate": {
    "row_index": 3,
    "col_index": 4
  }
}
```

**E_P1G1X12.json**
```json
{
  "color": 1,
  "coordinate": {
    "row_index": 5,
    "col_index": 2
  }
}
```

**E_P1G1X13.json**
```json
{
  "color": 5,
  "coordinate": {
    "row_index": 5,
    "col_index": 4
  }
}
```

---

### 7.2 1차 (node vs node)

저장 위치: 각 pair의 grid 폴더 (최소 공통 조상)

**E_P0G0X6-P0G0X7.json** — color 같음, row 같음, col 다름
```json
{
  "id1": "task.P0.G0.X6",
  "id2": "task.P0.G0.X7",
  "result": {
    "type": "DIFF",
    "score": "1/2",
    "category": {
      "color": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": 1, "comp2": 1
      },
      "coordinate": {
        "type": "DIFF", "score": "1/2",
        "category": {
          "row_index": {
            "type": "COMM", "score": "1/1", "category": {},
            "comp1": 6, "comp2": 6
          },
          "col_index": {
            "type": "DIFF", "score": "0/1", "category": {},
            "comp1": 6, "comp2": 7
          }
        }
      }
    }
  }
}
```

**E_P1G0X8-P1G0X9.json** — color 같음, row 같음, col 다름
```json
{
  "id1": "task.P1.G0.X8",
  "id2": "task.P1.G0.X9",
  "result": {
    "type": "DIFF",
    "score": "1/2",
    "category": {
      "color": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": 3, "comp2": 3
      },
      "coordinate": {
        "type": "DIFF", "score": "1/2",
        "category": {
          "row_index": {
            "type": "COMM", "score": "1/1", "category": {},
            "comp1": 7, "comp2": 7
          },
          "col_index": {
            "type": "DIFF", "score": "0/1", "category": {},
            "comp1": 6, "comp2": 7
          }
        }
      }
    }
  }
}
```

**E_P0G1X10-P0G1X11.json** — color 다름, row 같음, col 다름
```json
{
  "id1": "task.P0.G1.X10",
  "id2": "task.P0.G1.X11",
  "result": {
    "type": "DIFF",
    "score": "0/2",
    "category": {
      "color": {
        "type": "DIFF", "score": "0/1", "category": {},
        "comp1": 1, "comp2": 5
      },
      "coordinate": {
        "type": "DIFF", "score": "1/2",
        "category": {
          "row_index": {
            "type": "COMM", "score": "1/1", "category": {},
            "comp1": 3, "comp2": 3
          },
          "col_index": {
            "type": "DIFF", "score": "0/1", "category": {},
            "comp1": 2, "comp2": 4
          }
        }
      }
    }
  }
}
```

**E_P1G1X12-P1G1X13.json** — color 다름, row 같음, col 다름
```json
{
  "id1": "task.P1.G1.X12",
  "id2": "task.P1.G1.X13",
  "result": {
    "type": "DIFF",
    "score": "0/2",
    "category": {
      "color": {
        "type": "DIFF", "score": "0/1", "category": {},
        "comp1": 1, "comp2": 5
      },
      "coordinate": {
        "type": "DIFF", "score": "1/2",
        "category": {
          "row_index": {
            "type": "COMM", "score": "1/1", "category": {},
            "comp1": 5, "comp2": 5
          },
          "col_index": {
            "type": "DIFF", "score": "0/1", "category": {},
            "comp1": 2, "comp2": 4
          }
        }
      }
    }
  }
}
```

---

### 7.3 2차 (edge vs edge)

비교 대상: 1차 result의 `type`, `score`, `category` 3개 필드 (총점 3/3 기준)
저장 위치: 두 edge의 최소 공통 조상 (TASK 폴더)

**E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9).json**
```json
{
  "id1": "E_P0G0X6-P0G0X7",
  "id2": "E_P1G0X8-P1G0X9",
  "result": {
    "type": "DIFF",
    "score": "2/3",
    "category": {
      "result.type": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "DIFF", "comp2": "DIFF"
      },
      "result.score": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "1/2", "comp2": "1/2"
      },
      "result.category": {
        "type": "DIFF",
        "score": "0/2",
        "category": {
          "color": {
            "type": "DIFF",
            "score": "3/5",
            "category": {
              "color.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "COMM", "comp2": "COMM"
              },
              "color.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "1/1", "comp2": "1/1"
              },
              "color.category": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": {}, "comp2": {}
              },
              "color.comp1": {
                "type": "DIFF", "score": "0/1", "category": {},
                "comp1": 1, "comp2": 3
              },
              "color.comp2": {
                "type": "DIFF", "score": "0/1", "category": {},
                "comp1": 1, "comp2": 3
              }
            }
          },
          "coordinate": {
            "type": "DIFF",
            "score": "2/3",
            "category": {
              "coordinate.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              },
              "coordinate.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "1/2", "comp2": "1/2"
              },
              "coordinate.category": {
                "type": "DIFF",
                "score": "1/2",
                "category": {
                  "row_index": {
                    "type": "DIFF",
                    "score": "3/5",
                    "category": {
                      "row.type": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "COMM", "comp2": "COMM"
                      },
                      "row.score": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "1/1", "comp2": "1/1"
                      },
                      "row.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": {}, "comp2": {}
                      },
                      "row.comp1": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": 6, "comp2": 7
                      },
                      "row.comp2": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": 6, "comp2": 7
                      }
                    }
                  },
                  "col_index": {
                    "type": "COMM",
                    "score": "5/5",
                    "category": {
                      "col.type": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "DIFF", "comp2": "DIFF"
                      },
                      "col.score": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "0/1", "comp2": "0/1"
                      },
                      "col.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": {}, "comp2": {}
                      },
                      "col.comp1": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": 6, "comp2": 6
                      },
                      "col.comp2": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": 7, "comp2": 7
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**E_(E_P0G1X10-P0G1X11)-(E_P1G1X12-P1G1X13).json**
```json
{
  "id1": "E_P0G1X10-P0G1X11",
  "id2": "E_P1G1X12-P1G1X13",
  "result": {
    "type": "DIFF",
    "score": "2/3",
    "category": {
      "result.type": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "DIFF", "comp2": "DIFF"
      },
      "result.score": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "0/2", "comp2": "0/2"
      },
      "result.category": {
        "type": "DIFF",
        "score": "1/2",
        "category": {
          "color": {
            "type": "COMM",
            "score": "5/5",
            "category": {
              "color.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              },
              "color.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "0/1", "comp2": "0/1"
              },
              "color.category": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": {}, "comp2": {}
              },
              "color.comp1": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": 1, "comp2": 1
              },
              "color.comp2": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": 5, "comp2": 5
              }
            }
          },
          "coordinate": {
            "type": "DIFF",
            "score": "2/3",
            "category": {
              "coordinate.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              },
              "coordinate.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "1/2", "comp2": "1/2"
              },
              "coordinate.category": {
                "type": "DIFF",
                "score": "1/2",
                "category": {
                  "row_index": {
                    "type": "DIFF",
                    "score": "3/5",
                    "category": {
                      "row.type": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "COMM", "comp2": "COMM"
                      },
                      "row.score": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "1/1", "comp2": "1/1"
                      },
                      "row.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": {}, "comp2": {}
                      },
                      "row.comp1": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": 3, "comp2": 5
                      },
                      "row.comp2": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": 3, "comp2": 5
                      }
                    }
                  },
                  "col_index": {
                    "type": "COMM",
                    "score": "5/5",
                    "category": {
                      "col.type": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "DIFF", "comp2": "DIFF"
                      },
                      "col.score": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "0/1", "comp2": "0/1"
                      },
                      "col.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": {}, "comp2": {}
                      },
                      "col.comp1": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": 2, "comp2": 2
                      },
                      "col.comp2": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": 4, "comp2": 4
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

### 7.4 3차 (2차 edge vs 2차 edge)

비교 대상: 위 두 2차 relation
저장 위치: TASK 폴더

두 2차 relation의 차이:
- 2차A: `result.score = "1/2"` (X6-X7 패턴, color가 COMM)
- 2차B: `result.score = "0/2"` (X10-X11 패턴, color가 DIFF)
- 핵심 차이: color의 type이 A에서는 COMM, B에서는 DIFF

**E_(E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9))-(E_(E_P0G1X10-P0G1X11)-(E_P1G1X12-P1G1X13)).json**
```json
{
  "id1": "E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9)",
  "id2": "E_(E_P0G1X10-P0G1X11)-(E_P1G1X12-P1G1X13)",
  "result": {
    "type": "DIFF",
    "score": "2/3",
    "category": {
      "result.type": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "DIFF", "comp2": "DIFF"
      },
      "result.score": {
        "type": "COMM", "score": "1/1", "category": {},
        "comp1": "2/3", "comp2": "2/3"
      },
      "result.category": {
        "type": "DIFF",
        "score": "2/3",
        "category": {
          "result.type": {
            "type": "COMM",
            "score": "5/5",
            "category": {
              "result.type.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "COMM", "comp2": "COMM"
              },
              "result.type.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "1/1", "comp2": "1/1"
              },
              "result.type.category": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": {}, "comp2": {}
              },
              "result.type.comp1": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              },
              "result.type.comp2": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              }
            }
          },
          "result.score": {
            "type": "DIFF",
            "score": "3/5",
            "category": {
              "result.score.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "COMM", "comp2": "COMM"
              },
              "result.score.score": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "1/1", "comp2": "1/1"
              },
              "result.score.category": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": {}, "comp2": {}
              },
              "result.score.comp1": {
                "type": "DIFF", "score": "0/1", "category": {},
                "comp1": "1/2", "comp2": "0/2"
              },
              "result.score.comp2": {
                "type": "DIFF", "score": "0/1", "category": {},
                "comp1": "1/2", "comp2": "0/2"
              }
            }
          },
          "result.category": {
            "type": "DIFF",
            "score": "2/3",
            "category": {
              "result.category.type": {
                "type": "COMM", "score": "1/1", "category": {},
                "comp1": "DIFF", "comp2": "DIFF"
              },
              "result.category.score": {
                "type": "DIFF", "score": "0/1", "category": {},
                "comp1": "0/2", "comp2": "1/2"
              },
              "result.category.category": {
                "type": "DIFF",
                "score": "1/2",
                "category": {
                  "color": {
                    "type": "DIFF",
                    "score": "2/3",
                    "category": {
                      "color.type": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": "DIFF", "comp2": "COMM"
                      },
                      "color.score": {
                        "type": "DIFF", "score": "0/1", "category": {},
                        "comp1": "3/5", "comp2": "5/5"
                      },
                      "color.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": {}, "comp2": {}
                      }
                    }
                  },
                  "coordinate": {
                    "type": "COMM",
                    "score": "3/3",
                    "category": {
                      "coordinate.type": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "DIFF", "comp2": "DIFF"
                      },
                      "coordinate.score": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "2/3", "comp2": "2/3"
                      },
                      "coordinate.category": {
                        "type": "COMM", "score": "1/1", "category": {},
                        "comp1": "DIFF(1/2)", "comp2": "DIFF(1/2)"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 8. compare 함수 구현 시 유의사항

- 입력 타입 판별: 입력이 property(dict with raw values)인지, 1차 이상의 relation result(dict with type/score/category)인지 구분해야 한다.
- 재귀 적용: `category` 안의 각 항목은 동일한 compare 함수를 재귀 호출한다.
- 2차 이상에서 비교 항목은 항상 `type`, `score`, `category` 3개다. scalar leaf에서는 여기에 `comp1`, `comp2`가 추가된다.
- score는 중복 정보처럼 보이지만 독립적으로 비교한다. score가 같더라도 category 구성이 다를 수 있기 때문이다.
- 파일 저장 시 이름은 섹션 6의 네이밍 규칙을 따르며, 저장 위치는 두 입력의 최소 공통 조상 폴더다.
