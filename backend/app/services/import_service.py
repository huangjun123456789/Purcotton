"""数据导入服务"""
import pandas as pd
import re
import json
from io import BytesIO
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.warehouse import Warehouse, Zone, Aisle, Shelf, Location, ShelfType, ImportRecord
from app.services.heatmap_service import HeatmapService


class ImportService:
    """数据导入服务类"""
    
    # 必需的列名映射
    REQUIRED_COLUMNS = {
        "location_code": ["库位编码", "location_code", "库位", "full_code"],
        "date": ["日期", "date", "统计日期"],
        "pick_frequency": ["拣货频率", "pick_frequency", "拣货次数", "frequency"],
    }
    
    OPTIONAL_COLUMNS = {
        "turnover_rate": ["周转率", "turnover_rate", "turnover"],
        "inventory_qty": ["库存数量", "inventory_qty", "inventory", "库存"],
        "inbound_qty": ["入库数量", "inbound_qty", "inbound", "入库"],
        "outbound_qty": ["出库数量", "outbound_qty", "outbound", "出库"],
        "display_label": ["显示标识", "display_label", "标识", "自定义编码"],
    }
    
    # 默认仓库名称
    DEFAULT_WAREHOUSE_CODE = "WH001"
    DEFAULT_WAREHOUSE_NAME = "默认仓库"
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.heatmap_service = HeatmapService(db)
        # 缓存已创建的实体，避免重复查询
        self._warehouse_cache: Dict[str, Warehouse] = {}
        self._zone_cache: Dict[str, Zone] = {}
        self._aisle_cache: Dict[str, Aisle] = {}
        self._shelf_cache: Dict[str, Shelf] = {}
        self._location_cache: Dict[str, Location] = {}
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> str | None:
        """在 DataFrame 中查找列名"""
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    def _parse_date(self, date_value) -> datetime:
        """
        解析多种日期格式
        支持: 2026/1/31, 2026-1-31, 2026-01-31, 2026/01/31, pd.Timestamp 等
        """
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            date_str = date_value.strip()
            # 尝试多种日期格式
            date_formats = [
                "%Y-%m-%d",      # 2026-01-31
                "%Y/%m/%d",      # 2026/01/31
                "%Y-%m-%d %H:%M:%S",  # 带时间
                "%Y/%m/%d %H:%M:%S",
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # 尝试 ISO 格式
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                pass
            
            # 尝试处理单数字月日 (如 2026/1/31 -> 2026-01-31)
            import re
            match = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})(.*)$', date_str)
            if match:
                year, month, day, rest = match.groups()
                normalized = f"{year}-{int(month):02d}-{int(day):02d}"
                if rest:
                    # 处理时间部分
                    time_match = re.match(r'[\sT]+(\d{1,2}):(\d{1,2}):?(\d{1,2})?', rest)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2))
                        second = int(time_match.group(3) or 0)
                        return datetime(int(year), int(month), int(day), hour, minute, second)
                return datetime.strptime(normalized, "%Y-%m-%d")
        
        # 默认返回当前日期
        return datetime.now()
    
    def _parse_location_code(self, full_code: str) -> Optional[Dict[str, str]]:
        """
        解析库位编码，支持多种格式：
        - 格式1: C-01巷-货架01-C1 (库区-巷道-货架-库位，库位格式为库区代码+顺序号)
        - 格式2: A-01巷-货架01-A1 (旧格式，兼容)
        - 格式3: A-01-01-A1 (简化格式)
        
        返回解析后的各部分，如：
        {
            "zone_code": "C",
            "aisle_code": "01巷",
            "shelf_code": "货架01",
            "location_code": "C1",
            "row_label": "A",
            "column_number": 1
        }
        """
        parts = full_code.split("-")
        if len(parts) < 4:
            return None
        
        # 提取各部分
        zone_code = parts[0]
        aisle_code = parts[1]
        shelf_code = parts[2]
        location_code = parts[3]
        
        # 解析库位编码，格式为: 库区代码 + 顺序号 (如 C1, C2, B1, LP1, LP2)
        # 支持单字符(C, B)和多字符(LP)库区代码
        match = re.match(r'^([A-Z]+)(\d+)$', location_code)
        if not match:
            return None
        
        location_zone_code = match.group(1)
        seq_number = int(match.group(2))
        
        # 根据顺序号推算行列（假设默认5列）
        default_columns = 5
        row_idx = (seq_number - 1) // default_columns
        col_idx = (seq_number - 1) % default_columns
        row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        row_label = row_labels[row_idx] if row_idx < len(row_labels) else "A"
        column_number = col_idx + 1
        
        return {
            "zone_code": zone_code,
            "aisle_code": aisle_code,
            "shelf_code": shelf_code,
            "location_code": location_code,
            "row_label": row_label,
            "column_number": column_number
        }
    
    async def _get_or_create_warehouse(self) -> Warehouse:
        """获取或创建仓库（优先使用已存在的第一个仓库）"""
        # 检查缓存
        if "_active_warehouse" in self._warehouse_cache:
            return self._warehouse_cache["_active_warehouse"]
        
        # 优先获取已存在的第一个活跃仓库
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.id).limit(1)
        )
        warehouse = result.scalar_one_or_none()
        
        # 如果没有仓库，创建默认仓库
        if not warehouse:
            warehouse = Warehouse(
                code=self.DEFAULT_WAREHOUSE_CODE,
                name=self.DEFAULT_WAREHOUSE_NAME
            )
            self.db.add(warehouse)
            await self.db.flush()
        
        self._warehouse_cache["_active_warehouse"] = warehouse
        return warehouse
    
    async def _get_or_create_zone(self, warehouse_id: int, zone_code: str) -> Zone:
        """获取或创建库区"""
        cache_key = f"{warehouse_id}_{zone_code}"
        if cache_key in self._zone_cache:
            return self._zone_cache[cache_key]
        
        result = await self.db.execute(
            select(Zone).where(
                Zone.warehouse_id == warehouse_id,
                Zone.code == zone_code
            )
        )
        zone = result.scalar_one_or_none()
        
        if not zone:
            zone = Zone(
                warehouse_id=warehouse_id,
                code=zone_code,
                name=f"{zone_code}库区"
            )
            self.db.add(zone)
            await self.db.flush()
        
        self._zone_cache[cache_key] = zone
        return zone
    
    async def _get_or_create_aisle(self, zone_id: int, aisle_code: str, y_coordinate: int = 0) -> Aisle:
        """获取或创建巷道"""
        cache_key = f"{zone_id}_{aisle_code}"
        if cache_key in self._aisle_cache:
            return self._aisle_cache[cache_key]
        
        result = await self.db.execute(
            select(Aisle).where(
                Aisle.zone_id == zone_id,
                Aisle.code == aisle_code
            )
        )
        aisle = result.scalar_one_or_none()
        
        if not aisle:
            # 计算 y 坐标
            count_result = await self.db.execute(
                select(Aisle).where(Aisle.zone_id == zone_id)
            )
            existing_count = len(list(count_result.scalars().all()))
            
            aisle = Aisle(
                zone_id=zone_id,
                code=aisle_code,
                name=aisle_code,
                y_coordinate=existing_count,
                sort_order=existing_count
            )
            self.db.add(aisle)
            await self.db.flush()
        
        self._aisle_cache[cache_key] = aisle
        return aisle
    
    async def _get_or_create_shelf(self, aisle_id: int, shelf_code: str, rows: int = 4, columns: int = 5, display_label: str = None) -> Shelf:
        """获取或创建货架"""
        cache_key = f"{aisle_id}_{shelf_code}"
        if cache_key in self._shelf_cache:
            shelf = self._shelf_cache[cache_key]
            # 如果提供了 display_label 且与现有值不同，则更新
            if display_label and shelf.display_label != display_label:
                shelf.display_label = display_label
                await self.db.flush()
            return shelf
        
        result = await self.db.execute(
            select(Shelf).where(
                Shelf.aisle_id == aisle_id,
                Shelf.code == shelf_code
            )
        )
        shelf = result.scalar_one_or_none()
        
        if not shelf:
            # 计算 x 坐标
            count_result = await self.db.execute(
                select(Shelf).where(Shelf.aisle_id == aisle_id)
            )
            existing_count = len(list(count_result.scalars().all()))
            
            shelf = Shelf(
                aisle_id=aisle_id,
                code=shelf_code,
                name=shelf_code,
                display_label=display_label,
                shelf_type=ShelfType.NORMAL,
                rows=rows,
                columns=columns,
                x_coordinate=existing_count,
                sort_order=existing_count
            )
            self.db.add(shelf)
            await self.db.flush()
        else:
            # 如果提供了 display_label 且与现有值不同，则更新
            if display_label and shelf.display_label != display_label:
                shelf.display_label = display_label
                await self.db.flush()
        
        self._shelf_cache[cache_key] = shelf
        return shelf
    
    async def _get_location_by_full_code(self, full_code: str) -> Optional[Location]:
        """
        直接通过完整库位编码查找库位
        
        这是首选方法，避免解析和重建库位编码可能导致的格式不匹配问题
        """
        # 先检查缓存
        if full_code in self._location_cache:
            return self._location_cache[full_code]
        
        # 查询数据库
        result = await self.db.execute(
            select(Location).where(Location.full_code == full_code)
        )
        location = result.scalar_one_or_none()
        
        if location:
            self._location_cache[full_code] = location
        
        return location
    
    async def _update_shelf_display_label(self, shelf_id: int, display_label: str) -> None:
        """
        更新货架的显示标识
        
        使用缓存避免重复更新同一货架
        """
        cache_key = f"shelf_label_{shelf_id}"
        
        # 如果已经更新过且值相同，跳过
        if cache_key in self._shelf_cache:
            cached_label = getattr(self._shelf_cache[cache_key], 'display_label', None)
            if cached_label == display_label:
                return
        
        # 查询货架
        result = await self.db.execute(
            select(Shelf).where(Shelf.id == shelf_id)
        )
        shelf = result.scalar_one_or_none()
        
        if shelf and shelf.display_label != display_label:
            shelf.display_label = display_label
            await self.db.flush()
            self._shelf_cache[cache_key] = shelf
    
    async def _get_or_create_location(self, parsed: Dict[str, Any], display_label: str = None) -> Optional[Location]:
        """
        获取或创建库位
        
        parsed: 解析后的库位信息
        display_label: 货架显示标识（可选）
        """
        full_code = f"{parsed['zone_code']}-{parsed['aisle_code']}-{parsed['shelf_code']}-{parsed['location_code']}"
        
        # 先检查缓存
        if full_code in self._location_cache:
            # 即使库位已存在，也需要更新货架的 display_label
            if display_label:
                location = self._location_cache[full_code]
                # 获取并更新货架的 display_label
                warehouse = await self._get_or_create_warehouse()
                zone = await self._get_or_create_zone(warehouse.id, parsed['zone_code'])
                aisle = await self._get_or_create_aisle(zone.id, parsed['aisle_code'])
                await self._get_or_create_shelf(aisle.id, parsed['shelf_code'], display_label=display_label)
            return self._location_cache[full_code]
        
        # 查询数据库
        result = await self.db.execute(
            select(Location).where(Location.full_code == full_code)
        )
        location = result.scalar_one_or_none()
        
        if location:
            self._location_cache[full_code] = location
            # 即使库位已存在，也需要更新货架的 display_label
            if display_label:
                warehouse = await self._get_or_create_warehouse()
                zone = await self._get_or_create_zone(warehouse.id, parsed['zone_code'])
                aisle = await self._get_or_create_aisle(zone.id, parsed['aisle_code'])
                await self._get_or_create_shelf(aisle.id, parsed['shelf_code'], display_label=display_label)
            return location
        
        # 需要创建库位，先确保上级结构存在
        warehouse = await self._get_or_create_warehouse()
        zone = await self._get_or_create_zone(warehouse.id, parsed['zone_code'])
        aisle = await self._get_or_create_aisle(zone.id, parsed['aisle_code'])
        
        # 计算货架需要的行列数
        row_index = ord(parsed['row_label']) - ord('A')
        col_index = parsed['column_number'] - 1
        
        # 货架至少需要能容纳当前库位
        min_rows = row_index + 1
        min_cols = parsed['column_number']
        
        shelf = await self._get_or_create_shelf(aisle.id, parsed['shelf_code'], max(4, min_rows), max(5, min_cols), display_label)
        
        # 检查库位是否已存在（货架可能已有）
        result = await self.db.execute(
            select(Location).where(Location.full_code == full_code)
        )
        location = result.scalar_one_or_none()
        
        if not location:
            # 创建库位
            location = Location(
                shelf_id=shelf.id,
                code=parsed['location_code'],
                full_code=full_code,
                row_label=parsed['row_label'],
                column_number=parsed['column_number'],
                row_index=row_index,
                column_index=col_index
            )
            self.db.add(location)
            await self.db.flush()
        
        self._location_cache[full_code] = location
        return location
    
    def _validate_columns(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, str], List[str]]:
        """
        验证 DataFrame 的列
        返回: (是否有效, 列映射, 错误列表)
        """
        column_mapping = {}
        errors = []
        
        # 检查必需列
        for field, possible_names in self.REQUIRED_COLUMNS.items():
            found_col = self._find_column(df, possible_names)
            if found_col:
                column_mapping[field] = found_col
            else:
                errors.append(f"缺少必需列: {field} (可用名称: {', '.join(possible_names)})")
        
        # 检查可选列
        for field, possible_names in self.OPTIONAL_COLUMNS.items():
            found_col = self._find_column(df, possible_names)
            if found_col:
                column_mapping[field] = found_col
        
        return len(errors) == 0, column_mapping, errors
    
    async def import_from_excel(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        从 Excel 文件导入数据
        
        返回:
        {
            "success": True/False,
            "total_rows": 总行数,
            "imported_rows": 成功导入行数,
            "failed_rows": 失败行数,
            "errors": [错误列表]
        }
        """
        try:
            # 读取 Excel
            df = pd.read_excel(BytesIO(file_content))
            return await self._process_dataframe(df, filename, "excel")
        except Exception as e:
            # 保存失败的导入记录
            await self._save_import_record(filename, "excel", 0, 0, 0, "failed", [f"读取 Excel 文件失败: {str(e)}"])
            return {
                "success": False,
                "total_rows": 0,
                "imported_rows": 0,
                "failed_rows": 0,
                "errors": [f"读取 Excel 文件失败: {str(e)}"]
            }
    
    async def import_from_csv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        从 CSV 文件导入数据
        """
        try:
            # 尝试不同编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                try:
                    df = pd.read_csv(BytesIO(file_content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                await self._save_import_record(filename, "csv", 0, 0, 0, "failed", ["无法解析 CSV 文件编码，请使用 UTF-8 或 GBK 编码"])
                return {
                    "success": False,
                    "total_rows": 0,
                    "imported_rows": 0,
                    "failed_rows": 0,
                    "errors": ["无法解析 CSV 文件编码，请使用 UTF-8 或 GBK 编码"]
                }
            
            return await self._process_dataframe(df, filename, "csv")
        except Exception as e:
            await self._save_import_record(filename, "csv", 0, 0, 0, "failed", [f"读取 CSV 文件失败: {str(e)}"])
            return {
                "success": False,
                "total_rows": 0,
                "imported_rows": 0,
                "failed_rows": 0,
                "errors": [f"读取 CSV 文件失败: {str(e)}"]
            }
    
    async def _save_import_record(
        self, 
        filename: str, 
        file_type: str, 
        total_rows: int, 
        success_rows: int, 
        failed_rows: int, 
        status: str, 
        errors: Optional[List[str]] = None
    ) -> ImportRecord:
        """保存导入记录"""
        record = ImportRecord(
            filename=filename,
            file_type=file_type,
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=failed_rows,
            status=status,
            errors=json.dumps(errors, ensure_ascii=False) if errors else None,
            import_time=datetime.now()  # 使用本地时间
        )
        self.db.add(record)
        await self.db.flush()
        return record
    
    async def get_import_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取导入历史记录"""
        result = await self.db.execute(
            select(ImportRecord)
            .order_by(desc(ImportRecord.import_time))
            .limit(limit)
        )
        records = result.scalars().all()
        
        return [
            {
                "id": r.id,
                "filename": r.filename,
                "file_type": r.file_type,
                "total_rows": r.total_rows,
                "success_rows": r.success_rows,
                "failed_rows": r.failed_rows,
                "status": r.status,
                "errors": json.loads(r.errors) if r.errors else None,
                "import_time": r.import_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
    
    async def _process_dataframe(self, df: pd.DataFrame, filename: str = "", file_type: str = "excel") -> Dict[str, Any]:
        """处理 DataFrame 并导入数据"""
        total_rows = len(df)
        
        # 验证列
        is_valid, column_mapping, validation_errors = self._validate_columns(df)
        if not is_valid:
            await self._save_import_record(filename, file_type, total_rows, 0, total_rows, "failed", validation_errors)
            await self.db.commit()
            return {
                "success": False,
                "total_rows": total_rows,
                "imported_rows": 0,
                "failed_rows": total_rows,
                "errors": validation_errors
            }
        
        # 重置缓存
        self._warehouse_cache = {}
        self._zone_cache = {}
        self._aisle_cache = {}
        self._shelf_cache = {}
        self._location_cache = {}
        
        # 清空旧的热力数据（每次导入前自动清除）
        from app.models.warehouse import LocationHeatData
        await self.db.execute(
            LocationHeatData.__table__.delete()
        )
        
        # 准备数据并导入
        row_errors = []
        imported_count = 0
        skipped_count = 0  # 跳过的行数（库位不存在）
        skipped_locations = set()  # 记录跳过的库位编码（用于去重统计）
        imported_dates = set()  # 记录导入数据的日期
        
        for idx, row in df.iterrows():
            try:
                # 解析日期
                date_value = row[column_mapping["date"]]
                date = self._parse_date(date_value)
                
                location_code = str(row[column_mapping["location_code"]]).strip()
                
                # 获取可选字段的值
                def get_optional_value(field: str, default=0):
                    col_name = column_mapping.get(field, "")
                    if col_name and col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val):
                            return val
                    return default
                
                # 获取显示标识（可选）
                display_label_value = get_optional_value("display_label", None)
                display_label = str(display_label_value).strip() if display_label_value and pd.notna(display_label_value) else None
                
                # 优先直接通过完整编码查找库位（避免解析可能导致的格式不匹配）
                location = await self._get_location_by_full_code(location_code)
                
                if not location:
                    # 如果直接查找失败，尝试解析并创建
                    parsed = self._parse_location_code(location_code)
                    if parsed:
                        location = await self._get_or_create_location(parsed, display_label)
                
                if not location:
                    # 库位不存在时跳过该行，不计入错误
                    skipped_count += 1
                    skipped_locations.add(location_code)
                    continue
                
                # 如果提供了显示标识，更新对应货架的 display_label
                if display_label and location.shelf_id:
                    await self._update_shelf_display_label(location.shelf_id, display_label)
                
                # 获取可选字段的值（重新定义以便后续使用）
                def get_optional_value(field: str, default=0):
                    col_name = column_mapping.get(field, "")
                    if col_name and col_name in row.index:
                        val = row[col_name]
                        if pd.notna(val):
                            return val
                    return default
                
                pick_frequency = int(get_optional_value("pick_frequency", 0) or 0)
                turnover_rate = float(get_optional_value("turnover_rate", 0) or 0)
                inventory_qty = int(get_optional_value("inventory_qty", 0) or 0)
                inbound_qty = int(get_optional_value("inbound_qty", 0) or 0)
                outbound_qty = int(get_optional_value("outbound_qty", 0) or 0)
                
                # 更新热度数据
                await self.heatmap_service.update_heat_data(
                    location_id=location.id,
                    date=date,
                    pick_frequency=pick_frequency,
                    turnover_rate=turnover_rate,
                    inventory_qty=inventory_qty,
                    inbound_qty=inbound_qty,
                    outbound_qty=outbound_qty
                )
                imported_count += 1
                imported_dates.add(date.strftime("%Y-%m-%d"))
                
            except Exception as e:
                row_errors.append(f"第 {idx + 2} 行处理失败: {str(e)}")
        
        # 确定状态（跳过的行不计入失败）
        actual_failed = len(row_errors)
        if imported_count == 0 and actual_failed > 0:
            status = "failed"
        elif actual_failed > 0:
            status = "partial"
        else:
            status = "success"
        
        # 生成跳过库位的提示信息
        skip_info = None
        if skipped_count > 0:
            skip_info = f"跳过 {skipped_count} 行（{len(skipped_locations)} 个库位不存在）"
        
        # 保存导入记录
        save_errors = row_errors.copy() if row_errors else []
        if skip_info:
            save_errors.insert(0, skip_info)
        
        await self._save_import_record(
            filename, file_type, total_rows, imported_count, 
            actual_failed, status, save_errors if save_errors else None
        )
        
        # 提交所有更改
        await self.db.commit()
        
        # 计算导入数据的日期范围
        date_range = None
        if imported_dates:
            sorted_dates = sorted(imported_dates)
            date_range = {
                "start_date": sorted_dates[0],
                "end_date": sorted_dates[-1]
            }
        
        # 构建返回的错误/提示信息
        return_messages = []
        if skip_info:
            return_messages.append(skip_info)
        if row_errors:
            return_messages.extend(row_errors)
        
        return {
            "success": imported_count > 0,
            "total_rows": total_rows,
            "imported_rows": imported_count,
            "skipped_rows": skipped_count,
            "failed_rows": actual_failed,
            "errors": return_messages if return_messages else None,
            "date_range": date_range
        }
    
    async def get_import_template_with_locations(self) -> pd.DataFrame:
        """
        获取导入模板（使用数据库中实际的库位编码）
        
        始终从数据库获取实际存在的库位编码，确保模板与数据库一致
        """
        from app.models.warehouse import Location
        
        # 查询数据库中的库位（取不同区域的库位作为示例，最多5个）
        result = await self.db.execute(
            select(Location)
            .where(Location.is_active == True)
            .order_by(Location.id)
            .limit(5)
        )
        locations = result.scalars().all()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if locations and len(locations) > 0:
            # 使用实际的库位编码
            location_codes = [loc.full_code for loc in locations]
            num_examples = len(location_codes)
            
            # 生成与库位数量匹配的示例数据
            return pd.DataFrame({
                "库位编码": location_codes,
                "日期": [today] * num_examples,
                "拣货频率": [100, 50, 80, 120, 90][:num_examples],
                "周转率": [0.8, 0.5, 0.6, 0.7, 0.4][:num_examples],
                "库存数量": [200, 100, 150, 180, 120][:num_examples],
                "入库数量": [50, 30, 40, 60, 35][:num_examples],
                "出库数量": [80, 40, 60, 70, 50][:num_examples],
                "显示标识": [loc.code for loc in locations],  # 使用库位简码作为显示标识示例
            })
        else:
            # 没有库位数据时返回提示性模板
            return pd.DataFrame({
                "库位编码": ["请先在系统中创建库位"],
                "日期": [today],
                "拣货频率": [0],
                "周转率": [0],
                "库存数量": [0],
                "入库数量": [0],
                "出库数量": [0],
                "显示标识": [""],
            })
