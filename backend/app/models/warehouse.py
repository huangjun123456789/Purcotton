"""仓库相关数据模型"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Enum, Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ShelfType(enum.Enum):
    """货架类型枚举"""
    NORMAL = "normal"           # 普通货架
    HIGH_RACK = "high_rack"     # 高位货架
    GROUND_STACK = "ground_stack"  # 地堆
    MEZZANINE = "mezzanine"     # 阁楼货架
    CANTILEVER = "cantilever"   # 悬臂货架


class Warehouse(Base):
    """仓库表"""
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="仓库编码")
    name = Column(String(100), nullable=False, comment="仓库名称")
    address = Column(String(255), comment="仓库地址")
    description = Column(Text, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    zones = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")


class Zone(Base):
    """库区表"""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, comment="库区编码")
    name = Column(String(100), nullable=False, comment="库区名称")
    description = Column(Text, comment="描述")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="zones")
    aisles = relationship("Aisle", back_populates="zone", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_zone_warehouse", "warehouse_id"),
    )


class Aisle(Base):
    """通道/巷道表"""
    __tablename__ = "aisles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, comment="通道编码，如 01巷")
    name = Column(String(100), nullable=False, comment="通道名称")
    y_coordinate = Column(Integer, nullable=False, comment="Y轴坐标（用于前端渲染）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    zone = relationship("Zone", back_populates="aisles")
    shelves = relationship("Shelf", back_populates="aisle", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_aisle_zone", "zone_id"),
    )


class Shelf(Base):
    """货架表"""
    __tablename__ = "shelves"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    aisle_id = Column(Integer, ForeignKey("aisles.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, comment="货架编码，如 货架01")
    name = Column(String(100), nullable=False, comment="货架名称")
    display_label = Column(String(50), nullable=True, comment="显示标识，用于热力图展示")
    shelf_type = Column(Enum(ShelfType), default=ShelfType.NORMAL, comment="货架类型")
    rows = Column(Integer, default=4, comment="行数（A-D）")
    columns = Column(Integer, default=5, comment="列数（1-5）")
    layers = Column(Integer, default=1, comment="层数（货架高度方向的层数）")
    x_coordinate = Column(Integer, nullable=False, comment="X轴坐标（用于前端渲染）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    aisle = relationship("Aisle", back_populates="shelves")
    locations = relationship("Location", back_populates="shelf", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_shelf_aisle", "aisle_id"),
        Index("idx_shelf_type", "shelf_type"),
    )


class Location(Base):
    """库位表"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, comment="库位编码，如 A1, B2")
    full_code = Column(String(100), nullable=False, unique=True, comment="完整库位编码")
    row_label = Column(String(10), nullable=False, comment="行标签，如 A, B, C, D")
    column_number = Column(Integer, nullable=False, comment="列号，如 1, 2, 3")
    row_index = Column(Integer, nullable=False, comment="行索引（0-based，用于前端渲染）")
    column_index = Column(Integer, nullable=False, comment="列索引（0-based，用于前端渲染）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    shelf = relationship("Shelf", back_populates="locations")
    heat_data = relationship("LocationHeatData", back_populates="location", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_location_shelf", "shelf_id"),
        Index("idx_location_code", "code"),
        Index("idx_location_full_code", "full_code"),
    )


class LocationHeatData(Base):
    """库位热度数据表"""
    __tablename__ = "location_heat_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False, comment="统计日期")
    pick_frequency = Column(Integer, default=0, comment="拣货频率")
    turnover_rate = Column(Float, default=0.0, comment="周转率")
    heat_value = Column(Float, default=0.0, comment="热度值")
    inventory_qty = Column(Integer, default=0, comment="库存数量")
    inbound_qty = Column(Integer, default=0, comment="入库数量")
    outbound_qty = Column(Integer, default=0, comment="出库数量")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    location = relationship("Location", back_populates="heat_data")
    
    __table_args__ = (
        Index("idx_heat_location", "location_id"),
        Index("idx_heat_date", "date"),
        Index("idx_heat_location_date", "location_id", "date"),
    )


class ImportRecord(Base):
    """导入记录表"""
    __tablename__ = "import_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment="文件名")
    file_type = Column(String(20), nullable=False, comment="文件类型(excel/csv)")
    total_rows = Column(Integer, default=0, comment="总行数")
    success_rows = Column(Integer, default=0, comment="成功导入行数")
    failed_rows = Column(Integer, default=0, comment="失败行数")
    status = Column(String(20), default="success", comment="状态(success/partial/failed)")
    errors = Column(Text, comment="错误信息JSON")
    import_time = Column(DateTime, nullable=False, comment="导入时间")  # 由代码设置本地时间
    
    __table_args__ = (
        Index("idx_import_time", "import_time"),
    )
