from ui.components.message_box import MessageBoxTypeEnum, CustomMessageBox
from utils.common import get_file_extension

def validate_file_extension(filename, ext, parent=None):
    if get_file_extension(filename) in ext:
        return True
    else:
        message_box = CustomMessageBox(
            "Warning",
            f"You have to choose the right file type ({' '.join(f'.{str(value)}' for value in ext)})",
            parent=parent,
            icon=MessageBoxTypeEnum.Warning.value
        )
        message_box.show()