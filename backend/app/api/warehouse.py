"""仓库管理 API"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.warehouse_service import WarehouseService
from app.schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    ZoneCreate, ZoneResponse,
    AisleCreate, AisleResponse,
    ShelfCreate, ShelfResponse,
    LocationResponse, ShelfTypeEnum,
    ShelfDisplayLabelUpdate
)

router = APIRouter()


# ==================== Warehouse ====================

@router.post("/", response_model=WarehouseResponse, summary="创建仓库")
async def create_warehouse(
    data: WarehouseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新仓库"""
    service = WarehouseService(db)
    return await service.create_warehouse(data)


@router.get("/", response_model=List[WarehouseResponse], summary="获取仓库列表")
async def get_warehouses(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取所有仓库"""
    service = WarehouseService(db)
    return await service.get_warehouses(is_active)


@router.get("/{warehouse_id}", response_model=WarehouseResponse, summary="获取单个仓库")
async def get_warehouse(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取指定仓库"""
    service = WarehouseService(db)
    warehouse = await service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse


@router.put("/{warehouse_id}", response_model=WarehouseResponse, summary="更新仓库")
async def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新仓库信息"""
    service = WarehouseService(db)
    warehouse = await service.update_warehouse(warehouse_id, data)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse


# ==================== Zone ====================

@router.post("/zone", response_model=ZoneResponse, summary="创建库区")
async def create_zone(
    data: ZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新库区"""
    service = WarehouseService(db)
    return await service.create_zone(data)


@router.get("/{warehouse_id}/zones", response_model=List[ZoneResponse], summary="获取库区列表")
async def get_zones(
    warehouse_id: int,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取指定仓库的所有库区"""
    service = WarehouseService(db)
    return await service.get_zones(warehouse_id, is_active)


# ==================== Aisle ====================

@router.post("/aisle", response_model=AisleResponse, summary="创建通道")
async def create_aisle(
    data: AisleCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新通道"""
    service = WarehouseService(db)
    return await service.create_aisle(data)


@router.get("/zone/{zone_id}/aisles", response_model=List[AisleResponse], summary="获取通道列表")
async def get_aisles(
    zone_id: int,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取指定库区的所有通道"""
    service = WarehouseService(db)
    return await service.get_aisles(zone_id, is_active)


# ==================== Shelf ====================

@router.post("/shelf", response_model=ShelfResponse, summary="创建货架")
async def create_shelf(
    data: ShelfCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新货架（自动创建库位）"""
    service = WarehouseService(db)
    return await service.create_shelf(data)


@router.get("/aisle/{aisle_id}/shelves", response_model=List[ShelfResponse], summary="获取货架列表")
async def get_shelves(
    aisle_id: int,
    shelf_type: ShelfTypeEnum = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取指定通道的所有货架"""
    service = WarehouseService(db)
    from app.models.warehouse import ShelfType
    shelf_type_enum = ShelfType(shelf_type.value) if shelf_type else None
    return await service.get_shelves(aisle_id, shelf_type_enum, is_active)


# ==================== Shelf Display Label ====================

@router.put("/shelf/{shelf_id}/display-label", response_model=ShelfResponse, summary="更新货架显示标识")
async def update_shelf_display_label(
    shelf_id: int,
    data: ShelfDisplayLabelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新货架的显示标识（用于热力图展示）"""
    service = WarehouseService(db)
    shelf = await service.update_shelf_display_label(shelf_id, data.display_label)
    if not shelf:
        raise HTTPException(status_code=404, detail="货架不存在")
    return shelf


# ==================== Location ====================

@router.get("/shelf/{shelf_id}/locations", response_model=List[LocationResponse], summary="获取库位列表")
async def get_locations(
    shelf_id: int,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """获取指定货架的所有库位"""
    service = WarehouseService(db)
    return await service.get_locations(shelf_id, is_active)


# ==================== 布局管理 ====================

@router.get("/{warehouse_id}/layout", summary="获取仓库布局数据")
async def get_warehouse_layout(
    warehouse_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取仓库的完整布局数据，用于画布编辑器加载"""
    service = WarehouseService(db)
    warehouse = await service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return await service.get_warehouse_layout(warehouse_id)


@router.post("/setup", response_model=WarehouseResponse, summary="批量设置仓库布局")
async def setup_warehouse_layout(
    warehouse_code: str,
    warehouse_name: str,
    zones_config: List[dict] = Body(..., description="库区配置列表"),
    db: AsyncSession = Depends(get_db)
):
    """
    批量设置仓库布局
    
    zones_config 示例:
    ```json
    [
        {
            "code": "A",
            "name": "A库区",
            "aisles": [
                {
                    "code": "01巷",
                    "name": "01巷道",
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
    ```
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Setting up warehouse layout: code={warehouse_code}, name={warehouse_name}")
        logger.info(f"Zones config: {zones_config}")
        service = WarehouseService(db)
        result = await service.setup_warehouse_layout(warehouse_code, warehouse_name, zones_config)
        logger.info(f"Layout setup successful for warehouse: {warehouse_code}")
        return result
    except Exception as e:
        logger.error(f"Layout setup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"布局生成失败: {str(e)}")
