"""数据导入 API"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from typing import List, Dict, Any
from app.database import get_db
from app.services.import_service import ImportService

router = APIRouter()


@router.get("/history", summary="获取导入历史记录")
async def get_import_history(
    limit: int = Query(20, description="返回记录数量"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取最近的导入记录"""
    service = ImportService(db)
    return await service.get_import_history(limit)


@router.post("/excel", summary="导入 Excel 数据")
async def import_excel(
    file: UploadFile = File(..., description="Excel 文件 (.xlsx, .xls)"),
    db: AsyncSession = Depends(get_db)
):
    """
    从 Excel 文件导入热度数据
    
    支持的列名:
    - 库位编码 / location_code (必需)
    - 日期 / date (必需)
    - 拣货频率 / pick_frequency (必需)
    - 周转率 / turnover_rate (可选)
    - 库存数量 / inventory_qty (可选)
    - 入库数量 / inbound_qty (可选)
    - 出库数量 / outbound_qty (可选)
    """
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 和 .xls 格式")
    
    content = await file.read()
    service = ImportService(db)
    result = await service.import_from_excel(content, file.filename)
    
    return result


@router.post("/csv", summary="导入 CSV 数据")
async def import_csv(
    file: UploadFile = File(..., description="CSV 文件"),
    db: AsyncSession = Depends(get_db)
):
    """
    从 CSV 文件导入热度数据
    
    支持 UTF-8 和 GBK 编码
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="仅支持 .csv 格式")
    
    content = await file.read()
    service = ImportService(db)
    result = await service.import_from_csv(content, file.filename)
    
    return result


@router.get("/template/excel", summary="下载 Excel 导入模板")
async def download_excel_template(db: AsyncSession = Depends(get_db)):
    """下载 Excel 导入模板（使用数据库中实际的库位编码）"""
    service = ImportService(db)
    df = await service.get_import_template_with_locations()
    
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=heat_data_template.xlsx"
        }
    )


@router.get("/template/csv", summary="下载 CSV 导入模板")
async def download_csv_template(db: AsyncSession = Depends(get_db)):
    """下载 CSV 导入模板（使用数据库中实际的库位编码）"""
    service = ImportService(db)
    df = await service.get_import_template_with_locations()
    
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=heat_data_template.csv"
        }
    )
