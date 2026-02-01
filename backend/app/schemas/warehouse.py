"""仓库相关 Pydantic 模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ShelfTypeEnum(str, Enum):
    """货架类型枚举"""
    NORMAL = "normal"
    HIGH_RACK = "high_rack"
    GROUND_STACK = "ground_stack"
    MEZZANINE = "mezzanine"
    CANTILEVER = "cantilever"


# ==================== Warehouse ====================

class WarehouseBase(BaseModel):
    """仓库基础模式"""
    code: str = Field(..., max_length=50, description="仓库编码")
    name: str = Field(..., max_length=100, description="仓库名称")
    address: Optional[str] = Field(None, max_length=255, description="仓库地址")
    description: Optional[str] = Field(None, description="描述")


class WarehouseCreate(WarehouseBase):
    """创建仓库"""
    pass


class WarehouseUpdate(BaseModel):
    """更新仓库"""
    name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    """仓库响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Zone ====================

class ZoneBase(BaseModel):
    """库区基础模式"""
    code: str = Field(..., max_length=50, description="库区编码")
    name: str = Field(..., max_length=100, description="库区名称")
    description: Optional[str] = None
    sort_order: int = 0


class ZoneCreate(ZoneBase):
    """创建库区"""
    warehouse_id: int


class ZoneResponse(ZoneBase):
    """库区响应"""
    id: int
    warehouse_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Aisle ====================

class AisleBase(BaseModel):
    """通道基础模式"""
    code: str = Field(..., max_length=50, description="通道编码")
    name: str = Field(..., max_length=100, description="通道名称")
    y_coordinate: int = Field(..., description="Y轴坐标")
    sort_order: int = 0


class AisleCreate(AisleBase):
    """创建通道"""
    zone_id: int


class AisleResponse(AisleBase):
    """通道响应"""
    id: int
    zone_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Shelf ====================

class ShelfBase(BaseModel):
    """货架基础模式"""
    code: str = Field(..., max_length=50, description="货架编码")
    name: str = Field(..., max_length=100, description="货架名称")
    display_label: Optional[str] = Field(None, max_length=50, description="显示标识")
    shelf_type: ShelfTypeEnum = ShelfTypeEnum.NORMAL
    rows: int = Field(4, ge=1, le=26, description="行数")
    columns: int = Field(5, ge=1, le=100, description="列数")
    layers: int = Field(1, ge=1, le=10, description="层数")
    x_coordinate: int = Field(..., description="X轴坐标")
    sort_order: int = 0


class ShelfCreate(ShelfBase):
    """创建货架"""
    aisle_id: int


class ShelfResponse(ShelfBase):
    """货架响应"""
    id: int
    aisle_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Location ====================

class LocationResponse(BaseModel):
    """库位响应"""
    id: int
    shelf_id: int
    code: str
    full_code: str
    row_label: str
    column_number: int
    row_index: int
    column_index: int
    is_active: bool
    
    class Config:
        from_attributes = True


# ==================== LocationHeatData ====================

class LocationHeatDataResponse(BaseModel):
    """库位热度数据响应"""
    id: int
    location_id: int
    date: datetime
    pick_frequency: int
    turnover_rate: float
    heat_value: float
    inventory_qty: int
    inbound_qty: int
    outbound_qty: int
    
    class Config:
        from_attributes = True


# ==================== Heatmap ====================

class HeatmapFilterParams(BaseModel):
    """热力图筛选参数"""
    zone_id: Optional[int] = Field(None, description="库区ID")
    shelf_type: Optional[ShelfTypeEnum] = Field(None, description="货架类型")
    time_range: str = Field("today", description="时间范围: today, 7days, 30days, custom")
    start_date: Optional[datetime] = Field(None, description="开始日期（自定义时间范围时使用）")
    end_date: Optional[datetime] = Field(None, description="结束日期（自定义时间范围时使用）")


class LocationHeatItem(BaseModel):
    """单个库位热度项"""
    location_id: int
    location_code: str
    full_code: str
    row_label: str
    column_number: int
    row_index: int
    column_index: int
    heat_value: float
    pick_frequency: int
    turnover_rate: float
    inventory_qty: int


class ShelfHeatData(BaseModel):
    """货架热度数据"""
    shelf_id: int
    shelf_code: str
    shelf_name: str
    display_label: Optional[str] = None
    shelf_type: ShelfTypeEnum
    x_coordinate: int
    rows: int
    columns: int
    layers: int = 1
    locations: List[LocationHeatItem]


class ShelfDisplayLabelUpdate(BaseModel):
    """更新货架显示标识"""
    display_label: str = Field(..., max_length=50, description="显示标识")


class AisleHeatData(BaseModel):
    """通道热度数据"""
    aisle_id: int
    aisle_code: str
    aisle_name: str
    y_coordinate: int
    shelves: List[ShelfHeatData]


class HeatmapDataResponse(BaseModel):
    """热力图数据响应"""
    zone_id: int
    zone_code: str
    zone_name: str
    aisles: List[AisleHeatData]
    min_heat: float
    max_heat: float
    time_range: str
    start_date: datetime
    end_date: datetime
