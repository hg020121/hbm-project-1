# api/models/hbm.py
# ERD 기반 SQLAlchemy ORM 모델 (9개 테이블)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from typing import Optional, List
from api.db import Base


class Engineer(Base):
    __tablename__ = "ENGINEER"

    engineer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    dept: Mapped[str] = mapped_column(String(50), nullable=False)

    pre_analyses: Mapped[List["PreAnalysis"]] = relationship("PreAnalysis", back_populates="engineer")
    stackings: Mapped[List["Stacking"]] = relationship("Stacking", back_populates="engineer")
    reflows: Mapped[List["Reflow"]] = relationship("Reflow", back_populates="engineer")
    injections: Mapped[List["Injection"]] = relationship("Injection", back_populates="engineer")
    results: Mapped[List["ResultAnalysis"]] = relationship("ResultAnalysis", back_populates="engineer")


class HbmCarrierLot(Base):
    __tablename__ = "HBM_CARRIER_LOT"

    lot_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, server_default=func.now())

    incoming: Mapped[Optional["Incoming"]] = relationship("Incoming", back_populates="lot", uselist=False)
    pre_analysis: Mapped[Optional["PreAnalysis"]] = relationship("PreAnalysis", back_populates="lot", uselist=False)
    ai_recommends: Mapped[List["AiRecommend"]] = relationship("AiRecommend", back_populates="lot")
    stackings: Mapped[List["Stacking"]] = relationship("Stacking", back_populates="lot")
    reflows: Mapped[List["Reflow"]] = relationship("Reflow", back_populates="lot")
    injection: Mapped[Optional["Injection"]] = relationship("Injection", back_populates="lot", uselist=False)
    result: Mapped[Optional["ResultAnalysis"]] = relationship("ResultAnalysis", back_populates="lot", uselist=False)


class Incoming(Base):
    __tablename__ = "INCOMING"

    incoming_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    vendor_id: Mapped[str] = mapped_column(String(30), nullable=False)
    viscosity: Mapped[float] = mapped_column(Float, nullable=False)
    cte: Mapped[float] = mapped_column(Float, nullable=False)
    incoming_date: Mapped[Date] = mapped_column(Date, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="incoming")


class PreAnalysis(Base):
    __tablename__ = "PRE_ANALYSIS"

    pre_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(20), ForeignKey("ENGINEER.engineer_id"), nullable=False)
    measured_viscosity: Mapped[float] = mapped_column(Float, nullable=False)
    measured_cte: Mapped[float] = mapped_column(Float, nullable=False)
    measured_date: Mapped[Date] = mapped_column(Date, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="pre_analysis")
    engineer: Mapped["Engineer"] = relationship("Engineer", back_populates="pre_analyses")


class AiRecommend(Base):
    __tablename__ = "AI_RECOMMEND"

    recommend_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    recommend_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    recommend_temp: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, server_default=func.now())

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="ai_recommends")
    stackings: Mapped[List["Stacking"]] = relationship("Stacking", back_populates="ai_recommend")


class Stacking(Base):
    __tablename__ = "STACKING"

    stack_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(20), ForeignKey("ENGINEER.engineer_id"), nullable=False)
    recommend_id: Mapped[str] = mapped_column(String(30), ForeignKey("AI_RECOMMEND.recommend_id"), nullable=False)
    stack_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)
    void_area_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stack_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="stackings")
    engineer: Mapped["Engineer"] = relationship("Engineer", back_populates="stackings")
    ai_recommend: Mapped["AiRecommend"] = relationship("AiRecommend", back_populates="stackings")


class Reflow(Base):
    __tablename__ = "REFLOW"

    reflow_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(20), ForeignKey("ENGINEER.engineer_id"), nullable=False)
    reflow_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    reflow_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="reflows")
    engineer: Mapped["Engineer"] = relationship("Engineer", back_populates="reflows")


class Injection(Base):
    __tablename__ = "INJECTION"

    injection_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(20), ForeignKey("ENGINEER.engineer_id"), nullable=False)
    inject_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    injection_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="injection")
    engineer: Mapped["Engineer"] = relationship("Engineer", back_populates="injections")


class ResultAnalysis(Base):
    __tablename__ = "RESULT_ANALYSIS"

    result_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(30), ForeignKey("HBM_CARRIER_LOT.lot_id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(20), ForeignKey("ENGINEER.engineer_id"), nullable=False)
    void_area_pct: Mapped[float] = mapped_column(Float, nullable=False)
    final_result: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis_date: Mapped[Date] = mapped_column(Date, nullable=False)

    lot: Mapped["HbmCarrierLot"] = relationship("HbmCarrierLot", back_populates="result")
    engineer: Mapped["Engineer"] = relationship("Engineer", back_populates="results")
