from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CameraFrame:
    source_id: str
    frame_path: Path


class FolderCameraIngestion:
    def __init__(self, source_id: str, folder: Path) -> None:
        self.source_id = source_id
        self.folder = folder

    def frames(self) -> Iterable[CameraFrame]:
        for path in sorted(self.folder.glob("*.jpg")):
            yield CameraFrame(source_id=self.source_id, frame_path=path)
