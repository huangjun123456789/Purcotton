"""仓库服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.warehouse import Warehouse, Zone, Aisle, Shelf, Location, ShelfType
from app.schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, ZoneCreate, 
    AisleCreate, ShelfCreate
)


class WarehouseService:
    """仓库服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Warehouse ====================
    
    async def create_warehouse(self, data: WarehouseCreate) -> Warehouse:
        """创建仓库"""
        warehouse = Warehouse(**data.model_dump())
        self.db.add(warehouse)
        await self.db.flush()
        await self.db.refresh(warehouse)
        return warehouse
    
    async def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """获取单个仓库"""
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        return result.scalar_one_or_none()
    
    async def get_warehouses(self, is_active: bool = True) -> List[Warehouse]:
        """获取仓库列表"""
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.is_active == is_active)
        )
        return list(result.scalars().all())
    
    async def update_warehouse(self, warehouse_id: int, data: WarehouseUpdate) -> Optional[Warehouse]:
        """更新仓库"""
        warehouse = await self.get_warehouse(warehouse_id)
        if not warehouse:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(warehouse, key, value)
        
        await self.db.flush()
        await self.db.refresh(warehouse)
        return warehouse
    
    # ==================== Zone ====================
    
    async def create_zone(self, data: ZoneCreate) -> Zone:
        """创建库区"""
        zone = Zone(**data.model_dump())
        self.db.add(zone)
        await self.db.flush()
        await self.db.refresh(zone)
        return zone
    
    async def get_zones(self, warehouse_id: int, is_active: bool = True) -> List[Zone]:
        """获取库区列表"""
        result = await self.db.execute(
            select(Zone)
            .where(and_(Zone.warehouse_id == warehouse_id, Zone.is_active == is_active))
            .order_by(Zone.sort_order)
        )
        return list(result.scalars().all())
    
    # ==================== Aisle ====================
    
    async def create_aisle(self, data: AisleCreate) -> Aisle:
        """创建通道"""
        aisle = Aisle(**data.model_dump())
        self.db.add(aisle)
        await self.db.flush()
        await self.db.refresh(aisle)
        return aisle
    
    async def get_aisles(self, zone_id: int, is_active: bool = True) -> List[Aisle]:
        """获取通道列表"""
        result = await self.db.execute(
            select(Aisle)
            .where(and_(Aisle.zone_id == zone_id, Aisle.is_active == is_active))
            .order_by(Aisle.sort_order)
        )
        return list(result.scalars().all())
    
    # ==================== Shelf ====================
    
    async def create_shelf(self, data: ShelfCreate) -> Shelf:
        """创建货架"""
        shelf = Shelf(**data.model_dump())
        self.db.add(shelf)
        await self.db.flush()
        await self.db.refresh(shelf)
        
        # 自动创建库位
        await self._create_locations_for_shelf(shelf)
        
        return shelf
    
    async def _create_locations_for_shelf(self, shelf: Shelf):
        """为货架创建库位"""
        # 获取货架的完整路径用于生成库位编码
        aisle = await self.db.get(Aisle, shelf.aisle_id)
        zone = await self.db.get(Zone, aisle.zone_id)
        warehouse = await self.db.get(Warehouse, zone.warehouse_id)
        
        row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for row_idx in range(shelf.rows):
            row_label = row_labels[row_idx]
            for col_idx in range(shelf.columns):
                col_num = col_idx + 1
                # 库位编码格式: 库区代码 + 顺序号（如 C1, C2, B1, B2）
                # 顺序号 = 行索引 * 列数 + 列索引 + 1
                seq_num = row_idx * shelf.columns + col_idx + 1
                code = f"{zone.code}{seq_num}"
                # 加入仓库编码确保全局唯一
                full_code = f"{warehouse.code}-{zone.code}-{aisle.code}-{shelf.code}-{code}"
                
                location = Location(
                    shelf_id=shelf.id,
                    code=code,
                    full_code=full_code,
                    row_label=row_label,
                    column_number=col_num,
                    row_index=row_idx,
                    column_index=col_idx
                )
                self.db.add(location)
        
        await self.db.flush()
    
    async def get_shelves(
        self, 
        aisle_id: int, 
        shelf_type: Optional[ShelfType] = None,
        is_active: bool = True
    ) -> List[Shelf]:
        """获取货架列表"""
        conditions = [Shelf.aisle_id == aisle_id, Shelf.is_active == is_active]
        if shelf_type:
            conditions.append(Shelf.shelf_type == shelf_type)
        
        result = await self.db.execute(
            select(Shelf)
            .where(and_(*conditions))
            .order_by(Shelf.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_shelf(self, shelf_id: int) -> Optional[Shelf]:
        """获取单个货架"""
        result = await self.db.execute(
            select(Shelf).where(Shelf.id == shelf_id)
        )
        return result.scalar_one_or_none()
    
    async def update_shelf_display_label(self, shelf_id: int, display_label: str) -> Optional[Shelf]:
        """更新货架的显示标识"""
        shelf = await self.get_shelf(shelf_id)
        if not shelf:
            return None
        
        shelf.display_label = display_label
        await self.db.flush()
        await self.db.refresh(shelf)
        await self.db.commit()
        return shelf
    
    # ==================== Location ====================
    
    async def get_locations(self, shelf_id: int, is_active: bool = True) -> List[Location]:
        """获取库位列表"""
        result = await self.db.execute(
            select(Location)
            .where(and_(Location.shelf_id == shelf_id, Location.is_active == is_active))
            .order_by(Location.row_index, Location.column_index)
        )
        return list(result.scalars().all())
    
    async def get_location_by_code(self, full_code: str) -> Optional[Location]:
        """根据完整编码获取库位"""
        result = await self.db.execute(
            select(Location).where(Location.full_code == full_code)
        )
        return result.scalar_one_or_none()
    
    async def get_warehouse_layout(self, warehouse_id: int) -> dict:
        """
        获取仓库的完整布局数据，用于画布编辑器加载
        
        返回格式:
        {
            "zones": [
                {
                    "code": "A",
                    "name": "A库区",
                    "color": "#409eff",
                    "aisles": [
                        {
                            "code": "01巷",
                            "name": "01巷",
                            "y_coordinate": 0,
                            "shelves": [
                                {
                                    "code": "货架01",
                                    "shelf_type": "normal",
                                    "rows": 4,
                                    "columns": 5,
                                    "x_coordinate": 0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        """
        # 库区颜色列表
        zone_colors = [
            '#409eff', '#67c23a', '#e6a23c', '#f56c6c', 
            '#909399', '#9c27b0', '#00bcd4', '#ff9800'
        ]
        
        zones = await self.get_zones(warehouse_id)
        layout_data = {"zones": []}
        
        for zone_idx, zone in enumerate(zones):
            zone_data = {
                "code": zone.code,
                "name": zone.name,
                "color": zone_colors[zone_idx % len(zone_colors)],
                "aisles": []
            }
            
            aisles = await self.get_aisles(zone.id)
            for aisle in aisles:
                aisle_data = {
                    "code": aisle.code,
                    "name": aisle.name,
                    "y_coordinate": aisle.y_coordinate,
                    "shelves": []
                }
                
                shelves = await self.get_shelves(aisle.id)
                for shelf in shelves:
                    shelf_data = {
                        "code": shelf.code,
                        "name": shelf.name,
                        "shelf_type": shelf.shelf_type.value,
                        "rows": shelf.rows,
                        "columns": shelf.columns,
                        "layers": shelf.layers if hasattr(shelf, 'layers') else 1,
                        "x_coordinate": shelf.x_coordinate
                    }
                    aisle_data["shelves"].append(shelf_data)
                
                zone_data["aisles"].append(aisle_data)
            
            layout_data["zones"].append(zone_data)
        
        return layout_data
    
    # ==================== 批量创建 ====================
    
    async def setup_warehouse_layout(
        self,
        warehouse_code: str,
        warehouse_name: str,
        zones_config: List[dict]
    ) -> Warehouse:
        """
        批量设置仓库布局
        
        zones_config 示例:
        [
            {
                "code": "A",
                "name": "A库区",
                "aisles": [
                    {
                        "code": "01巷",
                        "name": "01巷",
                        "y_coordinate": 0,
                        "shelves": [
                            {
                                "code": "货架01",
                                "name": "货架01",
                                "shelf_type": "normal",
                                "rows": 4,
                                "columns": 5,
                                "x_coordinate": 0
                            }
                        ]
                    }
                ]
            }
        ]
        """
        # 先查找仓库是否已存在
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.code == warehouse_code)
        )
        warehouse = result.scalar_one_or_none()
        
        if warehouse:
            # 仓库已存在，先删除所有现有的库区（级联删除巷道、货架、库位）
            zones_result = await self.db.execute(
                select(Zone).where(Zone.warehouse_id == warehouse.id)
            )
            existing_zones = list(zones_result.scalars().all())
            for zone in existing_zones:
                await self.db.delete(zone)
            await self.db.flush()
        else:
            # 仓库不存在，创建新仓库
            warehouse = Warehouse(code=warehouse_code, name=warehouse_name)
            self.db.add(warehouse)
            await self.db.flush()
        
        for zone_idx, zone_config in enumerate(zones_config):
            zone = Zone(
                warehouse_id=warehouse.id,
                code=zone_config["code"],
                name=zone_config["name"],
                sort_order=zone_idx
            )
            self.db.add(zone)
            await self.db.flush()
            
            for aisle_idx, aisle_config in enumerate(zone_config.get("aisles", [])):
                aisle = Aisle(
                    zone_id=zone.id,
                    code=aisle_config["code"],
                    name=aisle_config["name"],
                    y_coordinate=aisle_config.get("y_coordinate", aisle_idx),
                    sort_order=aisle_idx
                )
                self.db.add(aisle)
                await self.db.flush()
                
                for shelf_idx, shelf_config in enumerate(aisle_config.get("shelves", [])):
                    shelf_type_str = shelf_config.get("shelf_type", "normal")
                    shelf_type = ShelfType(shelf_type_str)
                    
                    shelf = Shelf(
                        aisle_id=aisle.id,
                        code=shelf_config["code"],
                        name=shelf_config["name"],
                        shelf_type=shelf_type,
                        rows=shelf_config.get("rows", 4),
                        columns=shelf_config.get("columns", 5),
                        layers=shelf_config.get("layers", 1),
                        x_coordinate=shelf_config.get("x_coordinate", shelf_idx),
                        sort_order=shelf_idx
                    )
                    self.db.add(shelf)
                    await self.db.flush()
                    
                    # 创建库位
                    await self._create_locations_for_shelf(shelf)
        
        await self.db.refresh(warehouse)
        return warehouse
