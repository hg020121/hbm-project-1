-- STEP 1: AS-IS 파편화 테이블 생성
-- DB: hbm_fragmented_db (파편화 상태 전용)
-- FK 없음 / 수기 연결 / 언어·단위 불통일
-- ============================================================

CREATE DATABASE IF NOT EXISTS hbm_fragmented_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hbm_fragmented_db;

-- 기존 테이블 삭제 (역순)
DROP TABLE IF EXISTS result_analysis;
DROP TABLE IF EXISTS process_log;
DROP TABLE IF EXISTS pre_analysis;
DROP TABLE IF EXISTS incoming;


-- -------------------------------------------------------
-- [1번] 입고 테이블
-- 협력사에서 제공해주는 정보 저장
-- -------------------------------------------------------
CREATE TABLE incoming (
    lot_id          VARCHAR(30)     NOT NULL    COMMENT 'LOT ID (수기 관리)',
    vendor_id       VARCHAR(30)                 COMMENT '협력사 ID (형식 불통일)',
    viscosity       FLOAT                       COMMENT '점도 (협력사 단위 불통일)',
    cte             FLOAT                       COMMENT 'CTE (협력사 단위 불통일)',
    incoming_date   VARCHAR(30)                 COMMENT '입고 날짜 (형식 불통일)',

    PRIMARY KEY (lot_id)
) COMMENT = '[입고] 협력사 제공 소재 입고 정보 - FK 없음, 수기 관리';


-- -------------------------------------------------------
-- [2번] 사전 분석 테이블
-- 자체적으로 측정한 정보 저장
-- -------------------------------------------------------
CREATE TABLE pre_analysis (
    lot_id              VARCHAR(30)     NOT NULL    COMMENT 'LOT ID (수기 매칭)',
    measured_viscosity  FLOAT                       COMMENT '측정 점도 (단위 불통일)',
    measured_cte        FLOAT                       COMMENT '측정 CTE (단위 불통일)',
    measured_date       VARCHAR(30)                 COMMENT '측정 날짜 (형식 불통일)',

    PRIMARY KEY (lot_id)
) COMMENT = '[사전 분석] 자체 측정 데이터 - FK 없음, 엑셀 관리';


-- -------------------------------------------------------
-- [3번] 공정 테이블 (EAV 구조)
-- 공정 이름, 파라미터, 값이 하나의 행으로 혼합 저장
-- stacking  → 파라미터: 압력
-- reflow    → 파라미터: 온도
-- injection → 파라미터: 주입압력
-- -------------------------------------------------------
CREATE TABLE process_log (
    process_id      VARCHAR(30)     NOT NULL    COMMENT '공정 ID (수기)',
    lot_id          VARCHAR(30)                 COMMENT 'LOT ID (수기 매칭)',
    process_name    VARCHAR(30)                 COMMENT '공정 이름 (명칭 불통일)',
    process_param   VARCHAR(50)                 COMMENT '공정 파라미터명 (명칭 불통일)',
    process_value   VARCHAR(50)                 COMMENT '공정 값 (단위 포함 문자열)',
    process_date    VARCHAR(30)                 COMMENT '공정 날짜 (형식 불통일)',

    PRIMARY KEY (process_id)
) COMMENT = '[공정] EAV 구조 - stacking/reflow/injection 혼합, FK 없음';


-- -------------------------------------------------------
-- [4번] 결과 분석 테이블
-- 공정을 거친 반도체에 대한 최종 평가
-- -------------------------------------------------------
CREATE TABLE result_analysis (
    lot_id          VARCHAR(30)     NOT NULL    COMMENT 'LOT ID (수기 매칭)',
    void_area_pct   FLOAT                       COMMENT '반도체 내 void 영역 비율 (%)',
    final_result    VARCHAR(20)                 COMMENT '판정 결과 (사용/재활용/사용불가)',
    analysis_date   VARCHAR(30)                 COMMENT '분석 날짜 (형식 불통일)',

    PRIMARY KEY (lot_id)
) COMMENT = '[결과 분석] 최종 반도체 평가 - FK 없음, 수기 관리';