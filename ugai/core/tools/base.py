from dataclasses import dataclass
from typing import Callable
@dataclass(frozen=True)
class ToolSpec: name:str; handler:Callable; effects:tuple[str,...]=("read",); approval_required:bool=False
