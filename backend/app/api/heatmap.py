"""热力图 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.services.heatmap_service import HeatmapService
from app.schemas.warehouse import (
    HeatmapFilterParams, HeatmapDataResponse, ShelfTypeEnum
)

router = APIRouter()


@router.get("/zone/{zone_id}", response_model=HeatmapDataResponse, summary="获取热力图数据")
async def get_heatmap_data(
    zone_id: int,
    time_range: str = Query("today", description="时间范围: today, 7days, 30days, custom"),
    shelf_type: Optional[ShelfTypeEnum] = Query(None, description="货架类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期（自定义时间范围时使用）"),
    end_date: Optional[datetime] = Query(None, description="结束日期（自定义时间范围时使用）"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定库区的热力图数据
    
    - **zone_id**: 库区ID
    - **time_range**: 时间范围 (today/7days/30days/custom)
    - **shelf_type**: 货架类型筛选（可选）
    - **start_date**: 自定义开始日期（time_range=custom 时使用）
    - **end_date**: 自定义结束日期（time_range=custom 时使用）
    """
    params = HeatmapFilterParams(
        zone_id=zone_id,
        shelf_type=shelf_type,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date
    )
    
    service = HeatmapService(db)
    result = await service.get_heatmap_data(zone_id, params)
    
    if not result:
        raise HTTPException(status_code=404, detail="库区不存在")
    
    return result


@router.post("/update", summary="更新库位热度数据")
async def update_heat_data(
    location_id: int,
    date: datetime,
    pick_frequency: int,
    turnover_rate: float = 0.0,
    inventory_qty: int = 0,
    inbound_qty: int = 0,
    outbound_qty: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    更新或创建单个库位的热度数据
    
    - **location_id**: 库位ID
    - **date**: 统计日期
    - **pick_frequency**: 拣货频率
    - **turnover_rate**: 周转率
    - **inventory_qty**: 库存数量
    - **inbound_qty**: 入库数量
    - **outbound_qty**: 出库数量
    """
    service = HeatmapService(db)
    result = await service.update_heat_data(
        location_id=location_id,
        date=date,
        pick_frequency=pick_frequency,
        turnover_rate=turnover_rate,
        inventory_qty=inventory_qty,
        inbound_qty=inbound_qty,
        outbound_qty=outbound_qty
    )
    
    return {
        "success": True,
        "message": "热度数据更新成功",
        "data": {
            "id": result.id,
            "heat_value": result.heat_value
        }
    }


@router.post("/batch-update", summary="批量更新热度数据")
async def batch_update_heat_data(
    data_list: list,
    db: AsyncSession = Depends(get_db)
):
    """
    批量更新热度数据
    
    data_list 格式:
    ```json
    [
        {
            "location_code": "A-01巷-货架01-A1",
            "date": "2024-01-01",
            "pick_frequency": 100,
            "turnover_rate": 0.5,
            "inventory_qty": 50,
            "inbound_qty": 10,
            "outbound_qty": 20
        }
    ]
    ```
    """
    service = HeatmapService(db)
    updated_count = await service.batch_update_heat_data(data_list)
    
    return {
        "success": True,
        "message": f"成功更新 {updated_count} 条记录",
        "updated_count": updated_count
    }


@router.get("/debug/heat-data", summary="调试：获取热力数据统计")
async def debug_heat_data(
    db: AsyncSession = Depends(get_db)
):
    """调试接口：获取数据库中热力数据的统计信息"""
    from sqlalchemy import select, func
    from app.models.warehouse import LocationHeatData, Location, Shelf, Aisle, Zone, Warehouse
    
    # 统计热力数据
    heat_count = await db.execute(select(func.count(LocationHeatData.id)))
    total_heat_records = heat_count.scalar()
    
    # 获取热力数据样本
    heat_sample = await db.execute(
        select(LocationHeatData).order_by(LocationHeatData.id.desc()).limit(10)
    )
    samples = heat_sample.scalars().all()
    
    # 获取库位统计
    location_count = await db.execute(select(func.count(Location.id)))
    total_locations = location_count.scalar()
    
    # 获取库区统计
    zone_result = await db.execute(select(Zone))
    zones = zone_result.scalars().all()
    
    # 获取仓库统计
    warehouse_result = await db.execute(select(Warehouse))
    warehouses = warehouse_result.scalars().all()
    
    return {
        "total_heat_records": total_heat_records,
        "total_locations": total_locations,
        "warehouses": [{"id": w.id, "code": w.code, "name": w.name} for w in warehouses],
        "zones": [{"id": z.id, "code": z.code, "name": z.name, "warehouse_id": z.warehouse_id} for z in zones],
        "heat_data_samples": [
            {
                "id": s.id,
                "location_id": s.location_id,
                "date": str(s.date),
                "pick_frequency": s.pick_frequency,
                "heat_value": s.heat_value
            }
            for s in samples
        ]
    }


@router.delete("/clear-all", summary="清空所有热力数据")
async def clear_all_heat_data(
    db: AsyncSession = Depends(get_db)
):
    """清空所有热力数据，用于重新导入"""
    from sqlalchemy import delete
    from app.models.warehouse import LocationHeatData
    
    # 删除所有热力数据
    result = await db.execute(delete(LocationHeatData))
    await db.commit()
    
    deleted_count = result.rowcount
    
    return {
        "success": True,
        "message": f"已清空 {deleted_count} 条热力数据",
        "deleted_count": deleted_count
    }
