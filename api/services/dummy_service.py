# api/services/dummy_service.py
# step4 방식 기반 더미 데이터 생성 서비스

import random
from datetime import date, timedelta, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import api.models.hbm as model


async def generate_dummy_lots(db: AsyncSession, count: int = 10, yield_rate: float = 0.98) -> dict:
    """
    step4 더미 데이터 생성 방식 기반
    새 LOT 데이터를 동적으로 생성하여 DB에 삽입
    """
    random.seed()

    # 현재 LOT 수 확인
    current_count = (await db.execute(select(func.count()).select_from(model.HbmCarrierLot))).scalar()
    engineers = (await db.execute(select(model.Engineer))).scalars().all()
    if not engineers:
        return {"error": "엔지니어 데이터가 없습니다. step4 SQL을 먼저 실행해주세요."}

    eng_ids = [e.engineer_id for e in engineers]
    vendors = ["HC-001", "HC-002", "NM-001", "NM-002", "DP-001", "DP-002"]
    base_date = date.today()

    rec_count = (await db.execute(select(func.count()).select_from(model.AiRecommend))).scalar()
    stk_count = (await db.execute(select(func.count()).select_from(model.Stacking))).scalar()
    rfw_count = (await db.execute(select(func.count()).select_from(model.Reflow))).scalar()
    inj_count = (await db.execute(select(func.count()).select_from(model.Injection))).scalar()
    rst_count = (await db.execute(select(func.count()).select_from(model.ResultAnalysis))).scalar()
    inc_count = (await db.execute(select(func.count()).select_from(model.Incoming))).scalar()
    pre_count = (await db.execute(select(func.count()).select_from(model.PreAnalysis))).scalar()

    created_lots = []
    defect_indices = random.sample(range(count), max(1, int(count * (1 - yield_rate))))

    for i in range(count):
        idx = current_count + i + 1
        lot_id = f"LOT-{idx:03d}"
        is_defect = i in defect_indices

        # HBM_CARRIER_LOT
        lot = model.HbmCarrierLot(lot_id=lot_id, lot_status="DONE")
        db.add(lot)
        await db.flush()

        # INCOMING
        inc_count += 1
        incoming = model.Incoming(
            incoming_id=f"INC-{inc_count:03d}",
            lot_id=lot_id,
            vendor_id=random.choice(vendors),
            viscosity=round(random.uniform(3.40, 4.30), 2),
            cte=round(random.uniform(17.5, 21.0), 1),
            incoming_date=base_date - timedelta(days=random.randint(1, 30)),
        )
        db.add(incoming)

        # PRE_ANALYSIS
        pre_count += 1
        pre = model.PreAnalysis(
            pre_id=f"PRE-{pre_count:03d}",
            lot_id=lot_id,
            engineer_id=random.choice(eng_ids[:3]),
            measured_viscosity=round(incoming.viscosity + random.uniform(-0.05, 0.05), 2),
            measured_cte=round(incoming.cte + random.uniform(-0.2, 0.2), 1),
            measured_date=incoming.incoming_date + timedelta(days=1),
        )
        db.add(pre)

        # void 패턴 (초반 높고 점점 감소 - step4 패턴)
        n_stacks = 10
        start_void = random.uniform(0.82, 0.92) if not is_defect else random.uniform(0.85, 0.95)
        voids = [start_void]
        for _ in range(1, n_stacks):
            if is_defect:
                delta = random.uniform(-0.02, 0.05)
                voids.append(round(min(0.99, max(0.80, voids[-1] + delta)), 3))
            else:
                delta = random.uniform(0.03, 0.08)
                voids.append(round(max(0.01, voids[-1] - delta), 3))

        # AI_RECOMMEND + STACKING (10회)
        for seq in range(1, n_stacks + 1):
            rec_count += 1
            stk_count += 1
            rec_pressure = round(2.00 + seq * 0.05 + random.uniform(-0.02, 0.02), 2)
            rec_temp = round(247.0 + seq * 0.5 + random.uniform(-0.5, 0.5), 1)
            proc_date = datetime.combine(
                pre.measured_date + timedelta(days=seq),
                datetime.min.time()
            )
            rec = model.AiRecommend(
                recommend_id=f"REC-{rec_count:03d}",
                lot_id=lot_id,
                recommend_pressure=rec_pressure,
                recommend_temp=rec_temp,
            )
            db.add(rec)
            await db.flush()

            stk = model.Stacking(
                stack_id=f"STK-{stk_count:03d}",
                lot_id=lot_id,
                engineer_id=random.choice(eng_ids[:3]),
                recommend_id=rec.recommend_id,
                stack_seq=seq,
                pressure=round(rec_pressure + random.uniform(-0.03, 0.03), 2),
                void_area_pct=voids[seq - 1],
                stack_date=proc_date,
            )
            db.add(stk)

        # REFLOW (9회)
        for seq in range(1, 10):
            rfw_count += 1
            rfw = model.Reflow(
                reflow_id=f"RFW-{rfw_count:03d}",
                lot_id=lot_id,
                engineer_id=random.choice(eng_ids[:3]),
                reflow_seq=seq,
                temperature=round(247.0 + seq * 0.5 + random.uniform(-0.5, 0.5), 1),
                reflow_date=datetime.combine(
                    pre.measured_date + timedelta(days=seq),
                    datetime.min.time()
                ),
            )
            db.add(rfw)

        # INJECTION
        inj_count += 1
        inj = model.Injection(
            injection_id=f"INJ-{inj_count:03d}",
            lot_id=lot_id,
            engineer_id=random.choice(eng_ids[3:]),
            inject_pressure=round(random.uniform(0.33, 0.46), 2),
            injection_date=datetime.combine(
                pre.measured_date + timedelta(days=11),
                datetime.min.time()
            ),
        )
        db.add(inj)

        # RESULT_ANALYSIS
        rst_count += 1
        final_void = round(random.uniform(0.80, 0.95), 3) if is_defect else round(random.uniform(0.01, 0.08), 3)
        final_result = "사용불가" if is_defect else random.choices(["사용", "재활용"], weights=[85, 15])[0]
        rst = model.ResultAnalysis(
            result_id=f"RST-{rst_count:03d}",
            lot_id=lot_id,
            engineer_id=random.choice(eng_ids[3:]),
            void_area_pct=final_void,
            final_result=final_result,
            analysis_date=pre.measured_date + timedelta(days=12),
        )
        db.add(rst)

        await db.flush()
        created_lots.append(lot_id)

    await db.commit()
    return {
        "created": len(created_lots),
        "lot_ids": created_lots,
        "defect_lots": [created_lots[i] for i in defect_indices if i < len(created_lots)],
    }
