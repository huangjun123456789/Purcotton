"""热力图服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from app.models.warehouse import (
    Zone, Aisle, Shelf, Location, LocationHeatData, ShelfType
)
from app.schemas.warehouse import (
    HeatmapFilterParams, HeatmapDataResponse,
    AisleHeatData, ShelfHeatData, LocationHeatItem,
    ShelfTypeEnum
)
from app.config import settings


class HeatmapService:
    """热力图服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _get_date_range(self, params: HeatmapFilterParams) -> Tuple[datetime, datetime]:
        """根据筛选参数获取日期范围"""
        now = datetime.now()
        # end_date 设置为未来30天，确保包含所有数据
        end_date = (now + timedelta(days=30)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        if params.time_range == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif params.time_range == "7days":
            start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif params.time_range == "30days":
            start_date = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif params.time_range == "all":
            # 全部数据：从很早到很晚
            start_date = datetime(2000, 1, 1)
            end_date = datetime(2100, 12, 31, 23, 59, 59)
        elif params.time_range == "custom":
            start_date = params.start_date or (now - timedelta(days=30))
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            end_date = params.end_date or now
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # 默认显示全部数据
            start_date = datetime(2000, 1, 1)
            end_date = datetime(2100, 12, 31, 23, 59, 59)
        
        return start_date, end_date
    
    async def get_heatmap_data(
        self, 
        zone_id: int,
        params: HeatmapFilterParams
    ) -> Optional[HeatmapDataResponse]:
        """获取热力图数据"""
        # 获取库区信息
        zone_result = await self.db.execute(
            select(Zone).where(Zone.id == zone_id)
        )
        zone = zone_result.scalar_one_or_none()
        if not zone:
            return None
        
        start_date, end_date = self._get_date_range(params)
        
        # 构建查询
        aisle_query = select(Aisle).where(
            and_(Aisle.zone_id == zone_id, Aisle.is_active == True)
        ).order_by(Aisle.sort_order)
        
        aisle_result = await self.db.execute(aisle_query)
        aisles = aisle_result.scalars().all()
        
        aisles_data = []
        all_heat_values = []
        
        for aisle in aisles:
            # 获取货架
            shelf_conditions = [Shelf.aisle_id == aisle.id, Shelf.is_active == True]
            if params.shelf_type:
                shelf_conditions.append(Shelf.shelf_type == ShelfType(params.shelf_type.value))
            
            shelf_query = select(Shelf).where(and_(*shelf_conditions)).order_by(Shelf.sort_order)
            shelf_result = await self.db.execute(shelf_query)
            shelves = shelf_result.scalars().all()
            
            shelves_data = []
            for shelf in shelves:
                # 获取库位及其热度数据
                location_query = (
                    select(Location)
                    .where(and_(Location.shelf_id == shelf.id, Location.is_active == True))
                    .order_by(Location.row_index, Location.column_index)
                )
                location_result = await self.db.execute(location_query)
                locations = location_result.scalars().all()
                
                locations_data = []
                for location in locations:
                    # 获取该库位在时间范围内的聚合热度数据
                    heat_data = await self._get_aggregated_heat_data(
                        location.id, start_date, end_date
                    )
                    
                    heat_value = heat_data.get("heat_value", 0)
                    all_heat_values.append(heat_value)
                    
                    locations_data.append(LocationHeatItem(
                        location_id=location.id,
                        location_code=location.code,
                        full_code=location.full_code,
                        row_label=location.row_label,
                        column_number=location.column_number,
                        row_index=location.row_index,
                        column_index=location.column_index,
                        heat_value=heat_value,
                        pick_frequency=heat_data.get("pick_frequency", 0),
                        turnover_rate=heat_data.get("turnover_rate", 0),
                        inventory_qty=heat_data.get("inventory_qty", 0)
                    ))
                
                shelves_data.append(ShelfHeatData(
                    shelf_id=shelf.id,
                    shelf_code=shelf.code,
                    shelf_name=shelf.name,
                    display_label=shelf.display_label,
                    shelf_type=ShelfTypeEnum(shelf.shelf_type.value),
                    x_coordinate=shelf.x_coordinate,
                    rows=shelf.rows,
                    columns=shelf.columns,
                    layers=shelf.layers if hasattr(shelf, 'layers') else 1,
                    locations=locations_data
                ))
            
            if shelves_data:
                aisles_data.append(AisleHeatData(
                    aisle_id=aisle.id,
                    aisle_code=aisle.code,
                    aisle_name=aisle.name,
                    y_coordinate=aisle.y_coordinate,
                    shelves=shelves_data
                ))
        
        min_heat = min(all_heat_values) if all_heat_values else 0
        max_heat = max(all_heat_values) if all_heat_values else 0
        
        return HeatmapDataResponse(
            zone_id=zone.id,
            zone_code=zone.code,
            zone_name=zone.name,
            aisles=aisles_data,
            min_heat=min_heat,
            max_heat=max_heat,
            time_range=params.time_range,
            start_date=start_date,
            end_date=end_date
        )
    
    async def _get_aggregated_heat_data(
        self, 
        location_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> dict:
        """获取聚合的热度数据"""
        # 直接使用 datetime 比较，更可靠且兼容性更好
        query = select(
            func.sum(LocationHeatData.pick_frequency).label("total_pick_frequency"),
            func.avg(LocationHeatData.turnover_rate).label("avg_turnover_rate"),
            func.sum(LocationHeatData.inventory_qty).label("total_inventory_qty"),
            func.sum(LocationHeatData.heat_value).label("total_heat_value")
        ).where(
            and_(
                LocationHeatData.location_id == location_id,
                LocationHeatData.date >= start_date,
                LocationHeatData.date <= end_date
            )
        )
        
        result = await self.db.execute(query)
        row = result.one_or_none()
        
        # 检查是否有匹配的数据（任何一个聚合值不为 NULL 即表示有数据）
        has_data = row and (
            row.total_pick_frequency is not None or 
            row.total_heat_value is not None or
            row.total_inventory_qty is not None
        )
        
        if has_data:
            pick_frequency = int(row.total_pick_frequency or 0)
            turnover_rate = float(row.avg_turnover_rate or 0)
            inventory_qty = int(row.total_inventory_qty or 0)
            heat_value = float(row.total_heat_value or 0)
            
            # 如果数据库中存储的 heat_value 为 0，使用 pick_frequency 作为热度值
            if heat_value == 0 and pick_frequency > 0:
                heat_value = float(pick_frequency)
            
            return {
                "pick_frequency": pick_frequency,
                "turnover_rate": turnover_rate,
                "inventory_qty": inventory_qty,
                "heat_value": heat_value
            }
        
        return {
            "pick_frequency": 0,
            "turnover_rate": 0,
            "inventory_qty": 0,
            "heat_value": 0
        }
    
    async def update_heat_data(
        self,
        location_id: int,
        date: datetime,
        pick_frequency: int,
        turnover_rate: float,
        inventory_qty: int = 0,
        inbound_qty: int = 0,
        outbound_qty: int = 0
    ) -> LocationHeatData:
        """更新或创建库位热度数据"""
        # 查找是否已存在该日期的数据
        # 将日期归一化为当天的 00:00:00 到 23:59:59
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = select(LocationHeatData).where(
            and_(
                LocationHeatData.location_id == location_id,
                LocationHeatData.date >= date_start,
                LocationHeatData.date <= date_end
            )
        )
        result = await self.db.execute(query)
        heat_data = result.scalar_one_or_none()
        
        # 计算热度值: 暂时仅使用拣货频次作为热度指标
        heat_value = float(pick_frequency)
        
        if heat_data:
            # 更新现有数据
            heat_data.pick_frequency = pick_frequency
            heat_data.turnover_rate = turnover_rate
            heat_data.heat_value = heat_value
            heat_data.inventory_qty = inventory_qty
            heat_data.inbound_qty = inbound_qty
            heat_data.outbound_qty = outbound_qty
        else:
            # 创建新数据
            heat_data = LocationHeatData(
                location_id=location_id,
                date=date,
                pick_frequency=pick_frequency,
                turnover_rate=turnover_rate,
                heat_value=heat_value,
                inventory_qty=inventory_qty,
                inbound_qty=inbound_qty,
                outbound_qty=outbound_qty
            )
            self.db.add(heat_data)
        
        await self.db.flush()
        await self.db.refresh(heat_data)
        return heat_data
    
    async def batch_update_heat_data(self, data_list: List[dict]) -> int:
        """
        批量更新热度数据
        
        data_list 格式:
        [
            {
                "location_code": "A-01巷-货架01-A1",  # 完整库位编码
                "date": "2024-01-01",
                "pick_frequency": 100,
                "turnover_rate": 0.5,
                "inventory_qty": 50,
                "inbound_qty": 10,
                "outbound_qty": 20
            }
        ]
        """
        updated_count = 0
        
        for item in data_list:
            # 根据库位编码查找库位
            location_query = select(Location).where(
                Location.full_code == item["location_code"]
            )
            location_result = await self.db.execute(location_query)
            location = location_result.scalar_one_or_none()
            
            if location:
                date = item["date"]
                if isinstance(date, str):
                    date = datetime.fromisoformat(date)
                
                await self.update_heat_data(
                    location_id=location.id,
                    date=date,
                    pick_frequency=item.get("pick_frequency", 0),
                    turnover_rate=item.get("turnover_rate", 0),
                    inventory_qty=item.get("inventory_qty", 0),
                    inbound_qty=item.get("inbound_qty", 0),
                    outbound_qty=item.get("outbound_qty", 0)
                )
                updated_count += 1
        
        return updated_count
