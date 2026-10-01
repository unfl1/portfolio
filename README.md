# 강현준 포트폴리오

[포트폴리오 웹사이트](https://unfl1.github.io/portfolio/)

| 프로젝트 | 담당 역할 | 주요 개발 내용 |
| --- | --- | --- |
| [Jiki](#jiki) | 백엔드 개발 및 팀장 | 약속 참여 관리, 접근 권한 검증, 벌금과 보상 정산 |
| [다잡아](#다잡아) | 프론트엔드 | 크롤링 기반 채용공고 탐색, 페이지네이션, 자기소개서 관리, 매칭 결과 시각화 |
| [나만의 도서관](#나만의-도서관) | 프론트엔드와 백엔드 개발, 배포 환경 구축 | 도커 - 쿠버네티스 환경 실습, 도서 공유 서비스, Jenkins 배포 자동화, 부하 테스트 |

<br>
<br>

# Jiki

**약속 참여 여부와 도착 상태에 따른 벌금과 보상 정산 서비스**

**담당 역할**: 백엔드, 팀장<br>
**기술**: Java, Spring Boot, Spring Data JPA, Spring Security, MariaDB<br>
**GitHub**: [CapstoneDesign-timeisgold/Back](https://github.com/CapstoneDesign-timeisgold/Back)

## 시스템 구조

[![지키 서비스 아키텍처](assets/jiki/jiki-architecture.png)](assets/jiki/jiki-architecture.png)

## 핵심 기능

- 약속 - 약속 생성 및 조회, 참여자 초대, 초대 수락과 거절, 참여 취소, 참여 마감 설정, 도착 상태 관리
- 정산 - 벌금과 보상 계산, 내부 잔액 반영, 정산 결과 및 거래 내역 조회
- 기타 - JWT 인증, 친구 요청과 수락 및 거절, 친구 목록 조회

## 문제 해결

### 1. 참여 상태 변경과 정산의 충돌 방지

#### 전체적인 아키텍처

[![참여 변경과 정산이 같은 약속 잠금을 사용하는 구조](assets/jiki/01-participation.png)](assets/jiki/01-participation.png)

#### 문제

- 참여 변경과 정산이 동시에 실행되면 정산 대상이 달라질 수 있는 구조.
- 대상 조회 후 금액 반영 전에 참여 상태가 바뀔 가능성 존재.
- 잠금 대기 전에 읽은 상태로 처리하면 최신 변경을 놓치는 문제.

#### 해결

- 두 작업을 순서대로 처리하도록 동일한 약속 행에 `PESSIMISTIC_WRITE` 잠금 적용.
- 약속 잠금 후 참여 행을 잠금 조회해 최신 상태로 처리.
- 마감 이후나 정산 완료 후 변경을 차단하고, 수락한 참여자만 정산 대상에 포함.

#### 결과

- 참여 변경과 정산의 처리 순서를 통일하고, 잠금 획득 후 최신 상태를 확인하는 구조로 변경.
- 마감 직전 변경 허용, 마감 정각부터 변경 차단, 정산 완료 후 도착 상태 변경 차단 검증.
- H2 JPA 테스트로 참여 상태와 마감 정보 저장, 첫 수락 이후 마감 변경 제한 확인.

### 2. 동시 정산 충돌과 금액 누락을 해결하고 재시도 정상 처리

#### 전체적인 아키텍처

[![약속 잠금과 계정 잠금 후 잔액과 거래 기록을 함께 저장하는 구조](assets/jiki/03-settlement.png)](assets/jiki/03-settlement.png)

#### 문제

- 서로 다른 약속이 같은 계정을 동시에 정산하는 실험에서 20회 모두 데드락 발생.
- 벌금 나눗셈의 나머지 1원 소실과 관리자 입금 기록 누락 확인.
- 완료된 정산을 다시 요청하면 409를 반환해 응답 유실 후 재시도를 정상 처리하지 못하는 문제.

#### 해결

- 공유 계정의 교차 대기를 막도록 사용자 ID 순서로 잠그고, DB의 현재 잔액을 조회해 계산.
- 잔액과 거래 기록, 확정 결과를 한 트랜잭션으로 저장하고 나머지는 관리자에게 적립.
- 약속 ID로 저장된 결과를 재사용해 재요청에 204 반환, 거래 유일 제약으로 중복 기록 방지.

#### 결과

- 동시 정산 20회에서 데드락 실패 20회 → 0회. 추가 10회에서도 잔액과 거래 기록 일치 확인.
- 1,000원 배분 시 333원씩 3명에게 지급하고 1원은 관리자에게 적립해 전체 잔액 보존.
- k6 VU 10 재시도 300건의 204 응답 3건 → 300건, 금액 반영은 약속별 1회 유지. 일반 테스트 82개 통과.

### 3. 약속 목록 N+1 개선으로 SQL 202회에서 2회로 감소

#### 전체적인 아키텍처

[![목록 조회에서 반복 SQL을 fetch join으로 줄인 구조](assets/jiki/02-query.png)](assets/jiki/02-query.png)

#### 문제

- 약속 10개 조회에 SQL 22회, 50개에 102회, 100개에 202회 실행.
- 참여 정보 조회 후 약속과 생성자를 지연 로딩하면서 개별 SQL 반복.
- 수락 상태를 애플리케이션에서 필터링해 조회 조건을 DB에 반영하지 못한 구조.

#### 해결

- 반복 조회를 없애도록 수락 상태를 DB 조건으로 옮기고 약속과 생성자에 fetch join 적용.
- 약속 10개, 50개, 100개에서 SQL 횟수가 일정한지 확인하는 회귀 테스트 추가.
- 동일 데이터로 k6 VU 1, 10, 30에서 개선 전후를 각 3회 측정하고 응답 데이터 검증.

#### 결과

- 약속 100개 조회 SQL 202회 → 2회, 약 99% 감소. 10개와 50개에서도 2회 유지.
- VU 10의 p95 응답 시간 3회 중앙값 58.09ms → 8.81ms, 84.8% 감소.
- 개선 전후 본 측정 82,405건에서 HTTP 오류와 응답 데이터 불일치 0건.

## 근거 자료

- [목록 조회 개선 기록](https://github.com/CapstoneDesign-timeisgold/Back/blob/main/back/docs/IMPROVEMENT_LOG.md)
- [참여 마감 설계와 검증 범위](https://github.com/CapstoneDesign-timeisgold/Back/blob/main/back/docs/PARTICIPATION_DEADLINE.md)
- [정산 설계와 측정 조건](https://github.com/CapstoneDesign-timeisgold/Back/blob/main/back/docs/SETTLEMENT_INTEGRITY.md)
- [Nginx 설정과 실행 안내](https://github.com/CapstoneDesign-timeisgold/Back/tree/main/back/deploy/nginx)

<br>
<br>

# 다잡아

**AI로 자기소개서를 분석해 크롤링으로 수집한 채용공고와 매칭하는 서비스**

**담당 역할**: 프론트엔드<br>
**기술**: JavaScript, React, Redux Toolkit, React Redux, Redux Persist, Tailwind CSS<br>
**GitHub**: [TABA-DaJobA/Front](https://github.com/TABA-DaJobA/Front)

## 시스템 구조

[![다잡아 서비스 아키텍처](assets/dajoba/dajoba-architecture.png)](assets/dajoba/dajoba-architecture.png)

## 핵심 기능

- **채용공고 탐색**: 직군별 필터, 페이지네이션, 공고 상세 조회
- **자기소개서 관리**: 작성, 조회, 수정, 삭제, 글자 수 표시, 새 자기소개서 초안 저장과 복원
- **매칭 결과 확인**: 기업별 매칭 점수와 순위 시각화, 추천 공고 연결

## 사용자 경험 개선

### 1. 서버 페이지네이션으로 채용공고 조회 범위와 탐색 방식 개선

#### 전체적인 아키텍처

[![채용공고 페이지네이션 흐름](assets/dajoba/01-pagination.png)](assets/dajoba/01-pagination.png)

#### 문제

- 전체 공고를 한 번에 불러와 로딩이 길고, 어디까지 확인했는지 알기 어렵다는 사용자 의견.
- 화면에 필요한 범위만 조회하고 현재 탐색 위치를 표시할 필요.

#### 해결

- 요청 범위를 줄이도록 서버 페이지네이션 API를 연동해 페이지당 최대 20건 조회.
- 화면과 API의 페이지 번호를 맞추고 서버의 전체 페이지 수를 탐색 버튼에 반영.
- 페이지 번호를 10개씩 표시하고 현재 페이지 강조, 이전과 다음 구간 이동 구현.

#### 결과

- 전체 공고 일괄 조회에서 페이지당 최대 20건 조회로 변경.
- 현재 페이지를 확인하며 목록을 나누어 탐색하는 화면 구성.
- 요청 번호 변환, 공고와 전체 페이지 수 반영, 첫 페이지와 마지막 페이지의 이동 제한 확인.

### 2. 분석 대기 화면에 스피너를 추가해 대기 상태 안내

#### 전체적인 아키텍처

[![분석 대기 표시 흐름](assets/dajoba/02-loading.png)](assets/dajoba/02-loading.png)

#### 문제

- 정적인 안내 문구만으로는 분석 대기 중인지 화면이 멈춘 것인지 구분하기 어렵다는 사용자 의견.

#### 해결

- 대기 상태가 보이도록 안내 문구 옆에 CSS 회전 애니메이션을 적용한 스피너 추가.
- 서버에서 매칭 결과를 받으면 대기 화면을 결과 화면으로 전환.

#### 결과

- 분석 중임을 시각적으로 안내하고, 스피너 회전과 결과 수신 후 화면 전환 확인.

### 3. 자기소개서 초안 자동 저장과 복원으로 작성 내용 유실 방지

#### 전체적인 아키텍처

[![자기소개서 초안 저장과 복원 흐름](assets/dajoba/03-draft.png)](assets/dajoba/03-draft.png)

#### 문제

- 저장 전 새로고침이나 화면 이동 시 자기소개서 입력 내용 유실.
- 지연 저장 대기 중 화면을 떠나면 마지막 입력이 누락될 가능성.
- 계정 변경이나 늦은 서버 응답이 다른 초안에 영향을 줄 가능성.

#### 해결

- 초안을 사용자별 브라우저 저장소에 보관하고, 입력 중단 0.8초 후 저장하거나 화면 이탈 시 즉시 저장.
- 재방문 시 복원과 삭제를 선택하도록 구성하고, 계정 변경 시 입력 상태 초기화.
- 서버 저장 성공 시 초안 삭제, 실패 시 유지. 중복 제출과 이탈 후 응답의 초안 간섭 방지.

#### 결과

- 같은 브라우저에서 재방문 시 초안을 복원해 이어서 작성 가능.
- 저장 대기 중 이탈 시 마지막 입력 보존, 서버 저장 실패 시 재시도할 내용 유지.
- Jest와 React Testing Library 테스트 11개 통과. 사용자별 분리와 저장소 오류, 늦은 응답 처리 검증.

<br>
<br>

# 나만의 도서관

**Docker와 Kubernetes 기반 클라우드 배포 및 운영**

**담당 역할**: 프론트엔드 및 백엔드 개발, 클라우드 배포 환경 구축, Jenkins 빌드 자동화<br>
**기술**: React, Java, Spring Boot, Spring Data JPA, MariaDB, Docker, Kubernetes, Jenkins, k6, Grafana<br>
**GitHub**: [백엔드](https://github.com/unfl1/mylibraryback) / [프론트엔드](https://github.com/unfl1/mylibraryfront) / [클라우드 배포 버전](https://github.com/unfl1/mylibrary)

## 시스템 구조

[![GitHub와 Jenkins, Kubernetes 컨테이너 배포 환경, k6와 Grafana를 연결한 전체 시스템 구조](assets/mylibrary/system-overview.png)](assets/mylibrary/system-overview.png)

## 핵심 기능

- 도서 공유 - 도서 대여 게시글 등록, 목록 및 상세 조회, 제목 검색, 본인 게시글 조회와 삭제
- 이미지 및 댓글 - 게시글 이미지 첨부와 조회, 댓글 기능
- 회원 - 회원가입과 로그인

직접 개발한 서비스를 대상으로 Docker 이미지 구성, Kubernetes 배포 환경 구축, Jenkins 빌드 자동화, k6 부하 테스트 및 수동 Pod 확장 수행

## 배포 환경 구축

### 1. 프론트엔드 및 백엔드 컨테이너화와 Kubernetes 배포

#### 전체적인 아키텍처

[![React, Spring Boot, MariaDB의 Docker 컨테이너를 Kubernetes로 관리하는 구조](assets/mylibrary/service-containers.png)](assets/mylibrary/service-containers.png)

#### 구축 과정

- 프론트엔드와 백엔드별 Dockerfile을 작성해 실행 환경과 시작 명령 정의.
- React 빌드는 `serve`로 제공하고, 백엔드는 Java 17 환경에서 JAR 실행.
- Kubernetes에 배포하고 DB 연결, 외부 API 접근, 이미지 저장 위치 조정.

#### 결과

- 프론트엔드와 백엔드 컨테이너를 클라우드 Kubernetes 환경에서 실행.
- 서비스별 실행 환경과 시작 명령을 Dockerfile로 관리.

### 2. GitHub Webhook과 Jenkins 연동 및 빌드 자동화

#### 전체적인 아키텍처

[![로컬 개발, GitHub, Jenkins, Kubernetes로 이어지는 배포 흐름](assets/mylibrary/delivery-flow.png)](assets/mylibrary/delivery-flow.png)

#### 구축 과정

- 클라우드 서버에 Jenkins 설치 후 GitHub Webhook 연동.
- 코드 push 시 빌드를 실행하도록 설정하고 실행 결과 확인.

#### 결과

- GitHub 코드 변경 감지부터 Jenkins 빌드 실행까지 자동화.

### 3. k6 부하 테스트와 수동 Pod 확장

#### 전체적인 아키텍처

[![k6, 서버, Grafana를 활용한 부하 테스트와 모니터링](assets/mylibrary/load-monitoring.png)](assets/mylibrary/load-monitoring.png)

#### 수행 과정

- Kubernetes에 배포한 서비스에 k6로 HTTP 요청 부하 발생.
- 부하 테스트 중 Pod 수를 수동으로 늘려 실행 규모 조정.
- Grafana 대시보드로 배포 환경 상태 확인.

#### 결과

- 클라우드 서비스 부하 테스트와 Kubernetes 수동 스케일 아웃 수행.
