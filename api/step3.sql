-- ============================================================
-- STEP 3: 통합 DB 및 테이블 생성 (DDL)
-- DB: hbm_integrated_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS hbm_integrated_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hbm_integrated_db;

DROP TABLE IF EXISTS RESULT_ANALYSIS;
DROP TABLE IF EXISTS INJECTION;
DROP TABLE IF EXISTS REFLOW;
DROP TABLE IF EXISTS STACKING;
DROP TABLE IF EXISTS AI_RECOMMEND;
DROP TABLE IF EXISTS PRE_ANALYSIS;
DROP TABLE IF EXISTS INCOMING;
DROP TABLE IF EXISTS HBM_CARRIER_LOT;
DROP TABLE IF EXISTS ENGINEER;


CREATE TABLE ENGINEER (
    engineer_id     VARCHAR(20)     NOT NULL,
    name            VARCHAR(50)     NOT NULL,
    dept            VARCHAR(50)     NOT NULL,
    PRIMARY KEY (engineer_id)
);

CREATE TABLE HBM_CARRIER_LOT (
    lot_id          VARCHAR(30)     NOT NULL,
    lot_status      VARCHAR(30)     NOT NULL,
    created_at      DATETIME        DEFAULT NOW(),
    PRIMARY KEY (lot_id)
);

CREATE TABLE INCOMING (
    incoming_id     VARCHAR(30)     NOT NULL,
    lot_id          VARCHAR(30)     NOT NULL,
    vendor_id       VARCHAR(30)     NOT NULL,
    viscosity       FLOAT           NOT NULL,
    cte             FLOAT           NOT NULL,
    incoming_date   DATE            NOT NULL,
    PRIMARY KEY (incoming_id),
    CONSTRAINT fk_incoming_lot
        FOREIGN KEY (lot_id) REFERENCES HBM_CARRIER_LOT (lot_id)
);

CREATE TABLE PRE_ANALYSIS (
    pre_id              VARCHAR(30)     NOT NULL,
    lot_id              VARCHAR(30)     NOT NULL,
    engineer_id         VARCHAR(20)     NOT NULL,
    measured_viscosity  FLOAT           NOT NULL,
    measured_cte        FLOAT           NOT NULL,
    measured_date       DATE            NOT NULL,
    PRIMARY KEY (pre_id),
    CONSTRAINT fk_pre_lot
        FOREIGN KEY (lot_id)      REFERENCES HBM_CARRIER_LOT (lot_id),
    CONSTRAINT fk_pre_engineer
        FOREIGN KEY (engineer_id) REFERENCES ENGINEER (engineer_id)
);

CREATE TABLE AI_RECOMMEND (
    recommend_id        VARCHAR(30)     NOT NULL,
    lot_id              VARCHAR(30)     NOT NULL,
    recommend_pressure  FLOAT           NOT NULL,
    recommend_temp      FLOAT           NOT NULL,
    recommended_at      DATETIME        DEFAULT NOW(),
    PRIMARY KEY (recommend_id),
    CONSTRAINT fk_recommend_lot
        FOREIGN KEY (lot_id) REFERENCES HBM_CARRIER_LOT (lot_id)
);

CREATE TABLE STACKING (
    stack_id        VARCHAR(30)     NOT NULL,
    lot_id          VARCHAR(30)     NOT NULL,
    engineer_id     VARCHAR(20)     NOT NULL,
    recommend_id    VARCHAR(30)     NOT NULL,
    stack_seq       INT             NOT NULL,
    pressure        FLOAT           NOT NULL,
    void_area_pct   FLOAT                       COMMENT 'stacking 후 측정 void 비율 (NULL 가능)',
    stack_date      DATETIME        NOT NULL,
    PRIMARY KEY (stack_id),
    CONSTRAINT fk_stack_lot
        FOREIGN KEY (lot_id)        REFERENCES HBM_CARRIER_LOT (lot_id),
    CONSTRAINT fk_stack_engineer
        FOREIGN KEY (engineer_id)   REFERENCES ENGINEER (engineer_id),
    CONSTRAINT fk_stack_recommend
        FOREIGN KEY (recommend_id)  REFERENCES AI_RECOMMEND (recommend_id)
);

CREATE TABLE REFLOW (
    reflow_id       VARCHAR(30)     NOT NULL,
    lot_id          VARCHAR(30)     NOT NULL,
    engineer_id     VARCHAR(20)     NOT NULL,
    reflow_seq      INT             NOT NULL,
    temperature     FLOAT           NOT NULL,
    reflow_date     DATETIME        NOT NULL,
    PRIMARY KEY (reflow_id),
    CONSTRAINT fk_reflow_lot
        FOREIGN KEY (lot_id)      REFERENCES HBM_CARRIER_LOT (lot_id),
    CONSTRAINT fk_reflow_engineer
        FOREIGN KEY (engineer_id) REFERENCES ENGINEER (engineer_id)
);

CREATE TABLE INJECTION (
    injection_id        VARCHAR(30)     NOT NULL,
    lot_id              VARCHAR(30)     NOT NULL,
    engineer_id         VARCHAR(20)     NOT NULL,
    inject_pressure     FLOAT           NOT NULL,
    injection_date      DATETIME        NOT NULL,
    PRIMARY KEY (injection_id),
    CONSTRAINT fk_injection_lot
        FOREIGN KEY (lot_id)      REFERENCES HBM_CARRIER_LOT (lot_id),
    CONSTRAINT fk_injection_engineer
        FOREIGN KEY (engineer_id) REFERENCES ENGINEER (engineer_id)
);

CREATE TABLE RESULT_ANALYSIS (
    result_id       VARCHAR(30)     NOT NULL,
    lot_id          VARCHAR(30)     NOT NULL,
    engineer_id     VARCHAR(20)     NOT NULL,
    void_area_pct   FLOAT           NOT NULL,
    final_result    VARCHAR(20)     NOT NULL,
    analysis_date   DATE            NOT NULL,
    PRIMARY KEY (result_id),
    CONSTRAINT fk_result_lot
        FOREIGN KEY (lot_id)      REFERENCES HBM_CARRIER_LOT (lot_id),
    CONSTRAINT fk_result_engineer
        FOREIGN KEY (engineer_id) REFERENCES ENGINEER (engineer_id)
);