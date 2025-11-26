'''
파일명: scratch_manager.py
최종 수정일: 2025-11-21
버전: v01
파일 개요: TTL 기반 Scratch Space 관리자 (임시 데이터 저장 및 자동 정리)
변경 이력:
	- 2025-11-21: v01 - 초기 생성 (Ephemeral Disk Cache with TTL Eviction)
'''
from pathlib import Path
import json
import shutil
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import uuid
import logging


class ScratchSpaceManager:
	"""
	TTL 기반 Scratch Space 관리자

	대용량 기후 데이터를 임시로 디스크에 저장하고,
	TTL(Time To Live) 기반으로 자동 정리하는 시스템

	특징:
	- 세션별 격리된 디렉토리 생성
	- 메타데이터 기반 TTL 관리
	- 다양한 포맷 지원 (JSON, NumPy, Pickle, NetCDF)
	- 자동 만료 및 정리

	사용 예시:
		manager = ScratchSpaceManager()
		session_id = manager.create_session(ttl_hours=4)
		manager.save_data(session_id, "climate.json", data, format="json")
		data = manager.load_data(session_id, "climate.json", format="json")
		manager.cleanup_expired()
	"""

	def __init__(self, base_path: str = "./scratch", default_ttl_hours: int = 24):
		"""
		ScratchSpaceManager 초기화

		Args:
			base_path: Scratch Space 기본 경로 (기본값: "./scratch")
			default_ttl_hours: 기본 TTL 시간 (기본값: 24시간)
		"""
		self.base_path = Path(base_path)
		self.base_path.mkdir(exist_ok=True)
		self.default_ttl = timedelta(hours=default_ttl_hours)
		self.logger = logging.getLogger(__name__)

		# .gitignore 파일 생성 (scratch 디렉토리는 git 추적 안 함)
		gitignore_path = self.base_path / ".gitignore"
		if not gitignore_path.exists():
			with open(gitignore_path, "w") as f:
				f.write("*\n!.gitignore\n")

	def create_session(
		self,
		session_id: Optional[str] = None,
		ttl_hours: Optional[int] = None,
		metadata: Optional[Dict[str, Any]] = None
	) -> str:
		"""
		새 분석 세션 디렉토리 생성

		Args:
			session_id: 세션 ID (기본값: 자동 생성 UUID)
			ttl_hours: TTL 시간 (기본값: default_ttl_hours)
			metadata: 추가 메타데이터 (선택)

		Returns:
			생성된 세션 ID
		"""
		session_id = session_id or str(uuid.uuid4())[:8]
		session_path = self.base_path / f"run_{session_id}"
		session_path.mkdir(exist_ok=True)

		# 메타데이터 저장
		ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
		now = datetime.now()
		expires_at = now + ttl

		session_metadata = {
			"session_id": session_id,
			"created_at": now.isoformat(),
			"expires_at": expires_at.isoformat(),
			"ttl_hours": ttl_hours or (self.default_ttl.total_seconds() / 3600),
			"files": [],
			"status": "active"
		}

		# 사용자 정의 메타데이터 병합
		if metadata:
			session_metadata.update(metadata)

		with open(session_path / "metadata.json", "w") as f:
			json.dump(session_metadata, f, indent=2, ensure_ascii=False)

		self.logger.info(f"Created scratch session: {session_id} (TTL: {ttl_hours or self.default_ttl.total_seconds() / 3600}h, Expires: {expires_at})")

		return session_id

	def get_session_path(self, session_id: str) -> Path:
		"""
		세션 디렉토리 경로 반환

		Args:
			session_id: 세션 ID

		Returns:
			세션 디렉토리 경로
		"""
		return self.base_path / f"run_{session_id}"

	def session_exists(self, session_id: str) -> bool:
		"""
		세션 존재 여부 확인

		Args:
			session_id: 세션 ID

		Returns:
			세션 존재 여부
		"""
		return self.get_session_path(session_id).exists()

	def get_metadata(self, session_id: str) -> Dict[str, Any]:
		"""
		세션 메타데이터 조회

		Args:
			session_id: 세션 ID

		Returns:
			메타데이터 딕셔너리
		"""
		metadata_file = self.get_session_path(session_id) / "metadata.json"

		if not metadata_file.exists():
			raise FileNotFoundError(f"Session metadata not found: {session_id}")

		with open(metadata_file) as f:
			return json.load(f)

	def update_metadata(self, session_id: str, updates: Dict[str, Any]):
		"""
		세션 메타데이터 업데이트

		Args:
			session_id: 세션 ID
			updates: 업데이트할 메타데이터 딕셔너리
		"""
		metadata = self.get_metadata(session_id)
		metadata.update(updates)

		metadata_file = self.get_session_path(session_id) / "metadata.json"
		with open(metadata_file, "w") as f:
			json.dump(metadata, f, indent=2, ensure_ascii=False)

	def save_data(
		self,
		session_id: str,
		filename: str,
		data: Any,
		format: str = "json"
	) -> str:
		"""
		데이터 저장

		Args:
			session_id: 세션 ID
			filename: 파일명
			data: 저장할 데이터
			format: 포맷 ("json", "numpy", "pickle", "netcdf")

		Returns:
			저장된 파일 경로
		"""
		session_path = self.get_session_path(session_id)

		if not session_path.exists():
			raise FileNotFoundError(f"Session not found: {session_id}")

		file_path = session_path / filename

		try:
			if format == "json":
				with open(file_path, "w", encoding="utf-8") as f:
					json.dump(data, f, indent=2, ensure_ascii=False)

			elif format == "numpy":
				import numpy as np
				np.save(file_path, data)

			elif format == "pickle":
				import pickle
				with open(file_path, "wb") as f:
					pickle.dump(data, f)

			elif format == "netcdf":
				# xarray 또는 netCDF4 사용
				if hasattr(data, 'to_netcdf'):
					data.to_netcdf(file_path)
				else:
					raise ValueError("Data must be xarray.Dataset or xarray.DataArray for netcdf format")

			else:
				raise ValueError(f"Unsupported format: {format}")

			# 메타데이터 업데이트 (파일 목록 추가)
			metadata = self.get_metadata(session_id)
			if "files" not in metadata:
				metadata["files"] = []

			file_info = {
				"filename": filename,
				"format": format,
				"saved_at": datetime.now().isoformat(),
				"size_bytes": file_path.stat().st_size
			}

			# 중복 제거 (같은 파일명이면 덮어쓰기)
			metadata["files"] = [f for f in metadata["files"] if f["filename"] != filename]
			metadata["files"].append(file_info)

			self.update_metadata(session_id, metadata)

			self.logger.debug(f"Saved {filename} ({format}) to session {session_id}")

			return str(file_path)

		except Exception as e:
			self.logger.error(f"Failed to save {filename} to session {session_id}: {e}")
			raise

	def load_data(
		self,
		session_id: str,
		filename: str,
		format: str = "json"
	) -> Any:
		"""
		데이터 로드

		Args:
			session_id: 세션 ID
			filename: 파일명
			format: 포맷 ("json", "numpy", "pickle", "netcdf")

		Returns:
			로드된 데이터
		"""
		file_path = self.get_session_path(session_id) / filename

		if not file_path.exists():
			raise FileNotFoundError(f"File not found: {file_path}")

		try:
			if format == "json":
				with open(file_path, encoding="utf-8") as f:
					return json.load(f)

			elif format == "numpy":
				import numpy as np
				return np.load(file_path, allow_pickle=True)

			elif format == "pickle":
				import pickle
				with open(file_path, "rb") as f:
					return pickle.load(f)

			elif format == "netcdf":
				import xarray as xr
				return xr.open_dataset(file_path)

			else:
				raise ValueError(f"Unsupported format: {format}")

		except Exception as e:
			self.logger.error(f"Failed to load {filename} from session {session_id}: {e}")
			raise

	def list_files(self, session_id: str) -> list:
		"""
		세션의 파일 목록 조회

		Args:
			session_id: 세션 ID

		Returns:
			파일 정보 리스트
		"""
		metadata = self.get_metadata(session_id)
		return metadata.get("files", [])

	def cleanup_expired(self, dry_run: bool = False) -> int:
		"""
		TTL 만료된 세션 정리

		Args:
			dry_run: True이면 실제 삭제 없이 목록만 반환 (기본값: False)

		Returns:
			정리된 세션 개수
		"""
		now = datetime.now()
		cleaned = 0

		for session_dir in self.base_path.glob("run_*"):
			metadata_file = session_dir / "metadata.json"

			if not metadata_file.exists():
				self.logger.warning(f"Metadata not found for session: {session_dir.name}, skipping")
				continue

			try:
				with open(metadata_file) as f:
					metadata = json.load(f)

				expires_at = datetime.fromisoformat(metadata["expires_at"])

				if now > expires_at:
					if dry_run:
						self.logger.info(f"[DRY RUN] Would clean expired session: {session_dir.name} (expired: {expires_at})")
					else:
						shutil.rmtree(session_dir)
						self.logger.info(f"🗑️  Cleaned expired session: {session_dir.name} (expired: {expires_at})")

					cleaned += 1

			except Exception as e:
				self.logger.error(f"Error processing session {session_dir.name}: {e}")
				continue

		if cleaned > 0:
			self.logger.info(f"Cleanup complete: {cleaned} session(s) removed")

		return cleaned

	def cleanup_session(self, session_id: str):
		"""
		특정 세션 즉시 삭제

		Args:
			session_id: 세션 ID
		"""
		session_path = self.get_session_path(session_id)

		if session_path.exists():
			shutil.rmtree(session_path)
			self.logger.info(f"🗑️  Deleted session: {session_id}")
		else:
			self.logger.warning(f"Session not found: {session_id}")

	def get_stats(self) -> Dict[str, Any]:
		"""
		Scratch Space 통계 조회

		Returns:
			통계 정보 딕셔너리
		"""
		sessions = list(self.base_path.glob("run_*"))
		total_sessions = len(sessions)

		total_size = 0
		active_sessions = 0
		expired_sessions = 0
		now = datetime.now()

		for session_dir in sessions:
			metadata_file = session_dir / "metadata.json"

			if metadata_file.exists():
				try:
					with open(metadata_file) as f:
						metadata = json.load(f)

					expires_at = datetime.fromisoformat(metadata["expires_at"])

					if now > expires_at:
						expired_sessions += 1
					else:
						active_sessions += 1
				except:
					pass

			# 디렉토리 크기 계산
			for file_path in session_dir.rglob("*"):
				if file_path.is_file():
					total_size += file_path.stat().st_size

		return {
			"total_sessions": total_sessions,
			"active_sessions": active_sessions,
			"expired_sessions": expired_sessions,
			"total_size_bytes": total_size,
			"total_size_mb": round(total_size / (1024 * 1024), 2),
			"base_path": str(self.base_path)
		}
